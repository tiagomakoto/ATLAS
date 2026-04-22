"""
atlas_backend/core/relatorios.py

Módulo para geração de relatórios de TUNE e ONBOARDING.
"""

import os
import json
import tempfile
from datetime import datetime
from pathlib import Path
import re

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
    data_hoje = datetime.now().strftime("%Y-%m-%d")
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
            entry["data_aplicado"] = datetime.now().strftime("%Y-%m-%d")
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


def gerar_relatorio_calibracao_gate_bloqueado(
    ticker: str,
    gate_resultado: dict,
    calibracao: dict,
) -> dict:
    """
    Gera relatório .md de calibração com 5 seções obrigatórias.
    Funciona tanto para GATE BLOQUEADO quanto para outros resultados.
    Campos ausentes degradam graciosamente exibindo "não disponível".

    Returns:
        {
            "id": int,
            "arquivo": "CALIB_GATE_BLOQUEADO_{ticker}_{data}.md",
            "caminho": str,
            "gate_resultado": dict,
            "steps": dict,
            "data": str
        }
    """
    id_rel = _gerar_id()
    id_str = f"{id_rel:03d}"
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    arquivo = f"CALIB_GATE_BLOQUEADO_{id_str}_{ticker}_{data_hoje}.md"
    path_rel = RELATORIOS_DIR / arquivo

    # === Dados ambientais e TUNE ===
    env  = _get_ativo_env(ticker)
    tune = _parse_tune_historico(env["historico_config"])

    # === Dados do gate / fire ===
    criterios     = gate_resultado.get("criterios") or []
    resultado_gate = gate_resultado.get("resultado") or "BLOQUEADO"
    ciclo         = gate_resultado.get("ciclo") or datetime.now().strftime("%Y-%m")
    fire_diag     = calibracao.get("fire_diagnostico") or {}
    steps         = calibracao.get("steps") or {}

    # --- helpers locais ---
    def _fmt(v, fmt=None):
        """Formata valor ou retorna 'não disponível' se None."""
        if v is None:
            return "não disponível"
        return f"{v:{fmt}}" if fmt else str(v)

    def _delta(atual, sug):
        """Calcula delta formatado ou 'N/D'."""
        if atual is None or sug is None:
            return "N/D"
        return f"{sug - atual:+.2f}"

    # =========================================================
    # Seção 1 — IDENTIFICAÇÃO
    # =========================================================
    sec1 = (
        f"# Relatório de Calibração — {ticker} — {resultado_gate}\n"
        f"**ID:** {id_str}  **Data:** {data_hoje}  **Ciclo:** {ciclo}\n"
        f"**Sistema:** Delta Chaos v1.0 / ATLAS v2.6\n"
        f"**Gerado por:** ATLAS\n\n"
        f"| Campo | Valor |\n"
        f"|-------|-------|\n"
        f"| IV Rank (último ciclo) | {_fmt(env['iv_rank'])} |\n"
        f"| Regime ORBIT atual | {_fmt(env['regime'])} |\n"
        f"| Estado REFLECT atual | {_fmt(env['reflect_state'])} |\n"
    )

    # =========================================================
    # Seção 2 — GATE — CRITÉRIOS
    # =========================================================
    if criterios:
        rows_gate = ""
        for c in criterios:
            icon = "✓" if c.get("passou") else "✗"
            rows_gate += (
                f"| {c.get('id', 'N/D')} — {c.get('nome', 'N/D')} "
                f"| {c.get('valor', 'N/D')} | {icon} |\n"
            )

        resultado_icon = (
            "✗ BLOQUEADO" if resultado_gate == "BLOQUEADO"
            else f"✓ {resultado_gate}"
        )

        falhas_block = ""
        if resultado_gate == "BLOQUEADO":
            falhou = [c for c in criterios if not c.get("passou")]
            if falhou:
                falhas_block = "\n### Critérios que falharam\n\n"
                for c in falhou:
                    falhas_block += (
                        f"- **{c.get('id', 'N/D')} — {c.get('nome', 'N/D')}**: "
                        f"observado `{c.get('valor', 'N/D')}` (threshold não atingido)\n"
                    )

        sec2 = (
            "## GATE — Critérios de Validação\n\n"
            "| Critério | Valor observado | Resultado |\n"
            "|----------|-----------------|-----------|\n"
            f"{rows_gate}\n"
            f"**Resultado:** {resultado_icon}\n"
            f"{falhas_block}"
        )
    else:
        sec2 = (
            "## GATE — Critérios de Validação\n\n"
            "Detalhamento de critérios não disponível — "
            "verificar gate_resultado no JSON do ativo.\n"
        )

    # =========================================================
    # Seção 3 — TUNE — PARÂMETROS CALIBRADOS
    # =========================================================
    tp_atual   = env["take_profit"]
    stop_atual = env["stop_loss"]

    if tune["tp_sug"] is not None or tune["stop_sug"] is not None:
        # Janela
        if tune["janela_anos"] is not None and tune["ano_ini"] is not None:
            janela_str = f"{tune['janela_anos']} anos ({tune['ano_ini']}–{tune['ano_fim']})"
        else:
            janela_str = "não disponível"

        # Trials
        if tune["trials_feitos"] is not None and tune["trials_total"] is not None:
            trials_str = f"{tune['trials_feitos']}/{tune['trials_total']}"
            if tune["early_stop"]:
                trials_str += " — early stop"
        else:
            trials_str = "não disponível"

        # REFLECT mask
        if tune["reflect_real"] is not None and tune["total_ciclos"] is not None and tune["total_ciclos"] > 0:
            pct_real = tune["reflect_real"] / tune["total_ciclos"] * 100
            reflect_str = f"{tune['reflect_real']} ciclos de {tune['total_ciclos']} ({pct_real:.0f}%)"
        else:
            reflect_str = "não disponível"

        sec3 = (
            "## TUNE — Parâmetros Calibrados\n\n"
            "| Parâmetro | Atual | Sugerido | Delta |\n"
            "|-----------|-------|----------|-----------|\n"
            f"| TP | {_fmt(tp_atual, '.2f')} | {_fmt(tune['tp_sug'], '.2f')} | {_delta(tp_atual, tune['tp_sug'])} |\n"
            f"| STOP | {_fmt(stop_atual, '.2f')} | {_fmt(tune['stop_sug'], '.2f')} | {_delta(stop_atual, tune['stop_sug'])} |\n\n"
            f"- **IR válido:** {_fmt(tune['ir'])}\n"
            f"- **N trades (janela):** {_fmt(tune['n_trades'])}\n"
            f"- **Confiança:** {_fmt(tune['confianca'])}\n"
            f"- **Janela:** {janela_str}\n"
            f"- **Trials:** {trials_str}\n"
            f"- **Máscara REFLECT:** {reflect_str}\n"
        )
    else:
        sec3 = (
            "## TUNE — Parâmetros Calibrados\n\n"
            "TUNE não executado neste ciclo.\n"
        )

    # =========================================================
    # Seção 4 — EDGE POR REGIME
    # =========================================================
    regimes = fire_diag.get("regimes") or []
    if regimes:
        rows_fire = ""
        for r in regimes:
            n = r.get("trades") or 0
            aviso = " ⚠ amostra insuficiente" if n < 10 else ""
            rows_fire += (
                f"| {r.get('regime', 'N/D')} | {n}{aviso} "
                f"| {r.get('acerto_pct', 0):.1f}% "
                f"| {r.get('ir', 0):.2f} "
                f"| {r.get('estrategia_dominante', 'N/D')} |\n"
            )
        sec4 = (
            "## Edge por Regime\n\n"
            "| Regime | N trades | Acerto % | IR | Estratégia dominante |\n"
            "|--------|----------|----------|----|----------------------|\n"
            f"{rows_fire}"
        )
    else:
        sec4 = (
            "## Edge por Regime\n\n"
            "Diagnóstico FIRE não disponível — GATE bloqueou antes do FIRE.\n"
        )

    # =========================================================
    # Seção 5 — LIMITAÇÕES CONHECIDAS
    # =========================================================
    limitacoes = []

    n_trades  = tune["n_trades"]
    confianca = tune["confianca"]
    if n_trades is not None:
        if n_trades < 20 or (confianca and confianca != "Alta"):
            msg = f"PE-001 (confiança estatística): N trades = {n_trades}"
            if confianca and confianca != "Alta":
                msg += f", confiança = {confianca}"
            msg += " — resultado com validade limitada."
            limitacoes.append(msg)
    else:
        limitacoes.append(
            "PE-001 (confiança estatística): dados de TUNE não disponíveis para avaliação."
        )

    if tune["reflect_masked"] is not None and tune["total_ciclos"] and tune["total_ciclos"] > 0:
        pct_masked = tune["reflect_masked"] / tune["total_ciclos"] * 100
        if pct_masked > 30:
            limitacoes.append(
                f"PE-005/PE-006 (pesos REFLECT): {pct_masked:.0f}% dos ciclos foram mascarados "
                "— IR válido pode estar inflado."
            )

    if tune["janela_anos"] is not None and tune["janela_anos"] <= 3:
        limitacoes.append(
            f"Janela curta ({tune['janela_anos']} anos) — "
            "eventos extremos históricos podem estar fora da amostra."
        )

    if not limitacoes:
        limitacoes.append("Nenhuma limitação crítica identificada neste ciclo.")

    lim_lines = "\n".join(
        f"- **{l}**" if l.startswith("PE-") else f"- {l}"
        for l in limitacoes
    )
    motivo_final = gate_resultado.get("motivo") or "verificar gate_resultado"
    sec5 = (
        "## Limitações Conhecidas\n\n"
        f"{lim_lines}\n\n"
        f"**Resultado final:** {resultado_gate} — {motivo_final}\n"
    )

    # =========================================================
    # Montar template completo
    # =========================================================
    template = (
        sec1 + "\n---\n\n" +
        sec2 + "\n---\n\n" +
        sec3 + "\n---\n\n" +
        sec4 + "\n---\n\n" +
        sec5 +
        "\n---\n\n*Este relatório foi gerado automaticamente pelo sistema ATLAS.*\n"
    )

    # Escrita atômica: temp → replace
    RELATORIOS_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(RELATORIOS_DIR), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(template)
        os.replace(tmp_path, path_rel)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    # Atualizar index.json
    entry = {
        "id": id_str,
        "ticker": ticker,
        "data": data_hoje,
        "tipo": "CALIB_GATE_BLOQUEADO",
        "arquivo": arquivo,
        "gate_resultado": gate_resultado,
        "steps": steps,
    }
    index = _carregar_index()
    index.append(entry)
    _salvar_index(index)

    return {
        "id": id_rel,
        "arquivo": arquivo,
        "caminho": str(path_rel),
        "gate_resultado": gate_resultado,
        "steps": steps,
        "data": data_hoje,
    }


