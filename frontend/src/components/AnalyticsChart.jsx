export default function AnalyticsChart({ chartData }) {
  if (!chartData?.labels?.length) return null
  const { labels, values, unit = 'MT' } = chartData
  const max = Math.max(...values, 1)
  const w = 640
  const h = 220
  const pad = { t: 16, r: 12, b: 48, l: 40 }
  const innerW = w - pad.l - pad.r
  const innerH = h - pad.t - pad.b
  const bw = innerW / labels.length
  const bar = Math.max(18, bw * 0.48)

  return (
    <div style={{ marginTop: 20 }}>
      <p style={{ fontSize: 12, color: '#5f6368', marginBottom: 8 }}>
        {unit} · from indexed metrics
      </p>
      <svg viewBox={`0 0 ${w} ${h}`} width="100%" role="img" aria-label="Metric comparison">
        {[0.25, 0.5, 0.75, 1].map((g) => (
          <line
            key={g}
            x1={pad.l}
            x2={w - pad.r}
            y1={pad.t + innerH * (1 - g)}
            y2={pad.t + innerH * (1 - g)}
            stroke="#dadce0"
          />
        ))}
        {values.map((v, i) => {
          const bh = (v / max) * innerH
          const x = pad.l + i * bw + (bw - bar) / 2
          const y = pad.t + innerH - bh
          return (
            <g key={labels[i]}>
              <rect x={x} y={y} width={bar} height={bh} rx="2" fill="#1b3a4b" />
              <text x={x + bar / 2} y={y - 6} textAnchor="middle" fontSize="11" fill="#202124">
                {v}
              </text>
              <text
                x={x + bar / 2}
                y={h - 16}
                textAnchor="middle"
                fontSize="10"
                fill="#5f6368"
              >
                {String(labels[i]).slice(0, 18)}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}
