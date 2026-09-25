const SB_URL = String(import.meta.env.VITE_SUPABASE_URL || '').replace(/\/$/, '')
const SB_ANON = String(import.meta.env.VITE_SUPABASE_ANON_KEY || '')

const SQL_TRIGGERS = [
  'compare', 'production', 'chart', 'graph', 'metric', 'trend',
  'between', 'versus', 'vs', 'total', 'average', 'output', 'tonnes',
  'obr', 'stripping', 'target', 'historical', 'growth',
]

export function supabaseConfigured() {
  return Boolean(SB_URL && SB_ANON)
}

async function rest(table, params = '') {
  const url = `${SB_URL}/rest/v1/${table}${params}`
  const res = await fetch(url, {
    headers: {
      apikey: SB_ANON,
      Authorization: `Bearer ${SB_ANON}`,
      Accept: 'application/json',
    },
  })
  if (!res.ok) {
    throw new Error(`Supabase ${table} ${res.status}`)
  }
  return res.json()
}

export async function cloudHealth() {
  await rest('documents', '?select=id&limit=1')
  return { status: 'ok', store: 'supabase', python_ok: false }
}

export async function cloudDocuments() {
  return rest(
    'documents',
    '?select=id,filename,file_type,status,upload_timestamp&order=upload_timestamp.desc'
  )
}

export async function cloudConflicts() {
  return rest(
    'conflicts',
    '?select=subsidiary,mine,year,parameter,val1,source1,val2,source2,discrepancy_pct,statutory_impact,reconciliation_status&order=id.desc'
  )
}

export async function cloudTopics() {
  const chunks = await rest('document_chunks', '?select=text')
  const domain = {
    'Coal Production': 40,
    'Gevra Mine': 36,
    'Kusmunda': 32,
    'Overburden Removal': 30,
    'Stripping Ratio': 28,
    'SECL': 26,
    'Environmental Clearance': 22,
    'Geological Reserves': 20,
  }
  for (const row of chunks) {
    const txt = String(row.text || '').toLowerCase()
    for (const key of Object.keys(domain)) {
      if (txt.includes(key.toLowerCase())) domain[key] += 3
    }
  }
  return Object.entries(domain).map(([text, value]) => ({ text, value }))
}

function intentOf(query) {
  const q = query.toLowerCase()
  return SQL_TRIGGERS.some((w) => q.includes(w)) ? 'sql' : 'rag'
}

export async function cloudQuery(query) {
  const intent = intentOf(query)
  if (intent === 'sql') {
    const rows = await rest('metrics', '?select=*&order=year.asc')
    const q = query.toLowerCase()
    const filtered = rows.filter((r) => {
      const blob = `${r.mine || ''} ${r.subsidiary || ''} ${r.parameter || ''} ${r.year || ''}`.toLowerCase()
      if (q.includes('gevra') && !blob.includes('gevra')) return false
      if (q.includes('obr') || q.includes('overburden')) {
        return (r.parameter || '').toLowerCase().includes('overburden') || (r.parameter || '').toLowerCase().includes('obr')
      }
      if (q.includes('stripping')) {
        return (r.parameter || '').toLowerCase().includes('stripping')
      }
      return (r.parameter || '').toLowerCase().includes('production') || !r.parameter
    })
    const use = (filtered.length ? filtered : rows).slice(0, 8)
    return {
      intent: 'sql',
      answer: use.length
        ? `Structured metrics from the Supabase archive (${use.length} rows). Figures come from ingested filings, not a language model.`
        : 'No metric rows in Supabase yet.',
      chart_data: {
        type: 'bar',
        unit: 'MT',
        labels: use.map((r) => `${r.mine || 'Mine'} (${r.year || 'FY'})`),
        values: use.map((r) => Number(r.value) || 0),
      },
      sources: use.slice(0, 4).map((r) => ({
        document_name: r.source_doc || 'archive',
        page_number: r.page_number || 1,
        bounding_box: [60, 100, 540, 200],
      })),
    }
  }

  const chunks = await rest(
    'document_chunks',
    '?select=document_name,page_number,text,bounding_box'
  )
  const words = query.toLowerCase().split(/\W+/).filter((w) => w.length > 3)
  const scored = chunks.map((c) => {
    const text = String(c.text || '').toLowerCase()
    const score = words.reduce((n, w) => n + (text.includes(w) ? 1 : 0), 0)
    return { ...c, score }
  })
  scored.sort((a, b) => b.score - a.score)
  const top = scored.filter((c) => c.score > 0).slice(0, 4)
  const pick = top[0] || scored[0]
  const quote = pick?.text ? `"${String(pick.text).slice(0, 420)}"` : 'No matching passage.'
  return {
    intent: 'rag',
    answer: pick
      ? `From ${pick.document_name} (page ${pick.page_number}): ${quote}`
      : 'The archive has no chunks yet.',
    chart_data: null,
    sources: (top.length ? top : pick ? [pick] : []).map((s) => ({
      document_name: s.document_name,
      page_number: s.page_number,
      bounding_box: s.bounding_box || [60, 100, 540, 200],
    })),
  }
}

export async function cloudGet(path) {
  if (path.startsWith('/health')) return cloudHealth()
  if (path.startsWith('/api/documents')) return cloudDocuments()
  if (path.startsWith('/api/topics')) return cloudTopics()
  if (path.startsWith('/api/conflicts')) return cloudConflicts()
  throw new Error(`No cloud route for ${path}`)
}
