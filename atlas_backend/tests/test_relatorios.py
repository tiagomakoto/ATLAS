import pytest
from atlas_backend.core.relatorios import (
    gerar_diagnostico_executivo,
    formatar_relatorio_markdown,
    gerar_relatorio_tune
)


def test_gerar_diagnostico_executivo_ir_alto_confianca_alta():
    dados = {
        "ir_valido": 1.5,
        "confianca": "alta",
        "n_trades": 50,
        "reflect_mask_pct": 10,
        "janela_anos": 5,
        "ano_teste_ini": "2021"
    }
    diagnóstico = gerar_diagnostico_executivo(dados)
    assert "Edge forte confirmado" in diagnóstico
    assert "APLICAR" in diagnóstico
    assert "10% dos ciclos foram mascarados" not in diagnóstico  # < 30%
    assert "janela de 5 anos" not in diagnóstico  # janela > 3 não inclui alerta


def test_gerar_diagnostico_executivo_ir_baixo():
    dados = {
        "ir_valido": 0.3,
        "confianca": "baixa",
        "n_trades": 15,
        "reflect_mask_pct": 0,
        "janela_anos": 5
    }
    diagnóstico = gerar_diagnostico_executivo(dados)
    assert "IR válido abaixo de 0.5" in diagnóstico
    assert "MANTER parâmetros atuais" in diagnóstico


def test_gerar_diagnostico_executivo_amostra_insuficiente():
    dados = {
        "ir_valido": 0.8,
        "confianca": "amostra_insuficiente",
        "n_trades": 10,
        "reflect_mask_pct": 0,
        "janela_anos": 5
    }
    diagnóstico = gerar_diagnostico_executivo(dados)
    assert "Amostra insuficiente" in diagnóstico
    assert "NÃO APLICAR" in diagnóstico


def test_gerar_diagnostico_executivo_reflect_mask_alta():
    dados = {
        "ir_valido": 1.2,
        "confianca": "alta",
        "n_trades": 40,
        "reflect_mask_pct": 35,
        "janela_anos": 5
    }
    diagnóstico = gerar_diagnostico_executivo(dados)
    assert "35% dos ciclos foram mascarados" in diagnóstico


def test_gerar_diagnostico_executivo_janela_curta():
    dados = {
        "ir_valido": 1.0,
        "confianca": "alta",
        "n_trades": 30,
        "reflect_mask_pct": 0,
        "janela_anos": 2,
        "ano_teste_ini": "2024"
    }
    diagnóstico = gerar_diagnostico_executivo(dados)
    assert "janela de 2 anos" in diagnóstico
    assert "eventos extremos históricos" in diagnóstico


def test_formatar_relatorio_markdown_estrutura():
    dados = {
        "ticker": "VALE3",
        "ciclo": "2026-04",
        "data": "2026-04-13",
        "tp_atual": 0.75,
        "stop_atual": 1.50,
        "tp_novo": 0.80,
        "stop_novo": 1.75,
        "delta_tp": 0.05,
        "delta_stop": 0.25,
        "ir_valido": 1.234,
        "n_trades": 47,
        "confianca": "alta",
        "janela_anos": 5,
        "ano_teste_ini": "2021",
        "trials_rodados": 187,
        "trials_total": 200,
        "early_stop": True,
        "retomado": False,
        "reflect_mask": 12,
        "total_ciclos": 58,
        "reflect_mask_pct": 20.7,
        "ciclos_reais": 46,
        "ciclos_fallback": 12,
        "n_tp": 31,
        "n_stop": 9,
        "n_venc": 7,
        "acerto_pct": 73.2,
        "pior_data": "2023-03-15",
        "pior_motivo": "STOP",
        "pior_pnl": -412.0,
        "diagnostico_executivo": "Edge forte confirmado. TUNE sugere ajuste de TP/STOP com alta confiança estatística (N=47). Recomendação: APLICAR.",
        "historico_tunes": [
            {"data": "2026-04-13", "tp": "0.75", "stop": "1.50", "ir": "1.123", "confianca": "Alta"},
            {"data": "2026-01-08", "tp": "0.70", "stop": "1.50", "ir": "0.987", "confianca": "Baixa"}
        ],
        "json_completo": {}
    }
    markdown = formatar_relatorio_markdown(dados)
    
    # Verifica se todas as seções estão presentes
    assert "# Relatório de TUNE" in markdown
    assert "## Diagnóstico executivo" in markdown
    assert "## Parâmetros TUNE" in markdown
    assert "## Qualidade da otimização" in markdown
    assert "## Máscara REFLECT" in markdown
    assert "## Distribuição de saídas" in markdown
    assert "## Pior trade" in markdown
    assert "## Histórico de TUNEs aplicados" in markdown
    assert "## Dados brutos (JSON)" in markdown
    assert "TUNE_VALE3_2026-04_2026-04-13.md" not in markdown  # nome de arquivo não deve estar no conteúdo
    assert "Os valores foram otimizados usando proxies intradiários" in markdown
    assert "0.75" in markdown   # TP atual na tabela de parâmetros ou histórico
    assert "1.50" in markdown   # STOP no histórico de TUNEs aplicados
    assert "1.123" in markdown  # IR no histórico de TUNEs aplicados
    assert "Alta" in markdown
    assert "2023-03-15" in markdown
    assert "R$-412.00" in markdown
    assert "```json" in markdown
    assert "```" in markdown


def test_gerar_relatorio_tune_com_dados():
    # Este teste requer um ativo com historico_config
    # Como não temos acesso a dados reais em testes unitários, apenas verificamos se a função não quebra
    try:
        result = gerar_relatorio_tune("VALE3")
        assert isinstance(result, dict)
        assert "ticker" in result
        assert "ciclo" in result
        assert "data" in result
        assert "diagnostico_executivo" in result
        assert "markdown" in result
    except ValueError as e:
        # Se não houver TUNE, espera-se ValueError
        assert "Nenhum TUNE executado" in str(e)


def test_gerar_relatorio_tune_sem_dados():
    # Testa comportamento quando o ativo não existe no filesystem
    # Após migração para get_ativo_raw, ativo inexistente levanta FileNotFoundError
    with pytest.raises(FileNotFoundError):
        gerar_relatorio_tune("TICKER_INEXISTENTE")