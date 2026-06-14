# Autonomous Research Agent

Production-grade AI research agent built with LangGraph, Groq (Llama 3.1),
FastAPI, and Tavily. Takes a research question, plans sub-queries, searches
the web, scrapes sources, and produces a cited markdown report.

## Tech stack
- **LLM**: Groq llama-3.1-8b-instant (free)
- **Orchestration**: LangGraph
- **Search**: Tavily API (free tier)
- **API**: FastAPI + Uvicorn

## Setup

    python -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env   # fill in your API keys

## Run from terminal

    python scripts/run_agent.py "Your research question here"

## Run as API server

    uvicorn app.main:app --reload --port 8000

Then open: http://localhost:8000/docs

## API usage

1. POST /research/start      → returns sub-queries
2. POST /research/approve    → runs agent, returns full report

## Run tests

    pytest tests/ -v