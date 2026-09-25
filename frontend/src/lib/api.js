import { cloudGet, cloudQuery, supabaseConfigured } from './cloud'

const BASE = String(import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

export function apiUrl(path) {
  if (!path.startsWith('/')) path = `/${path}`
  return `${BASE}${path}`
}

export function pythonApiEnabled() {
  return Boolean(BASE) || ['localhost', '127.0.0.1'].includes(window.location.hostname)
}

async function tryPython(path, options) {
  const res = await fetch(apiUrl(path), options)
  if (!res.ok) throw new Error(`${res.status} ${path}`)
  return res.json()
}

export async function getJson(path) {
  if (pythonApiEnabled()) {
    try {
      return await tryPython(path)
    } catch {
      /* hosted demo falls through to Supabase */
    }
  }
  if (supabaseConfigured()) return cloudGet(path)
  throw new Error('No API and no Supabase config')
}

export async function postJson(path, body) {
  if (pythonApiEnabled()) {
    try {
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
    } catch (err) {
      if (path !== '/api/query' || !supabaseConfigured()) throw err
    }
  }
  if (path === '/api/query' && supabaseConfigured()) {
    return cloudQuery(body.query || '', body.history || [])
  }
  throw new Error('This action needs the Python API')
}
