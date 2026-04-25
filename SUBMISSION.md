# Submission Summary

## Project

MemoryMesh: a local-first decision-trail engine that lets people trace where an idea came from across everything they saved.

## One-Liner

Trace where an idea came from across everything you saved.

## What It Does

Users upload notes, PDFs, bookmarks, and screenshots. MemoryMesh chunks the content, creates local embeddings, stores named vectors and metadata in Actian VectorAI DB, and answers questions like “Where did this idea come from?” with exact source evidence and a multi-source decision trail.

## Advanced VectorAI Usage

- Named vectors: `semantic` and `intent` vector spaces in the same Actian collection.
- Filtered search by source type and metadata.
- Hybrid fusion using Reciprocal Rank Fusion across semantic and intent retrieval paths.
- HNSW tuning at collection creation.
- VDE stats for collection visibility and demo diagnostics.

## Why It Matters

Most people save ideas everywhere and later forget why they mattered. MemoryMesh does not just retrieve old notes; it reconstructs the evidence chain behind a decision, which is more useful and more memorable than generic personal search.

## Local-First Angle

The retrieval path runs locally with Dockerized Actian VectorAI DB and local embeddings, giving users privacy and ownership over sensitive personal or internal knowledge.
