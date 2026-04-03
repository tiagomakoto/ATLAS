export default function DigestPanel({ items, timestamp }) {
  if (!items?.length) return null;

  const icone = (tipo) => ({
    ok:                  "✓",
    alerta:              "⚠",
    bloqueado:           "✗",
    aprovacao_pendente:  "~",
    info:                "·"
  }[tipo] || "·");

  const cor = (tipo) => ({
    ok:                  "var(--atlas-green)",
    alerta:              "var(--atlas-red)",
    bloqueado:           "var(--atlas-red)",
    aprovacao_pendente:  "var(--atlas-amber)",
    info:                "var(--atlas-text-secondary)"
  }[tipo] || "var(--atlas-text-secondary)");

  return (
    <div style={{
      padding: 12,
      background: "var(--atlas-surface)",
      border: "1px solid var(--atlas-border)",
      borderRadius: 2,
      fontFamily: "monospace", fontSize: 10
    }}>
      <div style={{
        color: "var(--atlas-text-secondary)",
        textTransform: "uppercase",
        letterSpacing: 1, marginBottom: 10, fontSize: 9
      }}>
        Check Status — {timestamp
          ? new Date(timestamp).toLocaleString("pt-BR")
          : "—"}
      </div>

      {items.map((item, i) => (
        <div key={i} style={{
          display: "flex", gap: 12,
          padding: "3px 0",
          borderBottom: i < items.length - 1
            ? "1px solid var(--atlas-border)"
            : "none"
        }}>
          <span style={{ color: cor(item.tipo), width: 10 }}>
            {icone(item.tipo)}
          </span>
          <span style={{
            color: "var(--atlas-text-primary)",
            width: 60, flexShrink: 0
          }}>
            {item.modulo}
          </span>
          <span style={{ color: "var(--atlas-text-secondary)" }}>
            {item.mensagem}
          </span>
        </div>
      ))}
    </div>
  );
}