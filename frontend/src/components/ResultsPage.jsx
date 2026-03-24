const s = {
  page: {
    minHeight: '100vh',
    padding: '40px 16px',
    maxWidth: 860,
    margin: '0 auto',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 32,
    flexWrap: 'wrap',
    gap: 12,
  },
  titleGroup: {},
  title: { fontSize: '1.5rem', fontWeight: 700 },
  subtitle: { color: 'var(--text-muted)', fontSize: '0.875rem', marginTop: 2 },
  backBtn: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    color: 'var(--text)',
    padding: '8px 16px',
    borderRadius: 8,
    fontSize: '0.875rem',
    fontWeight: 500,
  },
  bestCard: {
    background: 'var(--green-bg)',
    border: '1px solid rgba(34,197,94,0.35)',
    borderRadius: 'var(--radius)',
    padding: '20px 24px',
    marginBottom: 24,
    display: 'flex',
    alignItems: 'flex-start',
    gap: 14,
  },
  bestIcon: { fontSize: 28, lineHeight: 1 },
  bestLabel: { fontSize: '0.75rem', fontWeight: 600, color: 'var(--green)', textTransform: 'uppercase', letterSpacing: '0.06em' },
  bestValue: { fontSize: '1.25rem', fontWeight: 700, color: '#86efac', marginTop: 2 },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 },
  card: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    padding: '20px 24px',
  },
  cardTitle: {
    fontSize: '0.75rem',
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    marginBottom: 16,
  },
  explanationText: { color: 'var(--text)', lineHeight: 1.7, fontSize: '0.95rem' },
  rankItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '10px 0',
    borderBottom: '1px solid var(--border)',
  },
  rankNum: {
    width: 28,
    height: 28,
    borderRadius: '50%',
    background: 'var(--surface2)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '0.8rem',
    fontWeight: 700,
    color: 'var(--text-muted)',
    flexShrink: 0,
  },
  rankNumFirst: {
    background: 'linear-gradient(135deg, var(--accent), #a78bfa)',
    color: '#fff',
  },
  rankOption: { flex: 1, fontWeight: 500, fontSize: '0.9rem' },
  rankBar: { flex: 2, height: 6, background: 'var(--border)', borderRadius: 3, overflow: 'hidden' },
  rankBarFill: { height: '100%', borderRadius: 3, background: 'linear-gradient(90deg, var(--accent), #a78bfa)' },
  rankScore: { fontSize: '0.8rem', color: 'var(--text-muted)', minWidth: 52, textAlign: 'right' },
  summaryCard: {
    background: 'linear-gradient(135deg, rgba(108,99,255,0.08), rgba(167,139,250,0.06))',
    border: '1px solid rgba(108,99,255,0.25)',
    borderRadius: 'var(--radius)',
    padding: '20px 24px',
    marginBottom: 24,
  },
  summaryTitle: {
    fontSize: '0.75rem',
    fontWeight: 600,
    color: 'var(--accent-light)',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    marginBottom: 14,
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
  summaryLine: {
    color: 'var(--text)',
    fontSize: '0.95rem',
    lineHeight: 1.75,
    marginBottom: 8,
  },
  tableWrap: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    overflow: 'hidden',
    marginBottom: 32,
  },
  tableTitle: {
    padding: '16px 20px',
    fontSize: '0.75rem',
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    borderBottom: '1px solid var(--border)',
  },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' },
  th: {
    padding: '10px 16px',
    textAlign: 'left',
    color: 'var(--text-muted)',
    fontWeight: 600,
    fontSize: '0.78rem',
    background: 'var(--surface2)',
    borderBottom: '1px solid var(--border)',
  },
  td: {
    padding: '11px 16px',
    borderBottom: '1px solid var(--border)',
    color: 'var(--text)',
  },
  tdMuted: { color: 'var(--text-muted)' },
  pill: {
    display: 'inline-block',
    padding: '2px 8px',
    borderRadius: 20,
    fontSize: '0.75rem',
    fontWeight: 600,
  },
};

function ScoreBar({ value, max }) {
  const pct = max > 0 ? Math.max(0, (value / max) * 100) : 0;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <div style={{ flex: 1, height: 5, background: 'var(--border)', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: 'linear-gradient(90deg, var(--accent), #a78bfa)', borderRadius: 3 }} />
      </div>
      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', minWidth: 44, textAlign: 'right' }}>
        {value.toFixed(3)}
      </span>
    </div>
  );
}

