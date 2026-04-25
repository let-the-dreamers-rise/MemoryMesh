import type { IngestResponse, SearchRequest, SearchResponse, StatsResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getStats(): Promise<StatsResponse> {
  return parseResponse<StatsResponse>(await fetch(`${API_BASE}/api/stats`));
}

export async function seedDemo(): Promise<IngestResponse[]> {
  return parseResponse<IngestResponse[]>(
    await fetch(`${API_BASE}/api/demo/seed`, { method: "POST" }),
  );
}

export async function searchMemory(payload: SearchRequest): Promise<SearchResponse> {
  return parseResponse<SearchResponse>(
    await fetch(`${API_BASE}/api/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  );
}

export async function ingestText(payload: {
  title: string;
  text: string;
  source_type: string;
  tags: string[];
}): Promise<IngestResponse> {
  return parseResponse<IngestResponse>(
    await fetch(`${API_BASE}/api/ingest/text`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  );
}

export async function ingestFiles(files: FileList): Promise<IngestResponse[]> {
  const form = new FormData();
  Array.from(files).forEach((file) => form.append("files", file));
  return parseResponse<IngestResponse[]>(
    await fetch(`${API_BASE}/api/ingest/files`, {
      method: "POST",
      body: form,
    }),
  );
}

