"""
atlas_backend/core/relatorios.py

Módulo para geração de relatórios de TUNE e ONBOARDING.
"""

import os
import json
import math
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import re
from collections import defaultdict

RELATORIOS_DIR = Path(__file__).parent / "relatorios"
INDEX_PATH = RELATORIOS_DIR / "index.json"


def _carregar_index():
    """Carrega index.json ou cria novo."""
    if not INDEX_PATH.exists():
        return []
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _salvar_index(index):
    """Salva index.json com escrita atômica."""
    tmp_path = INDEX_PATH.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, INDEX_PATH)


def _gerar_id():
    """Gera ID sequencial baseado no index atual."""
    index = _carregar_index()
    if not index:
        return 1
    ids = [int(r["id"]) for r in index if r.get("id").isdigit()]
    return max(ids) + 1 if ids else 1


def gerar_relatorio(ticker: str, ciclo: str, tipo: str, params: dict) -> dict:
    """
    Gera relatório .md e atualiza index.json.

    Args:
        ticker: Ex: "VALE3"
        ciclo: Ex: "2026-04"
        tipo: "TUNE" ou "ONBOARDING"
        params: {
            "tp_atual": float,
            "stop_atual": float,
            "tp_sugerido": float,
            "stop_sugerido": float,
            "delta_tp": float,
            "delta_stop": float,
            "recomendacao": "APLICAR" | "REVISAR" | "MANTER",
            "detalhes": dict
        }

    Returns:
        {
            "id": int,
            "arquivo": "RELATORIO_003_VALE3_2026-04.md",
            "ciclo": "2026-04",
            "tipo": "TUNE",
            "data_execucao": "2026-04-08"
        }
    """
    id_rel = _gerar_id()
    id_str = f"{id_rel:03d}"
    data_hoje = datetime.now(tz=ZoneInfo('America/Sao_Paulo')).strftime("%Y-%m-%d")
    arquivo = f"RELATORIO_{id_str}_{ticker}_{ciclo}.md"
    path_rel = RELATORIOS_DIR / arquivo

    # Template do relatório
    template = f"""# Relatório Delta Chaos — {ticker} — {ciclo}
**Tipo:** {tipo}
**ID:** {id_str}
**Data de execução:** {data_hoje}
**Gerado por:** Delta Chaos v1.0

---

## Como usar este relatório
Cole este arquivo numa sessão com o board Delta Chaos.
O board irá:
1. Explicar os resultados apresentados
2. Recomendar aplicar ou não os parâmetros sugeridos
3. Abrir tensões se houver divergência entre regime e parâmetros

---

## Resumo executivo
**Ativo:** {ticker}
**Período analisado:** Ver histórico ORBIT
**Dias úteis analisados:** Ver histórico ORBIT
**Regime dominante:** Ver histórico ORBIT

**Parâmetros atuais:**
TP: {params['tp_atual']*100:.1f}%
STOP: {params['stop_atual']*100:.1f}%

**Parâmetros sugeridos:**
TP: {params['tp_sugerido']*100:.1f}% (delta: {params['delta_tp']*100:+.1f}%)
STOP: {params['stop_sugerido']*100:.1f}% (delta: {params['delta_stop']*100:+.1f}%)

**Recomendação:** {params['recomendacao']}

---

## Dados completos
```json
{json.dumps({
    "tipo": tipo,
    "id": id_str,
    "ticker": ticker,
    "ciclo": ciclo,
    "data_execucao": data_hoje,
    "periodo_analisado": {
        "inicio": "Ver histórico ORBIT",
        "fim": "Ver histórico ORBIT",
        "dias_uteis": "Ver histórico ORBIT"
    },
    "regime_dominante": "Ver histórico ORBIT",
    "parametros_atuais": {
        "take_profit": params['tp_atual'],
        "stop_loss": params['stop_atual']
    },
    "parametros_sugeridos": {
        "take_profit": params['tp_sugerido'],
        "stop_loss": params['stop_sugerido']
    },
    "delta": {
        "take_profit": params['delta_tp'],
        "stop_loss": params['delta_stop']
    },
    "recomendacao": params['recomendacao'],
    "detalhes": params.get('detalhes', {})
}, indent=2, ensure_ascii=False)}
```
"""

    # Escrever relatório
    with open(path_rel, "w", encoding="utf-8") as f:
        f.write(template)

    # Atualizar index.json
    entry = {
        "id": id_str,
        "ticker": ticker,
        "ciclo": ciclo,
        "tipo": tipo,
        "data_execucao": data_hoje,
        "arquivo": arquivo,
        "aplicado": False
    }

    index = _carregar_index()
    index.append(entry)
    _salvar_index(index)

    return {
        "id": id_rel,
        "arquivo": arquivo,
        "ciclo": ciclo,
        "tipo": tipo,
        "data_execucao": data_hoje
    }


def marcar_aplicado(id_rel: str):
    """
    Marca relatório como aplicado no index.json.

    Args:
        id_rel: ID do relatório (ex: "003")
    """
    index = _carregar_index()
    for entry in index:
        if entry.get("id") == id_rel:
            entry["aplicado"] = True
            entry["data_aplicado"] = datetime.now(tz=ZoneInfo('America/Sao_Paulo')).strftime("%Y-%m-%d")
            break
    _salvar_index(index)


def obter_relatorio(id_rel: str) -> dict | None:
    """
    Retorna metadados do relatório pelo ID.

    Args:
        id_rel: ID do relatório (ex: "003")

    Returns:
        dict com metadados ou None se não encontrado
    """
    index = _carregar_index()
    for entry in index:
        if entry.get("id") == id_rel:
            return entry
    return None


def obter_todos_relatorios() -> list:
    """Retorna todos os relatórios do index.json."""
    return _carregar_index()


# =============================================================================
# RELATÓRIOS DE CALIBRAÇÃO (GATE bloqueado / completo com FIRE)
# =============================================================================

# --- Regex para parsear campo `motivo` do TUNE em historico_config ---
_RE_IR_CAL      = re.compile(r'IR=([+-]?\d+\.\d+)')
_RE_CONF_CAL    = re.compile(r'\b(Alta|Baixa|amostra_insuficiente)\b')
_RE_TRADES_CAL  = re.compile(r'N trades:\s*(\d+)')
_RE_TRIALS_CAL  = re.compile(r'Trials:\s*(\d+)/(\d+)')
_RE_REFLECT_CAL = re.compile(r'Ciclos com REFLECT real:\s*(\d+)')
_RE_FALLBACK_CAL = re.compile(r'Fallback B:\s*(\d+)')
_RE_TP_STOP_CAL = re.compile(r'TP=(\d+\.\d+)\s+STOP=(\d+\.\d+)')
_RE_ACERTO_CAL  = re.compile(r'Acerto:\s*([\d.]+)%')
_RE_MASKED_CAL  = re.compile(r'(\d+) ciclos mascarados de (\d+)')


def _get_ativo_env(ticker: str) -> dict:
    """
    Retorna campos ambientais do ativo para uso no relatório.
    Fallback None/[] em caso de erro ou campo ausente.
    """
    try:
        from atlas_backend.core.delta_chaos_reader import get_ativo_raw
        raw = get_ativo_raw(ticker)
    except Exception:
        raw = {}
    return {
        "iv_rank":        raw.get("iv_rank"),
        "regime":         raw.get("regime"),
        "reflect_state":  raw.get("reflect_state"),
        "take_profit":    raw.get("take_profit"),
        "stop_loss":      raw.get("stop_loss"),
        "historico_config": raw.get("historico_config") or [],
    }


