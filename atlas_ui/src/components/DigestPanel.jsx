export default function DigestPanel({ digestPorAtivo, timestamp }) {
  const tickers = Object.keys(digestPorAtivo || {});
  if (!tickers.length) return null;

  const icone = (status) => {
    if (!status || status === "pulado") return "~";
    if (typeof status === "string" && status.startsWith("erro")) return "✗";
    if (status === "ok") return "✓";
    if (status === "pulado — sem xlsx") return "~";
    if (status === "pulado — sem histórico") return "~";
    return "·";
  };

  const cor = (status) => {
    if (!status || status === "pulado") return "var(--atlas-text-secondary)";
    if (typeof status === "string" && status.startsWith("erro")) return "var(--atlas-red)";
    if (status === "ok") return "var(--atlas-green)";
    if (status === "pulado — sem xlsx") return "var(--atlas-text-secondary)";
    if (status === "pulado — sem histórico") return "var(--atlas-text-secondary)";
    return "var(--atlas-text-secondary)";
  };

  const statusGeral = (evento) => {
    const erros = evento.erros || [];
    if (erros.length > 0) return "erro";
    const bloco = evento.bloco_mensal;
    if (bloco) {
      if (bloco.orbit?.startsWith("erro")) return "erro";
      if (bloco.gate?.startsWith("erro")) return "erro";
    }
    if (evento.gate_eod === "BLOQUEADO") return "alerta";
    if (evento.gate_eod === "MONITORAR") return "alerta";
    return "ok";
  };

  const iconeGeral = (st) => ({ ok: "✓", alerta: "⚠", erro: "✗" }[st] || "·");
  const corGeral = (st) => ({
    ok: "var(--atlas-green)",
    alerta: "var(--atlas-amber)",
    erro: "var(--atlas-red)"
  }[st] || "var(--atlas-text-secondary)");

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

      {tickers.map((ticker) => {
        const ev = digestPorAtivo[ticker];
        const st = statusGeral(ev);

        return (
          <div key={ticker} style={{
            marginBottom: 8,
            paddingBottom: 8,
            borderBottom: "1px solid var(--atlas-border)"
          }}>
            {/* Header do ativo */}
            <div style={{
              display: "flex", justifyContent: "space-between",
              marginBottom: 4
            }}>
              <span style={{
                color: "var(--atlas-text-primary)",
                fontWeight: "bold", fontSize: 11
              }}>
                {ticker}
              </span>
              <span style={{ color: corGeral(st), fontSize: 11 }}>
                {iconeGeral(st)} {st}
              </span>
            </div>

            {/* reflect_daily */}
            <div style={{ display: "flex", gap: 12, padding: "2px 0", paddingLeft: 12 }}>
              <span style={{ color: cor(ev.reflect_daily), width: 10 }}>
                {icone(ev.reflect_daily)}
              </span>
              <span style={{ color: "var(--atlas-text-primary)", width: 80, flexShrink: 0 }}>
                reflect_daily
              </span>
              <span style={{ color: "var(--atlas-text-secondary)", fontSize: 9 }}>
                {ev.reflect_daily}
              </span>
            </div>

            {/* gate_eod */}
            <div style={{ display: "flex", gap: 12, padding: "2px 0", paddingLeft: 12 }}>
              <span style={{
                color: ev.gate_eod === "OPERAR" ? "var(--atlas-green)"
                  : ev.gate_eod === "MONITORAR" ? "var(--atlas-amber)"
                  : ev.gate_eod === "BLOQUEADO" ? "var(--atlas-red)"
                  : "var(--atlas-text-secondary)",
                width: 10
              }}>
                {ev.gate_eod === "OPERAR" ? "✓"
                  : ev.gate_eod === "MONITORAR" ? "~"
                  : ev.gate_eod === "BLOQUEADO" ? "✗"
                  : "·"}
              </span>
              <span style={{ color: "var(--atlas-text-primary)", width: 80, flexShrink: 0 }}>
                gate_eod
              </span>
              <span style={{
                color: ev.gate_eod === "OPERAR" ? "var(--atlas-green)" : "var(--atlas-text-secondary)",
                fontSize: 9
              }}>
                {ev.gate_eod}
              </span>
            </div>

            {/* posição */}
            {ev.posicao && (
              <div style={{ display: "flex", gap: 12, padding: "2px 0", paddingLeft: 12 }}>
                <span style={{
                  color: ev.posicao.aberta ? "var(--atlas-amber)" : "var(--atlas-text-secondary)",
                  width: 10
                }}>
                  {ev.posicao.aberta ? "⚠" : "·"}
                </span>
                <span style={{ color: "var(--atlas-text-primary)", width: 80, flexShrink: 0 }}>
                  posição
                </span>
                <span style={{ color: "var(--atlas-text-secondary)", fontSize: 9 }}>
                  {ev.posicao.aberta
                    ? `P&L ${ev.posicao.pnl_atual > 0 ? "+" : ""}${ev.posicao.pnl_atual}% — ${ev.posicao.acao}`
                    : "sem posição"}
                </span>
              </div>
            )}

            {/* bloco_mensal */}
            {ev.bloco_mensal && (
              <div style={{ paddingLeft: 12, marginTop: 4 }}>
                {/* orbit */}
                <div style={{ display: "flex", gap: 12, padding: "2px 0" }}>
                  <span style={{ color: cor(ev.bloco_mensal.orbit), width: 10 }}>
                    {icone(ev.bloco_mensal.orbit)}
                  </span>
                  <span style={{ color: "var(--atlas-text-primary)", width: 80, flexShrink: 0 }}>
                    orbit
                  </span>
                  <span style={{ color: "var(--atlas-text-secondary)", fontSize: 9 }}>
                    {ev.bloco_mensal.orbit}
                  </span>
                </div>

                {/* reflect_cycle */}
                <div style={{ display: "flex", gap: 12, padding: "2px 0" }}>
                  <span style={{ color: cor(ev.bloco_mensal.reflect_cycle), width: 10 }}>
                    {icone(ev.bloco_mensal.reflect_cycle)}
                  </span>
                  <span style={{ color: "var(--atlas-text-primary)", width: 80, flexShrink: 0 }}>
                    reflect_cycle
                  </span>
                  <span style={{ color: "var(--atlas-text-secondary)", fontSize: 9 }}>
                    {ev.bloco_mensal.reflect_cycle}
                  </span>
                </div>

                {/* gate */}
                <div style={{ display: "flex", gap: 12, padding: "2px 0" }}>
                  <span style={{ color: cor(ev.bloco_mensal.gate), width: 10 }}>
                    {icone(ev.bloco_mensal.gate)}
                  </span>
                  <span style={{ color: "var(--atlas-text-primary)", width: 80, flexShrink: 0 }}>
                    gate
                  </span>
                  <span style={{ color: "var(--atlas-text-secondary)", fontSize: 9 }}>
                    {ev.bloco_mensal.gate}
                    {ev.bloco_mensal.status_anterior && ev.bloco_mensal.status_novo && (
                      <span>
                        {" — "}
                        {ev.bloco_mensal.status_anterior !== ev.bloco_mensal.status_novo ? (
                          <span style={{ color: "var(--atlas-green)", fontWeight: "bold" }}>
                            ↑ {ev.bloco_mensal.status_novo}
                          </span>
                        ) : (
                          ev.bloco_mensal.status_novo
                        )}
                      </span>
                    )}
                  </span>
                </div>

                {/* tune */}
                <div style={{ display: "flex", gap: 12, padding: "2px 0" }}>
                  <span style={{ color: cor(ev.bloco_mensal.tune), width: 10 }}>
                    {icone(ev.bloco_mensal.tune)}
                  </span>
                  <span style={{ color: "var(--atlas-text-primary)", width: 80, flexShrink: 0 }}>
                    tune
                  </span>
                  <span style={{ color: "var(--atlas-text-secondary)", fontSize: 9 }}>
                    {ev.bloco_mensal.tune}
                  </span>
                </div>
              </div>
            )}

            {/* erros */}
            {(ev.erros || []).length > 0 && (
              <div style={{ paddingLeft: 12, marginTop: 2 }}>
                {ev.erros.map((err, i) => (
                  <div key={i} style={{
                    color: "var(--atlas-red)", fontSize: 9, padding: "1px 0"
                  }}>
                    ✗ {err}
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
