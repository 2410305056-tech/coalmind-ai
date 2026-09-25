import { useEffect, useState } from 'react'
import {
  Search, Upload, FileText, AlertTriangle, Download, Eye, X, RefreshCw,
} from 'lucide-react'
import ProofModal from './components/ProofModal'
import AnalyticsChart from './components/AnalyticsChart'
import Logo from './components/Logo'
import { apiUrl, getJson, postJson, pythonApiEnabled } from './lib/api'

const SUGGESTIONS = [
  'Compare coal production between 2022 and 2024',
  'Stripping ratio and overburden removal at Gevra mine',
  'Summarize environmental clearance for Kusmunda and Dipka',
]

const SUBS = [
  ['SECL', 'South Eastern Coalfields'],
  ['BCCL', 'Bharat Coking Coal'],
  ['CCL', 'Central Coalfields'],
  ['ECL', 'Eastern Coalfields'],
  ['WCL', 'Western Coalfields'],
  ['MCL', 'Mahanadi Coalfields'],
  ['NCL', 'Northern Coalfields'],
  ['CMPDI', 'Central Mine Planning & Design Institute'],
]

function plain(text) {
  return String(text || '')
    .replace(/\*\*/g, '')
    .replace(/^>\s?/gm, '')
}

export default function App() {
  const [tab, setTab] = useState('ask')
  const [health, setHealth] = useState({ status: 'checking', store: '—' })
  const [documents, setDocuments] = useState([])
  const [topics, setTopics] = useState([])
  const [conflicts, setConflicts] = useState([])
  const [docFilter, setDocFilter] = useState('all')
  const [uploading, setUploading] = useState(false)
  const [uploadNote, setUploadNote] = useState('')
  const [query, setQuery] = useState('')
  const [asking, setAsking] = useState(false)
  const [result, setResult] = useState(null)
  const [subsidiary, setSubsidiary] = useState('SECL')
  const [year, setYear] = useState('2023-24')
  const [reporting, setReporting] = useState(false)
  const [toast, setToast] = useState(null)
  const [proof, setProof] = useState(null)

  const notify = (title, message) => {
    setToast({ title, message })
    setTimeout(() => setToast(null), 3800)
  }

  const refresh = async () => {
    const [h, d, t, c] = await Promise.allSettled([
      getJson('/health'),
      getJson('/api/documents'),
      getJson('/api/topics'),
      getJson('/api/conflicts'),
    ])
    if (h.status === 'fulfilled') setHealth(h.value)
    else setHealth({ status: 'offline', store: '—' })
    if (d.status === 'fulfilled' && Array.isArray(d.value)) setDocuments(d.value)
    if (t.status === 'fulfilled' && Array.isArray(t.value)) setTopics(t.value)
    if (c.status === 'fulfilled' && Array.isArray(c.value)) setConflicts(c.value)
  }

  useEffect(() => { refresh() }, [])

  const onUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!pythonApiEnabled()) {
      notify('Read-only demo', 'Start the local API to ingest files.')
      e.target.value = ''
      return
    }
    setUploading(true)
    setUploadNote(`Reading ${file.name}…`)
    const body = new FormData()
    body.append('file', file)
    try {
      const res = await fetch(apiUrl('/api/upload'), { method: 'POST', body })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Upload failed')
      setUploadNote(data.message)
      notify('Document indexed', data.filename)
      refresh()
    } catch (err) {
      setUploadNote(err.message)
      notify('Upload failed', err.message)
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const ask = async (text) => {
    const q = (text ?? query).trim()
    if (!q) return
    setQuery(q)
    setAsking(true)
    try {
      const data = await postJson('/api/query', { query: q })
      setResult(data)
    } catch (err) {
      notify('Query failed', err.message)
    } finally {
      setAsking(false)
    }
  }

  const openProof = (source, docId) => {
    const match = documents.find(
      (d) => d.filename?.toLowerCase() === source?.document_name?.toLowerCase()
    )
    setProof({ source, documentId: docId || match?.id || documents[0]?.id || '' })
  }

  const downloadReport = async () => {
    if (!pythonApiEnabled()) {
      notify('Read-only demo', 'PDF briefs need the local Python API.')
      return
    }
    setReporting(true)
    try {
      const res = await fetch(apiUrl('/api/report/generate'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subsidiary, reporting_year: year }),
      })
      if (!res.ok) throw new Error('Could not generate the brief')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `CoalMind_Brief_${subsidiary}_${year}.pdf`
      a.click()
      URL.revokeObjectURL(url)
      notify('Brief ready', `${subsidiary} · ${year}`)
    } catch (err) {
      notify('Report failed', err.message)
    } finally {
      setReporting(false)
    }
  }

  const docs = documents.filter((d) =>
    docFilter === 'all' ? true : d.file_type?.toLowerCase() === docFilter
  )
  const online = health.status === 'ok'
  const pythonOn = health.python_ok !== false && pythonApiEnabled()

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <Logo size={40} />
          <div>
            <h1>CoalMind</h1>
            <p>CMPDI / Coal India document intelligence</p>
          </div>
        </div>
        <div className="top-meta">
          <span className="chip">SIH 26023</span>
          <span className="chip">
            <span className={`dot ${online ? 'ok' : 'bad'}`} />
            {online ? `Connected · ${health.store}` : 'API offline'}
          </span>
        </div>
      </header>

      <nav className="sidenav" aria-label="Primary">
        {[
          { id: 'ask', label: 'Ask', note: 'Search reports' },
          { id: 'files', label: 'Documents', note: 'Ingest files' },
          { id: 'review', label: 'Review', note: 'Conflicts & briefs' },
        ].map((item) => (
          <button
            key={item.id}
            className={`nav-btn ${tab === item.id ? 'active' : ''}`}
            onClick={() => setTab(item.id)}
          >
            <span>
              {item.label}
              <small>{item.note}</small>
            </span>
          </button>
        ))}
      </nav>

      <main className="main">
        {!online && (
          <div className="offline">
            Cannot reach FastAPI or Supabase. Check the network and keys.
          </div>
        )}
        {online && health.python_ok === false && (
          <div className="note">
            Connected to Supabase. Ask, documents, and conflicts are live.
            File upload and PDF briefs run only with the local API.
          </div>
        )}

        <div className="kpis">
          <div className="kpi">
            <span>Documents</span>
            <strong>{documents.length}</strong>
            <em>Indexed filings</em>
          </div>
          <div className="kpi">
            <span>Topics</span>
            <strong>{topics.length}</strong>
            <em>Extracted terms</em>
          </div>
          <button
            type="button"
            className="kpi clickable"
            onClick={() => setTab('review')}
          >
            <span>Discrepancies</span>
            <strong>{conflicts.length}</strong>
            <em>Cross-source mismatches</em>
          </button>
          <div className="kpi">
            <span>Engine</span>
            <strong style={{ fontSize: 18, marginTop: 10 }}>RAG + SQL</strong>
            <em>Cited answers</em>
          </div>
        </div>

        {tab === 'ask' && (
          <section>
            <div className="page-title">
              <h2>Ask the archive</h2>
              <p>Natural-language questions over ingested CMPDI / CIL reports. Answers include the source page.</p>
            </div>
            <div className="card">
              <div className="search-row">
                <input
                  type="text"
                  value={query}
                  placeholder="e.g. Compare coal production between 2022 and 2024"
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && ask()}
                />
                <button className="btn btn-primary" disabled={asking} onClick={() => ask()}>
                  {asking ? <RefreshCw size={16} /> : <Search size={16} />}
                  {asking ? 'Working' : 'Ask'}
                </button>
              </div>
              <div className="chips">
                {SUGGESTIONS.map((s) => (
                  <button key={s} type="button" onClick={() => ask(s)}>{s}</button>
                ))}
              </div>
            </div>

            {result && (
              <div className="stack">
                <div className="card">
                  <span className={`badge ${result.intent === 'sql' ? 'sql' : 'rag'}`}>
                    {result.intent === 'sql' ? 'Structured metrics' : 'Document search'}
                  </span>
                  <div className="answer" style={{ marginTop: 14 }}>
                    {plain(result.answer).split('\n\n').map((p, i) => (
                      <p key={i}>{p}</p>
                    ))}
                  </div>
                  {result.chart_data && (
                    <AnalyticsChart chartData={result.chart_data} />
                  )}
                </div>
                {result.sources?.length > 0 && (
                  <div className="card">
                    <h3>Sources</h3>
                    <p className="hint">Open the page the answer was drawn from.</p>
                    <div className="sources">
                      {result.sources.map((src, i) => (
                        <div className="source" key={`${src.document_name}-${i}`}>
                          <div>
                            <strong>{src.document_name}</strong>
                            <span>Page {src.page_number}</span>
                          </div>
                          <button className="btn btn-ghost" onClick={() => openProof(src)}>
                            <Eye size={14} /> View
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </section>
        )}

        {tab === 'files' && (
          <section>
            <div className="page-title">
              <h2>Documents</h2>
              <p>
                {pythonOn
                  ? 'PDF, Excel, and CSV up to 25 MB. Text, tables, and metrics are indexed together.'
                  : 'This hosted demo is read-only. Run the local API to ingest new files.'}
              </p>
            </div>
            <div className="card drop">
              <h3>Add a report</h3>
              <p>Annual returns, mine registers, and production sheets. Scanned files without OCR on the host are marked, not faked.</p>
              <label className="btn btn-primary" style={{ cursor: 'pointer' }}>
                <Upload size={16} />
                {uploading ? 'Indexing…' : 'Choose file'}
                <input type="file" accept=".pdf,.xlsx,.xls,.csv" hidden disabled={uploading} onChange={onUpload} />
              </label>
              {uploadNote && <p className="hint" style={{ marginTop: 14, marginBottom: 0 }}>{uploadNote}</p>}
            </div>

            <div className="toolbar">
              <h3 style={{ fontSize: 16, fontWeight: 500 }}>Library ({docs.length})</h3>
              <div className="seg">
                {['all', 'pdf', 'xlsx', 'csv'].map((t) => (
                  <button key={t} className={docFilter === t ? 'on' : ''} onClick={() => setDocFilter(t)}>
                    {t === 'all' ? 'All' : t.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            <div className="card table-wrap" style={{ padding: 0 }}>
              {docs.length === 0 ? (
                <div className="empty">No documents yet. Seed files load when the API starts with an empty store.</div>
              ) : (
                <table className="data">
                  <thead>
                    <tr>
                      <th>File</th>
                      <th>Type</th>
                      <th>Status</th>
                      <th>Indexed</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {docs.map((doc) => (
                      <tr key={doc.id}>
                        <td>{doc.filename}</td>
                        <td><span className={`badge ${doc.file_type}`}>{doc.file_type}</span></td>
                        <td><span className="badge ok">{doc.status}</span></td>
                        <td>{doc.upload_timestamp ? new Date(doc.upload_timestamp).toLocaleDateString() : '—'}</td>
                        <td>
                          <button
                            className="btn btn-ghost"
                            onClick={() => openProof({ document_name: doc.filename, page_number: 1, bounding_box: [60, 100, 540, 220] }, doc.id)}
                          >
                            <FileText size={14} /> Open
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </section>
        )}

        {tab === 'review' && (
          <section>
            <div className="page-title">
              <h2>Review</h2>
              <p>When two filings disagree on the same mine, year, and metric, both values are kept.</p>
            </div>
            <div className="split">
              <div className="card">
                <h3>
                  <AlertTriangle size={16} style={{ verticalAlign: 'text-bottom', marginRight: 6 }} />
                  Discrepancies ({conflicts.length})
                </h3>
                <p className="hint">Tolerance 5%. Different source files only.</p>
                {conflicts.length === 0 ? (
                  <div className="empty">No mismatches in the current store.</div>
                ) : conflicts.map((c, i) => (
                  <div className="conflict" key={i} style={{ marginBottom: 10 }}>
                    <header>
                      <strong>{c.mine} · {c.subsidiary} · {c.year}</strong>
                      <span className="badge warn">{c.parameter}</span>
                    </header>
                    <div className="pair">
                      <div className="box">
                        <small>{c.source1}</small>
                        <b>{c.val1}</b>
                      </div>
                      <span className="neq">≠</span>
                      <div className="box">
                        <small>{c.source2}</small>
                        <b>{c.val2}</b>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="card">
                <h3>Executive brief</h3>
                <p className="hint">One-page PDF for a subsidiary and financial year.</p>
                <div className="field">
                  <label htmlFor="sub">Subsidiary</label>
                  <select id="sub" value={subsidiary} onChange={(e) => setSubsidiary(e.target.value)}>
                    {SUBS.map(([code, name]) => (
                      <option key={code} value={code}>{code} — {name}</option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label htmlFor="yr">Financial year</label>
                  <select id="yr" value={year} onChange={(e) => setYear(e.target.value)}>
                    {['2021-22', '2022-23', '2023-24', '2024-25'].map((y) => (
                      <option key={y} value={y}>{y}</option>
                    ))}
                  </select>
                </div>
                <button className="btn btn-primary" style={{ marginTop: 16 }} disabled={reporting} onClick={downloadReport}>
                  <Download size={16} />
                  {reporting ? 'Building…' : 'Download PDF'}
                </button>
              </div>
            </div>

            <div className="card">
              <h3>Topics in the corpus</h3>
              <p className="hint">Click a term to ask about it.</p>
              <div className="topics">
                {(topics.length ? topics : [{ text: 'Coal production', value: 1 }]).slice(0, 24).map((t) => (
                  <button
                    key={t.text}
                    type="button"
                    style={{ fontSize: 12 + Math.min(8, (t.value || 1) / 12) }}
                    onClick={() => { setTab('ask'); ask(`Compare coal production and stripping ratio for ${t.text}`) }}
                  >
                    {t.text}
                  </button>
                ))}
              </div>
            </div>
          </section>
        )}
      </main>

      {proof && (
        <ProofModal
          isOpen
          onClose={() => setProof(null)}
          source={proof.source}
          documentId={proof.documentId}
        />
      )}

      {toast && (
        <div className="toast" role="status">
          <b>{toast.title}</b>
          {toast.message}
          <button
            type="button"
            onClick={() => setToast(null)}
            style={{ position: 'absolute', right: 8, top: 8, background: 'none', border: 0, color: '#fff', cursor: 'pointer' }}
            aria-label="Dismiss"
          >
            <X size={14} />
          </button>
        </div>
      )}
    </div>
  )
}