def gerar_relatorio_calibracao_completo(
    ticker: str,
    gate_resultado: dict,
    fire_diagnostico: dict,
    calibracao: dict,
) -> dict:
    """
    Gera relatório .md para cenário de calibração completa (GATE + FIRE aprovados).
    Inclui: validação GATE, diagnóstico FIRE, parâmetros, recomendações.

    Returns:
        {
            "id": int,
            "arquivo": "CALIB_COMPLETA_{ticker}_{data}.md",
            "caminho": str,
            "gate_resultado": dict,
            "fire_diagnostico": dict,
            "steps": dict,
            "data": str
        }
    """
    id_rel = _gerar_id()
    id_str = f"{id_rel:03d}"
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    arquivo = f"CALIB_COMPLETA_{id_str}_{ticker}_{data_hoje}.md"
    path_rel = RELATORIOS_DIR / arquivo

    steps = calibracao.get("steps", {})
    step1 = steps.get("1_backtest_dados", {})
    step2 = steps.get("2_tune", {})
    step3 = steps.get("3_gate_fire", {})

    criterios = gate_resultado.get("criterios", [])
    regimes = fire_diagnostico.get("regimes", [])
    cobertura = fire_diagnostico.get("cobertura", {})

    # Template do relatório
    template = f"""# Relatório de Calibração — {ticker} — CALIBRAÇÃO COMPLETA

**ID:** {id_str}
**Data:** {data_hoje}
**Status:** Calibração concluída com sucesso
**Gerado por:** ATLAS v2.6

---

## Resumo

A calibração do ativo **{ticker}** foi concluída com sucesso.
Todos os critérios de validação histórica (GATE) foram aprovados
e o diagnóstico de estratégia (FIRE) está disponível.

**Resultado GATE:** OPERAR ✓
**Resultado FIRE:** DIAGNÓSTICO DISPONÍVEL ✓

---

## Validação GATE — Critérios Aprovados

| ID | Critério | Status | Valor |
|{"|---|---|---|"}
"""
    for c in criterios:
        status_icon = "✓ APROVADO" if c.get("passou") else "✗ FALHOU"
        template += f"| {c.get('id', 'N/D')} | {c.get('nome', 'N/D')} | {status_icon} | {c.get('valor', 'N/D')} |\n"

    template += f"""
---

## Diagnóstico FIRE — Estratégia por Regime

"""
    if regimes:
        template += "| Regime | Trades | Acerto | IR | Estratégia Dominante |\n"
        template += "|---|---|---|---|---|\n"
        for r in regimes:
            template += f"| {r.get('regime', 'N/D')} | {r.get('trades', 0)} | {r.get('acerto_pct', 0):.1f}% | {r.get('ir', 0):.2f} | {r.get('estrategia_dominante', 'N/D')} |\n"

    template += f"""
### Cobertura Geral

- **Ciclos com operação:** {cobertura.get('ciclos_com_operacao', 0)} de {cobertura.get('total_ciclos', 0)}
- **Total de trades:** {cobertura.get('total_trades', 0)}
- **Acerto geral:** {cobertura.get('acerto_geral_pct', 0):.1f}%
- **P&L total:** R$ {cobertura.get('pnl_total', 0):,.2f}

"""
    if fire_diagnostico.get("stops_por_regime"):
        template += "### Stops por Regime\n\n"
        stops = fire_diagnostico.get("stops_por_regime", {})
        for regime, stop_info in stops.items():
            template += f"- **{regime}:** {stop_info}\n"
        template += "\n"

    template += f"""---

## Estado dos Steps

| Step | Módulo | Status | Iniciado | Concluído |
|{"|---|---|---|---|---|"}
| 1 | backtest_dados | {step1.get('status', 'N/D')} | {step1.get('iniciado_em', '-')} | {step1.get('concluido_em', '-')} |
| 2 | tune | {step2.get('status', 'N/D')} | {step2.get('iniciado_em', '-')} | {step2.get('concluido_em', '-')} |
| 3 | gate_fire | {step3.get('status', 'N/D')} | {step3.get('iniciado_em', '-')} | {step3.get('concluido_em', '-')} |

---

## Recomendações

1. **Ativo aprovado para operação** — parâmetros validados historicamente
2. Monitorar regime diariamente via ORBIT
3. Executar /daily/run para verificação automática de TP/STOP
4. Revisar FIRE periodicamente para identificar mudanças de regime

---

## Dados Técnicos

```json
{json.dumps({
    "ticker": ticker,
    "id": id_str,
    "data": data_hoje,
    "tipo": "CALIB_COMPLETA",
    "gate_resultado": gate_resultado,
    "fire_diagnostico": fire_diagnostico,
    "calibracao_steps": steps
}, indent=2, ensure_ascii=False)}
```

---

*Este relatório foi gerado automaticamente pelo sistema ATLAS.*
*O ativo está pronto para operação via FIRE.*
"""

    with open(path_rel, "w", encoding="utf-8") as f:
        f.write(template)

    entry = {
        "id": id_str,
        "ticker": ticker,
        "data": data_hoje,
        "tipo": "CALIB_COMPLETA",
        "arquivo": arquivo,
        "gate_resultado": gate_resultado,
        "fire_diagnostico": fire_diagnostico,
        "steps": steps,
    }

    index = _carregar_index()
    index.append(entry)
    _salvar_index(index)

    return {
        "id": id_rel,
        "arquivo": arquivo,
        "caminho": str(path_rel),
        "gate_resultado": gate_resultado,
        "fire_diagnostico": fire_diagnostico,
        "steps": steps,
        "data": data_hoje,
    }


