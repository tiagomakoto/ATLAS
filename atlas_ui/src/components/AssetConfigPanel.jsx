export default function AssetConfigPanel({ asset, draft, onChange }) {
  function updateField(key, value) {
    onChange({ ...draft, [key]: value });
  }

  if (!draft) {
    return (
      <div style={{ fontFamily: "monospace", fontSize: 11, color: "var(--atlas-text-secondary)", padding: 8 }}>
        Carregando configuração...
      </div>
    );
  }

  return (
    <div style={{ fontFamily: "monospace", fontSize: 12 }}>
      <h4 style={{ color: "var(--atlas-text-primary)", marginBottom: 8 }}>{asset}</h4>
      {Object.entries(draft).map(([k, v]) => (
        <FieldInput key={k} fieldKey={k} value={v} onChange={updateField} />
      ))}
    </div>
  );
}

function FieldInput({ fieldKey, value, onChange }) {
  if (typeof value === "boolean") {
    return (
      <div style={{ display: "flex", gap: 8, alignItems: "center", fontFamily: "monospace", fontSize: 11 }}>
        <label style={{ color: "var(--atlas-text-secondary)" }}>{fieldKey}</label>
        <input type="checkbox" checked={value} onChange={(e) => onChange(fieldKey, e.target.checked)} />
      </div>
    );
  }
  if (typeof value === "number") {
    return (
      <div style={{ display: "flex", gap: 8, alignItems: "center", fontFamily: "monospace", fontSize: 11 }}>
        <label style={{ color: "var(--atlas-text-secondary)" }}>{fieldKey}</label>
        <input type="number" step="any" value={value} style={{ background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", color: "var(--atlas-text-primary)", fontFamily: "monospace", fontSize: 11, padding: "2px 6px", borderRadius: 2, width: 100 }} onChange={(e) => onChange(fieldKey, parseFloat(e.target.value))} />
      </div>
    );
  }
  if (value === null || value === undefined) {
    return (
      <div style={{ fontFamily: "monospace", fontSize: 11 }}>
        <label style={{ color: "var(--atlas-text-secondary)" }}>{fieldKey}</label>
        <span style={{ color: "var(--atlas-red)", marginLeft: 8 }}>null</span>
      </div>
    );
  }
  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center", fontFamily: "monospace", fontSize: 11 }}>
      <label style={{ color: "var(--atlas-text-secondary)" }}>{fieldKey}</label>
      <input type="text" value={String(value)} style={{ background: "var(--atlas-surface)", border: "1px solid var(--atlas-border)", color: "var(--atlas-text-primary)", fontFamily: "monospace", fontSize: 11, padding: "2px 6px", borderRadius: 2, width: 100 }} onChange={(e) => onChange(fieldKey, e.target.value)} />
    </div>
  );
}