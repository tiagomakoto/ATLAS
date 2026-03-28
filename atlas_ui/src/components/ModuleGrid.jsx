export default function ModuleGrid({ modules }) {
  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "repeat(4, 1fr)",
      gap: 8
    }}>
      {Object.entries(modules).map(([name, status]) => {
        const color =
          status === "running" ? "var(--atlas-green)" :
          status === "error" ? "var(--atlas-red)" :
          status === "waiting" ? "var(--atlas-amber)" :
          "var(--atlas-border)";

        return (
          <div key={name} style={{
            padding: 8,
            background: "var(--atlas-surface)",
            border: `1px solid ${color}`,
            borderRadius: 2,
            fontFamily: "monospace",
            fontSize: 11
          }}>
            {name}
          </div>
        );
      })}
    </div>
  );
}