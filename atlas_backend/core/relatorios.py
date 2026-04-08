# ════════════════════════════════════════════════════════════════════
# DELTA CHAOS — RELATÓRIOS v1.0
# Gerência de relatórios TUNE e ONBOARDING
# ════════════════════════════════════════════════════════════════════

import os
import json
from datetime import datetime
from pathlib import Path

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
  TP:   {params['tp_atual']*100:.1f}%
  STOP: {params['stop_atual']*100:.1f}%

**Parâmetros sugeridos:**
  TP:   {params['tp_sugerido']*100:.1f}%   (delta: {params['delta_tp']*100:+.1f}%)
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
