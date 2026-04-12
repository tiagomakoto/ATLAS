// regimeColors.js — fonte única de verdade para cores de regime ORBIT
// Importar em AtivoView.jsx, DigestPanel.jsx e qualquer outro componente

export const REGIME_COLORS = {
  ALTA:              "var(--atlas-green)",
  BAIXA:             "var(--atlas-red)",
  NEUTRO_BULL:       "var(--atlas-green)",  // bull → verde
  NEUTRO_BEAR:       "var(--atlas-red)",    // bear → vermelho
  NEUTRO_LATERAL:    "var(--atlas-blue)",   // neutro → azul
  NEUTRO_TRANSICAO:  "var(--atlas-amber)", // transição → âmbar
  NEUTRO_MORTO:      "var(--atlas-blue)",   // neutro → azul
  RECUPERACAO:       "var(--atlas-green)",  // bull → verde
  PANICO:            "var(--atlas-red)",    // bear → vermelho
  NEUTRO:            "var(--atlas-blue)",   // fallback genérico
};

export const REGIME_BG_COLORS = {
  ALTA:              "rgba(34, 197, 94, 0.2)",
  BAIXA:             "rgba(239, 68, 68, 0.2)",
  NEUTRO_BULL:       "rgba(34, 197, 94, 0.2)",
  NEUTRO_BEAR:       "rgba(239, 68, 68, 0.2)",
  NEUTRO_LATERAL:    "rgba(59, 130, 246, 0.2)",
  NEUTRO_TRANSICAO:  "rgba(245, 158, 11, 0.2)",
  NEUTRO_MORTO:      "rgba(59, 130, 246, 0.2)",
  RECUPERACAO:       "rgba(34, 197, 94, 0.2)",
  PANICO:            "rgba(239, 68, 68, 0.2)",
  NEUTRO:            "rgba(59, 130, 246, 0.2)",
};

/**
 * Retorna a cor do regime. Faz match exato primeiro,
 * depois fallback por substring para compatibilidade.
 */
export function getRegimeColor(regime) {
  if (!regime) return "var(--atlas-text-secondary)";
  const r = regime.toUpperCase();
  if (REGIME_COLORS[r]) return REGIME_COLORS[r];
  // fallbacks por substring (nunca sobrescrevem match exato)
  if (r.includes("ALTA") || r.includes("BULL")) return REGIME_COLORS.ALTA;
  if (r.includes("BAIXA") || r.includes("BEAR")) return REGIME_COLORS.BAIXA;
  if (r.includes("PANICO")) return REGIME_COLORS.PANICO;
  if (r.includes("RECUPERACAO")) return REGIME_COLORS.RECUPERACAO;
  if (r.includes("NEUTRO")) return REGIME_COLORS.NEUTRO;
  return "var(--atlas-text-secondary)";
}

export function getRegimeBgColor(regime) {
  if (!regime) return "var(--atlas-surface)";
  const r = regime.toUpperCase();
  if (REGIME_BG_COLORS[r]) return REGIME_BG_COLORS[r];
  if (r.includes("ALTA") || r.includes("BULL")) return REGIME_BG_COLORS.ALTA;
  if (r.includes("BAIXA") || r.includes("BEAR")) return REGIME_BG_COLORS.BAIXA;
  if (r.includes("PANICO")) return REGIME_BG_COLORS.PANICO;
  if (r.includes("RECUPERACAO")) return REGIME_BG_COLORS.RECUPERACAO;
  if (r.includes("NEUTRO")) return REGIME_BG_COLORS.NEUTRO;
  return "var(--atlas-surface)";
}
