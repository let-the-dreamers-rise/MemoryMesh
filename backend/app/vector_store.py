from __future__ import annotations

import math
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .chunking import MemoryChunk, make_snippet
from .schemas import MemoryResult


@dataclass(slots=True)
class SearchBundle:
    hits: list[MemoryResult]
    semantic_count: int
    keyword_count: int
    fusion: str


def cosine_similarity(a: list[float], b: list[float]) -> float:
    total = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in b)) or 1.0
    return total / (norm_a * norm_b)


def parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def rrf_merge(
    result_sets: list[list[MemoryResult]],
    *,
    limit: int,
    weights: list[float] | None = None,
    ranking_constant: int = 60,
) -> list[MemoryResult]:
    weights = weights or [1.0] * len(result_sets)
    scores: dict[str, float] = {}
    objects: dict[str, MemoryResult] = {}

    for set_index, results in enumerate(result_sets):
        weight = weights[set_index] if set_index < len(weights) else 1.0
        for rank, item in enumerate(results, start=1):
            scores[item.id] = scores.get(item.id, 0.0) + weight / (ranking_constant + rank)
            objects.setdefault(item.id, item)

    merged = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)[:limit]
    output: list[MemoryResult] = []
    for item_id, score in merged:
        item = objects[item_id].model_copy(update={"score": round(float(score), 6), "channel": "rrf_hybrid"})
        output.append(item)
    return output


class InMemoryStore:
    """Fallback store that keeps the UI demo alive if Actian is not running."""

    backend_name = "in-memory fallback"

    def __init__(self, collection: str) -> None:
        self.collection = collection
        self._items: dict[str, tuple[MemoryChunk, dict[str, list[float]]]] = {}

    @property
    def connected(self) -> bool:
        return True

    def reset(self) -> None:
        self._items.clear()

    def upsert(self, chunks: list[MemoryChunk], vector_records: list[dict[str, list[float]]]) -> None:
        for chunk, vector_record in zip(chunks, vector_records):
            self._items[chunk.id] = (chunk, vector_record)

    def hybrid_search(
        self,
        *,
        query: str,
        dense_vector: list[float],
        keyword_vector: list[float],
        source_type: str = "all",
        tag: str | None = None,
        limit: int = 8,
    ) -> SearchBundle:
        dense = self._search_vector(
            query=query,
            vector=dense_vector,
            vector_name="semantic",
            source_type=source_type,
            tag=tag,
            limit=max(limit * 4, 20),
            channel="semantic",
        )
        keyword = self._search_vector(
            query=query,
            vector=keyword_vector,
            vector_name="intent",
            source_type=source_type,
            tag=tag,
            limit=max(limit * 4, 20),
            channel="keyword_intent",
        )
        fused = rrf_merge([dense, keyword], limit=limit, weights=[0.72, 0.28])
        return SearchBundle(
            hits=fused,
            semantic_count=len(dense),
            keyword_count=len(keyword),
            fusion="local RRF fallback",
        )

    def connections(
        self,
        *,
        query: str,
        vector: list[float],
        exclude_ids: set[str],
        limit: int = 5,
    ) -> list[MemoryResult]:
        results = self._search_vector(
            query=query,
            vector=vector,
            vector_name="semantic",
            source_type="all",
            tag=None,
            limit=limit + len(exclude_ids) + 4,
            channel="connection",
        )
        return [item for item in results if item.id not in exclude_ids][:limit]

    def count(self) -> int:
        return len(self._items)

    def source_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for chunk, _ in self._items.values():
            counts[chunk.source_type] = counts.get(chunk.source_type, 0) + 1
        counts["all"] = len(self._items)
        return counts

    def stats_note(self) -> str:
        return "Actian is not connected; start VectorAI DB and install the beta wheel for the judged run."

    def _search_vector(
        self,
        *,
        query: str,
        vector: list[float],
        vector_name: str,
        source_type: str,
        tag: str | None,
        limit: int,
        channel: str,
    ) -> list[MemoryResult]:
        scored: list[MemoryResult] = []
        tag_value = tag.strip().lower() if tag else None
        for chunk, stored_vectors in self._items.values():
            if source_type != "all" and chunk.source_type != source_type:
                continue
            if tag_value and tag_value not in chunk.tags:
                continue
            stored_vector = stored_vectors.get(vector_name) or stored_vectors.get("semantic")
            if stored_vector is None:
                continue
            score = cosine_similarity(vector, stored_vector)
            scored.append(_chunk_to_result(chunk, score, query, channel))
        return sorted(scored, key=lambda item: item.score, reverse=True)[:limit]