def _parse_tune_historico(historico_config: list) -> dict:
    """
    Extrai dados do último registro TUNE v2.0 de historico_config.
    Todos os campos têm fallback None quando ausentes.
    """
    empty = {
        "tp_sug": None, "stop_sug": None, "ir": None, "n_trades": None,
        "confianca": None, "janela_anos": None, "ano_ini": None, "ano_fim": None,
        "trials_feitos": None, "trials_total": None, "early_stop": False,
        "reflect_real": None, "total_ciclos": None, "reflect_masked": None,
        "acerto_pct": None, "ciclos_fallback": None,
    }
    tune_records = [r for r in (historico_config or []) if r.get("modulo") == "TUNE v2.0"]
    if not tune_records:
        return empty

    tune_records.sort(key=lambda x: x.get("data", ""), reverse=True)
    rec = tune_records[0]
    motivo    = rec.get("motivo", "") or ""
    valor_novo = rec.get("valor_novo", "") or ""

    # TP / STOP sugerido — preferir valor_novo; fallback para motivo
    tp_sug = stop_sug = None
    m = _RE_TP_STOP_CAL.search(valor_novo) or _RE_TP_STOP_CAL.search(motivo)
    if m:
        tp_sug, stop_sug = float(m.group(1)), float(m.group(2))

    # IR
    ir = None
    m = _RE_IR_CAL.search(motivo)
    if m:
        ir = float(m.group(1))

    # Confiança
    confianca = None
    m = _RE_CONF_CAL.search(motivo)
    if m:
        confianca = m.group(1)

    # N trades
    n_trades = None
    m = _RE_TRADES_CAL.search(motivo)
    if m:
        n_trades = int(m.group(1))

    # Trials
    trials_feitos = trials_total = None
    m = _RE_TRIALS_CAL.search(motivo)
    if m:
        trials_feitos, trials_total = int(m.group(1)), int(m.group(2))
    early_stop = "early stop" in motivo.lower()

    # Janela de teste (campo periodo_teste: "AAAA-AAAA")
    janela_anos = ano_ini = ano_fim = None
    periodo = rec.get("periodo_teste", "") or ""
    if periodo and "-" in periodo:
        parts = periodo.split("-")
        if len(parts) == 2:
            try:
                ano_ini, ano_fim = int(parts[0]), int(parts[1])
                janela_anos = ano_fim - ano_ini
            except ValueError:
                pass

    # REFLECT real
    reflect_real = None
    m = _RE_REFLECT_CAL.search(motivo)
    if m:
        reflect_real = int(m.group(1))

    # Ciclos mascarados / total
    total_ciclos = reflect_masked = None
    m = _RE_MASKED_CAL.search(motivo)
    if m:
        reflect_masked, total_ciclos = int(m.group(1)), int(m.group(2))

    # Fallback B
    ciclos_fallback = None
    m = _RE_FALLBACK_CAL.search(motivo)
    if m:
        ciclos_fallback = int(m.group(1))

    # Acerto %
    acerto_pct = None
    m = _RE_ACERTO_CAL.search(motivo)
    if m:
        acerto_pct = float(m.group(1))

    return {
        "tp_sug": tp_sug, "stop_sug": stop_sug, "ir": ir, "n_trades": n_trades,
        "confianca": confianca, "janela_anos": janela_anos,
        "ano_ini": ano_ini, "ano_fim": ano_fim,
        "trials_feitos": trials_feitos, "trials_total": trials_total,
        "early_stop": early_stop, "reflect_real": reflect_real,
        "total_ciclos": total_ciclos, "reflect_masked": reflect_masked,
        "acerto_pct": acerto_pct, "ciclos_fallback": ciclos_fallback,
    }


def _to_float(value, default=0.0):
    """Converte valor para float com fallback seguro."""
    try:
        if value is None:
            return float(default)
        if isinstance(value, str):
            v = value.strip().replace("%", "")
            if "," in v and "." in v:
                v = v.replace(".", "").replace(",", ".")
            elif "," in v and "." not in v:
                v = v.replace(",", ".")
            parsed = float(v)
        else:
            parsed = float(value)
        if math.isnan(parsed) or math.isinf(parsed):
            return float(default)
        return parsed
    except Exception:
        return float(default)


def _extract_tp_stop(*texts):
    """Extrai TP e STOP de textos como 'TP=0.80 STOP=1.20'."""
    normalized = []
    for t in texts:
        if t is None:
            continue
        if isinstance(t, str):
            if t.strip():
                normalized.append(t)
        else:
            normalized.append(str(t))
    combined = " ".join(normalized).strip()
    if not combined:
        return None, None
    tp_match = re.search(r"TP\s*=\s*([+-]?\d+(?:[.,]\d+)?)", combined, flags=re.IGNORECASE)
    stop_match = re.search(r"(?:STOP|STOPLOSS|SL)\s*=\s*([+-]?\d+(?:[.,]\d+)?)", combined, flags=re.IGNORECASE)
    tp = _to_float(tp_match.group(1), default=0.0) if tp_match else None
    stop = _to_float(stop_match.group(1), default=0.0) if stop_match else None
    return tp, stop


# =============================================================================
# Diagnóstico executivo (usado por exportar_relatorio_calibracao e gerar_relatorio_tune)
# =============================================================================

def gerar_diagnostico_executivo(dados_tune: dict[str, any]) -> str:
    """
    Gera diagnóstico executivo em linguagem natural baseado em regras determinísticas.

    Regras:
    - SE ir_valido >= 1.0 E confianca == "alta":
      → "Edge forte confirmado. TUNE sugere ajuste de TP/STOP com alta confiança estatística (N={n}). Recomendação: APLICAR."
    - SE ir_valido >= 0.5 E confianca == "baixa":
      → "Edge positivo com amostra limitada (N={n}). Ajuste sugerido é plausível mas incerto. Recomendação: REVISAR com board antes de aplicar."
    - SE ir_valido < 0.5:
      → "IR válido abaixo de 0.5. Parâmetros atuais podem ser superiores ao sugerido. Recomendação: MANTER parâmetros atuais."
    - SE confianca == "amostra_insuficiente":
      → "Amostra insuficiente (N={n} < 20). Resultado não confiável. Recomendação: NÃO APLICAR — aguardar mais ciclos."
    - SE reflect_mask_pct > 30%:
      → Acrescentar: " Atenção: {reflect_mask_pct:.0f}% dos ciclos foram mascarados pelo REFLECT — IR válido pode estar inflado."
    - SE janela_anos <= 3:
      → Acrescentar: " Atenção: janela de {janela_anos} anos (Optuna) exclui ciclos anteriores a {ano_teste_ini} — eventos extremos históricos não estão no cálculo."
    """

    ir_valido = dados_tune.get("ir_valido", 0)
    confianca = dados_tune.get("confianca", "")
    n_trades = dados_tune.get("n_trades", 0)
    reflect_mask_pct = dados_tune.get("reflect_mask_pct", 0)
    janela_anos = dados_tune.get("janela_anos", 0)
    ano_teste_ini = dados_tune.get("ano_teste_ini", "")

    # Base do diagnóstico
    if ir_valido >= 1.0 and confianca == "alta":
        diagnóstico = f"Edge forte confirmado. TUNE sugere ajuste de TP/STOP com alta confiança estatística (N={n_trades}). Recomendação: APLICAR."
    elif ir_valido >= 0.5 and confianca == "baixa":
        diagnóstico = f"Edge positivo com amostra limitada (N={n_trades}). Ajuste sugerido é plausível mas incerto. Recomendação: REVISAR com board antes de aplicar."
    elif ir_valido < 0.5:
        diagnóstico = "IR válido abaixo de 0.5. Parâmetros atuais podem ser superiores ao sugerido. Recomendação: MANTER parâmetros atuais."
    elif confianca == "amostra_insuficiente":
        diagnóstico = f"Amostra insuficiente (N={n_trades} < 20). Resultado não confiável. Recomendação: NÃO APLICAR — aguardar mais ciclos."
    else:
        diagnóstico = "Diagnóstico não classificado."

    # Acrescentar alertas
    if reflect_mask_pct > 30:
        diagnóstico += f" Atenção: {reflect_mask_pct:.0f}% dos ciclos foram mascarados pelo REFLECT — IR válido pode estar inflado."

    if janela_anos <= 3:
        diagnóstico += f" Atenção: janela de {janela_anos} anos (Optuna) exclui ciclos anteriores a {ano_teste_ini} — eventos extremos históricos não estão no cálculo."

    return diagnóstico


