from app.chunking import chunk_document, keyword_intent
from app.embeddings import EmbeddingService
from app.vector_store import MemoryEngine


def test_chunking_and_embedding_fallback() -> None:
    chunks = chunk_document(
        title="Test",
        text="USDC payment agent idea. Local memory search with filters and connections.",
        source_type="note",
        tags=["payments"],
    )
    assert chunks
    embeddings = EmbeddingService("hash")
    semantic_vectors = embeddings.encode([chunk.text for chunk in chunks])
    intent_vectors = embeddings.encode([keyword_intent(chunk.text) for chunk in chunks])
    assert len(semantic_vectors[0]) == 384
    assert len(intent_vectors[0]) == 384


def test_in_memory_hybrid_search() -> None:
    embeddings = EmbeddingService("hash")
    engine = MemoryEngine(
        url="localhost:1",
        collection="test",
        dimension=384,
        enable_actian=False,
    )
    chunks = chunk_document(
        title="USDC agent commerce idea",
        text="An AI agent can approve invoices and settle vendors in USDC.",
        source_type="note",
        tags=["usdc", "payments"],
    )
    semantic_vectors = embeddings.encode([chunk.text for chunk in chunks])
    intent_vectors = embeddings.encode([keyword_intent(chunk.text) for chunk in chunks])
    engine.upsert(
        chunks,
        [
            {"semantic": semantic_vector, "intent": intent_vector}
            for semantic_vector, intent_vector in zip(semantic_vectors, intent_vectors)
        ],
    )
    query = "startup idea about USDC payments"
    bundle = engine.hybrid_search(
        query=query,
        dense_vector=embeddings.encode_one(query),
        keyword_vector=embeddings.encode_one(keyword_intent(query)),
        source_type="all",
        tag=None,
        limit=3,
    )
    assert bundle.hits
    assert "USDC" in bundle.hits[0].text
