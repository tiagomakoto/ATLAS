const RANGES = [
  { value: "current", label: "Ciclo atual" },
  { value: "30d", label: "30 dias" },
  { value: "6m", label: "6 meses" },
  { value: "all", label: "Histórico completo" }
];

export default function TimeRangeSelector({ value, onChange }) {
  return (
    <div style={{ display: "flex", gap: 4 }}>
      {RANGES.map(r => (
        <button
          key={r.value}
          onClick={() => onChange(r.value)}
          style={{
            background: value === r.value
              ? "var(--atlas-blue)"
              : "var(--atlas-surface)",
            color: value === r.value
              ? "#fff"
              : "var(--atlas-text-secondary)",
            border: "1px solid var(--atlas-border)",
            borderRadius: 2,
            fontSize: 11
          }}
        >
          {r.label}
        </button>
      ))}
    </div>
  );
}