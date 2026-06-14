import json
import asyncio
from langchain_groq import ChatGroq

from app.core.config import get_settings
from app.core.logger import logger
from app.core.exceptions import PlannerError, WriterError
from app.core.cost_tracker import RunCost
from app.agent.state import AgentState
from app.agent.prompts import (
    PLANNER_PROMPT,
    WRITER_PROMPT,
    REFLECTION_PROMPT,
)
from app.agent.tools import web_search, scrape_url, summarise_text
from app.agent.callbacks import CostTrackingCallback

settings = get_settings()


# ── helpers ────────────────────────────────────────────────────────────────

def _make_llm(model: str, run_cost: RunCost):
    cb  = CostTrackingCallback(run_cost)
    llm = ChatGroq(
        model=model,
        temperature=0,
        api_key=settings.groq_api_key,
        callbacks=[cb],
    )
    return llm, cb


def _extract_json_array(raw: str) -> list:
    """
    Llama 3.1 sometimes prepends explanation before JSON.
    Finds the first [ ... ] block and parses it.
    """
    raw   = raw.replace("```json", "").replace("```", "").strip()
    start = raw.find("[")
    end   = raw.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON array found in: {raw[:200]}")
    return json.loads(raw[start:end])


# ── planner ────────────────────────────────────────────────────────────────

def planner_node(state: AgentState) -> dict:
    logger.info("planner_start", question=state["question"])
    run_cost = RunCost()
    llm, _   = _make_llm(settings.planner_model, run_cost)

    prompt = PLANNER_PROMPT.format(
        question=state["question"],
        num_queries=4,
    )

    raw = llm.invoke(prompt).content.strip()
    logger.debug("planner_raw_response", raw=raw[:300])

    try:
        sub_queries = _extract_json_array(raw)
        if not isinstance(sub_queries, list) or len(sub_queries) < 2:
            raise ValueError("Need at least 2 sub-queries")
    except Exception as e:
        raise PlannerError(f"Could not parse sub-queries: {e}")

    logger.info("planner_done",
                sub_queries=sub_queries,
                tokens=run_cost.total_tokens)

    return {
        "sub_queries":   sub_queries,
        "plan_approved": False,
    }


# ── tools (sync wrapper around async logic) ────────────────────────────────

def tools_node(state: AgentState) -> dict:
    """Synchronous entry point — LangGraph calls this directly."""
    return asyncio.run(_tools_node_async(state))


async def _tools_node_async(state: AgentState) -> dict:
    logger.info("tools_start", num_queries=len(state["sub_queries"]))

    run_cost     = RunCost()
    cb           = CostTrackingCallback(run_cost)
    failed_urls: list[str] = []

    async def safe_summarise(text: str, context: str) -> str:
        """Summarise with retry on rate limit."""
        for attempt in range(4):
            try:
                return summarise_text(text, context, cb)
            except Exception as e:
                if "429" in str(e) or "rate_limit" in str(e).lower():
                    wait = 20 * (attempt + 1)
                    logger.warning("summarise_rate_limit",
                                   attempt=attempt + 1,
                                   waiting_seconds=wait)
                    await asyncio.sleep(wait)
                else:
                    logger.error("summarise_error", error=str(e))
                    return "SOURCE_UNAVAILABLE"
        return "SOURCE_UNAVAILABLE"

    async def process_query(query: str) -> list[dict]:
        results = web_search.invoke({"query": query})
        items   = []
        for r in results[:1]:   # 1 URL per query to save tokens
            text       = scrape_url.invoke({"url": r["url"]})
            summary    = await safe_summarise(text, state["question"])
            scraped_ok = not text.startswith("SCRAPE_FAILED")
            if not scraped_ok:
                failed_urls.append(r["url"])
            items.append({
                "query":      query,
                "url":        r["url"],
                "title":      r["title"],
                "summary":    summary,
                "scraped_ok": scraped_ok,
            })
            # Wait between summarise calls
            await asyncio.sleep(12)
        return items

    all_results: list[dict] = []

    # Process one query at a time with pause between each
    for i, query in enumerate(state["sub_queries"]):
        logger.info("processing_query",
                    num=i + 1,
                    total=len(state["sub_queries"]),
                    query=query)
        try:
            result = await process_query(query)
            all_results.extend(result)
        except Exception as e:
            logger.error("query_failed", query=query, error=str(e))

        if i < len(state["sub_queries"]) - 1:
            logger.info("inter_query_pause", seconds=15)
            await asyncio.sleep(15)

    useful = [
        r for r in all_results
        if r["summary"] not in ("SOURCE_UNAVAILABLE", "NO_RELEVANT_CONTENT")
    ]

    logger.info("tools_done",
                total=len(all_results),
                useful=len(useful),
                failed=len(failed_urls),
                tokens=run_cost.total_tokens)

    return {
        "search_results": useful,
        "failed_urls":    failed_urls,
    }

# ── writer ─────────────────────────────────────────────────────────────────

def writer_node(state: AgentState) -> dict:
    logger.info("writer_start", num_sources=len(state["search_results"]))

    if not state["search_results"]:
        raise WriterError("No usable sources — cannot write report.")

    run_cost = RunCost()
    llm, _   = _make_llm(settings.writer_model, run_cost)

    sources_block = "\n\n".join([
        f"[{i+1}] {r['title']} ({r['url']})\n{r['summary']}"
        for i, r in enumerate(state["search_results"])
    ])

    prompt = WRITER_PROMPT.format(
        question=state["question"],
        sources=sources_block,
    )
    report = llm.invoke(prompt).content

    logger.info("writer_done",
                chars=len(report),
                tokens=run_cost.total_tokens)

    return {"final_report": report}


# ── reflection ─────────────────────────────────────────────────────────────

def reflection_node(state: AgentState) -> dict:
    logger.info("reflection_start")

    run_cost = RunCost()
    llm, _   = _make_llm(settings.summariser_model, run_cost)

    prompt = REFLECTION_PROMPT.format(report=state["final_report"])
    raw    = llm.invoke(prompt).content.strip()

    try:
        gaps       = _extract_json_array(raw)
        reflection = "Research gaps identified: " + "; ".join(gaps)
    except Exception:
        reflection = "Reflection parsing failed."

    logger.info("reflection_done", reflection=reflection)
    return {"reflection": reflection}