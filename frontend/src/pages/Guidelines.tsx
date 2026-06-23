export default function Guidelines() {
  return (
    <div className="content">
      <div className="page-header">
        <h2>Guidelines</h2>
        <p>How to create the perfect match day post.</p>
      </div>

      <div className="guide-section">
        <h3>1. Choose Your Event</h3>
        <p>Every event has a specific visual language. Goals are high-energy, Cards are dramatic, and Full-Time results are celebratory.</p>
      </div>
      <div className="guide-section">
        <h3>2. The Hero Asset</h3>
        <p>A high-resolution transparent PNG of the player is recommended. If unavailable, our system generates a premium brand silhouette.</p>
      </div>
      <div className="guide-section">
        <h3>3. Flag Accuracy</h3>
        <p>Always use the correct ISO 2-letter country code (e.g., 'np' for Nepal) to ensure the correct waving flag is generated.</p>
      </div>
      <div className="guide-section">
        <h3>4. Community Spirit</h3>
        <p>Keep captions respectful and exciting. We are here to celebrate the beautiful game!</p>
      </div>

      <style>{`
        .content { flex: 1; max-width: 800px; margin: clamp(40px, 8vw, 80px) auto; padding: 0 clamp(16px, 4vw, 24px); width: 100%; }
        .page-header { text-align: center; margin-bottom: clamp(32px, 6vw, 60px); }
        .page-header h2 { font-family: 'Playfair Display', serif; font-size: clamp(32px, 8vw, 54px); margin-bottom: 15px; }
        .page-header p { color: var(--text-dim); font-size: clamp(14px, 3vw, 20px); }
        .guide-section { background: var(--surface); padding: clamp(20px, 4vw, 30px); border-radius: 24px; border: 1px solid var(--border); margin-bottom: 24px; }
        .guide-section h3 { color: var(--red); font-size: clamp(18px, 3.5vw, 22px); margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }
        .guide-section p { color: var(--text-dim); line-height: 1.7; font-size: clamp(14px, 2.5vw, 16px); }
      `}</style>
    </div>
  )
}
