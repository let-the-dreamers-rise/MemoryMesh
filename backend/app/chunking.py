from __future__ import annotations

import re
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone


STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "and",
    "are",
    "because",
    "been",
    "before",
    "between",
    "but",
    "can",
    "could",
    "from",
    "had",
    "has",
    "have",
    "into",
    "just",
    "like",
    "more",
    "not",
    "that",
    "the",
    "their",
    "then",
    "there",
    "this",
    "was",
    "were",
    "what",
    "when",
    "where",
    "with",
    "would",
    "your",
}


@dataclass(slots=True)
class MemoryChunk:
    id: str
    document_id: str
    title: str
    source_type: str
    text: str
    chunk_index: int
    tags: list[str]
    created_at: datetime

    def payload(self) -> dict:
        tags_flat = " ".join(self.tags)
        return {
            "document_id": self.document_id,
            "title": self.title,
            "source_type": self.source_type,
            "text": self.text,
            "chunk_index": self.chunk_index,
            "tags": self.tags,
            "tags_flat": tags_flat,
            "created_at": self.created_at.isoformat(),
            "created_day": self.created_at.date().isoformat(),
        }


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower())


def extract_tags(text: str, manual_tags: list[str] | None = None, limit: int = 7) -> list[str]:
    manual = [tag.strip().lower() for tag in (manual_tags or []) if tag.strip()]
    counts = Counter(token for token in tokenize(text) if token not in STOPWORDS)
    auto = [word for word, _ in counts.most_common(limit * 2)]
    tags: list[str] = []
    for tag in manual + auto:
        if tag not in tags:
            tags.append(tag)
        if len(tags) >= limit:
            break
    return tags


def keyword_intent(query: str) -> str:
    terms = [token for token in tokenize(query) if token not in STOPWORDS]
    if not terms:
        return query
    weighted = " ".join(terms + terms[:4])
    return f"{query}. Keyword memory signals: {weighted}"


def chunk_document(
    *,
    title: str,
    text: str,
    source_type: str,
    tags: list[str] | None = None,
    created_at: datetime | str | None = None,
    chunk_size: int = 850,
    overlap: int = 140,
) -> list[MemoryChunk]:
    clean = normalize_whitespace(text)
    if not clean:
        return []

    document_id = str(uuid.uuid4())
    created_dt = _resolve_created_at(created_at)
    base_tags = extract_tags(clean, tags)
    chunks: list[MemoryChunk] = []
    start = 0
    index = 0

    while start < len(clean):
        end = min(start + chunk_size, len(clean))
        if end < len(clean):
            boundary = clean.rfind(" ", start, end)
            if boundary > start + int(chunk_size * 0.55):
                end = boundary

        chunk_text = clean[start:end].strip()
        if chunk_text:
            chunk_tags = extract_tags(chunk_text, base_tags)
            chunks.append(
                MemoryChunk(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    title=title.strip() or "Untitled memory",
                    source_type=source_type,
                    text=chunk_text,
                    chunk_index=index,
                    tags=chunk_tags,
                    created_at=created_dt,
                )
            )
            index += 1

        if end >= len(clean):
            break
        start = max(0, end - overlap)

    return chunks


def _resolve_created_at(value: datetime | str | None) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def make_snippet(text: str, query: str, size: int = 260) -> str:
    clean = normalize_whitespace(text)
    tokens = tokenize(query)
    first_hit = min(
        [clean.lower().find(token) for token in tokens if clean.lower().find(token) >= 0]
        or [0]
    )
    start = max(0, first_hit - size // 3)
    end = min(len(clean), start + size)
    snippet = clean[start:end].strip()
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(clean) else ""
    return f"{prefix}{snippet}{suffix}"
