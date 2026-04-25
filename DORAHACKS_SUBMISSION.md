# DoraHacks Submission Copy

## Project Name

MemoryMesh

## Tagline

Trace where an idea came from across everything you saved.

## Problem

People save ideas across notes, PDFs, bookmarks, and screenshots, then later lose the context behind those ideas. Generic note search only retrieves isolated matches. It does not reconstruct how a decision formed.

## Solution

MemoryMesh is a local-first decision-trail engine. Users upload mixed personal knowledge sources, and the app reconstructs the chain behind an idea with exact source evidence and related memories.

Example query:

`Where did my USDC agent commerce idea come from?`

The app returns:

- the strongest source note
- related bookmarks and screenshots
- a cross-source decision trail
- retrieval diagnostics from Actian VectorAI DB

## How Actian VectorAI DB Is Core

Actian VectorAI DB is the retrieval engine, not a bolt-on:

- named vectors in the same collection:
  - `semantic` for meaning
  - `intent` for retrieval intent
- filtered search by source type and metadata
- hybrid fusion with Reciprocal Rank Fusion
- HNSW tuning at collection creation
- VDE stats and local persistence

Without the vector database, the central product behavior does not exist.

## Why This Is Useful

This is useful for founders, researchers, and operators who need to recover not just old notes, but the evidence chain behind a decision.

## Technical Requirement Used

- Hybrid Fusion
- Filtered Search
- Named Vectors

## Local-First Angle

The retrieval stack runs locally with Dockerized Actian VectorAI DB and local embeddings, so sensitive personal knowledge stays on-device.

## Demo Plan

1. Seed the archive with notes, bookmarks, PDFs, and screenshot OCR.
2. Ask: `Where did my USDC agent commerce idea come from?`
3. Show the exact evidence.
4. Show the decision trail.
5. Show Actian diagnostics: named vectors, filters, and hybrid fusion.
6. Ask a second query: `When did I feel stuck but later figured it out?`

## Repo / Demo

- Public repo: add your GitHub URL here
- Demo video: add your Loom or YouTube URL here

