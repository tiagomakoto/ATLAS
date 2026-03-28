function formatDetails(details) {
  if (!details) return "";
  return Object.entries(details)
    .map(([k, v]) => `${k}: ${v}`)
    .join(" | ");
}

export default function EventFeed({ events }) {
  return (
    <div style={{
      maxHeight: 300,
      overflow: "auto",
      background: "var(--atlas-surface)",
      border: "1px solid var(--atlas-border)"
    }}>
      {events.map((e, i) => (
        <div key={i} style={{
          padding: "4px 8px",
          borderBottom: "1px solid var(--atlas-border)",
          fontFamily: "monospace",
          fontSize: 11
        }}>
          <span style={{ color: "var(--atlas-text-secondary)" }}>
            {e.timestamp?.slice(11, 19)}
          </span>
          {" "}
          <span style={{ color: "var(--atlas-text-primary)" }}>
            {e.event}
          </span>
          {e.details && (
            <span style={{ color: "var(--atlas-text-secondary)" }}>
              {" — "}{formatDetails(e.details)}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}