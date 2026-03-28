export default function ConfirmDialog({
  open,
  diff,
  description,
  onDescriptionChange,
  onConfirm,
  onCancel
}) {
  if (!open) return null;

  const canConfirm = description.trim().length > 0;

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      width: "100%",
      height: "100%",
      background: "rgba(0,0,0,0.7)",
      zIndex: 1000
    }}>
      <div style={{
        background: "var(--atlas-surface)",
        border: "1px solid var(--atlas-border)",
        padding: 20,
        margin: "80px auto",
        width: 400,
        borderRadius: 2
      }}>
        <div style={{
          fontFamily: "monospace",
          fontSize: 12,
          marginBottom: 12
        }}>
          Confirmar alteração de configuração
        </div>

        {diff && Object.keys(diff).length > 0 && (
          <div style={{ marginBottom: 12 }}>
            {Object.entries(diff).map(([k, v]) => (
              <div key={k}>
                {k}: {String(v.before)} → {String(v.after)}
              </div>
            ))}
          </div>
        )}

        <input
          value={description}
          onChange={e => onDescriptionChange(e.target.value)}
          placeholder="Descrição obrigatória"
          style={{
            width: "100%",
            marginBottom: 12
          }}
        />

        <button onClick={onCancel}>Cancelar</button>
        <button
          onClick={onConfirm}
          disabled={!canConfirm}
        >
          Confirmar
        </button>
      </div>
    </div>
  );
}