def exportar_relatorio_calibracao(ticker: str) -> dict:
    """
    Lê o estado atual da calibração do ticker e gera o relatório apropriado.
    Detecta se GATE foi aprovado ou bloqueado e gera o relatório correto.

    Returns:
        dict com dados do relatório gerado ou erro se calibração incompleta
    """
    from atlas_backend.core.delta_chaos_reader import get_ativo_raw

    dados_raw = get_ativo_raw(ticker)
    calibracao = dados_raw.get("calibracao", {})
    steps = calibracao.get("steps", {})

    step3 = steps.get("3_gate_fire", {})
    step3_status = step3.get("status", "idle")

    # Verificar se step 3 foi executado
    if step3_status not in ("done", "error"):
        return {
            "erro": "Calibração não chegou ao step 3 (gate_fire)",
            "step_atual": calibracao.get("step_atual"),
            "step3_status": step3_status,
        }

    gate_resultado = calibracao.get("gate_resultado") or {}
    fire_diagnostico = calibracao.get("fire_diagnostico") or {}

    # Determinar tipo de relatório
    gate_aprovado = gate_resultado.get("resultado") == "OPERAR"

    if gate_aprovado:
        return gerar_relatorio_calibracao_completo(
            ticker=ticker,
            gate_resultado=gate_resultado,
            fire_diagnostico=fire_diagnostico,
            calibracao=calibracao,
        )
    else:
        return gerar_relatorio_calibracao_gate_bloqueado(
            ticker=ticker,
            gate_resultado=gate_resultado,
            calibracao=calibracao,
        )


