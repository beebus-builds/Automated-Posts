import { useState, useEffect, useRef } from 'react'
import { api, HistoryEntry } from '../api/client'

export default function Dashboard() {
  const [caption, setCaption] = useState('')
  const [image, setImage] = useState<File | null>(null)
  const [preview, setPreview] = useState('')
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('')
  const [statusType, setStatusType] = useState('')
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => { api.getHistory().then(setHistory).catch(() => {}) }, [])

  const handleImage = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) {
      setImage(f)
      const reader = new FileReader()
      reader.onload = () => setPreview(reader.result as string)
      reader.readAsDataURL(f)
    }
  }

  const handlePost = async () => {
    if (!image) { setStatus('Select an image first'); setStatusType('error'); return }
    if (!caption.trim()) { setStatus('Write a caption'); setStatusType('error'); return }
    setLoading(true)
    setStatus('Posting to Facebook...')
    setStatusType('')
    try {
      const fd = new FormData()
      fd.append('image', image)
      fd.append('caption', caption)
      const r = await api.post(fd)
      setStatus(`Posted! ${r.fb_url || ''}`)
      setStatusType('success')
      setCaption('')
      setImage(null)
      setPreview('')
      if (fileRef.current) fileRef.current.value = ''
      api.getHistory().then(setHistory).catch(() => {})
    } catch (err) {
      setStatus(`Error: ${err instanceof Error ? err.message : 'Unknown'}`)
      setStatusType('error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="main-container">
      <div className="post-card">
        <h2>Post to Facebook</h2>

        <div className="upload-area" onClick={() => fileRef.current?.click()}>
          {preview ? <img src={preview} alt="preview" className="preview-img" /> : (
            <div className="upload-placeholder">
              <div className="upload-icon">+</div>
              <p>Click to select an image</p>
              <p className="hint">1080×1080 PNG recommended</p>
            </div>
          )}
          <input ref={fileRef} type="file" accept="image/*" onChange={handleImage} hidden />
        </div>

        <textarea
          className="caption-input"
          placeholder="Write your caption..."
          value={caption}
          onChange={e => setCaption(e.target.value)}
          rows={4}
        />

        <button className="post-btn" onClick={handlePost} disabled={loading || !image || !caption.trim()}>
          {loading ? <span className="spinner" /> : 'Post to Facebook'}
        </button>

        <div className={`status-msg ${statusType}`}>{status}</div>

        {history.length > 0 && (
          <div className="history-section">
            <button className="history-toggle" onClick={() => setShowHistory(!showHistory)}>
              {showHistory ? 'Hide' : 'Show'} History ({history.length})
            </button>
            {showHistory && (
              <div className="history-list">
                {history.map((h, i) => (
                  <div key={i} className="history-item">
                    <span className="hist-time">{h.timestamp.slice(0, 16).replace('T', ' ')}</span>
                    <span className="hist-cap">{h.caption.slice(0, 60)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <style>{`
        .main-container { flex: 1; display: flex; align-items: flex-start; justify-content: center; padding: clamp(24px, 5vw, 40px); }
        .post-card { background: var(--surface); padding: clamp(24px, 4vw, 40px); border-radius: clamp(20px, 3vw, 32px); border: 1px solid var(--border); max-width: 520px; width: 100%; box-shadow: 0 30px 60px rgba(0,0,0,0.5); animation: fadeIn 0.6s ease; }
        .post-card h2 { font-family: 'Playfair Display', serif; font-size: clamp(24px, 5vw, 32px); margin-bottom: clamp(16px, 3vw, 24px); text-align: center; }
        .upload-area { width: 100%; aspect-ratio: 1; background: var(--bg); border: 2px dashed var(--border); border-radius: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; overflow: hidden; margin-bottom: 16px; transition: border-color .3s; }
        .upload-area:hover { border-color: var(--red); }
        .preview-img { width: 100%; height: 100%; object-fit: cover; }
        .upload-placeholder { text-align: center; color: var(--text-dim); padding: 40px; }
        .upload-icon { font-size: 48px; font-weight: 200; color: var(--red); line-height: 1; margin-bottom: 8px; }
        .hint { font-size: 12px; opacity: 0.6; }
        .caption-input { width: 100%; background: var(--bg); border: 1px solid var(--border); border-radius: 12px; padding: 14px 16px; color: var(--text); font-size: 14px; resize: vertical; margin-bottom: 16px; box-sizing: border-box; outline: none; }
        .caption-input:focus { border-color: var(--red); }
        .post-btn { width: 100%; padding: 16px; border: none; border-radius: 14px; background: linear-gradient(135deg, var(--red), #ff1744); color: #fff; font-size: 18px; font-weight: 800; cursor: pointer; transition: all .3s; text-transform: uppercase; letter-spacing: .1em; box-shadow: 0 10px 30px var(--glow); display: flex; align-items: center; justify-content: center; gap: 10px; }
        .post-btn:hover { transform: scale(1.02); box-shadow: 0 15px 40px var(--glow); }
        .post-btn:disabled { background: var(--border); color: var(--text-dim); cursor: not-allowed; transform: none; box-shadow: none; }
        .spinner { width: 20px; height: 20px; border: 2px solid rgba(255,255,255,0.3); border-top: 2px solid #fff; border-radius: 50%; animation: spin 0.8s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .status-msg { margin-top: 16px; text-align: center; font-size: 13px; min-height: 20px; word-break: break-word; }
        .status-msg.success { color: #22c55e; font-weight: 600; }
        .status-msg.error { color: var(--red); font-weight: 600; }
        .history-section { margin-top: 20px; }
        .history-toggle { background: none; border: 1px solid var(--border); color: var(--text-dim); padding: 8px 16px; border-radius: 8px; cursor: pointer; font-size: 12px; width: 100%; }
        .history-list { margin-top: 8px; max-height: 200px; overflow-y: auto; }
        .history-item { display: flex; gap: 12px; padding: 8px 4px; border-bottom: 1px solid var(--border); font-size: 12px; }
        .hist-time { color: var(--text-dim); white-space: nowrap; font-size: 11px; }
        .hist-cap { color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        @media (max-width: 480px) {
          .post-card { padding: 20px 16px; border-radius: 16px; }
        }
      `}</style>
    </div>
  )
}