class ActianStore:
    backend_name = "Actian VectorAI DB"

    def __init__(self, url: str, collection: str, dimension: int) -> None:
        self.url = url
        self.collection = collection
        self.dimension = dimension
        self.client = None
        self._connect()
        self._ensure_collection()

    @property
    def connected(self) -> bool:
        return self.client is not None

    def _connect(self) -> None:
        from actian_vectorai import VectorAIClient

        self.client = VectorAIClient(self.url, timeout=20.0)
        self.client.connect()

    def _ensure_collection(self) -> None:
        from actian_vectorai import Distance, HnswConfigDiff, VectorParams

        assert self.client is not None
        if not self.client.collections.exists(self.collection):
            self.client.collections.create(
                self.collection,
                vectors_config={
                    "semantic": VectorParams(size=self.dimension, distance=Distance.Cosine),
                    "intent": VectorParams(size=self.dimension, distance=Distance.Cosine),
                },
                hnsw_config=HnswConfigDiff(m=32, ef_construct=256),
            )
        try:
            self.client.vde.open_collection(self.collection)
        except Exception:
            pass

    def reset(self) -> None:
        assert self.client is not None
        if self.client.collections.exists(self.collection):
            self.client.collections.delete(self.collection)
        self._ensure_collection()

    def upsert(self, chunks: list[MemoryChunk], vector_records: list[dict[str, list[float]]]) -> None:
        from actian_vectorai import PointStruct

        assert self.client is not None
        points = [
            PointStruct(id=chunk.id, vector=vector_record, payload=chunk.payload())
            for chunk, vector_record in zip(chunks, vector_records)
        ]
        if points:
            self.client.points.upsert(self.collection, points)
            try:
                self.client.vde.flush(self.collection)
            except Exception:
                pass

    def hybrid_search(
        self,
        *,
        query: str,
        dense_vector: list[float],
        keyword_vector: list[float],
        source_type: str = "all",
        tag: str | None = None,
        limit: int = 8,
    ) -> SearchBundle:
        assert self.client is not None
        search_limit = max(limit * 4, 20)
        filter_query = self._build_filter(source_type, tag)
        dense_raw = self.client.points.search(
            self.collection,
            vector=dense_vector,
            using="semantic",
            limit=search_limit,
            filter=filter_query,
        )
        keyword_raw = self.client.points.search(
            self.collection,
            vector=keyword_vector,
            using="intent",
            limit=search_limit,
            filter=filter_query,
        )
        dense = [_point_to_result(point, query, "semantic") for point in dense_raw]
        keyword = [_point_to_result(point, query, "keyword_intent") for point in keyword_raw]

        fused = self._actian_rrf(dense_raw, keyword_raw, query, limit)
        if not fused:
            fused = rrf_merge([dense, keyword], limit=limit, weights=[0.72, 0.28])

        return SearchBundle(
            hits=fused,
            semantic_count=len(dense_raw),
            keyword_count=len(keyword_raw),
            fusion="Actian SDK Reciprocal Rank Fusion",
        )

    def connections(
        self,
        *,
        query: str,
        vector: list[float],
        exclude_ids: set[str],
        limit: int = 5,
    ) -> list[MemoryResult]:
        assert self.client is not None
        raw = self.client.points.search(
            self.collection,
            vector=vector,
            using="semantic",
            limit=limit + len(exclude_ids) + 6,
        )
        results = [_point_to_result(point, query, "connection") for point in raw]
        return [item for item in results if item.id not in exclude_ids][:limit]

    def count(self) -> int:
        assert self.client is not None
        return int(self.client.points.count(self.collection))

    def source_counts(self) -> dict[str, int]:
        from actian_vectorai import Field, FilterBuilder

        assert self.client is not None
        counts = {"all": self.count()}
        for source_type in ("note", "pdf", "bookmark", "screenshot"):
            try:
                filter_query = FilterBuilder().must(Field("source_type").eq(source_type)).build()
                counts[source_type] = int(
                    self.client.points.count(self.collection, filter=filter_query)
                )
            except Exception:
                counts[source_type] = 0
        return counts

    def stats_note(self) -> str | None:
        return None

    def vde_state(self) -> str | None:
        try:
            assert self.client is not None
            return str(self.client.vde.get_state(self.collection))
        except Exception:
            return None

    def _build_filter(self, source_type: str, tag: str | None) -> Any:
        from actian_vectorai import Field, FilterBuilder

        builder = FilterBuilder()
        used = False
        if source_type != "all":
            builder.must(Field("source_type").eq(source_type))
            used = True
        if tag and tag.strip():
            builder.must(Field("tags_flat").text(tag.strip().lower()))
            used = True
        return builder.build() if used else None

    def _actian_rrf(
        self,
        dense_raw: list[Any],
        keyword_raw: list[Any],
        query: str,
        limit: int,
    ) -> list[MemoryResult]:
        try:
            from actian_vectorai import reciprocal_rank_fusion

            try:
                fused_raw = reciprocal_rank_fusion(
                    [dense_raw, keyword_raw],
                    limit=limit,
                    weights=[0.72, 0.28],
                )
            except TypeError:
                fused_raw = reciprocal_rank_fusion([dense_raw, keyword_raw], limit=limit)
            return [_point_to_result(point, query, "rrf_hybrid") for point in fused_raw]
        except Exception:
            return []