# =============================================================================
# NOVO: RELATÓRIO DE TUNE v2.0 (SPEC_RELATORIO_TUNE_v1.0.md)
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
    
    from atlas_backend.core.delta_chaos_reader import get_ativo
    
    # Obter dados do ativo
    dados_ativo = get_ativo(ticker)
    
    # Extrair historico_config
    historico_config = dados_ativo.get("historico_config", [])
    
    # Filtrar apenas registros de TUNE v2.0
    tune_records = [rec for rec in historico_config if rec.get("modulo") == "TUNE v2.0"]
    
    # Se não houver TUNE, retornar erro
    if not tune_records:
        raise ValueError(f"Nenhum TUNE executado para o ativo {ticker}")
    
    # Ordenar por data (mais recente primeiro)
    tune_records.sort(key=lambda x: x.get("data", ""), reverse=True)
    
    # Pegar o mais recente
    tune_mais_recente = tune_records[0]
    
    # Extrair dados do TUNE mais recente
    tp_atual = dados_ativo.get("take_profit", 0)
    stop_atual = dados_ativo.get("stop_loss", 0)
    tp_novo = tune_mais_recente.get("combinacao", "").split("=")[1].split(" ")[0] if "=" in tune_mais_recente.get("combinacao", "") else 0
    stop_novo = tune_mais_recente.get("combinacao", "").split("=")[2] if "=" in tune_mais_recente.get("combinacao", "") else 0
    
    # Extrair IR válido e confiança do motivo
    motivo = tune_mais_recente.get("motivo", "")
    ir_valido_match = re.search(r"IR=\+([\d.]+)", motivo)
    ir_valido = float(ir_valido_match.group(1)) if ir_valido_match else 0
    
    confianca_match = re.search(r"(Alta|Baixa)", motivo)
    confianca = confianca_match.group(1) if confianca_match else ""
    
    # Extrair janela de teste
    periodo_teste = tune_mais_recente.get("periodo_teste", "")
    if periodo_teste and "-" in periodo_teste:
        ano_ini, ano_fim = periodo_teste.split("-")
        janela_anos = int(ano_fim) - int(ano_ini)
        ano_teste_ini = ano_ini
    else:
        janela_anos = 0
        ano_teste_ini = ""
    
    # Extrair trials
    trials_match = re.search(r"Trials: (\d+)/\d+", motivo)
    trials_rodados = int(trials_match.group(1)) if trials_match else 0
    trials_total = 200  # Valor fixo da SPEC
    
    # Extrair early stop
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
    
    acerto_match = re.search(r"Acerto: ([\d.]+)%", motivo)
    acerto_pct = float(acerto_match.group(1)) if acerto_match else 0
    
    # Extrair pior trade
    pior_data_match = re.search(r"Data: (\d{4}-\d{2}-\d{2})", motivo)
    pior_data = pior_data_match.group(1) if pior_data_match else ""
    
    pior_motivo_match = re.search(r"Motivo: ([^\d]+)", motivo)
    pior_motivo = pior_motivo_match.group(1).strip() if pior_motivo_match else ""
    
    pior_pnl_match = re.search(r"P&L: -R\$(\d+,\d+)", motivo)
    pior_pnl_str = pior_pnl_match.group(1) if pior_pnl_match else "0"
    pior_pnl = float(pior_pnl_str.replace(",", ""))
    
    # Extrair n_trades
    n_trades_match = re.search(r"N trades: (\d+)", motivo)
    n_trades = int(n_trades_match.group(1)) if n_trades_match else 0
    
    # Calcular deltas
    delta_tp = float(tp_novo) - float(tp_atual)
    delta_stop = float(stop_novo) - float(stop_atual)
    
    # Montar histórico de TUNEs
    historico_tunes = []
    for record in tune_records:
        # Extrair TP, STOP, IR, confiança do motivo
        motivo_record = record.get("motivo", "")
        
        tp_match = re.search(r"TP=([\d.]+)", motivo_record)
        tp = tp_match.group(1) if tp_match else ""
        
        stop_match = re.search(r"STOP=([\d.]+)", motivo_record)
        stop = stop_match.group(1) if stop_match else ""
        
        ir_match = re.search(r"IR=\+([\d.]+)", motivo_record)
        ir = ir_match.group(1) if ir_match else ""
        
        confianca_record = ""
        if "Alta" in motivo_record:
            confianca_record = "Alta"
        elif "Baixa" in motivo_record:
            confianca_record = "Baixa"
        
        historico_tunes.append({
            "data": record.get("data", ""),
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
        "historico_tunes": historico_tunes
    })
    
    # Montar payload completo
    payload = {
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
        "markdown": markdown,
        "json_completo": dados_ativo
    }
    
    return payload

