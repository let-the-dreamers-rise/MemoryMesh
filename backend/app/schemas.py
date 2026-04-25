from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SourceType = Literal["all", "note", "pdf", "bookmark", "screenshot"]
SearchMode = Literal["second_brain", "emotional_memory", "idea_search", "decision_trail"]


class IngestTextRequest(BaseModel):
    title: str = Field(default="Untitled memory", min_length=1, max_length=160)
    text: str = Field(min_length=1)
    source_type: Literal["note", "pdf", "bookmark", "screenshot"] = "note"
    tags: list[str] = Field(default_factory=list)


class IngestResponse(BaseModel):
    document_id: str
    title: str
    source_type: str
    chunks_added: int
    tags: list[str]


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    source_type: SourceType = "all"
    tag: str | None = None
    mode: SearchMode = "second_brain"
    limit: int = Field(default=8, ge=1, le=20)


class MemoryResult(BaseModel):
    id: str
    document_id: str
    title: str
    source_type: str
    text: str
    snippet: str
    score: float
    tags: list[str]
    created_at: datetime
    channel: str = "hybrid"


class SearchDiagnostics(BaseModel):
    backend: str
    collection: str
    semantic_results: int
    keyword_results: int
    fused_results: int
    filter_applied: str
    fusion: str
    latency_ms: int


class SearchResponse(BaseModel):
    query: str
    answer: str
    results: list[MemoryResult]
    connections: list[MemoryResult]
    diagnostics: SearchDiagnostics


class StatsResponse(BaseModel):
    backend: str
    collection: str
    connected: bool
    total_chunks: int
    source_counts: dict[str, int]
    embedding_mode: str
    vector_dimension: int
    advanced_features: list[str]
    vde_state: str | None = None
    note: str | None = None
