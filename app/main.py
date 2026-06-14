from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.logger import setup_logging, logger
from app.api.routes import router
from app.api.middleware import register_middleware
from app.api.schemas import HealthResponse
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("server_starting", env=get_settings().app_env)
    yield
    logger.info("server_shutdown")


app = FastAPI(
    title="Autonomous Research Agent",
    description="Production-grade multi-step AI research agent with human-in-the-loop",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

register_middleware(app)
app.include_router(router)


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    return HealthResponse(
        status="ok",
        version="1.0.0",
        model=get_settings().planner_model,
    )