def exportar_relatorio_calibracao(ticker: str) -> dict:
    """
    Lê o estado atual da calibração do ticker e retorna os dados para
    o frontend gerar o relatório .md client-side.
    Não grava nenhum arquivo em disco.

    Returns:
        dict com gate_resultado, fire_diagnostico, steps, data,
        tune_stats, gate_stats, tune_ranking_estrategia e campos B57,
        ou erro se calibração não chegou ao step 3.
    """
    from atlas_backend.core.delta_chaos_reader import get_ativo_raw

    dados_raw = get_ativo_raw(ticker)
    calibracao = dados_raw.get("calibracao", {})
    steps = calibracao.get("steps", {})

    step3 = steps.get("3_gate_fire", {})
    step3_status = step3.get("status", "idle")

    if step3_status not in ("done", "error"):
        return {
            "erro": "Calibração não chegou ao step 3 (gate_fire)",
            "step_atual": calibracao.get("step_atual"),
            "step3_status": step3_status,
        }

    gate_resultado = calibracao.get("gate_resultado") or {}
    fire_diagnostico = calibracao.get("fire_diagnostico") or {}
    data_hoje = datetime.now(tz=ZoneInfo('America/Sao_Paulo')).strftime("%Y-%m-%d")

    historico_config = dados_raw.get("historico_config") or []

    tune_rec = next(
        (r for r in reversed(historico_config) if r.get("modulo") == "TUNE v2.0"),
        {},
    )
    gate_rec = next(
        (r for r in reversed(historico_config) if r.get("modulo") == "GATE v1.0"),
        {},
    )

    # ── tune_stats (legado) ──
    tune_stats = {
        "tp_sugerido":   tune_rec.get("valor_novo"),
        "ir_valido":     tune_rec.get("ir_valido"),
        "n_trades":      tune_rec.get("trades_valido"),
        "confianca_n":   tune_rec.get("confianca_n"),
        "janela_anos":   tune_rec.get("janela_anos"),
        "ano_teste_ini": tune_rec.get("ano_teste_ini"),
        "trials":        tune_rec.get("trials"),
        "reflect_mask":  tune_rec.get("reflect_mask"),
        "pnl_medio":     tune_rec.get("pnl_medio"),
        "pnl_mediana":   tune_rec.get("pnl_mediana"),
        "pnl_pior":      tune_rec.get("pnl_pior"),
        "n_stops":       tune_rec.get("n_stops"),
        "acerto_pct":    tune_rec.get("acerto_valido"),
    }

    # ── gate_stats (legado) ──
    gate_stats = {
        "n_trades_valido":       gate_rec.get("n_trades_valido"),
        "pnl_total":             gate_rec.get("pnl_total"),
        "pnl_medio":             gate_rec.get("pnl_medio"),
        "pnl_mediana":           gate_rec.get("pnl_mediana"),
        "pnl_pior":              gate_rec.get("pnl_pior"),
        "dd_max":                gate_rec.get("dd_max"),
        "stops_seguidos":        gate_rec.get("stops_seguidos"),
        "estrategia_por_regime": gate_rec.get("estrategia_por_regime"),
        "gate_valores":          gate_rec.get("gate_valores"),
    }

    tune_ranking = dados_raw.get("tune_ranking_estrategia") or {}

    # ═══════════════════════════════════════════════════════════════
    # B57 — Campos enriquecidos para relatório unificado
    # ═══════════════════════════════════════════════════════════════

    # TP/STOP atuais do ativo
    tp_atual = _to_float(dados_raw.get("take_profit", 0), default=0.0)
    stop_atual = _to_float(dados_raw.get("stop_loss", 0), default=0.0)

    # TP/STOP sugeridos pelo TUNE
    tp_extraido, stop_extraido = _extract_tp_stop(
        tune_rec.get("combinacao", ""),
        tune_rec.get("valor_novo", ""),
        tune_rec.get("motivo", ""),
    )
    tp_novo = tp_extraido if tp_extraido is not None else tp_atual
    stop_novo = stop_extraido if stop_extraido is not None else stop_atual
    delta_tp = tp_novo - tp_atual
    delta_stop = stop_novo - stop_atual

    # Trials
    trials_rodados = _to_float(tune_rec.get("trials_executados") or tune_rec.get("trials"), default=0)
    trials_total = _to_float(tune_rec.get("trials_total", 150), default=150)

    # Early stop / retomado
    motivo = str(tune_rec.get("motivo") or "")
    early_stop = bool(tune_rec.get("early_stop_ativado", False)) or "early stop" in motivo.lower()
    retomado = "Study retomado" in motivo

    # Reflect mask
    reflect_mask = _to_float(tune_rec.get("reflect_mask"), default=0)
    total_ciclos = _to_float(tune_rec.get("total_ciclos"), default=0)
    reflect_mask_pct = (reflect_mask / total_ciclos * 100) if total_ciclos > 0 else 0.0

    # Ciclos reais / fallback
    ciclos_reais = _to_float(tune_rec.get("ciclos_reais"), default=0)
    ciclos_fallback = _to_float(tune_rec.get("ciclos_fallback"), default=0)

    # Distribuição de saídas
    n_tp = _to_float(tune_rec.get("n_tp"), default=0)
    n_stop = _to_float(tune_rec.get("n_stops"), default=0)
    n_venc = _to_float(tune_rec.get("n_venc"), default=0)
    acerto_pct = _to_float(tune_rec.get("acerto_valido"), default=0.0)

    # Pior trade
    pior_data = str(tune_rec.get("pior_data") or "")
    pior_motivo = str(tune_rec.get("pior_motivo") or "")
    pior_pnl = _to_float(tune_rec.get("pnl_pior"), default=0.0)

    # Estado REFLECT atual
    reflect_state_atual = dados_raw.get("reflect_state")

    # Sizing
    historico_trades = dados_raw.get("historico", [])
    _ultimo_ciclo_hist = historico_trades[-1] if historico_trades else {}
    sizing_orbit = _to_float(_ultimo_ciclo_hist.get("sizing", 0.0), default=0.0)
    _reflect_mult_map = {"A": 1.0, "B": 1.0, "C": 0.5, "D": 0.0, "T": 0.0}
    reflect_mult = _reflect_mult_map.get(reflect_state_atual, 1.0)
    sizing_final = round(sizing_orbit * reflect_mult, 4)

    # P&L médio TUNE e GATE
    pnl_medio_tune = _to_float(tune_rec.get("pnl_medio"), default=0.0)
    pnl_medio_gate = _to_float(gate_rec.get("pnl_medio"), default=0.0)
    diferenca_tune_gate = round(pnl_medio_tune - pnl_medio_gate, 4)
    nota_obrigatoria_b57 = (
        abs(diferenca_tune_gate) > 0.5
        and bool(pnl_medio_tune) and bool(pnl_medio_gate)
        and (pnl_medio_tune * pnl_medio_gate < 0)
    )

    # Stops por ano
    stops_por_ano = {}
    for _trade in historico_trades:
        if _trade.get("motivo_saida") == "STOP":
            _dt = str(_trade.get("data", "") or _trade.get("data_saida", "") or "")
            if len(_dt) >= 4:
                _ano = _dt[:4]
                stops_por_ano[_ano] = stops_por_ano.get(_ano, 0) + 1

    # P&L por ano
    _pnl_por_ano_raw = defaultdict(list)
    for _trade in historico_trades:
        _dt = str(_trade.get("data", "") or _trade.get("data_saida", "") or "")
        _pnl = _trade.get("pnl")
        if len(_dt) >= 4 and _pnl is not None:
            try:
                _pnl_por_ano_raw[_dt[:4]].append(float(_pnl))
            except (ValueError, TypeError):
                pass
    pnl_por_ano = [
        {"ano": _a, "pnl_medio": round(sum(_v) / len(_v), 2), "n_trades": len(_v)}
        for _a, _v in sorted(_pnl_por_ano_raw.items())
    ]

    # Frequência de regimes
    freq_regimes = {}
    for _trade in historico_trades:
        _r = _trade.get("regime")
        if _r:
            freq_regimes[_r] = freq_regimes.get(_r, 0) + 1

    # GATE E5 — estabilidade ORBIT
    gate_valores_b57 = gate_rec.get("gate_valores") or {}
    anos_validos_usados = gate_rec.get("anos_validos_usados")
    ir_por_regime_janela = gate_rec.get("ir_por_regime_janela") or {}

    # Ranking v3.1 e estratégias atuais
    _ranking_raw = dados_raw.get("tune_ranking_estrategia") or {}
    _meta_ranking = _ranking_raw.get("_meta") or {}
    _versao_ranking = str(_meta_ranking.get("versao", ""))
    ranking_v31 = {}
    if _versao_ranking == "3.1":
        for _r, _rd in _ranking_raw.items():
            if _r != "_meta" and isinstance(_rd, dict):
                ranking_v31[_r] = _rd
    estrategias_atuais = dados_raw.get("estrategias") or {}

    # Histórico de TUNEs aplicados
    historico_tunes = []
    for record in historico_config:
        if "TUNE" in str(record.get("modulo") or "").upper():
            motivo_record = str(record.get("motivo") or "")
            tp_hist, stop_hist = _extract_tp_stop(
                record.get("valor_novo", ""),
                record.get("combinacao", ""),
                motivo_record,
            )
            ir_match = re.search(r"IR=([+-]?\d+(?:\.\d+)?)", motivo_record)
            ir = ir_match.group(1) if ir_match else ""
            confianca_record = ""
            if re.search(r"\bAlta\b", motivo_record, flags=re.IGNORECASE):
                confianca_record = "Alta"
            elif re.search(r"\bBaixa\b", motivo_record, flags=re.IGNORECASE):
                confianca_record = "Baixa"
            historico_tunes.append({
                "data": str(record.get("data") or ""),
                "tp": f"{tp_hist:.2f}" if tp_hist is not None else "",
                "stop": f"{stop_hist:.2f}" if stop_hist is not None else "",
                "ir": ir,
                "confianca": confianca_record,
            })

    # Diagnóstico executivo
    diagnostico_executivo = gerar_diagnostico_executivo({
        "ir_valido": _to_float(tune_rec.get("ir_valido"), default=0.0),
        "confianca": str(tune_rec.get("confianca_n") or ""),
        "n_trades": _to_float(tune_rec.get("trades_valido"), default=0),
        "reflect_mask_pct": reflect_mask_pct,
        "janela_anos": _to_float(tune_rec.get("janela_anos"), default=0),
        "ano_teste_ini": str(tune_rec.get("ano_teste_ini") or ""),
    })

    return {
        "gate_resultado": gate_resultado,
        "fire_diagnostico": fire_diagnostico,
        "steps": steps,
        "data": data_hoje,
        "tune_stats": tune_stats,
        "gate_stats": gate_stats,
        "tune_ranking_estrategia": tune_ranking,
        # B57 — campos enriquecidos
        "tp_atual": tp_atual,
        "stop_atual": stop_atual,
        "tp_novo": tp_novo,
        "stop_novo": stop_novo,
        "delta_tp": delta_tp,
        "delta_stop": delta_stop,
        "trials_rodados": int(trials_rodados),
        "trials_total": int(trials_total),
        "early_stop": early_stop,
        "retomado": retomado,
        "total_ciclos": int(total_ciclos),
        "reflect_mask_pct": reflect_mask_pct,
        "ciclos_reais": int(ciclos_reais),
        "ciclos_fallback": int(ciclos_fallback),
        "n_tp": int(n_tp),
        "n_stop": int(n_stop),
        "n_venc": int(n_venc),
        "acerto_pct": acerto_pct,
        "pior_data": pior_data,
        "pior_motivo": pior_motivo,
        "pior_pnl": pior_pnl,
        "diagnostico_executivo": diagnostico_executivo,
        "historico_tunes": historico_tunes,
        "ranking_v31": ranking_v31,
        "estrategias_atuais": estrategias_atuais,
        "stops_por_ano": stops_por_ano,
        "pnl_por_ano": pnl_por_ano,
        "reflect_state_atual": reflect_state_atual,
        "sizing_orbit": sizing_orbit,
        "reflect_mult": reflect_mult,
        "sizing_final": sizing_final,
        "pnl_medio_tune": pnl_medio_tune,
        "pnl_medio_gate": pnl_medio_gate,
        "diferenca_tune_gate": diferenca_tune_gate,
        "nota_obrigatoria_b57": nota_obrigatoria_b57,
        "freq_regimes": freq_regimes,
        "gate_valores": gate_valores_b57,
        "anos_validos_usados": anos_validos_usados,
        "ir_por_regime_janela": ir_por_regime_janela,
    }