def _chunk_to_result(chunk: MemoryChunk, score: float, query: str, channel: str) -> MemoryResult:
    return MemoryResult(
        id=chunk.id,
        document_id=chunk.document_id,
        title=chunk.title,
        source_type=chunk.source_type,
        text=chunk.text,
        snippet=make_snippet(chunk.text, query),
        score=round(float(score), 6),
        tags=chunk.tags,
        created_at=chunk.created_at,
        channel=channel,
    )


def _point_to_result(point: Any, query: str, channel: str) -> MemoryResult:
    payload = getattr(point, "payload", None) or {}
    text = str(payload.get("text") or "")
    return MemoryResult(
        id=str(getattr(point, "id", payload.get("id", ""))),
        document_id=str(payload.get("document_id", "")),
        title=str(payload.get("title", "Untitled memory")),
        source_type=str(payload.get("source_type", "note")),
        text=text,
        snippet=make_snippet(text, query),
        score=round(float(getattr(point, "score", 0.0)), 6),
        tags=list(payload.get("tags") or []),
        created_at=parse_datetime(payload.get("created_at")),
        channel=channel,
    )


class MemoryEngine:
    """Coordinates embeddings, Actian, and fallback behavior."""

    def __init__(self, *, url: str, collection: str, dimension: int, enable_actian: bool) -> None:
        self.collection = collection
        self._fallback = InMemoryStore(collection)
        self._store: InMemoryStore | ActianStore = self._fallback
        self._actian_error: str | None = None

        if enable_actian:
            try:
                self._store = ActianStore(url=url, collection=collection, dimension=dimension)
            except Exception as exc:
                self._actian_error = str(exc)

    @property
    def backend_name(self) -> str:
        return self._store.backend_name

    @property
    def connected(self) -> bool:
        return self._store.connected

    @property
    def note(self) -> str | None:
        if self._store is self._fallback and self._actian_error:
            return f"Actian connection fallback: {self._actian_error}"
        return self._store.stats_note()

    def reset(self) -> None:
        self._store.reset()

    def upsert(self, chunks: list[MemoryChunk], vector_records: list[dict[str, list[float]]]) -> None:
        self._store.upsert(chunks, vector_records)

    def hybrid_search(self, **kwargs: Any) -> SearchBundle:
        return self._store.hybrid_search(**kwargs)

    def connections(self, **kwargs: Any) -> list[MemoryResult]:
        return self._store.connections(**kwargs)

    def count(self) -> int:
        return self._store.count()

    def source_counts(self) -> dict[str, int]:
        return self._store.source_counts()

    def vde_state(self) -> str | None:
        if hasattr(self._store, "vde_state"):
            return self._store.vde_state()
        return None


def now_ms() -> int:
    return int(time.perf_counter() * 1000)
