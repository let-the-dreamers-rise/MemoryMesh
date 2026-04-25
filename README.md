# MemoryMesh

Trace where an idea came from across everything you saved.

MemoryMesh is a local-first decision-trail engine built for the Actian VectorAI DB Build Challenge. Instead of generic "chat with your notes," it reconstructs the source chain behind an idea by searching across notes, PDFs, bookmarks, and screenshots, then surfacing the exact evidence and related memories that led to the final answer.

## Why Judges Should Care

- This is not generic personal RAG. The core interaction is provenance reconstruction: "Where did this idea come from?"
- Actian VectorAI DB is the retrieval engine, not a bolt-on. The product only works because vector search, metadata filters, and hybrid fusion are central to the flow.
- The demo is immediate and understandable. Seed the archive, ask one question, and the app shows exact evidence plus the cross-source decision trail.
- The project is aligned with Actian's local-first positioning. Retrieval runs on-device with Dockerized VectorAI DB and local embeddings.

## The Problem

People save ideas across too many places: notes, bookmarked links, PDF snippets, screenshots, and random text files. Later, they may remember the final idea but not the chain of evidence behind it.

Traditional search fails because:

- keyword search misses semantically related material
- generic note search returns isolated matches without context
- most RAG demos answer a question, but do not reconstruct how the answer formed

## The Solution

MemoryMesh lets users ask questions like:

`Where did my USDC agent commerce idea come from?`

Instead of returning one matching chunk, the app returns:

- the strongest source memory
- supporting notes, bookmarks, PDFs, or screenshots
- a decision trail that shows how the idea connects across time and source type
- retrieval diagnostics that make the Actian usage visible in the demo

## Why Actian VectorAI DB Is Core

MemoryMesh is designed around advanced VectorAI usage:

- Named vectors: each memory stores both `semantic` and `intent` representations in the same collection.
- Filtered search: users can narrow retrieval by source type, tags, and metadata.
- Hybrid fusion: semantic and intent retrieval paths are fused with Reciprocal Rank Fusion.
- HNSW tuning: the collection is configured for fast approximate nearest-neighbor retrieval.
- Local persistence and diagnostics: retrieval happens locally, with collection status exposed in the UI.

Without the vector database, the central behavior of the product does not exist.

## What Makes This Different

Most hackathon knowledge apps stop at "upload docs and ask questions."

MemoryMesh is differentiated by:

- focusing on decision provenance instead of generic retrieval
- connecting mixed personal knowledge sources in one search flow
- making cross-source memory connections part of the answer
- turning advanced vector retrieval into a visible demo moment

## Judge-Facing Demo Flow

1. Click `Seed demo brain`.
2. Ask: `Where did my USDC agent commerce idea come from?`
3. Show the strongest evidence on the right.
4. Show the thought graph and connected memories below.
5. Point out the diagnostics pills and source filters.
6. Ask: `When did I feel stuck but later figured it out?`
7. Explain that this proves the system can recover similar situations, not just exact note matches.

## Judging Criteria Mapping

### Use of Actian VectorAI DB

- VectorAI DB stores the core memory index.
- Named vectors, metadata filters, and hybrid fusion are essential to the answer quality.
- The app is not a UI wrapped around static notes; retrieval is the product.

### Real-World Impact

- Founders can trace where a product idea came from.
- Researchers can recover supporting evidence behind a conclusion.
- Operators can reconnect past notes, links, and screenshots into a usable knowledge trail.

### Technical Execution

- FastAPI backend with ingestion, chunking, embedding, retrieval, and diagnostics
- React frontend with filters, evidence panels, and a thought-connection graph
- Local OCR and document extraction path for screenshots and PDFs
- Named-vector retrieval plus Reciprocal Rank Fusion over multiple search paths

### Demo and Presentation

- The problem is understandable in one sentence.
- The first query produces an immediate "aha" moment.
- The result view visibly proves the vector database is doing real work.

## Architecture

1. Ingest notes, PDFs, bookmarks, screenshots, or raw text.
2. Extract and chunk content into searchable memories.
3. Create embeddings locally.
4. Store vectors plus metadata in Actian VectorAI DB.
5. Run named-vector retrieval with optional filters.
6. Fuse results and return exact evidence plus connected memories.

## Stack

- Backend: FastAPI, Python
- Frontend: React, TypeScript, Vite
- Vector database: Actian VectorAI DB beta
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- OCR and parsing: `pytesseract`, `pypdf`, local extraction utilities

## Quick Start

1. Start Actian VectorAI DB.

```powershell
docker compose up -d
```

If Docker is unavailable, the app can still run in fallback mode for a UI demo, but the strongest submission should be recorded with Actian running.

2. Start the backend.

```powershell
.\start-backend.ps1
```

For a quick smoke test without the MiniLM download:

```powershell
.\start-backend.ps1 -Lite
```

3. Start the frontend.

```powershell
.\start-frontend.ps1
```

4. Open:

`http://localhost:5173`

## Repository Notes

- Do not commit the Actian beta `.whl` file.
- The project is configured to install the beta wheel from the organizer-provided local repo path.
- The repo includes a seeded demo flow so the judge-facing experience is reliable and fast.