function buildSummary(best_option, ranked, results) {
  if (!results.length || !ranked.length) return null;

  const best = ranked[0];
  const worst = ranked[ranked.length - 1];
  const isClose = ranked.length > 1 && Math.abs(best.score - ranked[1].score) < 0.05;

  // Avg salary for best option
  const bestResults = results.filter(r => r.option === best_option);
  const avgSalary = bestResults.reduce((s, r) => s + r.salary, 0) / bestResults.length;
  const avgRisk = bestResults.reduce((s, r) => s + r.risk_score, 0) / bestResults.length;
  const avgHappiness = bestResults.reduce((s, r) => s + r.happiness, 0) / bestResults.length;

  const riskLabel = avgRisk >= 0.65 ? 'high risk' : avgRisk >= 0.35 ? 'moderate risk' : 'low risk';
  const happinessLabel = avgHappiness >= 0.7 ? 'very happy' : avgHappiness >= 0.45 ? 'reasonably satisfied' : 'somewhat stressed';

  const lines = [];

  lines.push(`Out of ${ranked.length} options, the simulation points to **${best_option}** as your best path forward.`);

  lines.push(`On average, this choice could bring you around **$${Math.round(avgSalary).toLocaleString()} per year** — and you'd likely feel **${happinessLabel}** with the outcome. The overall risk level is **${riskLabel}**.`);

  if (isClose && ranked.length > 1) {
    lines.push(`It's worth noting that **${ranked[1].option}** is a close second — the difference is small, so if you have a personal preference for that path, it's not a bad choice either.`);
  } else if (ranked.length > 1) {
    lines.push(`Compared to **${worst.option}**, this option scores noticeably better when balancing salary, happiness, and risk together.`);
  }

  const bestScenario = bestResults.sort((a, b) => b.score - a.score)[0];
  const worstScenario = bestResults.sort((a, b) => a.score - b.score)[0];
  if (bestScenario && worstScenario && bestScenario.scenario !== worstScenario.scenario) {
    lines.push(`The best case for this option is the **"${bestScenario.scenario}"** scenario. Even in a tougher scenario like **"${worstScenario.scenario}"**, it still holds up reasonably well.`);
  }

  return lines;
}

function riskColor(v) {
  if (v >= 0.7) return { color: '#fca5a5', background: 'rgba(239,68,68,0.12)' };
  if (v >= 0.4) return { color: '#fde68a', background: 'rgba(234,179,8,0.12)' };
  return { color: '#86efac', background: 'rgba(34,197,94,0.12)' };
}

export default function ResultsPage({ result, onBack }) {
  const { best_option, explanation, results = [] } = result;

  const optionScores = {};
  results.forEach(({ option, score, probability }) => {
    if (!(option in optionScores)) optionScores[option] = 0;
    optionScores[option] += score * probability;
  });
  const ranked = Object.entries(optionScores)
    .map(([option, score]) => ({ option, score }))
    .sort((a, b) => b.score - a.score);

  const maxScoreAbs = Math.max(...ranked.map(r => Math.abs(r.score)), 0.001);
  const summary = buildSummary(best_option, ranked, results);

  // Render **bold** markdown in a string as JSX
  function renderLine(text, key) {
    const parts = text.split(/\*\*(.+?)\*\*/g);
    return (
      <p key={key} style={s.summaryLine}>
        {parts.map((p, i) => i % 2 === 1 ? <strong key={i}>{p}</strong> : p)}
      </p>
    );
  }

  return (
    <div style={s.page}>
      <div style={s.header}>
        <div style={s.titleGroup}>
          <div style={s.title}>Simulation Results</div>
          <div style={s.subtitle}>{results.length} scenarios across {ranked.length} options</div>
        </div>
        <button style={s.backBtn} onClick={onBack}>← New Simulation</button>
      </div>

      {/* Best option */}
      <div style={s.bestCard}>
        <div style={s.bestIcon}>🏆</div>
        <div>
          <div style={s.bestLabel}>Recommended Option</div>
          <div style={s.bestValue}>{best_option}</div>
        </div>
      </div>

      {/* Plain-English summary */}
      {summary && (
        <div style={s.summaryCard}>
          <div style={s.summaryTitle}>💡 What this means for you</div>
          {summary.map((line, i) => renderLine(line, i))}
        </div>
      )}

      {/* Explanation + Ranked side by side */}
      <div style={s.grid}>
        <div style={s.card}>
          <div style={s.cardTitle}>AI Explanation</div>
          <p style={s.explanationText}>{explanation}</p>
        </div>

        <div style={s.card}>
          <div style={s.cardTitle}>Ranked Options</div>
          {ranked.map(({ option, score }, i) => (
            <div key={option} style={{ ...s.rankItem, borderBottom: i === ranked.length - 1 ? 'none' : '1px solid var(--border)' }}>
              <div style={{ ...s.rankNum, ...(i === 0 ? s.rankNumFirst : {}) }}>{i + 1}</div>
              <div style={s.rankOption}>{option}</div>
              <div style={{ flex: 2 }}>
                <ScoreBar value={score} max={maxScoreAbs} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Scenarios table */}
      <div style={s.tableWrap}>
        <div style={s.tableTitle}>Scenario Breakdown</div>
        <table style={s.table}>
          <thead>
            <tr>
              {['Scenario', 'Option', 'Salary', 'Risk', 'Happiness', 'Score'].map(h => (
                <th key={h} style={s.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {results.map((r, i) => (
              <tr key={i} style={{ background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.015)' }}>
                <td style={s.td}>{r.scenario}</td>
                <td style={{ ...s.td, ...s.tdMuted }}>{r.option}</td>
                <td style={s.td}>${r.salary?.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                <td style={s.td}>
                  <span style={{ ...s.pill, ...riskColor(r.risk_score) }}>{r.risk_score?.toFixed(2)}</span>
                </td>
                <td style={s.td}>
                  <span style={{ ...s.pill, ...riskColor(1 - r.happiness) }}>{r.happiness?.toFixed(2)}</span>
                </td>
                <td style={{ ...s.td, ...s.tdMuted }}>{r.score?.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