# =============================================================================
# NOVO: RELATÓRIO DE TUNE v2.0 (SPEC_RELATORIO_TUNE_v1.0.md)
# =============================================================================

def gerar_relatorio_tune(ticker: str, historico: bool = False) -> dict[str, any]:
    """
    Lê historico_config[] do master JSON e monta payload completo do relatório.
    
    Retorna:
    {
        "ticker": str,
        "ciclo": str,
        "data": str,
        "tp_atual": float,
        "stop_atual": float,
        "tp_novo": float,
        "stop_novo": float,
        "delta_tp": float,
        "delta_stop": float,
        "ir_valido": float,
        "n_trades": int,
        "confianca": str,
        "janela_anos": int,
        "ano_teste_ini": str,
        "trials_rodados": int,
        "trials_total": int,
        "early_stop": bool,
        "retomado": bool,
        "reflect_mask": int,
        "total_ciclos": int,
        "reflect_mask_pct": float,
        "ciclos_reais": int,
        "ciclos_fallback": int,
        "n_tp": int,
        "n_stop": int,
        "n_venc": int,
        "acerto_pct": float,
        "pior_data": str,
        "pior_motivo": str,
        "pior_pnl": float,
        "diagnostico_executivo": str,
        "historico_tunes": List[Dict[str, Any]],
        "markdown": str,
        "json_completo": Dict[str, Any]
    }
    """
    
    from atlas_backend.core.delta_chaos_reader import get_ativo_raw

    def _json_safe(value):
        """Converte estrutura arbitrária para algo serializável em JSON estrito."""
        if value is None:
            return None
        if isinstance(value, (str, bool, int)):
            return value
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return None
            return value
        if isinstance(value, dict):
            return {str(k): _json_safe(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [_json_safe(v) for v in value]
        # fallback para objetos não serializáveis (datetime, numpy types, etc.)
        try:
            json.dumps(value, ensure_ascii=False)
            return value
        except Exception:
            return str(value)
    
    # Obter dados do ativo
    dados_ativo = get_ativo_raw(ticker)

    # Extrair ranking v3.1 e estratégias atuais (para seções Etapa A/B)
    _ranking_raw      = dados_ativo.get("tune_ranking_estrategia") or {}
    _meta_ranking     = _ranking_raw.get("_meta") or {}
    _versao_ranking   = str(_meta_ranking.get("versao", ""))
    _estrategias_atu  = dados_ativo.get("estrategias") or {}
    ranking_v31: dict = {}
    if _versao_ranking == "3.1":
        for _r, _rd in _ranking_raw.items():
            if _r != "_meta" and isinstance(_rd, dict):
                ranking_v31[_r] = _rd

    # Regime representativo para fallback do bloco "Qualidade da Otimização" (v3.1)
    _rep_v31: dict = {}
    if ranking_v31:
        _curr_regime = str(dados_ativo.get("regime") or "")
        _cand = ranking_v31.get(_curr_regime) or {}
        if _cand.get("ir_calibrado") is not None or _cand.get("n_trades_calibracao") is not None:
            _rep_v31 = _cand
        if not _rep_v31:
            _best_ir: float = -float("inf")
            for _rd in ranking_v31.values():
                _ir = _rd.get("ir_calibrado")
                if isinstance(_ir, (int, float)) and not math.isnan(float(_ir)) and float(_ir) > _best_ir:
                    _best_ir = float(_ir)
                    _rep_v31 = _rd

    # Extrair historico_config com tolerância a dados malformados
    historico_config_raw = dados_ativo.get("historico_config")
    if not isinstance(historico_config_raw, list):
        historico_config_raw = []
    historico_config = [rec for rec in historico_config_raw if isinstance(rec, dict)]

    # Filtrar registros de TUNE (aceita variações de versão/nomenclatura)
    tune_records = [
        rec for rec in historico_config
        if "TUNE" in str(rec.get("modulo") or "").upper()
    ]
    
    # Se não houver TUNE, retornar erro
    if not tune_records:
        raise ValueError(f"Nenhum TUNE executado para o ativo {ticker}")
    
    # Ordenar por data (mais recente primeiro)
    tune_records.sort(key=lambda x: str((x or {}).get("data") or ""), reverse=True)

    # TUNE v3.1 grava 3 registros por regime; só estrategia.* tem campos estruturados
    _tune_est = [r for r in tune_records if str(r.get("parametro") or "").startswith("estrategia.")]
    tune_mais_recente = _tune_est[0] if _tune_est else tune_records[0]
    
    def _to_float(value, default=0.0):
        try:
            if value is None:
                return float(default)
            if isinstance(value, str):
                v = value.strip().replace("%", "")
                if "," in v and "." in v:
                    v = v.replace(".", "").replace(",", ".")
                elif "," in v and "." not in v:
                    v = v.replace(",", ".")
                parsed = float(v)
            else:
                parsed = float(value)
            if math.isnan(parsed) or math.isinf(parsed):
                return float(default)
            return parsed
        except Exception:
            return float(default)

    def _extract_tp_stop(*texts):
        # Aceita formatos variados, ex: "TP=0.80 STOP=1.20", "TP=0.80 | STOP=1.20", etc.
        normalized = []
        for t in texts:
            if t is None:
                continue
            if isinstance(t, str):
                if t.strip():
                    normalized.append(t)
            else:
                normalized.append(str(t))
        combined = " ".join(normalized).strip()
        if not combined:
            return None, None
        tp_match = re.search(r"TP\s*=\s*([+-]?\d+(?:[.,]\d+)?)", combined, flags=re.IGNORECASE)
        stop_match = re.search(r"(?:STOP|STOPLOSS|SL)\s*=\s*([+-]?\d+(?:[.,]\d+)?)", combined, flags=re.IGNORECASE)
        tp = _to_float(tp_match.group(1), default=0.0) if tp_match else None
        stop = _to_float(stop_match.group(1), default=0.0) if stop_match else None
        return tp, stop

    # Extrair dados do TUNE mais recente
    tp_atual = _to_float(dados_ativo.get("take_profit", 0), default=0.0)
    stop_atual = _to_float(dados_ativo.get("stop_loss", 0), default=0.0)
    tp_extraido, stop_extraido = _extract_tp_stop(
        tune_mais_recente.get("combinacao", ""),
        tune_mais_recente.get("valor_novo", ""),
        tune_mais_recente.get("motivo", ""),
    )
    tp_novo = tp_extraido if tp_extraido is not None else tp_atual
    stop_novo = stop_extraido if stop_extraido is not None else stop_atual
    
    # Extrair IR válido e confiança do motivo
    motivo = str(tune_mais_recente.get("motivo") or "")

    # PADRÃO v3.1 — leitura estruturada (prioridade); FALLBACK regex para legado v2.0
    _is_v31 = str(tune_mais_recente.get("versao_tune") or "") == "3.1"

    if _is_v31 and tune_mais_recente.get("ir_calibrado") is not None:
        ir_valido = _to_float(tune_mais_recente.get("ir_calibrado"), default=0.0)
    elif _rep_v31.get("ir_calibrado") is not None:
        ir_valido = _to_float(_rep_v31.get("ir_calibrado"), default=0.0)
    else:
        ir_valido_match = re.search(r"IR=([+-]?\d+(?:\.\d+)?)", motivo)
        ir_valido = _to_float(ir_valido_match.group(1), default=0.0) if ir_valido_match else 0.0

    # Confiança: v3.1 deriva de n_trades_calibracao; legado via regex
    if _is_v31 or _rep_v31:
        _n_calib_raw = (tune_mais_recente.get("n_trades_calibracao")
                        if _is_v31 else None) or _rep_v31.get("n_trades_calibracao")
        _n_calib = int(_n_calib_raw or 0)
        if _n_calib >= 30:
            confianca = "alta"
        elif _n_calib >= 20:
            confianca = "baixa"
        elif _n_calib > 0:
            confianca = "amostra_insuficiente"
        else:
            confianca_match = re.search(r"(Alta|Baixa|amostra_insuficiente)", motivo, flags=re.IGNORECASE)
            confianca = confianca_match.group(1).lower() if confianca_match else ""
    else:
        confianca_match = re.search(r"(Alta|Baixa|amostra_insuficiente)", motivo, flags=re.IGNORECASE)
        confianca = confianca_match.group(1).lower() if confianca_match else ""

    # Extrair janela de teste
    _janela_src = tune_mais_recente.get("janela_anos_usada") if _is_v31 else None
    if _janela_src is None:
        _janela_src = _rep_v31.get("janela_anos")
    if _janela_src is not None:
        janela_anos = int(_janela_src or 0)
        ano_teste_ini = str(datetime.now(tz=ZoneInfo('America/Sao_Paulo')).year - janela_anos) if janela_anos else ""
    else:
        periodo_teste = str(tune_mais_recente.get("periodo_teste") or "")
        if periodo_teste and "-" in periodo_teste:
            try:
                ano_ini, ano_fim = periodo_teste.split("-")
                janela_anos = int(ano_fim) - int(ano_ini)
                ano_teste_ini = ano_ini
            except Exception:
                janela_anos = 0
                ano_teste_ini = ""
        else:
            janela_anos = 0
            ano_teste_ini = ""

    # Extrair trials
    _trials_src = tune_mais_recente.get("trials_executados") if _is_v31 else None
    if _trials_src is None:
        _trials_src = _rep_v31.get("trials_rodados")
    if _trials_src is not None:
        trials_rodados = int(_trials_src or 0)
        _meta_trials = tune_mais_recente.get("_meta") or _meta_ranking or {}
        trials_total = int(_to_float(_meta_trials.get("trials_por_candidato", 150), default=150))
    else:
        trials_match = re.search(r"Trials:\s*(\d+)\s*/\s*(\d+)", motivo)
        trials_rodados = int(trials_match.group(1)) if trials_match else 0
        trials_total = int(trials_match.group(2)) if trials_match else 0
        if trials_total <= 0:
            meta = tune_mais_recente.get("_meta") or {}
            trials_total = int(_to_float(meta.get("trials_por_candidato", 150), default=150))

    # Extrair early stop
    _early_src = tune_mais_recente.get("early_stop_ativado") if _is_v31 else None
    if _early_src is None and _rep_v31:
        _early_src = _rep_v31.get("early_stop_ativado")
    if _early_src is not None:
        early_stop = bool(_early_src)
    else:
        early_stop = "early stop" in motivo.lower()
    
    # Extrair retomado
    retomado = "Study retomado" in motivo
    
    # Extrair reflect mask
    reflect_mask_match = re.search(r"(\d+) ciclos mascarados de (\d+)", motivo)
    reflect_mask = int(reflect_mask_match.group(1)) if reflect_mask_match else 0
    total_ciclos = int(reflect_mask_match.group(2)) if reflect_mask_match else 0
    reflect_mask_pct = (reflect_mask / total_ciclos * 100) if total_ciclos > 0 else 0
    
    # Extrair ciclos reais e fallback
    ciclos_reais_match = re.search(r"Ciclos com REFLECT real: (\d+)", motivo)
    ciclos_reais = int(ciclos_reais_match.group(1)) if ciclos_reais_match else 0
    
    ciclos_fallback_match = re.search(r"Fallback B: (\d+)", motivo)
    ciclos_fallback = int(ciclos_fallback_match.group(1)) if ciclos_fallback_match else 0
    
    # Extrair distribuição de saídas
    n_tp_match = re.search(r"TP: (\d+) ", motivo)
    n_tp = int(n_tp_match.group(1)) if n_tp_match else 0
    
    n_stop_match = re.search(r"STOP: (\d+) ", motivo)
    n_stop = int(n_stop_match.group(1)) if n_stop_match else 0
    
    n_venc_match = re.search(r"VENC: (\d+)", motivo)
    n_venc = int(n_venc_match.group(1)) if n_venc_match else 0
    
    acerto_match = re.search(r"Acerto:\s*([0-9\.,]+)%", motivo)
    acerto_pct = _to_float(acerto_match.group(1), default=0.0) if acerto_match else 0.0
    
    # Extrair pior trade
    pior_data_match = re.search(r"Data: (\d{4}-\d{2}-\d{2})", motivo)
    pior_data = pior_data_match.group(1) if pior_data_match else ""
    
    pior_motivo_match = re.search(r"Motivo: ([^\d]+)", motivo)
    pior_motivo = pior_motivo_match.group(1).strip() if pior_motivo_match else ""
    
    pior_pnl_match = re.search(r"P&L:\s*(-?)R\$\s*([0-9\.,]+)", motivo)
    if pior_pnl_match:
        sinal = -1.0 if pior_pnl_match.group(1) == "-" else 1.0
        pior_pnl = sinal * _to_float(pior_pnl_match.group(2), default=0.0)
    else:
        pior_pnl = 0.0
    
    # Extrair n_trades — PADRÃO v3.1 estruturado; FALLBACK regex legado
    _n_src = tune_mais_recente.get("n_trades_calibracao") if _is_v31 else None
    if _n_src is None:
        _n_src = _rep_v31.get("n_trades_calibracao")
    if _n_src is not None:
        n_trades = int(_n_src or 0)
    else:
        n_trades_match = re.search(r"N trades: (\d+)", motivo)
        n_trades = int(n_trades_match.group(1)) if n_trades_match else 0

    # B57 — 6 campos diagnóstico
    historico_trades = dados_ativo.get("historico", [])

    stops_por_ano: dict = {}
    for _trade in historico_trades:
        if _trade.get("motivo_saida") == "STOP":
            _dt = str(_trade.get("data", "") or _trade.get("data_saida", "") or "")
            if len(_dt) >= 4:
                _ano = _dt[:4]
                stops_por_ano[_ano] = stops_por_ano.get(_ano, 0) + 1

    from collections import defaultdict as _defaultdict
    _pnl_por_ano_raw: dict = _defaultdict(list)
    for _trade in historico_trades:
        _dt = str(_trade.get("data", "") or _trade.get("data_saida", "") or "")
        _pnl = _trade.get("pnl")
        if len(_dt) >= 4 and _pnl is not None:
            try:
                _pnl_por_ano_raw[_dt[:4]].append(float(_pnl))
            except (ValueError, TypeError):
                pass
    pnl_por_ano = [
        {"ano": _a, "pnl_medio": round(sum(_v) / len(_v), 2), "n_trades": len(_v)}
        for _a, _v in sorted(_pnl_por_ano_raw.items())
    ]

    reflect_state_atual = dados_ativo.get("reflect_state", None)

    _reflect_mult_map = {"A": 1.0, "B": 1.0, "C": 0.5, "D": 0.0, "T": 0.0}
    reflect_mult = _reflect_mult_map.get(reflect_state_atual, 1.0)
    _ultimo_ciclo_hist = historico_trades[-1] if historico_trades else {}
    sizing_orbit = float(_ultimo_ciclo_hist.get("sizing", 0.0) or 0.0)
    sizing_final = round(sizing_orbit * reflect_mult, 4)

    pnl_medio_tune = _to_float(tune_mais_recente.get("pnl_medio"), default=0.0)
    _gate_records_b57 = [
        rec for rec in historico_config
        if "GATE" in str(rec.get("modulo") or "").upper()
    ]
    _gate_records_b57.sort(key=lambda x: str((x or {}).get("data") or ""), reverse=True)
    pnl_medio_gate = _to_float(
        _gate_records_b57[0].get("pnl_medio") if _gate_records_b57 else None,
        default=0.0
    )
    _gate_rec_recente_b57 = _gate_records_b57[0] if _gate_records_b57 else {}
    gate_valores_b57       = _gate_rec_recente_b57.get("gate_valores") or {}
    anos_validos_usados_b57 = _gate_rec_recente_b57.get("anos_validos_usados")
    ir_por_regime_janela_b57 = _gate_rec_recente_b57.get("ir_por_regime_janela") or {}
    diferenca_tune_gate = round(pnl_medio_tune - pnl_medio_gate, 4)
    nota_obrigatoria_b57 = (
        abs(diferenca_tune_gate) > 0.5 and
        bool(pnl_medio_tune) and bool(pnl_medio_gate) and
        (pnl_medio_tune * pnl_medio_gate < 0)
    )

    freq_regimes: dict = {}
    for _trade in historico_trades:
        _r = _trade.get("regime")
        if _r:
            freq_regimes[_r] = freq_regimes.get(_r, 0) + 1

    # Calcular deltas
    delta_tp = _to_float(tp_novo, default=0.0) - _to_float(tp_atual, default=0.0)
    delta_stop = _to_float(stop_novo, default=0.0) - _to_float(stop_atual, default=0.0)
    
    # Montar histórico de TUNEs
    historico_tunes = []
    for record in (tune_records if historico else tune_records[:1]):
        if not isinstance(record, dict):
            continue
        # Extrair TP, STOP, IR, confiança do motivo
        motivo_record = str(record.get("motivo") or "")
        
        tp_hist, stop_hist = _extract_tp_stop(
            record.get("valor_novo", ""),
            record.get("combinacao", ""),
            motivo_record,
        )
        tp = f"{tp_hist:.2f}" if tp_hist is not None else ""
        stop = f"{stop_hist:.2f}" if stop_hist is not None else ""
        
        ir_match = re.search(r"IR=([+-]?\d+(?:\.\d+)?)", motivo_record)
        ir = ir_match.group(1) if ir_match else ""
        
        confianca_record = ""
        if re.search(r"\bAlta\b", motivo_record, flags=re.IGNORECASE):
            confianca_record = "Alta"
        elif re.search(r"\bBaixa\b", motivo_record, flags=re.IGNORECASE):
            confianca_record = "Baixa"
        
        historico_tunes.append({
            "data": str(record.get("data") or ""),
            "tp": tp,
            "stop": stop,
            "ir": ir,
            "confianca": confianca_record
        })
    
    # Gerar diagnóstico executivo
    diagnostico_executivo = gerar_diagnostico_executivo({
        "ir_valido": ir_valido,
        "confianca": confianca,
        "n_trades": n_trades,
        "reflect_mask_pct": reflect_mask_pct,
        "janela_anos": janela_anos,
        "ano_teste_ini": ano_teste_ini
    })
    
    # Gerar markdown
    if historico:
        json_completo = _json_safe(dados_ativo)
    else:
        # Remove the 'historico' array to reduce payload size (trades data not needed for board decision)
        dados_reduzido = {k: v for k, v in dados_ativo.items() if k != "historico"}
        json_completo = _json_safe(dados_reduzido)

    markdown = formatar_relatorio_markdown({
        "ticker": ticker,
        "ciclo": tune_mais_recente.get("ciclo_id", ""),
        "data": tune_mais_recente.get("data", ""),
        "tp_atual": tp_atual,
        "stop_atual": stop_atual,
        "tp_novo": tp_novo,
        "stop_novo": stop_novo,
        "delta_tp": delta_tp,
        "delta_stop": delta_stop,
        "ir_valido": ir_valido,
        "n_trades": n_trades,
        "confianca": confianca,
        "janela_anos": janela_anos,
        "ano_teste_ini": ano_teste_ini,
        "trials_rodados": trials_rodados,
        "trials_total": trials_total,
        "early_stop": early_stop,
        "retomado": retomado,
        "reflect_mask": reflect_mask,
        "total_ciclos": total_ciclos,
        "reflect_mask_pct": reflect_mask_pct,
        "ciclos_reais": ciclos_reais,
        "ciclos_fallback": ciclos_fallback,
        "n_tp": n_tp,
        "n_stop": n_stop,
        "n_venc": n_venc,
        "acerto_pct": acerto_pct,
        "pior_data": pior_data,
        "pior_motivo": pior_motivo,
        "pior_pnl": pior_pnl,
        "diagnostico_executivo": diagnostico_executivo,
        "historico_tunes": historico_tunes,
        "json_completo": json_completo,
        "ranking_v31": ranking_v31,
        "estrategias_atuais": _estrategias_atu,
        "stops_por_ano": stops_por_ano,
        "pnl_por_ano": pnl_por_ano,
        "reflect_state_atual": reflect_state_atual,
        "sizing_orbit": sizing_orbit,
        "reflect_mult": reflect_mult,
        "sizing_final": sizing_final,
        "pnl_medio_tune": pnl_medio_tune,
        "pnl_medio_gate": pnl_medio_gate,
        "diferenca_tune_gate": diferenca_tune_gate,
        "nota_obrigatoria_b57": nota_obrigatoria_b57,
        "freq_regimes": freq_regimes,
        "gate_valores": gate_valores_b57,
        "anos_validos_usados": anos_validos_usados_b57,
        "ir_por_regime_janela": ir_por_regime_janela_b57,
        }, incluir_json_bruto=historico)
    
    # Montar payload completo
    payload = {
        "ticker": ticker,
        "ciclo": str(tune_mais_recente.get("ciclo_id") or ""),
        "data": str(tune_mais_recente.get("data") or ""),
        "tp_atual": tp_atual,
        "stop_atual": stop_atual,
        "tp_novo": tp_novo,
        "stop_novo": stop_novo,
        "delta_tp": delta_tp,
        "delta_stop": delta_stop,
        "ir_valido": ir_valido,
        "n_trades": n_trades,
        "confianca": confianca,
        "janela_anos": janela_anos,
        "ano_teste_ini": ano_teste_ini,
        "trials_rodados": trials_rodados,
        "trials_total": trials_total,
        "early_stop": early_stop,
        "retomado": retomado,
        "reflect_mask": reflect_mask,
        "total_ciclos": total_ciclos,
        "reflect_mask_pct": reflect_mask_pct,
        "ciclos_reais": ciclos_reais,
        "ciclos_fallback": ciclos_fallback,
        "n_tp": n_tp,
        "n_stop": n_stop,
        "n_venc": n_venc,
        "acerto_pct": acerto_pct,
        "pior_data": pior_data,
        "pior_motivo": pior_motivo,
        "pior_pnl": pior_pnl,
        "diagnostico_executivo": diagnostico_executivo,
        "historico_tunes": historico_tunes,
        "markdown": markdown,
        "json_completo": json_completo
    }

    return _json_safe(payload)

def formatar_relatorio_markdown(dados: dict[str, any], incluir_json_bruto: bool = True) -> str:
    """
    Formata relatório completo em Markdown para exportação.
    """
    import json
    
    # Cabeçalho
    markdown = f"# Relatório de TUNE — {dados['ticker']} — {dados['ciclo']}\n"
    markdown += f"**Data de execução:** {dados['data']}\n"
    markdown += f"**Gerado por:** ATLAS v2.6\n\n"
    markdown += "---\n\n"
    
    # Como usar este relatório
    markdown += "## Como usar este relatório\n"
    markdown += "Cole este arquivo numa sessão com o board Delta Chaos.\n"
    markdown += "O board irá:\n"
    markdown += "\n"
    markdown += "1. Avaliar os resultados apresentados\n"
    markdown += "2. Recomendar APLICAR, REVISAR ou MANTER os parâmetros\n"
    markdown += "3. Abrir tensões se houver divergência entre regime e parâmetros\n"
    markdown += "\n"
    markdown += "---\n\n"
    
    # Limitação de simulação
    markdown += "## ⚠️ Limitação de simulação\n"
    markdown += "Os valores foram otimizados usando proxies intradiários: mínimo do dia\n"
    markdown += "como proxy de TP e máximo do dia como proxy de STOP. Em dias de alta\n"
    markdown += "volatilidade, esses proxies podem superestimar ganhos de TP e\n"
    markdown += "subestimar custos de STOP.\n"
    markdown += "\n"
    markdown += "---\n\n"
    
    # Diagnóstico executivo
    markdown += "## Diagnóstico executivo\n"
    markdown += f"{dados['diagnostico_executivo']}\n\n"
    markdown += "---\n\n"

    # Etapa A — Eleição de Estratégia por Regime (v3.1)
    ranking_v31      = dados.get("ranking_v31") or {}
    estrategias_atu  = dados.get("estrategias_atuais") or {}
    if ranking_v31:
        markdown += "## Eleição de Estratégia por Regime (Etapa A — IR ordinal)\n"
        markdown += "> IR_eleicao é ordinal — serve apenas para comparar candidatos entre si.\n"
        markdown += "> Não é comparável ao IR_calibrado da Etapa B.\n\n"
        markdown += "| Regime | Status Eleição | Estratégia Eleita | N Trades | Candidatos (top-3) | Motivo | Alerta |\n"
        markdown += "|--------|---------------|-------------------|----------|--------------------|--------|--------|\n"
        for regime in sorted(ranking_v31.keys()):
            rd            = ranking_v31[regime]
            status        = rd.get("eleicao_status", "—")
            eleita        = rd.get("estrategia_eleita") or "—"
            n_tr_raw      = rd.get("n_trades_reais")
            n_tr_str      = str(n_tr_raw) if n_tr_raw is not None else "—"
            atual         = estrategias_atu.get(regime)
            alerta        = ""
            if eleita != "—" and atual and eleita != atual:
                alerta = "**⚠️ MUDANÇA DE ESTRATÉGIA**"

            # Candidatos: top-3 de ranking_eleicao; vencedor com valores calibrados de Etapa B
            ranking_cands = rd.get("ranking_eleicao") or []
            cand_parts = []
            for c in ranking_cands[:3]:
                if not isinstance(c, dict):
                    continue
                est   = c.get("estrategia", "?")
                ir_c  = c.get("ir_mediana")
                ir_s  = f"{ir_c:+.3f}" if isinstance(ir_c, (int, float)) else "?"
                if est == eleita and isinstance(rd.get("tp_calibrado"), (int, float)):
                    cand_parts.append(
                        f"{est}✓ IR={ir_s} TP={rd['tp_calibrado']:.2f} STOP={rd['stop_calibrado']:.2f}"
                    )
                else:
                    cand_parts.append(f"{est} IR={ir_s}")
            cands_str = "; ".join(cand_parts) if cand_parts else "—"

            # Motivo: apenas para regimes sem eleição
            if status == "bloqueado":
                motivo_reg = "bloqueado_regra"
            elif status == "estrutural_fixo" and (n_tr_raw or 0) == 0:
                motivo_reg = "sem_trades"
            else:
                motivo_reg = "—"

            markdown += f"| {regime} | {status} | {eleita} | {n_tr_str} | {cands_str} | {motivo_reg} | {alerta} |\n"
        markdown += "\n---\n\n"

        # Etapa B — Calibração TP/Stop por Regime (v3.1)
        markdown += "## Calibração TP/Stop por Regime (Etapa B — IR calibrado)\n"
        markdown += "| Regime | Status Calib | TP Calibrado | Stop Calibrado | IR_calibrado | N_trades_calib | Aplicação |\n"
        markdown += "|--------|-------------|-------------|----------------|-------------|----------------|----------|\n"
        _APLICACAO_LABEL = {
            "automatica":           "✓ aplicado automaticamente",
            "pendente_anomalia":    "⚠️ ANOMALIA — aguardando CEO",
            "anomalia_aprovada_ceo": "✓ anomalia aprovada por CEO",
            "anomalia_rejeitada_ceo": "✗ anomalia rejeitada — ciclo anterior mantido",
        }
        for regime in sorted(ranking_v31.keys()):
            rd          = ranking_v31[regime]
            status      = rd.get("eleicao_status", "—")
            if status not in ("competitiva", "estrutural_fixo"):
                continue
            if not rd.get("estrategia_eleita"):
                continue
            status_calib = rd.get("status_calibracao") or "—"
            tp_c         = rd.get("tp_calibrado")
            stop_c       = rd.get("stop_calibrado")
            ir_c         = rd.get("ir_calibrado")
            n_c          = rd.get("n_trades_calibracao", "—")
            tp_str       = f"{tp_c:.2f}" if isinstance(tp_c, (int, float)) else "—"
            stop_str     = f"{stop_c:.2f}" if isinstance(stop_c, (int, float)) else "—"
            ir_str       = f"{ir_c:+.3f}" if isinstance(ir_c, (int, float)) else "—"
            aplicacao_raw = rd.get("aplicacao") or ""
            aplicacao_str = _APLICACAO_LABEL.get(aplicacao_raw, aplicacao_raw or "—")
            # Anomalia: acrescenta motivos inline
            anomalia = rd.get("anomalia") or {}
            if anomalia.get("detectada") and anomalia.get("motivos"):
                motivos_str = "; ".join(anomalia["motivos"])
                aplicacao_str += f" ({motivos_str})"
            markdown += f"| {regime} | {status_calib} | {tp_str} | {stop_str} | {ir_str} | {n_c} | {aplicacao_str} |\n"
        markdown += "\n---\n\n"
    elif dados.get("ranking_v31") is not None:
        markdown += "> *Relatório v3.0 — campos v3.1 indisponíveis. Re-rodar TUNE para atualizar.*\n\n---\n\n"

    # Parâmetros TUNE
    markdown += "## Parâmetros TUNE\n"
    markdown += "| Campo | Atual | Sugerido | Delta |\n"
    markdown += "|---------------|--------|----------|--------|\n"
    markdown += f"| Take Profit | {dados['tp_atual']} | {dados['tp_novo']} | {dados['delta_tp']:+.2f} |\n"
    markdown += f"| Stop Loss | {dados['stop_atual']} | {dados['stop_novo']} | {dados['delta_stop']:+.2f} |\n"
    markdown += "\n"
    markdown += "---\n\n"
    
    # Qualidade da otimização
    markdown += "## Qualidade da otimização\n"
    markdown += f"- IR válido (janela de teste): {dados['ir_valido']}\n"
    markdown += f"- N trades na janela: {dados['n_trades']}\n"
    markdown += f"- Confiança: {dados['confianca']}\n"
    markdown += f"- Janela de teste: {dados['janela_anos']} anos ({dados['ano_teste_ini']}–{datetime.now(tz=ZoneInfo('America/Sao_Paulo')).year})\n"
    markdown += f"- Trials rodados: {dados['trials_rodados']} / {dados['trials_total']}\n"
    markdown += f"- Early stop ativado: {'SIM' if dados['early_stop'] else 'NÃO'}\n"
    markdown += f"- Study Optuna retomado: {'SIM' if dados['retomado'] else 'NÃO'}\n"
    markdown += "\n"
    markdown += "---\n\n"

    # GATE E5 — Estabilidade ORBIT
    markdown += "## GATE E5 — Estabilidade ORBIT\n"
    _gv = dados.get("gate_valores") or {}
    _e5_str = _gv.get("E5 — ORBIT") or "—"
    markdown += f"- Resultado: {_e5_str}\n"
    markdown += f"- Anos válidos usados: {dados.get('anos_validos_usados', '—')}\n"
    markdown += f"- IR por regime (janela válida):\n"
    _ir_reg = dados.get("ir_por_regime_janela") or {}
    for _r, _ir in sorted(_ir_reg.items(), key=lambda x: -x[1]):
        _marker = " ← PASSOU" if _ir >= 0.10 else " ← bloqueado"
        markdown += f"  - {_r}: {_ir:+.4f}{_marker}\n"
    markdown += "\n---\n\n"

    # Máscara REFLECT
    markdown += "## Máscara REFLECT\n"
    markdown += f"- Ciclos mascarados (Edge C/D/T): {dados['reflect_mask']} de {dados['total_ciclos']} ({dados['reflect_mask_pct']:.1f}%)\n"
    markdown += f"- Ciclos com REFLECT real: {dados['ciclos_reais']}\n"
    markdown += f"- Ciclos com fallback B: {dados['ciclos_fallback']}\n"
    markdown += "\n"
    markdown += "---\n\n"
    
    # Distribuição de saídas
    markdown += "## Distribuição de saídas (janela de teste)\n"
    _total_saidas = max((dados['n_tp'] or 0) + (dados['n_stop'] or 0) + (dados['n_venc'] or 0), 1)
    markdown += f"- Take Profit: {dados['n_tp']} ({(dados['n_tp'] or 0) / _total_saidas * 100:.1f}%)\n"
    markdown += f"- Stop Loss:   {dados['n_stop']} ({(dados['n_stop'] or 0) / _total_saidas * 100:.1f}%)\n"
    markdown += f"- Vencimento:  {dados['n_venc']} ({(dados['n_venc'] or 0) / _total_saidas * 100:.1f}%)\n"
    markdown += f"- Acerto: {dados['acerto_pct']:.1f}%\n"
    markdown += "\n"
    markdown += "---\n\n"

    # Distribuição temporal de stops
    markdown += "## Distribuição temporal de stops\n"
    stops_por_ano = dados.get("stops_por_ano") or {}
    if stops_por_ano:
        markdown += "| Ano | Stops |\n"
        markdown += "|-----|-------|\n"
        for _ano, _n in sorted(stops_por_ano.items()):
            markdown += f"| {_ano} | {_n} |\n"
    else:
        markdown += "_Sem stops registrados no histórico._\n"
    markdown += "\n"
    markdown += "---\n\n"

    # P&L por ano
    markdown += "## P&L por ano\n"
    pnl_por_ano = dados.get("pnl_por_ano") or []
    if pnl_por_ano:
        markdown += "| Ano | P&L médio/trade | N trades |\n"
        markdown += "|-----|-----------------|----------|\n"
        for _row in pnl_por_ano:
            _sinal = "+" if _row["pnl_medio"] >= 0 else ""
            markdown += f"| {_row['ano']} | R$ {_sinal}{_row['pnl_medio']:,.2f} | {_row['n_trades']} |\n"
    else:
        markdown += "_Sem histórico de trades disponível._\n"
    markdown += "\n"
    markdown += "---\n\n"

    # Frequência de regimes
    markdown += "## Frequência de regimes (janela de backtest)\n"
    freq_regimes = dados.get("freq_regimes") or {}
    if freq_regimes:
        markdown += "| Regime | Ciclos |\n"
        markdown += "|--------|--------|\n"
        for _regime, _ciclos in sorted(freq_regimes.items(), key=lambda x: -x[1]):
            markdown += f"| {_regime} | {_ciclos} |\n"
    else:
        markdown += "_Sem dados de regime no histórico._\n"
    markdown += "\n"
    markdown += "---\n\n"

    # Estado REFLECT atual
    markdown += "## Estado REFLECT atual\n"
    _rs = dados.get("reflect_state_atual") or "—"
    _sf = dados.get("sizing_final", 0.0)
    _so = dados.get("sizing_orbit", 0.0)
    _rm = dados.get("reflect_mult", 1.0)
    markdown += f"- Estado: {_rs}\n"
    markdown += f"- Sizing final recomendado: {_sf} (orbit {_so} × reflect {_rm})\n"
    markdown += "\n"
    markdown += "---\n\n"

    # Reconciliação TUNE × GATE
    markdown += "## Reconciliação TUNE × GATE\n"
    _pt = dados.get("pnl_medio_tune", 0.0)
    _pg = dados.get("pnl_medio_gate", 0.0)
    _diff = dados.get("diferenca_tune_gate", 0.0)
    _sinal_diff = "+" if _diff >= 0 else ""
    markdown += f"- P&L médio TUNE: R$ {_pt:,.2f}\n"
    markdown += f"- P&L médio GATE: R$ {_pg:,.2f}\n"
    markdown += f"- Diferença: R$ {_sinal_diff}{_diff:,.2f}\n"
    if dados.get("nota_obrigatoria_b57"):
        markdown += "> ⚠ Divergência significativa entre janelas TUNE e GATE. Revisar com board\n"
        markdown += "> antes de aplicar parâmetros. Possível sobreajuste ou viés de janela.\n"
    markdown += "\n"
    markdown += "---\n\n"

    # Pior trade
    markdown += "## Pior trade (janela de teste)\n"
    markdown += f"- Data: {dados['pior_data']}\n"
    markdown += f"- Motivo: {dados['pior_motivo']}\n"
    markdown += f"- P&L: R${dados['pior_pnl']:,.2f}\n"
    markdown += "\n"
    markdown += "---\n\n"
    
    # Histórico de TUNEs aplicados
    markdown += "## Histórico de TUNEs aplicados\n"
    markdown += "| Data | TP | STOP | IR válido | Confiança |\n"
    markdown += "|------|-----|------|-----------|-----------|\n"
    for tune in dados['historico_tunes']:
        markdown += f"| {tune['data']} | {tune['tp']} | {tune['stop']} | {tune['ir']} | {tune['confianca']} |\n"
    markdown += "\n"
    markdown += "---\n\n"
    
    # Dados brutos (JSON)
    if incluir_json_bruto:
        markdown += "## Dados brutos (JSON)\n"
        markdown += "```json\n"
        markdown += json.dumps(dados['json_completo'], indent=2, ensure_ascii=False)
        markdown += "\n```\n"
    
    return markdown
