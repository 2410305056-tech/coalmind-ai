import { Download } from 'lucide-react'

function plain(text) {
  return String(text || '')
    .replace(/\*\*/g, '')
    .replace(/^>\s?/gm, '')
    .replace(/^[-*•]\s+/gm, '')
}

function bulletsFrom(result) {
  const lines = plain(result?.answer)
    .split(/\n+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 12)
  const picked = []
  for (const line of lines) {
    if (picked.length >= 3) break
    if (line.length > 220) picked.push(`${line.slice(0, 217)}…`)
    else picked.push(line)
  }
  while (picked.length < 3) picked.push('See cited source for remaining detail.')
  return picked.slice(0, 3)
}

export default function BriefingCard({ result, onViewSource }) {
  if (!result) return null
  const bullets = bulletsFrom(result)
  const labels = result.chart_data?.labels || []
  const values = result.chart_data?.values || []
  const unit = result.chart_data?.unit || 'MT'
  const cite = result.sources?.[0]

  const downloadNote = () => {
    const table = labels.map((l, i) => `${l}\t${values[i]} ${unit}`).join('\n')
    const body = [
      'CoalMind AI — Officer briefing note',
      `Generated: ${new Date().toLocaleString()}`,
      '',
      '1. Key points',
      ...bullets.map((b, i) => `  ${i + 1}. ${b}`),
      '',
      '2. Figures',
      table || '  (no structured metrics for this question)',
      '',
      '3. Citation',
      cite
        ? `  ${cite.document_name}, page ${cite.page_number}`
        : '  Archive source not attached',
      '',
      'Prepared for CMPDI / CIL review. Figures are grounded on ingested filings.',
    ].join('\n')
    const blob = new Blob([body], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'CoalMind_Officer_Note.txt'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="card briefing">
      <div className="briefing-head">
        <h3>Officer briefing</h3>
        <button type="button" className="btn btn-primary" onClick={downloadNote}>
          <Download size={14} /> Download as note
        </button>
      </div>
      <ol className="brief-bullets">
        {bullets.map((b) => <li key={b}>{b}</li>)}
      </ol>
      {labels.length > 0 && (
        <div className="table-wrap" style={{ padding: 0, marginTop: 12 }}>
          <table className="data">
            <thead>
              <tr>
                <th>Mine / period</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {labels.slice(0, 8).map((l, i) => (
                <tr key={l}>
                  <td>{l}</td>
                  <td>{values[i]} {unit}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {cite && (
        <p className="cite-line">
          Citation: <strong>{cite.document_name}</strong> · page {cite.page_number}{' '}
          {onViewSource && (
            <button type="button" className="btn btn-ghost" onClick={() => onViewSource(cite)}>
              Open
            </button>
          )}
        </p>
      )}
    </div>
  )
}
