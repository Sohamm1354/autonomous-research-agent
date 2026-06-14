import uuid
import time
import asyncio
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.agent.graph import agent_graph
from app.agent.state import AgentState
from app.api.schemas import (
    StartRequest, StartResponse,
    ApprovalRequest, ReportResponse,
    HistoryListResponse, HistoryDetail, DeleteResponse,
)
from app.core.logger import logger
from app.core.exceptions import PlannerError
from app.core.history_store import history_store

router = APIRouter(prefix="/research", tags=["Research Agent"])


# ── Helpers ────────────────────────────────────────────────────

def _empty_state(question: str, run_id: str) -> dict:
    return {
        "question":        question,
        "sub_queries":     [],
        "plan_approved":   False,
        "search_results":  [],
        "failed_urls":     [],
        "final_report":    "",
        "reflection":      "",
        "run_id":          run_id,
        "total_tokens":    0,
        "total_cost_usd":  0.0,
        "elapsed_seconds": 0.0,
        "messages":        [],
    }


def _send(event_type: str, message: str, **kwargs) -> str:
    """Format a server-sent event."""
    payload = {"type": event_type, "message": message, **kwargs}
    return f"data: {json.dumps(payload)}\n\n"


# ── Start ──────────────────────────────────────────────────────

@router.post("/start", response_model=StartResponse)
async def start_research(req: StartRequest):
    """
    Step 1 — Run the planner node.
    Returns sub-queries for human review before any web requests are made.
    """
    thread_id = str(uuid.uuid4())
    config    = {"configurable": {"thread_id": thread_id}}

    logger.info("api_start", thread_id=thread_id, question=req.question)

    try:
        def _invoke():
            for _ in agent_graph.stream(
                _empty_state(req.question, thread_id),
                config,
                stream_mode="values",
            ):
                pass

        await asyncio.to_thread(_invoke)

        snapshot    = agent_graph.get_state(config)
        sub_queries = snapshot.values.get("sub_queries", [])

    except PlannerError as e:
        logger.error("planner_error", error=str(e))
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("start_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

    return StartResponse(thread_id=thread_id, sub_queries=sub_queries)


# ── Approve ────────────────────────────────────────────────────

@router.post("/approve", response_model=ReportResponse)
async def approve_and_run(req: ApprovalRequest):
    """
    Step 2 — Approve the plan and run the full agent.
    Runs tools → writer → reflection and returns the complete report.
    """
    if not req.approved:
        raise HTTPException(status_code=400, detail="Plan rejected by user.")

    config = {"configurable": {"thread_id": req.thread_id}}
    start  = time.time()

    # Update checkpointed state with approval
    update = {"plan_approved": True}
    if req.revised_queries:
        update["sub_queries"] = req.revised_queries

    agent_graph.update_state(config, update)

    final_state = None

    def _resume():
        nonlocal final_state
        for event in agent_graph.stream(
            None,
            config,
            stream_mode="values",
        ):
            final_state = event

    # Retry up to 3 times on Groq rate limit errors
    last_error = None
    for attempt in range(3):
        try:
            await asyncio.to_thread(_resume)
            break
        except Exception as e:
            last_error = e
            if "429" in str(e) or "rate_limit" in str(e).lower():
                wait = 30 * (attempt + 1)
                logger.warning("rate_limit_retry",
                               attempt=attempt + 1,
                               waiting_seconds=wait)
                await asyncio.sleep(wait)
            else:
                logger.error("approve_error", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(
            status_code=429,
            detail="Groq rate limit exceeded after 3 retries. Wait 60 seconds and try again."
        )

    # Fallback — read directly from checkpoint
    if not final_state:
        final_state = agent_graph.get_state(config).values

    elapsed = round(time.time() - start, 2)

    # Save completed run to history
    entry = history_store.save(
        question=final_state.get("question", ""),
        final_report=final_state.get("final_report", ""),
        reflection=final_state.get("reflection", ""),
        failed_urls=final_state.get("failed_urls", []),
        elapsed_sec=elapsed,
        source_count=len(final_state.get("search_results", [])),
        sub_queries=final_state.get("sub_queries", []),
    )

    logger.info("api_done",
                thread_id=req.thread_id,
                elapsed=elapsed,
                history_id=entry.id)

    return ReportResponse(
        thread_id=req.thread_id,
        question=final_state.get("question", ""),
        final_report=final_state.get("final_report", ""),
        reflection=final_state.get("reflection", ""),
        failed_urls=final_state.get("failed_urls", []),
        elapsed_sec=elapsed,
        total_tokens=final_state.get("total_tokens", 0),
        cost_usd=0.0,
        history_id=entry.id,
    )


# ── Streaming progress ─────────────────────────────────────────

@router.get("/stream/{thread_id}", tags=["Research Agent"])
async def stream_progress(thread_id: str):
    """
    SSE endpoint — streams live agent progress to the frontend.
    Connect after calling /approve to get real-time step updates.
    """
    async def event_generator():
        config = {"configurable": {"thread_id": thread_id}}

        yield _send("connected", "Connected to agent stream")

        try:
            prev_sources  = 0
            prev_report   = ""
            prev_reflect  = ""

            def _stream_events():
                results = []
                for event in agent_graph.stream(
                    None,
                    config,
                    stream_mode="values",
                ):
                    results.append(event)
                return results

            events = await asyncio.to_thread(_stream_events)

            for event in events:
                sources = event.get("search_results", [])
                report  = event.get("final_report", "")
                reflect = event.get("reflection", "")

                # Tools node completed
                if len(sources) > prev_sources:
                    prev_sources = len(sources)
                    yield _send(
                        "tools_done",
                        f"Scraped {len(sources)} sources successfully",
                        count=len(sources),
                    )
                    await asyncio.sleep(0.1)

                # Writer node completed
                if report and report != prev_report:
                    prev_report = report
                    yield _send(
                        "writer_done",
                        "Report written successfully",
                        report=report,
                    )
                    await asyncio.sleep(0.1)

                # Reflection node completed
                if reflect and reflect != prev_reflect:
                    prev_reflect = reflect
                    yield _send(
                        "reflection_done",
                        reflect,
                        reflection=reflect,
                    )
                    await asyncio.sleep(0.1)

            yield _send("done", "Research complete")

        except Exception as e:
            logger.error("stream_error", thread_id=thread_id, error=str(e))
            if "429" in str(e) or "rate_limit" in str(e).lower():
                yield _send("error",
                    "Groq rate limit hit. Please wait 60 seconds and try again.")
            else:
                yield _send("error", f"Agent error: {str(e)}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "Connection":        "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


# ── History ────────────────────────────────────────────────────

@router.get("/history", response_model=HistoryListResponse, tags=["History"])
async def get_history():
    """Get all past research runs, newest first."""
    entries = history_store.get_all()
    return HistoryListResponse(entries=entries, total=len(entries))


@router.get("/history/{entry_id}", response_model=HistoryDetail, tags=["History"])
async def get_history_entry(entry_id: str):
    """Get full details of a single past research run."""
    entry = history_store.get_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="History entry not found.")
    return HistoryDetail(**entry.to_dict())


@router.delete("/history/{entry_id}", response_model=DeleteResponse, tags=["History"])
async def delete_history_entry(entry_id: str):
    """Delete a single history entry."""
    deleted = history_store.delete_by_id(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="History entry not found.")
    return DeleteResponse(deleted=True, message="Entry deleted.")


@router.delete("/history", response_model=DeleteResponse, tags=["History"])
async def delete_all_history():
    """Delete all history entries."""
    count = history_store.delete_all()
    return DeleteResponse(
        deleted=True,
        message=f"Deleted {count} entries."
    )