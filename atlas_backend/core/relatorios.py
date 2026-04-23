"""
atlas_backend/core/relatorios.py

Módulo para geração de relatórios de TUNE e ONBOARDING.
"""

import os
import json
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


def exportar_relatorio_calibracao(ticker: str) -> dict:
    """
    Lê o estado atual da calibração do ticker e retorna os dados para
    o frontend gerar o relatório .md client-side.
    Não grava nenhum arquivo em disco.

    Returns:
        dict com gate_resultado, fire_diagnostico, steps e data,
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
    data_hoje = datetime.now().strftime("%Y-%m-%d")

    return {
        "gate_resultado": gate_resultado,
        "fire_diagnostico": fire_diagnostico,
        "steps": steps,
        "data": data_hoje,
    }


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