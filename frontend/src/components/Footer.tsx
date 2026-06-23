export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-grid">
        <div className="footer-col footer-about">
          <h3>MATCH DAY</h3>
          <p>Dedicated to the heartbeat of Nepal's football.</p>
        </div>
        <div className="footer-col">
          <h3>Quick Links</h3>
          <ul className="footer-links">
            <li><a href="/">The Arena</a></li>
            <li><a href="/vault">The Vault</a></li>
            <li><a href="/community">Community</a></li>
          </ul>
        </div>
        <div className="footer-col">
          <h3>Network</h3>
          <ul className="footer-links">
            <li><a href="#">Sponsors</a></li>
            <li><a href="#">Press Kit</a></li>
          </ul>
        </div>
        <div className="footer-col">
          <h3>Legal</h3>
          <ul className="footer-links">
            <li><a href="#">Privacy Policy</a></li>
            <li><a href="#">Terms</a></li>
          </ul>
        </div>
      </div>
      <div className="footer-bottom">
        <div>&copy; 2026 Match Day - Nepal's Football Community.</div>
        <div>Designed for the Game.</div>
      </div>

      <style>{`
        .footer { background: var(--surface); border-top: 1px solid var(--border); padding: clamp(32px, 6vw, 60px) clamp(16px, 4vw, 24px) clamp(20px, 4vw, 30px); margin-top: auto; }
        .footer-grid { max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: clamp(20px, 4vw, 40px); }
        .footer-col h3 { font-family: 'Playfair Display', serif; font-size: clamp(16px, 3vw, 20px); margin-bottom: clamp(16px, 3vw, 24px); color: #fff; position: relative; display: inline-block; }
        .footer-col h3::after { content: ''; position: absolute; bottom: -4px; left: 0; width: 30px; height: 2px; background: var(--red); }
        .footer-links { list-style: none; }
        .footer-links li { margin-bottom: 12px; }
        .footer-links a { color: var(--text-dim); font-size: clamp(13px, 2.5vw, 14px); transition: all .3s; }
        .footer-links a:hover { color: var(--red); padding-left: 5px; }
        .footer-bottom { max-width: 1200px; margin: clamp(24px, 4vw, 40px) auto 0; padding-top: clamp(16px, 3vw, 24px); border-top: 1px solid var(--border); display: flex; flex-wrap: wrap; gap: 8px; justify-content: space-between; font-size: clamp(11px, 2vw, 12px); color: var(--text-dim); }
        @media (max-width: 480px) {
          .footer-grid { grid-template-columns: 1fr; }
          .footer-bottom { flex-direction: column; align-items: center; text-align: center; }
        }
      `}</style>
    </footer>
  )
}
