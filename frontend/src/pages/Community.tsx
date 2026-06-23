export default function Community() {
  return (
    <div className="content">
      <div className="page-header">
        <h2>Community</h2>
        <p>Join Nepal's fastest growing football community.</p>
      </div>

      <div className="community-card">
        <h3>About Us</h3>
        <p>Match Day is dedicated to bringing real-time football coverage to Nepal's passionate fanbase. From live match updates to post-match analysis, we bridge the gap between the pitch and the people.</p>
      </div>

      <div className="community-card">
        <h3>Community Stats</h3>
        <div className="community-stats">
          <div className="stat-box">
            <div className="number">1K+</div>
            <div className="label">Facebook Fans</div>
          </div>
          <div className="stat-box">
            <div className="number">100+</div>
            <div className="label">Matches Covered</div>
          </div>
          <div className="stat-box">
            <div className="number">24/7</div>
            <div className="label">Live Coverage</div>
          </div>
        </div>
      </div>

      <div className="community-card">
        <h3>Stay Connected</h3>
        <p>Follow us on Facebook for live match updates, goal alerts, and post-match analysis. Together we celebrate the beautiful game.</p>
      </div>

      <style>{`
        .content { flex: 1; max-width: 800px; margin: clamp(40px, 8vw, 80px) auto; padding: 0 clamp(16px, 4vw, 24px); width: 100%; }
        .page-header { text-align: center; margin-bottom: clamp(32px, 6vw, 60px); }
        .page-header h2 { font-family: 'Playfair Display', serif; font-size: clamp(32px, 8vw, 54px); margin-bottom: 15px; }
        .page-header p { color: var(--text-dim); font-size: clamp(14px, 3vw, 20px); }
        .community-card { background: var(--surface); padding: clamp(20px, 4vw, 30px); border-radius: 24px; border: 1px solid var(--border); margin-bottom: 24px; }
        .community-card h3 { color: var(--red); font-size: clamp(18px, 3.5vw, 22px); margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }
        .community-card p { color: var(--text-dim); line-height: 1.7; font-size: clamp(14px, 2.5vw, 16px); }
        .community-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: clamp(12px, 3vw, 20px); margin-top: 20px; }
        .stat-box { background: rgba(255,255,255,0.03); padding: 20px; border-radius: 16px; text-align: center; }
        .stat-box .number { font-size: clamp(24px, 5vw, 36px); font-weight: 800; color: var(--red); }
        .stat-box .label { font-size: 12px; color: var(--text-dim); margin-top: 4px; }
        @media (max-width: 480px) { .community-stats { grid-template-columns: 1fr; } }
      `}</style>
    </div>
  )
}
