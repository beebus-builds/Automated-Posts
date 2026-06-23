import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

const navLinks = [
  { path: '/', label: 'The Arena' },
  { path: '/vault', label: 'The Vault' },
  { path: '/community', label: 'Community' },
  { path: '/guidelines', label: 'Guidelines' },
]

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)
  const location = useLocation()

  const closeMenu = () => setMenuOpen(false)

  return (
    <nav className="nav-system">
      <div className="nav-top">
        <div className="brand-tag">Match Day v2.0</div>
        <div className="nav-ticker">
          <div className="ticker-content">AUTOMATED BROADCAST ACTIVE: Monitoring live games 24/7...</div>
        </div>
        <div className="nav-auth">PRO ACCOUNT</div>
      </div>

      <div className="nav-main">
        <Link to="/" className="nav-brand">
          <div className="nav-logo-mark">MD</div>
          <h1>MATCH DAY</h1>
        </Link>

        <button
          className={`nav-toggle ${menuOpen ? 'active' : ''}`}
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Menu"
        >
          <span className="nav-toggle-bar" />
          <span className="nav-toggle-bar" />
          <span className="nav-toggle-bar" />
        </button>

        <div className={`nav-links ${menuOpen ? 'open' : ''}`}>
          {navLinks.map(link => (
            <Link
              key={link.path}
              to={link.path}
              className={`nav-link${location.pathname === link.path ? ' active' : ''}`}
              onClick={closeMenu}
            >
              {link.label}
            </Link>
          ))}
          <Link to="/" className="nav-cta" onClick={closeMenu}>Post</Link>
        </div>
      </div>

      <style>{`
        .nav-system { position: sticky; top: 0; z-index: 1000; width: 100%; }
        .nav-top { background: var(--navy-dark); height: 40px; display: flex; align-items: center; justify-content: space-between; padding: 0 16px; border-bottom: 1px solid var(--border); font-size: 11px; color: var(--text-dim); }
        .nav-ticker { flex: 1; margin: 0 16px; overflow: hidden; white-space: nowrap; background: rgba(255,255,255,0.03); padding: 4px 12px; border-radius: 20px; }
        .ticker-content { display: inline-block; animation: ticker 30s linear infinite; }
        .nav-main { background: rgba(26,35,50,0.8); backdrop-filter: blur(20px); padding: 12px 16px; display: flex; align-items: center; justify-content: space-between; border-bottom: 3px solid var(--red); clip-path: polygon(0 0, 100% 0, 100% 90%, 98% 100%, 0 100%); }
        .nav-brand { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
        .nav-logo-mark { width: 32px; height: 32px; background: var(--red); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 12px; color: #fff; box-shadow: 0 0 15px var(--glow); }
        .nav-brand h1 { font-size: clamp(16px, 4vw, 22px); font-weight: 800; }
        .nav-links { display: flex; gap: clamp(8px, 2vw, 32px); align-items: center; }
        .nav-link { color: var(--text-dim); font-size: clamp(11px, 2.5vw, 14px); font-weight: 600; transition: all .3s; position: relative; white-space: nowrap; }
        .nav-link:hover { color: var(--text); }
        .nav-link.active { color: var(--text); }
        .nav-link.active::after { content: ''; position: absolute; bottom: -2px; left: 0; width: 100%; height: 2px; background: var(--red); }
        .nav-cta { background: var(--red); color: #fff; padding: 6px 14px; border-radius: 50px; font-size: clamp(11px, 2.5vw, 13px); font-weight: 800; white-space: nowrap; }
        .nav-toggle { display: none; background: none; border: none; color: var(--text); font-size: 28px; cursor: pointer; padding: 4px 8px; line-height: 1; }
        .nav-toggle-bar { display: block; width: 24px; height: 2px; background: var(--text); margin: 5px 0; transition: all .3s; border-radius: 2px; }
        .nav-toggle.active .nav-toggle-bar:nth-child(1) { transform: rotate(45deg) translate(5px, 5px); }
        .nav-toggle.active .nav-toggle-bar:nth-child(2) { opacity: 0; }
        .nav-toggle.active .nav-toggle-bar:nth-child(3) { transform: rotate(-45deg) translate(5px, -5px); }
        @media (max-width: 768px) {
          .nav-toggle { display: block; }
          .nav-links { display: none; position: absolute; top: 100%; left: 0; right: 0; background: rgba(19,29,43,0.98); backdrop-filter: blur(20px); flex-direction: column; padding: 16px; gap: 4px; border-bottom: 3px solid var(--red); z-index: 999; }
          .nav-links.open { display: flex; }
          .nav-links .nav-link, .nav-links .nav-cta { width: 100%; text-align: center; padding: 12px 16px; font-size: 14px; border-radius: 8px; }
          .nav-main { position: relative; clip-path: none; }
          .nav-ticker { display: none; }
        }
      `}</style>
    </nav>
  )
}
