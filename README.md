# MemoryMesh

Trace where an idea came from across everything you saved.

MemoryMesh is a local-first decision-trail engine built for the Actian VectorAI DB Build Challenge. Instead of generic “chat with your notes,” it reconstructs where an idea came from by searching across notes, PDFs, bookmarks, and screenshots, then surfacing the source chain behind the final answer.

## Why It Wins

- VectorAI DB is central: every memory chunk is embedded, stored, filtered, and retrieved from Actian VectorAI DB.
- Advanced usage is visible: named vectors (`semantic` + `intent`), filtered search, client-side RRF hybrid fusion, HNSW collection tuning, VDE stats, and local persistence.
- Demo is instant: seed sample memories, ask where an idea came from, reveal exact source evidence and a multi-source decision trail.
- Bonus-friendly: retrieval runs locally with Dockerized VectorAI DB and a local embedding model.

## Features

- Upload `.txt`, `.md`, `.pdf`, `.json`, `.png`, `.jpg`, and `.jpeg` files.
- Local MiniLM embeddings through `sentence-transformers/all-MiniLM-L6-v2`.
- Automatic fallback hashing embeddings for quick UI demos when ML dependencies are not installed.
- Filter by source type: notes, PDFs, bookmarks, screenshots.
- Named vectors in Actian VectorAI DB: `semantic` for meaning and `intent` for retrieval intent.
- Hybrid retrieval: semantic and intent searches fused with Reciprocal Rank Fusion.
- Decision trails: reconstruct the chain of notes, bookmarks, PDFs, and screenshots behind an idea.
- Judge-facing diagnostics: backend status, VectorAI collection, result counts, fusion mode, filter mode.

## Quick Start

1. Start Actian VectorAI DB.

```powershell
docker compose up -d
```

If Docker is not installed, the app still runs in demo fallback mode, but the hackathon submission should be recorded with Actian running.

2. Start the backend.

```powershell
.\start-backend.ps1
```

For a quick UI smoke test without the MiniLM download, run `.\start-backend.ps1 -Lite`.

If the local Python installation cannot create a working virtual environment, the script automatically falls back to a workspace-local `.deps` directory so the backend can still start.

3. Start the frontend.

```powershell
.\start-frontend.ps1
```

Open `http://localhost:5173`.

## Demo Script

1. Click `Seed demo brain`.
2. Search: `Where did my USDC agent commerce idea come from?`
3. Point out the exact source evidence and the decision trail reconstruction.
4. Click source filters such as `bookmark` or `note`.
5. Search: `When did I feel stuck but later figured it out?`
6. Show the cross-source trail to demonstrate why vector retrieval is the product, not a bolt-on.

## Judging Criteria Mapping

- Use of Actian VectorAI DB: named-vector collection creation, HNSW tuning, payload filters, point upsert/search, hybrid fusion, VDE stats.
- Real-world impact: founders, researchers, and operators can recover not just notes but the provenance of a decision.
- Technical execution: FastAPI backend, typed React frontend, local extraction/chunking/embedding pipeline, named-vector retrieval.
- Demo and presentation: polished UI with visible diagnostics and a memorable “where did this idea come from?” moment.

## Notes

Do not commit the beta `.whl` file. The `.gitignore` excludes wheels, and setup installs it from the organizer-provided beta repo path.
