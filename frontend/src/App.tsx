import { FormEvent, useEffect, useMemo, useState } from "react";
import { getStats, ingestFiles, ingestText, searchMemory, seedDemo } from "./api";
import type { MemoryResult, SearchMode, SearchResponse, SourceType, StatsResponse } from "./types";

const SOURCE_OPTIONS: { id: SourceType; label: string }[] = [
  { id: "all", label: "All sources" },
  { id: "note", label: "Notes" },
  { id: "pdf", label: "PDFs" },
  { id: "bookmark", label: "Bookmarks" },
  { id: "screenshot", label: "Screenshots" },
];

const MODE_OPTIONS: { id: SearchMode; label: string; prompt: string }[] = [
  {
    id: "decision_trail",
    label: "Decision trail",
    prompt: "Where did my USDC agent commerce idea come from?",
  },
  {
    id: "second_brain",
    label: "Second brain",
    prompt: "What was my startup idea about USDC payments?",
  },
  {
    id: "idea_search",
    label: "Idea recovery",
    prompt: "Which old notes connect to local-first AI products?",
  },
  {
    id: "emotional_memory",
    label: "Emotional memory",
    prompt: "When did I feel stuck but later figured it out?",
  },
];

export default function App() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [query, setQuery] = useState(MODE_OPTIONS[0].prompt);
  const [sourceType, setSourceType] = useState<SourceType>("all");
  const [mode, setMode] = useState<SearchMode>("second_brain");
  const [tag, setTag] = useState("");
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("Ready to build your private memory layer.");
  const [manualTitle, setManualTitle] = useState("Fresh hackathon thought");
  const [manualText, setManualText] = useState("");

  const activeMode = useMemo(() => MODE_OPTIONS.find((item) => item.id === mode) ?? MODE_OPTIONS[0], [mode]);

  async function refreshStats() {
    try {
      const next = await getStats();
      setStats(next);
    } catch (error) {
      setStatus(`Backend not reachable yet: ${(error as Error).message}`);
    }
  }

  useEffect(() => {
    void refreshStats();
  }, []);

  async function handleSeed() {
    setLoading(true);
    setStatus("Seeding a demo brain with notes, bookmarks, PDF clips, and screenshot text...");
    try {
      const seeded = await seedDemo();
      setStatus(`Seeded ${seeded.reduce((sum, item) => sum + item.chunks_added, 0)} memory chunks.`);
      await refreshStats();
      await runSearch(activeMode.prompt);
    } catch (error) {
      setStatus(`Seed failed: ${(error as Error).message}`);
    } finally {
      setLoading(false);
    }
  }

  async function runSearch(nextQuery = query) {
    const cleanQuery = nextQuery.trim();
    if (!cleanQuery) {
      setStatus("Type a question first.");
      return;
    }
    setLoading(true);
    setQuery(cleanQuery);
    setStatus("Searching semantic memory, keyword intent, and thought connections...");
    try {
      const result = await searchMemory({
        query: cleanQuery,
        source_type: sourceType,
        tag: tag.trim() || null,
        mode,
        limit: 8,
      });
      setResponse(result);
      setStatus(`Found ${result.results.length} fused memories in ${result.diagnostics.latency_ms} ms.`);
      await refreshStats();
    } catch (error) {
      setStatus(`Search failed: ${(error as Error).message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearchSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runSearch();
  }

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setLoading(true);
    setStatus(`Ingesting ${files.length} file(s)...`);
    try {
      const result = await ingestFiles(files);
      const chunks = result.reduce((sum, item) => sum + item.chunks_added, 0);
      setStatus(`Added ${chunks} chunks from ${result.length} upload(s).`);
      await refreshStats();
    } catch (error) {
      setStatus(`Upload failed: ${(error as Error).message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleManualIngest() {
    if (!manualText.trim()) {
      setStatus("Add note text before saving.");
      return;
    }
    setLoading(true);
    setStatus("Embedding and storing your note...");
    try {
      const result = await ingestText({
        title: manualTitle,
        text: manualText,
        source_type: "note",
        tags: ["manual", "idea"],
      });
      setManualText("");
      setStatus(`Saved '${result.title}' as ${result.chunks_added} chunk(s).`);
      await refreshStats();
    } catch (error) {
      setStatus(`Save failed: ${(error as Error).message}`);
    } finally {
      setLoading(false);
    }
  }

  function selectMode(nextMode: SearchMode) {
    const option = MODE_OPTIONS.find((item) => item.id === nextMode) ?? MODE_OPTIONS[0];
    setMode(nextMode);
    setQuery(option.prompt);
  }

  return (
    <main className="app-shell">
      <div className="ambient-grid" aria-hidden="true" />
      <StatusRail stats={stats} status={status} onSeed={handleSeed} loading={loading} />

      <section className="workspace">
        <header className="hero">
          <div className="hero-copy">
            <p className="eyebrow">Actian VectorAI DB Build Challenge</p>
            <h1>MemoryMesh</h1>
            <p className="hero-line">Trace where an idea came from across notes, PDFs, bookmarks, and screenshots.</p>
          </div>
          <div className="hero-proof">
            <span>Named vectors</span>
            <span>Filtered search</span>
            <span>RRF hybrid fusion</span>
            <span>Decision trail</span>
          </div>
        </header>

        <section className="control-surface">
          <div className="search-zone">
            <form onSubmit={handleSearchSubmit}>
              <label htmlFor="memory-query">Reconstruct the decision trail</label>
              <div className="query-row">
                <textarea
                  id="memory-query"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Ask where an idea came from, or recover a vague memory..."
                />
                <button className="primary-action" disabled={loading} type="submit">
                  {loading ? "Thinking" : "Search"}
                </button>
              </div>
            </form>

            <div className="mode-row" aria-label="Search modes">
              {MODE_OPTIONS.map((option) => (
                <button
                  key={option.id}
                  className={mode === option.id ? "mode active" : "mode"}
                  onClick={() => selectMode(option.id)}
                  type="button"
                >
                  {option.label}
                </button>
              ))}
            </div>

            <div className="filter-row" aria-label="Source filters">
              {SOURCE_OPTIONS.map((option) => (
                <button
                  key={option.id}
                  className={sourceType === option.id ? "source-pill active" : "source-pill"}
                  onClick={() => setSourceType(option.id)}
                  type="button"
                >
                  {option.label}
                </button>
              ))}
              <input
                className="tag-filter"
                value={tag}
                onChange={(event) => setTag(event.target.value)}
                placeholder="Optional tag filter"
              />
            </div>
          </div>

          <div className="ingest-zone">
            <div className="upload-lane">
              <p>Drop in memories</p>
              <span>PDFs, notes, bookmarks, screenshots</span>
              <label className="file-button" htmlFor="file-upload">
                Choose files
              </label>
              <input
                id="file-upload"
                type="file"
                multiple
                accept=".txt,.md,.pdf,.json,.png,.jpg,.jpeg"
                onChange={(event) => void handleFiles(event.currentTarget.files)}
              />
            </div>

            <div className="manual-note">
              <input
                value={manualTitle}
                onChange={(event) => setManualTitle(event.target.value)}
                aria-label="Manual note title"
              />
              <textarea
                value={manualText}
                onChange={(event) => setManualText(event.target.value)}
                placeholder="Paste a raw idea here, then save it into the mesh."
              />
              <button onClick={handleManualIngest} disabled={loading} type="button">
                Save note
              </button>
            </div>
          </div>
        </section>

        <section className="answer-stage">
          <ThoughtGraph response={response} mode={mode} />
          <AnswerPanel response={response} mode={mode} />
        </section>
      </section>
    </main>
  );
}

function StatusRail({
  stats,
  status,
  onSeed,
  loading,
}: {
  stats: StatsResponse | null;
  status: string;
  onSeed: () => void;
  loading: boolean;
}) {
  const sourceCounts = stats?.source_counts ?? {};
  return (
    <aside className="status-rail">
      <div>
        <p className="rail-label">Private index</p>
        <h2>{stats?.total_chunks ?? 0}</h2>
        <span>memory chunks</span>
      </div>

      <div className="db-status">
        <p>Backend</p>
        <strong>{stats?.backend ?? "Waiting for API"}</strong>
        <small>{stats?.collection ?? "memorymesh_thoughts"}</small>
        {stats?.vde_state ? <small>VDE: {stats.vde_state}</small> : null}
      </div>

      <div className="source-counts">
        {["note", "pdf", "bookmark", "screenshot"].map((source) => (
          <div key={source}>
            <span>{source}</span>
            <strong>{sourceCounts[source] ?? 0}</strong>
          </div>
        ))}
      </div>

      <button className="seed-button" onClick={onSeed} disabled={loading} type="button">
        Seed demo brain
      </button>

      <p className="live-status">{status}</p>
      {stats?.note ? <p className="warning-note">{stats.note}</p> : null}
    </aside>
  );
}

function ThoughtGraph({
  response,
  mode,
}: {
  response: SearchResponse | null;
  mode: SearchMode;
}) {
  const nodes = response ? response.results.slice(0, 4) : [];
  const connections = response ? response.connections.slice(0, 3) : [];
  const heading = mode === "decision_trail" ? "Decision trail" : "Thought connections";
  const subheading =
    response
      ? `${connections.length} related memories`
      : mode === "decision_trail"
        ? "waiting for an origin question"
        : "waiting for a question";

  return (
    <div className="graph-panel">
      <div className="graph-heading">
        <p>{heading}</p>
        <span>{subheading}</span>
      </div>
      <div className="graph-canvas">
        <svg viewBox="0 0 640 360" role="img" aria-label="Memory connection graph">
          <path className="graph-line line-one" d="M320 178 C220 96 162 76 92 104" />
          <path className="graph-line line-two" d="M320 178 C456 72 518 80 570 132" />
          <path className="graph-line line-three" d="M320 178 C456 260 508 296 578 276" />
          <path className="graph-line line-four" d="M320 178 C210 268 156 292 82 254" />
          <circle className="core-node" cx="320" cy="178" r="54" />
        </svg>

        <div className="core-label">
          <span>{mode === "decision_trail" ? "Origin query" : "Query"}</span>
          <strong>{response ? response.query : "Ask anything"}</strong>
        </div>

        <GraphNode className="node-a" item={nodes[0]} fallback="Exact note" />
        <GraphNode className="node-b" item={connections[0]} fallback="Old idea" />
        <GraphNode className="node-c" item={connections[1]} fallback="Related moment" />
        <GraphNode className="node-d" item={connections[2] ?? nodes[1]} fallback="Source trail" />
      </div>
    </div>
  );
}

function GraphNode({
  item,
  fallback,
  className,
}: {
  item?: MemoryResult;
  fallback: string;
  className: string;
}) {
  return (
    <div className={`graph-node ${className}`}>
      <span>{item?.source_type ?? "memory"}</span>
      <strong>{item?.title ?? fallback}</strong>
    </div>
  );
}

function AnswerPanel({
  response,
  mode,
}: {
  response: SearchResponse | null;
  mode: SearchMode;
}) {
  if (!response) {
    return (
      <section className="answer-panel empty-state">
        <p className="eyebrow">Demo path</p>
        <h2>Seed the archive, then ask where the USDC idea came from.</h2>
        <p>
          The app will return exact evidence, source filters, named-vector retrieval,
          hybrid fusion diagnostics, and a cross-source decision trail.
        </p>
      </section>
    );
  }

  return (
    <section className="answer-panel">
      <div className="answer-header">
        <p className="eyebrow">Answer from your archive</p>
        <div className="diagnostic-strip">
          <span>{response.diagnostics.backend}</span>
          <span>{response.diagnostics.fusion}</span>
          <span>{response.diagnostics.filter_applied}</span>
          <span>{response.diagnostics.latency_ms} ms</span>
        </div>
      </div>

      <h2>{response.answer}</h2>

      <div className="result-grid">
        <ResultColumn title="Exact evidence" items={response.results} />
        <ResultColumn
          title={mode === "decision_trail" ? "Decision trail" : "Connected thoughts"}
          items={response.connections}
          compact
        />
      </div>
    </section>
  );
}

function ResultColumn({
  title,
  items,
  compact = false,
}: {
  title: string;
  items: MemoryResult[];
  compact?: boolean;
}) {
  return (
    <div className={compact ? "result-column compact" : "result-column"}>
      <h3>{title}</h3>
      {items.length === 0 ? <p className="muted">No matches yet.</p> : null}
      {items.map((item) => (
        <article className="memory-hit" key={item.id}>
          <div className="hit-meta">
            <span>{item.source_type}</span>
            <span>{item.channel}</span>
            <span>{formatScore(item.score)}</span>
          </div>
          <h4>{item.title}</h4>
          <p>{compact ? item.snippet.slice(0, 190) : item.snippet}</p>
          <div className="tag-row">
            {item.tags.slice(0, 5).map((tag) => (
              <span key={`${item.id}-${tag}`}>{tag}</span>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}

function formatScore(score: number) {
  return score < 0.1 ? score.toFixed(4) : score.toFixed(3);
}
