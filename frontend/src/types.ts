export type SourceType = "all" | "note" | "pdf" | "bookmark" | "screenshot";
export type SearchMode = "second_brain" | "emotional_memory" | "idea_search" | "decision_trail";

export interface StatsResponse {
  backend: string;
  collection: string;
  connected: boolean;
  total_chunks: number;
  source_counts: Record<string, number>;
  embedding_mode: string;
  vector_dimension: number;
  advanced_features: string[];
  vde_state?: string | null;
  note?: string | null;
}

export interface IngestResponse {
  document_id: string;
  title: string;
  source_type: string;
  chunks_added: number;
  tags: string[];
}

export interface SearchRequest {
  query: string;
  source_type: SourceType;
  tag?: string | null;
  mode: SearchMode;
  limit: number;
}

export interface MemoryResult {
  id: string;
  document_id: string;
  title: string;
  source_type: string;
  text: string;
  snippet: string;
  score: number;
  tags: string[];
  created_at: string;
  channel: string;
}

export interface SearchDiagnostics {
  backend: string;
  collection: string;
  semantic_results: number;
  keyword_results: number;
  fused_results: number;
  filter_applied: string;
  fusion: string;
  latency_ms: number;
}

export interface SearchResponse {
  query: string;
  answer: string;
  results: MemoryResult[];
  connections: MemoryResult[];
  diagnostics: SearchDiagnostics;
}
