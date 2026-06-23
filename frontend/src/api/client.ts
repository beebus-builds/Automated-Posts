const API_BASE = import.meta.env.VITE_API_URL || '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || 'Request failed')
  return data
}

export interface PostResult {
  success: boolean
  post_id?: string
  caption?: string
  fb_url?: string
  error?: string
}

export interface HistoryEntry {
  post_id: string
  caption: string
  timestamp: string
  is_video?: boolean
}

export const api = {
  post: (formData: FormData) =>
    fetch(`${API_BASE}/post`, { method: 'POST', body: formData }).then(async r => {
      const d = await r.json()
      if (!r.ok) throw new Error(d.error || 'Post failed')
      return d as PostResult
    }),

  getHistory: () =>
    request<HistoryEntry[]>('/history'),
}
