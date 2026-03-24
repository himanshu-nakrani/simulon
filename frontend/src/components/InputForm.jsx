import { useState } from 'react';
import axios from 'axios';

// In production (GitHub Pages) point to the HF Space backend.
// In dev, Vite proxies /simulate to localhost:8000.
const API_BASE = import.meta.env.PROD
  ? 'https://himanshunakrani9-decision-simulator-api.hf.space'
  : '';

const s = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '24px 16px',
  },
  card: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    padding: '40px',
    width: '100%',
    maxWidth: 520,
    boxShadow: '0 24px 64px rgba(0,0,0,0.4)',
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    marginBottom: 8,
  },
  logoIcon: {
    width: 36,
    height: 36,
    background: 'linear-gradient(135deg, var(--accent), #a78bfa)',
    borderRadius: 10,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 18,
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: 700,
    color: 'var(--text)',
  },
  subtitle: {
    color: 'var(--text-muted)',
    fontSize: '0.9rem',
    marginBottom: 32,
  },
  field: { marginBottom: 24 },
  label: {
    display: 'block',
    fontSize: '0.85rem',
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    marginBottom: 8,
  },
  sliderRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    marginTop: 8,
  },
  sliderValue: {
    background: 'var(--surface2)',
    border: '1px solid var(--border)',
    borderRadius: 6,
    padding: '4px 10px',
    fontSize: '0.85rem',
    fontWeight: 600,
    color: 'var(--accent-light)',
    minWidth: 48,
    textAlign: 'center',
  },
  sliderLabels: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '0.75rem',
    color: 'var(--text-muted)',
    marginTop: 4,
  },
  error: {
    background: 'rgba(239,68,68,0.1)',
    border: '1px solid rgba(239,68,68,0.3)',
    borderRadius: 8,
    padding: '10px 14px',
    color: '#fca5a5',
    fontSize: '0.875rem',
    marginBottom: 20,
  },
  btn: {
    width: '100%',
    padding: '13px',
    background: 'linear-gradient(135deg, var(--accent), #a78bfa)',
    color: '#fff',
    fontSize: '1rem',
    fontWeight: 600,
    borderRadius: 8,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  spinner: {
    width: 16,
    height: 16,
    border: '2px solid rgba(255,255,255,0.3)',
    borderTopColor: '#fff',
    borderRadius: '50%',
    animation: 'spin 0.7s linear infinite',
  },
};

export default function InputForm({ onResult }) {
  const [decisionText, setDecisionText] = useState('');
  const [risk, setRisk] = useState(0.5);
  const [timeHorizon, setTimeHorizon] = useState(3);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { data } = await axios.post(`${API_BASE}/simulate`, {
        decision_text: decisionText,
        risk: parseFloat(risk),
        time_horizon: parseInt(timeHorizon, 10),
      });
      onResult(data);
    } catch (err) {
      const msg = err.response?.data?.detail
        ? JSON.stringify(err.response.data.detail)
        : err.message || 'An unexpected error occurred.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <div style={s.page}>
        <div style={s.card}>
          <div style={s.logo}>
            <div style={s.logoIcon}>🔮</div>
            <span style={s.title}>Decision Simulator</span>
          </div>
          <p style={s.subtitle}>Simulate parallel outcomes for any decision using AI + probability.</p>

          <form onSubmit={handleSubmit}>
            <div style={s.field}>
              <label style={s.label} htmlFor="decision-text">Your Decision</label>
              <textarea
                id="decision-text"
                rows={4}
                value={decisionText}
                onChange={(e) => setDecisionText(e.target.value)}
                placeholder="e.g. Should I switch jobs, move cities, or start a business?"
                required
              />
            </div>

            <div style={s.field}>
              <label style={s.label} htmlFor="risk-slider">Risk Tolerance</label>
              <div style={s.sliderRow}>
                <input
                  id="risk-slider"
                  type="range"
                  min={0} max={1} step={0.01}
                  value={risk}
                  onChange={(e) => setRisk(e.target.value)}
                  style={{ flex: 1 }}
                />
                <span style={s.sliderValue}>{parseFloat(risk).toFixed(2)}</span>
              </div>
              <div style={s.sliderLabels}>
                <span>Conservative</span>
                <span>Aggressive</span>
              </div>
            </div>

            <div style={s.field}>
              <label style={s.label} htmlFor="time-horizon">Time Horizon (years)</label>
              <input
                id="time-horizon"
                type="number"
                min={1} step={1}
                value={timeHorizon}
                onChange={(e) => setTimeHorizon(e.target.value)}
                required
              />
            </div>

            {error && <div style={s.error}>⚠ {error}</div>}

            <button type="submit" disabled={loading} style={s.btn}>
              {loading ? (
                <>
                  <span style={s.spinner} />
                  Simulating parallel universes…
                </>
              ) : (
                '✦ Run Simulation'
              )}
            </button>
          </form>
        </div>
      </div>
    </>
  );
}
