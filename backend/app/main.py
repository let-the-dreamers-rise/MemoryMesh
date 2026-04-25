from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .chunking import chunk_document, keyword_intent
from .config import get_settings
from .demo_seed import DEMO_MEMORIES
from .embeddings import EmbeddingService
from .extractors import extract_document
from .schemas import (
    IngestResponse,
    IngestTextRequest,
    SearchDiagnostics,
    SearchRequest,
    SearchResponse,
    StatsResponse,
)
from .vector_store import MemoryEngine, now_ms


settings = get_settings()
embeddings = EmbeddingService(settings.memorymesh_embedding_mode)
engine = MemoryEngine(
    url=settings.vectorai_url,
    collection=settings.memorymesh_collection,
    dimension=embeddings.dimension,
    enable_actian=settings.memorymesh_enable_actian,
)

app = FastAPI(
    title="MemoryMesh API",
    version="0.1.0",
    description="Local-first decision-trail search powered by Actian VectorAI DB.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "backend": engine.backend_name,
        "collection": settings.memorymesh_collection,
        "embedding_mode": embeddings.model_name,
    }


@app.get("/api/stats", response_model=StatsResponse)
def stats() -> StatsResponse:
    return StatsResponse(
        backend=engine.backend_name,
        collection=settings.memorymesh_collection,
        connected=engine.connected,
        total_chunks=engine.count(),
        source_counts=engine.source_counts(),
        embedding_mode=embeddings.model_name,
        vector_dimension=embeddings.dimension,
        advanced_features=[
            "VectorAI DB named vectors: semantic + intent",
            "Filtered search by source metadata",
            "Reciprocal Rank Fusion hybrid retrieval",
            "HNSW m=32 / ef_construct=256 collection tuning",
            "VDE collection state and flush hooks",
        ],
        vde_state=engine.vde_state(),
        note=engine.note,
    )


@app.post("/api/demo/seed", response_model=list[IngestResponse])
def seed_demo() -> list[IngestResponse]:
    engine.reset()
    responses: list[IngestResponse] = []
    for memory in DEMO_MEMORIES:
        responses.append(
            _ingest_text(
                title=memory["title"],
                text=memory["text"],
                source_type=memory["source_type"],
                tags=memory["tags"],
                created_at=memory.get("created_at"),
            )
        )
    return responses


@app.post("/api/ingest/text", response_model=IngestResponse)
def ingest_text(request: IngestTextRequest) -> IngestResponse:
    return _ingest_text(
        title=request.title,
        text=request.text,
        source_type=request.source_type,
        tags=request.tags,
    )


@app.post("/api/ingest/files", response_model=list[IngestResponse])
async def ingest_files(files: list[UploadFile] = File(...)) -> list[IngestResponse]:
    responses: list[IngestResponse] = []
    for upload in files:
        content = await upload.read()
        extracted = extract_document(upload.filename or "upload", content, upload.content_type)
        if not extracted.text.strip():
            raise HTTPException(status_code=422, detail=f"No readable text found in {upload.filename}")
        responses.append(
            _ingest_text(
                title=extracted.title,
                text=extracted.text,
                source_type=extracted.source_type,
                tags=extracted.tags,
            )
        )
    return responses


@app.post("/api/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    started = now_ms()
    dense_vector = embeddings.encode_one(request.query)
    keyword_query = keyword_intent(request.query)
    keyword_vector = embeddings.encode_one(keyword_query)

    bundle = engine.hybrid_search(
        query=request.query,
        dense_vector=dense_vector,
        keyword_vector=keyword_vector,
        source_type=request.source_type,
        tag=request.tag,
        limit=request.limit,
    )

    exclude = {item.id for item in bundle.hits[:3]}
    connection_seed = bundle.hits[0].text if bundle.hits else request.query
    connection_vector = embeddings.encode_one(connection_seed[:1200])
    connections = engine.connections(
        query=connection_seed,
        vector=connection_vector,
        exclude_ids=exclude,
        limit=5,
    )
    if request.mode == "decision_trail":
        connections = sorted(connections, key=lambda item: item.created_at)

    filter_label = _filter_label(request.source_type, request.tag)
    latency = max(0, now_ms() - started)
    return SearchResponse(
        query=request.query,
        answer=_synthesize_answer(request, bundle.hits, connections),
        results=bundle.hits,
        connections=connections,
        diagnostics=SearchDiagnostics(
            backend=engine.backend_name,
            collection=settings.memorymesh_collection,
            semantic_results=bundle.semantic_count,
            keyword_results=bundle.keyword_count,
            fused_results=len(bundle.hits),
            filter_applied=filter_label,
            fusion=bundle.fusion,
            latency_ms=latency,
        ),
    )


def _ingest_text(
    *,
    title: str,
    text: str,
    source_type: str,
    tags: list[str],
    created_at: str | None = None,
) -> IngestResponse:
    chunks = chunk_document(
        title=title,
        text=text,
        source_type=source_type,
        tags=tags,
        created_at=created_at,
    )
    if not chunks:
        raise HTTPException(status_code=422, detail="No text chunks were produced.")

    semantic_vectors = embeddings.encode([chunk.text for chunk in chunks])
    intent_vectors = embeddings.encode(
        [keyword_intent(f"{chunk.title}. {chunk.text}") for chunk in chunks]
    )
    vector_records = [
        {"semantic": semantic_vector, "intent": intent_vector}
        for semantic_vector, intent_vector in zip(semantic_vectors, intent_vectors)
    ]
    engine.upsert(chunks, vector_records)
    merged_tags: list[str] = []
    for chunk in chunks:
        for tag in chunk.tags:
            if tag not in merged_tags:
                merged_tags.append(tag)

    return IngestResponse(
        document_id=chunks[0].document_id,
        title=title,
        source_type=source_type,
        chunks_added=len(chunks),
        tags=merged_tags[:10],
    )


def _filter_label(source_type: str, tag: str | None) -> str:
    parts: list[str] = []
    if source_type != "all":
        parts.append(f"source_type={source_type}")
    if tag:
        parts.append(f"tag~{tag}")
    return ", ".join(parts) if parts else "none"


def _synthesize_answer(request: SearchRequest, results: list, connections: list) -> str:
    if not results:
        return (
            "I could not find a matching memory yet. Add notes, PDFs, bookmarks, "
            "or screenshots, then search again."
        )

    top = results[0]
    connection_titles = [item.title for item in connections[:3]]
    source_line = f"I found the strongest match in '{top.title}' ({top.source_type})."
    evidence_line = f"Relevant memory: {top.snippet}"

    if request.mode == "emotional_memory":
        mode_line = (
            "This looks like an emotional memory search: the match is based on the "
            "shape of the situation, not exact wording."
        )
    elif request.mode == "decision_trail":
        mode_line = (
            "This is a decision-trail search: I traced the idea across multiple source types "
            "using named vectors for meaning and intent."
        )
    elif request.mode == "idea_search":
        mode_line = "This looks like an idea recovery search: I prioritized intent and reusable concepts."
    else:
        mode_line = "This is a second-brain search: I fused semantic meaning with keyword-intent signals."

    if connection_titles:
        if request.mode == "decision_trail":
            connection_line = "Decision trail: " + " -> ".join(connection_titles) + "."
        else:
            connection_line = "Connected thoughts: " + "; ".join(connection_titles) + "."
    else:
        connection_line = "No strong connected thoughts yet."

    return " ".join([source_line, mode_line, evidence_line, connection_line])
