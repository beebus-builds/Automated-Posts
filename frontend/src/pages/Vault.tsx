import { useEffect, useState } from 'react'
import { api, HistoryEntry } from '../api/client'

export default function Vault() {
  const [entries, setEntries] = useState<HistoryEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadVault()
  }, [])

  const loadVault = async () => {
    setLoading(true)
    try {
      const data = await api.getHistory()
      setEntries(data)
    } catch {
      setError('Failed to load the vault.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="content">
      <div className="page-header">
        <h2>The Vault</h2>
        <p>Archiving the history of the game, one post at a time.</p>
      </div>

      {loading && <p className="empty-msg">Loading...</p>}
      {error && <p className="error-msg">{error}</p>}
      {!loading && !error && entries.length === 0 && (
        <p className="empty-msg">The vault is empty. Start posting in the Arena!</p>
      )}

      {entries.length > 0 && (
        <div className="vault-grid">
          {entries.map((entry, i) => (
            <div className="vault-card" key={i}>
              <img
                src="/api/image/placeholder.png"
                onError={e => { (e.target as HTMLImageElement).src = 'https://via.placeholder.com/400' }}
                alt="Post"
              />
              <div className="vault-card-info">
                <div className="vault-card-type">{entry.is_video ? 'Video' : 'Photo'}</div>
                <div className="vault-card-caption">{entry.caption}</div>
                <div className="vault-card-date">
                  {new Date(entry.timestamp).toLocaleDateString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <style>{`
        .content { flex: 1; max-width: 1200px; margin: clamp(32px, 6vw, 60px) auto; padding: 0 clamp(16px, 4vw, 24px); width: 100%; }
        .page-header { text-align: center; margin-bottom: clamp(32px, 5vw, 50px); }
        .page-header h2 { font-family: 'Playfair Display', serif; font-size: clamp(32px, 7vw, 48px); margin-bottom: 10px; }
        .page-header p { color: var(--text-dim); font-size: clamp(14px, 3vw, 18px); }
        .empty-msg, .error-msg { text-align: center; color: var(--text-dim); grid-column: 1 / -1; }
        .error-msg { color: var(--red); }
        .vault-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(280px, 100%), 1fr)); gap: clamp(16px, 3vw, 24px); }
        .vault-card { background: var(--surface); border: 1px solid var(--border); border-radius: 24px; overflow: hidden; transition: transform .3s; }
        .vault-card:hover { transform: translateY(-5px); border-color: var(--red); }
        .vault-card img { width: 100%; aspect-ratio: 1/1; object-fit: cover; display: block; }
        .vault-card-info { padding: clamp(14px, 3vw, 20px); }
        .vault-card-type { font-size: 10px; text-transform: uppercase; color: var(--red); font-weight: 800; letter-spacing: .1em; }
        .vault-card-caption { font-size: clamp(13px, 2.5vw, 14px); margin: 8px 0; line-height: 1.5; word-break: break-word; }
        .vault-card-date { font-size: 12px; color: var(--text-dim); }
        @media (max-width: 480px) { .vault-grid { grid-template-columns: 1fr; } }
      `}</style>
    </div>
  )
}
