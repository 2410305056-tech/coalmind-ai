const FOCUS = ['Gevra', 'Kusmunda', 'Dipka']

function latest(rows, needle) {
  const hits = rows.filter((r) => String(r.parameter || '').toLowerCase().includes(needle))
  hits.sort((a, b) => String(b.year || '').localeCompare(String(a.year || '')))
  return hits[0] || null
}

export function buildMineSnapshot(rows = []) {
  return FOCUS.map((mine) => {
    const mineRows = rows.filter((r) => String(r.mine || '').toLowerCase().startsWith(mine.toLowerCase()))
    const production = latest(mineRows, 'production')
    const obr = latest(mineRows, 'overburden') || latest(mineRows, 'obr')
    const stripping = latest(mineRows, 'stripping')
    const last = production || obr || stripping || mineRows[mineRows.length - 1] || null
    return {
      mine,
      subsidiary: last?.subsidiary || 'SECL',
      production,
      obr,
      stripping,
      last_source: last?.source_doc,
      last_year: last?.year,
    }
  })
}
