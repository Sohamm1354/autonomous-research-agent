import httpx
from bs4 import BeautifulSoup
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from tavily import TavilyClient

from app.core.config import get_settings
from app.core.logger import logger
from app.core.exceptions import ToolError
from app.agent.prompts import SUMMARISE_PROMPT

settings = get_settings()
tavily   = TavilyClient(api_key=settings.tavily_api_key)


@tool
def web_search(query: str) -> list[dict]:
    """Search the web. Returns list of dicts with url, title, snippet."""
    try:
        results = tavily.search(
            query=query,
            max_results=settings.max_search_results,
            search_depth="advanced",
        )
        logger.info("web_search_ok", query=query,
                    num_results=len(results["results"]))
        return [
            {
                "url":     r["url"],
                "title":   r["title"],
                "snippet": r["content"],
            }
            for r in results["results"]
        ]
    except Exception as e:
        logger.error("web_search_failed", query=query, error=str(e))
        raise ToolError("web_search", str(e))


@tool
def scrape_url(url: str) -> str:
    """Fetch a URL and return cleaned body text."""
    try:
        with httpx.Client(timeout=12, follow_redirects=True) as client:
            resp = client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchAgent/1.0)"},
            )
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer",
                         "header", "aside", "form"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        text = " ".join(text.split())                  # collapse whitespace
        text = text[: settings.max_scrape_chars]

        logger.info("scrape_ok", url=url, chars=len(text))
        return text

    except httpx.TimeoutException:
        logger.warning("scrape_timeout", url=url)
        return "SCRAPE_FAILED: timeout"
    except httpx.HTTPStatusError as e:
        logger.warning("scrape_http_error", url=url,
                       status=e.response.status_code)
        return f"SCRAPE_FAILED: HTTP {e.response.status_code}"
    except Exception as e:
        logger.error("scrape_error", url=url, error=str(e))
        return f"SCRAPE_FAILED: {e}"


def summarise_text(
    text: str,
    context: str,
    callback_handler=None,
) -> str:
    """Compress scraped text to only facts relevant to the context question."""
    if text.startswith("SCRAPE_FAILED"):
        return "SOURCE_UNAVAILABLE"

    callbacks = [callback_handler] if callback_handler else []
    llm = ChatGroq(
        model=settings.summariser_model,
        temperature=0,
        api_key=settings.groq_api_key,
        callbacks=callbacks,
    )
    prompt = SUMMARISE_PROMPT.format(question=context, text=text)
    result = llm.invoke(prompt).content.strip()

    return "NO_RELEVANT_CONTENT" if result == "NO_RELEVANT_CONTENT" else result