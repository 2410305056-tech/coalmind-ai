import { pythonApiEnabled, apiUrl } from '../lib/api'

export default function ProofModal({ isOpen, onClose, source, documentId }) {
  if (!isOpen || !source) return null
  const page = source.page_number || 1
  const raw = source.bounding_box
  const bbox = Array.isArray(raw) && raw.length >= 4 ? raw : [72, 120, 520, 200]
  const [x0, y0, x1, y1] = bbox
  const nw = 612
  const nh = 792
  const left = Math.max(2, Math.min(90, (x0 / nw) * 100))
  const top = Math.max(4, Math.min(90, (y0 / nh) * 100))
  const width = Math.max(12, Math.min(96 - left, ((x1 - x0) / nw) * 100))
  const height = Math.max(6, Math.min(40, ((y1 - y0) / nh) * 100))
  const canFile = pythonApiEnabled() && documentId
  const src = canFile ? apiUrl(`/api/documents/${documentId}/file`) : ''

  return (
    <div className="modal-back" onClick={onClose} role="presentation">
      <div className="modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
        <div className="modal-head">
          <div>
            <h3>{source.document_name}</h3>
            <p className="hint" style={{ margin: 0 }}>Page {page}</p>
          </div>
          <button className="btn btn-ghost" type="button" onClick={onClose}>Close</button>
        </div>
        <div className="modal-body">
          {src ? (
            <div className="pdf-frame">
              <iframe title="Source document" src={src} />
              <div
                className="hl"
                style={{ left: `${left}%`, top: `${top}%`, width: `${width}%`, height: `${height}%` }}
              />
            </div>
          ) : (
            <div className="empty">
              Citation: {source.document_name}, page {page}.
              Open the local API to preview the file.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
