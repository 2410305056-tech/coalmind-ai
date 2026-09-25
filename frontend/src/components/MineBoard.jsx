function metricLine(row, fallbackUnit) {
  if (!row) return '—'
  const unit = row.unit || fallbackUnit
  return `${row.value} ${unit} · ${row.year || ''}`
}

export default function MineBoard({ mines }) {
  if (!mines?.length) {
    return <div className="empty">No mine metrics yet. Load the SIH sample pack.</div>
  }
  return (
    <div className="mine-grid">
      {mines.map((m) => (
        <article className="card mine-tile" key={m.mine}>
          <header>
            <h3>{m.mine}</h3>
            <span className="badge sql">{m.subsidiary}</span>
          </header>
          <dl>
            <div>
              <dt>Coal production</dt>
              <dd>{metricLine(m.production, 'MT')}</dd>
            </div>
            <div>
              <dt>Overburden (OBR)</dt>
              <dd>{metricLine(m.obr, 'M.Cum')}</dd>
            </div>
            <div>
              <dt>Stripping ratio</dt>
              <dd>{metricLine(m.stripping, 'ratio')}</dd>
            </div>
          </dl>
          <p className="hint" style={{ marginBottom: 0 }}>
            Last source: {m.last_source || '—'} {m.last_year ? `· ${m.last_year}` : ''}
          </p>
        </article>
      ))}
    </div>
  )
}
