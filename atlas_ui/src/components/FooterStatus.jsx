export default function FooterStatus({ staleness }) {
  const formatStaleness = (ts) => {
    if (!ts || ts === 0) return "—";
    const seconds = Math.floor((Date.now() - ts) / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h`;
  };

  const stalenessText = formatStaleness(staleness);
  const seconds = staleness ? Math.floor((Date.now() - staleness) / 1000) : 0;
  const stalenessColor = seconds < 300
    ? "var(--atlas-green)"
    : seconds < 1800
    ? "var(--atlas-amber)"
    : "var(--atlas-red)";

  return (
    <div style={{
      borderTop: "1px solid var(--atlas-border)",
      padding: "6px 12px",
      display: "flex",
      justifyContent: "flex-end",
      fontFamily: "monospace",
      fontSize: 10,
      background: "var(--atlas-surface)"
    }}>
      <span style={{ color: "var(--atlas-text-secondary)" }}>Atualização: <span style={{ color: stalenessColor }}>{stalenessText}</span></span>
    </div>
  );
}