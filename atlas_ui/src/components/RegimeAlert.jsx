export default function RegimeAlert({ alert }) {
  if (!alert) return null;

  return (
    <div style={{
      position: "fixed",
      top: 20,
      right: 20,
      background: "var(--atlas-red)",
      color: "#fff",
      padding: 10,
      borderRadius: 2,
      fontFamily: "monospace",
      fontSize: 12
    }}>
      {alert.message}
    </div>
  );
}