def formatar_relatorio_markdown(dados: dict[str, any]) -> str:
    """
    Formata relatório completo em Markdown para exportação.
    """
    
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
    markdown += f"- Janela de teste: {dados['janela_anos']} anos ({dados['ano_teste_ini']}–{datetime.now().year})\n"
    markdown += f"- Trials rodados: {dados['trials_rodados']} / {dados['trials_total']}\n"
    markdown += f"- Early stop ativado: {'SIM' if dados['early_stop'] else 'NÃO'}\n"
    markdown += f"- Study Optuna retomado: {'SIM' if dados['retomado'] else 'NÃO'}\n"
    markdown += "\n"
    markdown += "---\n\n"
    
    # Máscara REFLECT
    markdown += "## Máscara REFLECT\n"
    markdown += f"- Ciclos mascarados (Edge C/D/E): {dados['reflect_mask']} de {dados['total_ciclos']} ({dados['reflect_mask_pct']:.1f}%)\n"
    markdown += f"- Ciclos com REFLECT real: {dados['ciclos_reais']}\n"
    markdown += f"- Ciclos com fallback B: {dados['ciclos_fallback']}\n"
    markdown += "\n"
    markdown += "---\n\n"
    
    # Distribuição de saídas
    markdown += "## Distribuição de saídas (janela de teste)\n"
    markdown += f"- Take Profit: {dados['n_tp']} ({dados['acerto_pct']:.1f}%)\n"
    markdown += f"- Stop Loss: {dados['n_stop']} ({dados['acerto_pct']:.1f}%)\n"
    markdown += f"- Vencimento: {dados['n_venc']} ({dados['acerto_pct']:.1f}%)\n"
    markdown += f"- Acerto: {dados['acerto_pct']:.1f}%\n"
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
    markdown += "## Dados brutos (JSON)\n"
    markdown += "```json\n"
    import json
    markdown += json.dumps(dados['json_completo'], indent=2, ensure_ascii=False)
    markdown += "\n```"
    
    return markdown