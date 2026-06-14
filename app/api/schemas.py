from pydantic import BaseModel, Field
from typing import Optional, List


class StartRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="The research question to investigate",
    )


class StartResponse(BaseModel):
    thread_id:   str
    sub_queries: List[str]
    message:     str = "Plan ready. Review sub-queries and approve."


class ApprovalRequest(BaseModel):
    thread_id:       str
    approved:        bool
    revised_queries: Optional[List[str]] = None


class ReportResponse(BaseModel):
    thread_id:    str
    question:     str
    final_report: str
    reflection:   str
    failed_urls:  List[str]
    elapsed_sec:  float
    total_tokens: int
    cost_usd:     float
    history_id:   Optional[str] = None   # ← new


class HealthResponse(BaseModel):
    status:  str
    version: str
    model:   str


# ── History schemas ────────────────────────────────────────────
class HistoryPreview(BaseModel):
    id:           str
    question:     str
    created_at:   str
    elapsed_sec:  float
    source_count: int
    preview:      str


class HistoryDetail(BaseModel):
    id:           str
    question:     str
    final_report: str
    reflection:   str
    failed_urls:  List[str]
    elapsed_sec:  float
    source_count: int
    created_at:   str
    sub_queries:  List[str]


class HistoryListResponse(BaseModel):
    entries: List[HistoryPreview]
    total:   int


class DeleteResponse(BaseModel):
    deleted: bool
    message: str