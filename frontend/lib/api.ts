const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const fetcher = (url: string) => fetch(url).then((res) => res.json())

export const apiClient = {
  health: () => fetcher(`${API_URL}/health`),
  stats: () => fetcher(`${API_URL}/api/stats`),
  entries: () => fetcher(`${API_URL}/api/reddit/entries`),
  insights: () => fetcher(`${API_URL}/api/insights`),

  ingestUrl: (url: string) =>
    fetch(`${API_URL}/api/reddit/ingest-url`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    }).then((res) => res.json()),

  ingestSeed: () =>
    fetch(`${API_URL}/api/reddit/ingest-seed`, {
      method: 'POST',
    }).then((res) => res.json()),

  refreshScores: () =>
    fetch(`${API_URL}/api/reddit/refresh-scores`, {
      method: 'POST',
    }).then((res) => res.json()),

  autoProcess: () =>
    fetch(`${API_URL}/api/pipeline/auto-process-ready`, {
      method: 'POST',
    }).then((res) => res.json()),

  generateInsights: () =>
    fetch(`${API_URL}/api/insights/generate`, {
      method: 'POST',
    }).then((res) => res.json()),
}
