import pytest
from unittest.mock import patch, MagicMock
from app.agent.tools import scrape_url, summarise_text


def test_scrape_url_returns_text():
    with patch("app.agent.tools.httpx.Client") as mock_client:
        mock_resp = MagicMock()
        mock_resp.text = "<html><body><p>Hello world content here.</p></body></html>"
        mock_resp.raise_for_status = MagicMock()
        mock_client.return_value.__enter__.return_value.get.return_value = mock_resp

        result = scrape_url.invoke({"url": "https://example.com"})
        assert "Hello world content here" in result


def test_scrape_url_handles_timeout():
    import httpx
    with patch("app.agent.tools.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.side_effect = \
            httpx.TimeoutException("timeout")
        result = scrape_url.invoke({"url": "https://slow-site.com"})
        assert result.startswith("SCRAPE_FAILED")


def test_summarise_skips_failed_scrape():
    result = summarise_text("SCRAPE_FAILED: timeout", "some question")
    assert result == "SOURCE_UNAVAILABLE"


def test_summarise_calls_llm():
    with patch("app.agent.tools.ChatGroq") as mock_groq:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "Summary of the text."
        mock_groq.return_value = mock_llm

        result = summarise_text("Some long article text here...", "What is AI?")
        assert result == "Summary of the text."