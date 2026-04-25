# 90-Second Demo Script

## Open

MemoryMesh is a local-first decision-trail engine. You can ask where an idea came from, and it reconstructs the notes, bookmarks, PDFs, and screenshots behind it.

## Step 1: Seed

Click `Seed demo brain`.

Say: "This loads notes, a PDF clipping, bookmarks, and screenshot OCR text. Each chunk is embedded locally and stored in Actian VectorAI DB."

## Step 2: Search

Ask:

```text
Where did my USDC agent commerce idea come from?
```

Say: "This is not keyword search only. The backend stores named vectors in Actian VectorAI DB: one for semantic meaning and one for retrieval intent. Then it runs both searches and merges them with Reciprocal Rank Fusion."

## Step 3: Show Evidence

Point to `Exact evidence`.

Say: "The top result cites the original note, so the user can trust where the answer came from."

## Step 4: Show Advanced Requirement

Point to diagnostics.

Say: "This run used Actian VectorAI DB, named vectors, source metadata filters, and hybrid fusion. If I filter to bookmarks or screenshots, the same query searches only that payload slice."

## Step 5: Show The Hook

Point to `Decision trail`.

Say: "This is the part judges remember. Instead of just retrieving one matching note, the app reconstructs the source chain that led to the idea."

## Step 6: Secondary Query

Ask:

```text
When did I feel stuck but later figured it out?
```

Say: "This proves the retrieval is semantic, not exact-match. It finds the similar situation and still returns source evidence and related memories."

## Close

MemoryMesh turns scattered personal knowledge into private, local, searchable provenance. VectorAI DB is not just storage here; it is the engine reconstructing the decision trail.
