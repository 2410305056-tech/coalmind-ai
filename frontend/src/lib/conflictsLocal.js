const KEY = 'coalmind-conflict-actions'

export function loadConflictActions() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || '{}') || {}
  } catch {
    return {}
  }
}

export function conflictKey(c) {
  return [c.id, c.mine, c.year, c.parameter].filter(Boolean).join('|')
}

export function saveConflictAction(c, status) {
  const all = loadConflictActions()
  all[conflictKey(c)] = { status, reviewed_at: new Date().toISOString() }
  localStorage.setItem(KEY, JSON.stringify(all))
  return all[conflictKey(c)]
}

export function mergeConflictActions(rows) {
  const extra = loadConflictActions()
  return (rows || []).map((c) => {
    const hit = extra[conflictKey(c)]
    if (!hit) return c
    return { ...c, reconciliation_status: hit.status, reviewed_at: hit.reviewed_at }
  })
}
