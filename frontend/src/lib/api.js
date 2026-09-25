const BASE = String(import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

export function apiUrl(path) {
  if (!path.startsWith('/')) path = `/${path}`
  return `${BASE}${path}`
}

export async function getJson(path) {
  const res = await fetch(apiUrl(path))
  if (!res.ok) throw new Error(`${res.status} ${path}`)
  return res.json()
}

export async function postJson(path, body) {
  const res = await fetch(apiUrl(path), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    let detail = `${res.status}`
    try {
      const err = await res.json()
      detail = err.detail || detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }
  return res.json()
}
