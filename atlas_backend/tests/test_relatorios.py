import pytest
from unittest.mock import patch, MagicMock
from atlas_backend.core.relatorios import formatar_relatorio_markdown


def test_formatar_relatorio_markdown_estrutura():
    """Teste existente - não modificar"""
    dados = {
        "ticker": "PETR4",
        "status": "active",
        "core": {"estrategia": "CSP", "regime": "ALTA"},
        "historico": [],
        "historico_config": [
            {
                "modulo": "TUNE v3.0",
                "data": "2026-04-25",
                "parametro": "test",
                "valor_anterior": None,
                "valor_novo": "valor",
                "motivo": "test"
            }
        ],
        "take_profit": 0.05,
        "stop_loss": 0.03,
        "calibracao": {
            "step_atual": 3,
            "steps": {
                "3_gate_fire": {
                    "gate_resultado": {
                        "resultado": "OPERAR",
                        "criterios": [{"id": "C1", "nome": "Taxa de acerto", "passou": True, "valor": "95%"}]
                    }
                }
            }
        },
        "ciclo": "2026-04",
        "data": "2026-04-25",
        "tp_atual": 0.05,
        "stop_atual": 0.03,
        "tp_novo": 0.06,
        "stop_novo": 0.04,
        "delta_tp": 0.01,
        "delta_stop": 0.01,
        "ir_valido": True,
        "n_trades": 50,
        "confianca": 0.95,
        "janela_anos": 2,
        "ano_teste_ini": 2024,
        "trials_rodados": 187,
        "trials_total": 200,
        "early_stop": False,
        "retomado": False,
        "reflect_mask": 0,
        "total_ciclos": 0,
        "reflect_mask_pct": 0.0,
        "ciclos_reais": 0,
        "ciclos_fallback": 0,
        "n_tp": 0,
        "n_stop": 0,
        "n_venc": 0,
        "acerto_pct": 0.0,
        "diagnostico_executivo": "IR válido (janela de teste): True\n- N trades na janela: 50\n- Confiança: 0.95\n- Janela de teste: 2 anos (2024–2026)\n- Trials rodados: 187 / 200\n- Early stop ativado: NÃO\n- Study Optuna retomado: NÃO",
        "historico_tunes": [],
        "pior_data": "2026-04-15",
        "pior_motivo": "Teste de pior trade",
        "pior_pnl": -12.50,
        "json_completo": {"test": "data"}
    }
    
    markdown = formatar_relatorio_markdown(dados)
    
    # Verificações existentes que devem continuar passando
    assert "# Relatório de TUNE — PETR4 — 2026-04" in markdown
    assert "## Dados brutos (JSON)" in markdown  # Este teste existe e deve continuar passando
    assert "```json" in markdown
    assert "## Histórico de TUNEs aplicados" in markdown


def test_formatar_relatorio_markdown_sem_json_bruto():
    """NOVO: Teste para verificar que a seção JSON é omitida quando incluir_json_bruto=False"""
    dados = {
        "ticker": "PETR4",
        "status": "active",
        "core": {"estrategia": "CSP", "regime": "ALTA"},
        "historico": [],
        "historico_config": [
            {
                "modulo": "TUNE v3.0",
                "data": "2026-04-25",
                "parametro": "test",
                "valor_anterior": None,
                "valor_novo": "valor",
                "motivo": "test"
            }
        ],
        "take_profit": 0.05,
        "stop_loss": 0.03,
        "calibracao": {
            "step_atual": 3,
            "steps": {
                "3_gate_fire": {
                    "gate_resultado": {
                        "resultado": "OPERAR",
                        "criterios": [{"id": "C1", "nome": "Taxa de acerto", "passou": True, "valor": "95%"}]
                    }
                }
            }
        },
        "ciclo": "2026-04",
        "data": "2026-04-25",
        "tp_atual": 0.05,
        "stop_atual": 0.03,
        "tp_novo": 0.06,
        "stop_novo": 0.04,
        "delta_tp": 0.01,
        "delta_stop": 0.01,
        "ir_valido": True,
        "n_trades": 50,
        "confianca": 0.95,
        "janela_anos": 2,
        "ano_teste_ini": 2024,
        "trials_rodados": 187,
        "trials_total": 200,
        "early_stop": False,
        "retomado": False,
        "reflect_mask": 0,
        "total_ciclos": 0,
        "reflect_mask_pct": 0.0,
        "ciclos_reais": 0,
        "ciclos_fallback": 0,
        "n_tp": 0,
        "n_stop": 0,
        "n_venc": 0,
        "acerto_pct": 0.0,
        "diagnostico_executivo": "IR válido (janela de teste): True\n- N trades na janela: 50\n- Confiança: 0.95\n- Janela de teste: 2 anos (2024–2026)\n- Trials rodados: 187 / 200\n- Early stop ativado: NÃO\n- Study Optuna retomado: NÃO",
        "historico_tunes": [],
        "pior_data": "2026-04-15",
        "pior_motivo": "Teste de pior trade",
        "pior_pnl": -12.50,
        "json_completo": {"test": "data"}
    }
    
    # Chamar com incluir_json_bruto=False (modo "Último TUNE")
    markdown = formatar_relatorio_markdown(dados, incluir_json_bruto=False)
    
    # Verificar que a seção JSON NÃO está presente
    assert "## Dados brutos (JSON)" not in markdown
    assert "```json" not in markdown
    
    # Verificar que outras seções importantes ainda estão presentes
    assert "# Relatório de TUNE — PETR4 — 2026-04" in markdown
    assert "## Histórico de TUNEs aplicados" in markdown
    assert "## Parâmetros TUNE" in markdown
    assert "## Qualidade da otimização" in markdown
    assert "## Diagnóstico executivo" in markdown