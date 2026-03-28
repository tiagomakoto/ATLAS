export default function HealthIndicator({ status, reason }) {
  const color =
    status === "green" ? "var(--atlas-green)" :
    status === "yellow" ? "var(--atlas-amber)" :
    "var(--atlas-red)";

  const label =
    status === "green" ? "Sistema operacional" :
    status === "yellow" ? "Dados desatualizados" :
    "Erro crítico detectado";

  return (
    <div title={reason || label} style={{
      display: "flex",
      alignItems: "center",
      gap: 6,
      cursor: "default"
    }}>
      <div style={{
        width: 10,
        height: 10,
        borderRadius: 2,
        background: color
      }} />
      <span style={{
        fontFamily: "monospace",
        fontSize: 11,
        color: color
      }}>
        {label}
      </span>
    </div>
  );
}