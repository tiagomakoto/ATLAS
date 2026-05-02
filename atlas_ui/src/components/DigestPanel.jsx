import { getRegimeColor } from "../store/regimeColors";

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

  // corRegime: usa getRegimeColor de ../store/regimeColors (fonte única)
  const corRegime = getRegimeColor;

  // ═══ Item 3: Cor baseada no STATUS do ativo ═══
  const corStatus = (status) => {
    if (!status) return "var(--atlas-text-secondary)";
    if (status === "OPERAR") return "var(--atlas-green)";
    if (status === "MONITORAR") return "var(--atlas-amber)";
    return "var(--atlas-text-secondary)"; // SEM_EDGE, etc
  };

  // ═══ NOVO: Cor baseada no REFLECT state ═══
  const corReflet = (state) => {
    if (!state) return "var(--atlas-text-secondary)";
    if (state === "A") return "var(--atlas-green)";
    if (state === "B") return "var(--atlas-blue)";
    if (state === "C") return "var(--atlas-amber)";
    if (state === "D") return "var(--atlas-red)";
    if (state === "T") return "var(--atlas-red)";
    if (state === "E") return "var(--atlas-red)";
    return "var(--atlas-text-secondary)";
  };

  // ═══ NOVO: Ícone baseado no REFLECT state ═══
  const iconeReflet = (state) => {
    if (!state) return "·";
    if (state === "A") return "✓";
    if (state === "B") return "~";
    if (state === "C") return "~";
    if (state === "D") return "✗";
    if (state === "T") return "✗";
    if (state === "E") return "✗";
    return "·";
  };
  
  // ═══ Helper para renderizar regime (ORBIT) com cores ═══
  const renderOrbitAntesDepois = (orbitStr, orbitAntes, orbitDepois) => {
    if (!orbitStr || !orbitStr.includes(" -> ")) {
      return <span style={{ color: "var(--atlas-text-secondary)", fontSize: 9 }}>{orbitStr}</span>;
    }
    
    const [antes, depois] = orbitStr.split(" -> ");
    return (
      <span style={{ fontSize: 9 }}>
        <span style={{ color: corRegime(antes) }}>{antes}</span>
        {" -> "}
        <span style={{ color: corRegime(depois), fontWeight: "bold" }}>{depois}</span>
      </span>
    );
  };

  // ═══ Helper para renderizar STATUS com cores ═══
  const renderStatusAntesDepois = (statusStr, statusAntes, statusDepois) => {
    if (!statusStr || !statusStr.includes(" -> ")) {
      return <span style={{ color: "var(--atlas-text-secondary)", fontSize: 9 }}>{statusStr}</span>;
    }
    
    const [antes, depois] = statusStr.split(" -> ");
    return (
      <span style={{ fontSize: 9 }}>
        <span style={{ color: corStatus(antes) }}>{antes}</span>
        {" -> "}
        <span style={{ color: corStatus(depois), fontWeight: "bold" }}>{depois}</span>
      </span>
    );
  };
  // ═══ FIM ═══

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
        Resumo por Ativo — {timestamp
          ? new Date(timestamp).toLocaleString("pt-BR")
          : "—"}
      </div>

      {tickers.map((ticker) => {
        const ev = digestPorAtivo[ticker];

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
              {ev.gate_eod === "BLOQUEADO — calibração não realizada" && (
                <span style={{ color: "var(--atlas-red)", fontSize: 9, alignSelf: "center" }}>
                  ✗ BLOQUEADO
                </span>
              )}
            </div>

            {/* motivo (ativos bloqueados) */}
            {ev.motivo && (
              <div style={{ display: "flex", gap: 12, padding: "2px 0", paddingLeft: 12 }}>
                <span style={{ color: "var(--atlas-red)", width: 10 }}>✗</span>
                <span style={{ color: "var(--atlas-text-primary)", width: 80, flexShrink: 0 }}>status</span>
                <span style={{ color: "var(--atlas-red)", fontSize: 9 }}>{ev.motivo}</span>
              </div>
            )}

            {/* xlsx eod — sempre mostrar */}
            <div style={{ display: "flex", gap: 12, padding: "2px 0", paddingLeft: 12 }}>
              <span style={{
                color: ev.xlsx === "ok" ? "var(--atlas-green)" : "var(--atlas-amber)",
                width: 10
              }}>
                {ev.xlsx === "ok" ? "✓" : ev.xlsx ? "✗" : "·"}
              </span>
              <span style={{ color: "var(--atlas-text-primary)", width: 80, flexShrink: 0 }}>
                xlsx eod
              </span>
              <span style={{ color: "var(--atlas-text-secondary)", fontSize: 9 }}>
                {ev.xlsx === "ok" ? "encontrado" : ev.xlsx || "não avaliado"}
              </span>
            </div>

            {/* posição — ativos não bloqueados */}
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
            {ev.posicao && ev.posicao.tp_stop_status && (
              <div style={{ display: "flex", gap: 12, padding: "2px 0", paddingLeft: 12 }}>
                <span style={{
                  color: ev.posicao.tp_stop_status === "ok"
                    ? "var(--atlas-green)"
                    : "var(--atlas-red)",
                  width: 10
                }}>
                  {ev.posicao.tp_stop_status === "ok" ? "✓" : "✗"}
                </span>
                <span style={{ color: "var(--atlas-text-primary)", width: 80, flexShrink: 0 }}>
                  tp/stop
                </span>
                <span style={{ color: "var(--atlas-text-secondary)", fontSize: 9 }}>
                  {ev.posicao.tp_stop_status === "ok"
                    ? "ok - mantendo"
                    : ev.posicao.tp_stop_status === "fechar"
                      ? `fechar — ${ev.posicao.motivo || "tp/stop atingido"}`
                      : ev.posicao.tp_stop_status === "sem_xlsx"
                        ? "xlsx indisponível"
                        : "—"}
                </span>
              </div>
            )}

            {/* bloco_mensal */}
            {ev.bloco_mensal && (
              <div style={{ paddingLeft: 12, marginTop: 4 }}>
                {/* regime */}
                <div style={{ display: "flex", gap: 12, padding: "2px 0" }}>
                  <span style={{ color: cor(ev.bloco_mensal.orbit), width: 10 }}>
                    {icone(ev.bloco_mensal.orbit)}
                  </span>
                  <span style={{ color: "var(--atlas-text-primary)", width: 80, flexShrink: 0 }}>
                    regime
                  </span>
                  {/* ═══ Item 3: Mostrar antes -> depois com cores (regime) ═══ */}
                  {renderOrbitAntesDepois(
                    ev.bloco_mensal.orbit,
                    ev.bloco_mensal.orbit_antes,
                    ev.bloco_mensal.orbit_depois
                  )}
                  {/* ═══ FIM ═══ */}
                </div>

                {/* reflect - REORDENADO: antes de status */}
                {ev.bloco_mensal.reflect_antes && (
                  <div style={{ display: "flex", gap: 12, padding: "2px 0" }}>
                    <span style={{ 
                      color: cor(ev.bloco_mensal.reflect_depois || ev.bloco_mensal.reflect_antes), 
                      width: 10 
                    }}>
                      {icone(ev.bloco_mensal.reflect_depois || ev.bloco_mensal.reflect_antes)}
                    </span>
                    <span style={{ color: "var(--atlas-text-primary)", width: 80, flexShrink: 0 }}>
                      reflect
                    </span>
                    <span style={{ fontSize: 9 }}>
                      {ev.bloco_mensal.reflect_antes && ev.bloco_mensal.reflect_depois ? (
                        <span>
                          <span style={{ color: corReflet(ev.bloco_mensal.reflect_antes) }}>
                            {ev.bloco_mensal.reflect_antes}
                          </span>
                          {" -> "}
                          <span style={{ color: corReflet(ev.bloco_mensal.reflect_depois), fontWeight: "bold" }}>
                            {ev.bloco_mensal.reflect_depois}
                          </span>
                        </span>
                      ) : (
                        <span style={{ color: "var(--atlas-text-secondary)" }}>
                          {ev.bloco_mensal.reflect_antes || "—"}
                        </span>
                      )}
                    </span>
                  </div>
                )}

                {/* status - REORDENADO: depois de reflect */}
                {ev.bloco_mensal.status_antes && (
                  <div style={{ display: "flex", gap: 12, padding: "2px 0" }}>
                    <span style={{ color: cor(ev.bloco_mensal.status), width: 10 }}>
                      {icone(ev.bloco_mensal.status)}
                    </span>
                    <span style={{ color: "var(--atlas-text-primary)", width: 80, flexShrink: 0 }}>
                      status
                    </span>
                    {/* ═══ Item 3: Mostrar status antes -> depois com cores ═══ */}
                    {renderStatusAntesDepois(
                      ev.bloco_mensal.status_antes && ev.bloco_mensal.status_depois 
                        ? `${ev.bloco_mensal.status_antes} -> ${ev.bloco_mensal.status_depois}`
                        : null,
                      ev.bloco_mensal.status_antes,
                      ev.bloco_mensal.status_depois
                    )}
                    {/* ═══ FIM ═══ */}
                  </div>
                )}

                {/* gate - ═══ Item 1: REMOVER ═══ */}
                {/*
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
                */}

                {/* tune - ═══ Item 1: REMOVER ═══ */}
                {/*
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
                */}
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
