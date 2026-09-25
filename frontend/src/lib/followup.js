const HINTS = [
  'only', 'show', 'just', 'now', 'also', 'same', 'what about',
  'and ', 'for ', 'filter', 'instead', 'that mine', 'this year',
]

export function expandQuery(query, history = []) {
  const q = String(query || '').trim()
  if (!q || !history.length) return q
  const lastUser = [...history].reverse().find((t) => t.role === 'user' && t.content)
  if (!lastUser?.content) return q
  const low = q.toLowerCase()
  const short = q.split(/\s+/).length <= 8
  const hinted = HINTS.some((h) => low.startsWith(h) || ` ${low} `.includes(` ${h.trim()} `))
  if (short || hinted) return `${lastUser.content}. Follow-up constraint: ${q}`
  return q
}
