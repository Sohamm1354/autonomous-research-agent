"""
In-memory history store for research runs.
In production you would replace this with a database (PostgreSQL, SQLite etc.)
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class HistoryEntry:
    id:            str
    question:      str
    final_report:  str
    reflection:    str
    failed_urls:   List[str]
    elapsed_sec:   float
    source_count:  int
    created_at:    str  # ISO format string
    sub_queries:   List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_preview(self) -> dict:
        """Short version for sidebar list — no full report."""
        return {
            "id":           self.id,
            "question":     self.question,
            "created_at":   self.created_at,
            "elapsed_sec":  self.elapsed_sec,
            "source_count": self.source_count,
            "preview":      self.final_report[:200] + "…" if len(self.final_report) > 200 else self.final_report,
        }


class HistoryStore:
    def __init__(self):
        self._store: Dict[str, HistoryEntry] = {}

    def save(
        self,
        question:     str,
        final_report: str,
        reflection:   str,
        failed_urls:  List[str],
        elapsed_sec:  float,
        source_count: int,
        sub_queries:  List[str] = [],
    ) -> HistoryEntry:
        entry = HistoryEntry(
            id=str(uuid.uuid4()),
            question=question,
            final_report=final_report,
            reflection=reflection,
            failed_urls=failed_urls,
            elapsed_sec=elapsed_sec,
            source_count=source_count,
            created_at=datetime.utcnow().isoformat() + "Z",
            sub_queries=sub_queries,
        )
        self._store[entry.id] = entry
        return entry

    def get_all(self) -> List[dict]:
        """Return all entries as previews, newest first."""
        entries = sorted(
            self._store.values(),
            key=lambda e: e.created_at,
            reverse=True,
        )
        return [e.to_preview() for e in entries]

    def get_by_id(self, entry_id: str) -> Optional[HistoryEntry]:
        return self._store.get(entry_id)

    def delete_by_id(self, entry_id: str) -> bool:
        if entry_id in self._store:
            del self._store[entry_id]
            return True
        return False

    def delete_all(self) -> int:
        count = len(self._store)
        self._store.clear()
        return count

    def count(self) -> int:
        return len(self._store)


# Single instance shared across all requests
history_store = HistoryStore()