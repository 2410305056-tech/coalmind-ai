const SB_URL = String(import.meta.env.VITE_SUPABASE_URL || '').replace(/\/$/, '')
const SB_ANON = String(import.meta.env.VITE_SUPABASE_ANON_KEY || '')
const GEMINI_KEY = String(import.meta.env.VITE_GEMINI_API_KEY || '')

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
  return {
    status: 'ok',
    store: 'supabase',
    python_ok: false,
    ai: true,
    ai_provider: GEMINI_KEY ? 'gemini' : 'grounded',
  }
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
    const facts = use.map((r) => ({
      mine: r.mine,
      year: r.year,
      parameter: r.parameter,
      value: r.value,
      unit: r.unit,
      source: r.source_doc,
      page: r.page_number,
    }))
    const fallback = facts.length
      ? `CoalMind AI reviewed ${facts.length} indexed figures.\n\n` +
        facts
          .map((r) => `- ${r.mine || 'Mine'} (${r.year || 'FY'}): ${r.value} ${r.unit || 'MT'} — ${r.source || 'archive'}`)
          .join('\n')
      : 'No metric rows in the archive yet.'
    const llm = await geminiAnswer(query, JSON.stringify(facts, null, 2))
    return {
      intent: 'sql',
      answer: llm || fallback,
      ai: true,
      ai_provider: llm ? 'gemini' : 'grounded',
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
  const quote = pick?.text ? String(pick.text).replace(/\s+/g, ' ').slice(0, 420) : ''
  const excerpts = (top.length ? top : pick ? [pick] : []).map((s) => ({
    document: s.document_name,
    page: s.page_number,
    text: String(s.text || '').slice(0, 800),
  }))
  const fallback = pick
    ? `CoalMind AI (grounded on the archive):\n\nFrom **${pick.document_name}** (page ${pick.page_number}):\n\n> ${quote}`
    : 'The archive has no chunks yet.'
  const llm = await geminiAnswer(query, JSON.stringify(excerpts, null, 2))
  return {
    intent: 'rag',
    answer: llm || fallback,
    ai: true,
    ai_provider: llm ? 'gemini' : 'grounded',
    chart_data: null,
    sources: (top.length ? top : pick ? [pick] : []).map((s) => ({
      document_name: s.document_name,
      page_number: s.page_number,
      bounding_box: s.bounding_box || [60, 100, 540, 200],
    })),
  }
}

async function geminiAnswer(query, context) {
  if (!GEMINI_KEY) return null
  try {
    const res = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_KEY}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          systemInstruction: {
            parts: [{
              text: 'You are CoalMind AI for CMPDI/CIL. Answer only from the archive context. Cite document and page. Do not invent numbers.',
            }],
          },
          contents: [{ parts: [{ text: `Context:\n${context}\n\nQuestion: ${query}` }] }],
          generationConfig: { temperature: 0.2 },
        }),
      },
    )
    if (!res.ok) return null
    const data = await res.json()
    return data?.candidates?.[0]?.content?.parts?.[0]?.text || null
  } catch {
    return null
  }
}

export async function cloudGet(path) {
  if (path.startsWith('/health')) return cloudHealth()
  if (path.startsWith('/api/documents')) return cloudDocuments()
  if (path.startsWith('/api/topics')) return cloudTopics()
  if (path.startsWith('/api/conflicts')) return cloudConflicts()
  throw new Error(`No cloud route for ${path}`)
}
