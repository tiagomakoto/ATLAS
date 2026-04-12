# Decision Log
Registro centralizado de decisões do board.
Cada entrada referencia módulos afetados via WikiLinks.
Status: open = tensão ativa | closed = resolvida e confirmada pelo CEO.

---

## Tensões abertas

| uid | título | gatilho | aberta em |
|-----|---------|---------|-----------|
| [[BOARD/tensoes_abertas/B01_cap_alpha_edge_A\|B1]] | Cap máximo do alpha em Edge A | TUNE sizing Fase 2 | 2026-03-22 |
| [[BOARD/tensoes_abertas/B02_protocolo_retomada_edge_E\|B2]] | Protocolo retomada Edge E — código não implementado | antes de capital real | 2026-03-22 |
| [[BOARD/tensoes_abertas/B03_N_dias_divergencia_alerta\|B3]] | N dias divergência para alerta REFLECT diário | após 1º trimestre paper | 2026-03-22 |
| [[BOARD/tensoes_abertas/B04_thresholds_A_E_optuna\|B4]] | Thresholds A–E via Optuna | 15 ciclos EOD com divergência | 2026-03-22 |
| [[BOARD/tensoes_abertas/B05_condutor_substituto\|B5]] | Condutor substituto de Howard | BOARD_REVIEW_REQUIRED | 2026-03-22 |
| [[BOARD/tensoes_abertas/B06_flag_deterioracao_sistemica\|B6]] | Flag deterioração sistêmica simultânea | BOARD_REVIEW_REQUIRED | 2026-03-22 |
| [[BOARD/tensoes_abertas/B07_protocolo_douglas_deterioracao\|B7]] | Protocolo Douglas — deterioração simultânea | BOARD_REVIEW_REQUIRED | 2026-03-22 |
| [[BOARD/tensoes_abertas/B08_calendar_spread_neutro_lateral\|B8]] | Calendar Spread NEUTRO_LATERAL — não implementado | BOARD_REVIEW_REQUIRED | 2026-03-22 |
| [[BOARD/tensoes_abertas/B09_tail_hedge_estrutural\|B9]] | Tail Hedge estrutural — aprovado, não implementado | BOARD_REVIEW_REQUIRED | 2026-03-22 |
| [[BOARD/tensoes_abertas/B10_gate_eifert_camadas_adicionais\|B10]] | Camadas adicionais gate Eifert | Fase 2 com API de vol | 2026-03-22 |
| [[BOARD/tensoes_abertas/B11_pesos_reflect_optuna\|B11]] | Pesos REFLECT 0.33/0.33/0.33 — calibração Optuna | 24 ciclos com 3 componentes ativos | 2026-03-22 |
| [[BOARD/tensoes_abertas/B14_pilares_pre_paper\|B14]] | Seis pilares pré-paper — capital segregado e protocolo | BOARD_REVIEW_REQUIRED | 2026-03-22 |
| [[BOARD/tensoes_abertas/B15_documentacao_sistema\|B15]] | Documentação técnica e executiva | BOARD_REVIEW_REQUIRED | 2026-03-22 |
| [[BOARD/tensoes_abertas/B17_proximos_ativos\|B17]] | Próximos ativos — expansão do universo | BBAS3: Edge B por 2-3 ciclos | 2026-03-22 |
| [[BOARD/tensoes_abertas/B18_reconciliacao_corretora\|B18]] | Reconciliação diária com corretora | BOARD_REVIEW_REQUIRED | 2026-03-22 |
| [[BOARD/tensoes_abertas/B19_versionamento_modulos\|B19]] | Versionamento de código — delta_chaos_versions.json | BOARD_REVIEW_REQUIRED | 2026-03-22 |
| [[BOARD/tensoes_abertas/B21_anos_validos_dinamico\|B21]] | anos_validos dinâmico no GATE v2.0 | GATE v2.0 | 2026-03-22 |
| [[BOARD/tensoes_abertas/B22_gate_v2_duas_janelas\|B22]] | GATE v2.0 — duas janelas de validação | BOARD_REVIEW_REQUIRED | 2026-03-22 |
| [[BOARD/tensoes_abertas/B23_criterio_parada_tune\|B23]] | Critério de parada do TUNE | TUNE v2.0 | 2026-03-22 |
| [[BOARD/tensoes_abertas/B26_divergencia_gate_tune_vale3\|B26]] | Divergência GATE vs TUNE em VALE3 | monitorar paper / TUNE v2.0 | 2026-03-22 |
| [[BOARD/tensoes_abertas/B27_BBAS3_edge_nao_testado\|B27]] | BBAS3 ALTA e NEUTRO_BEAR — edge não testado | REFLECT Edge B por 2-3 ciclos | 2026-03-22 |
| [[BOARD/tensoes_abertas/B28_bootstrap_ciclos_reflect\|B28]] | Bootstrap ciclos 1–3 REFLECT — exclusão backtest | antes de publicar backtest | 2026-03-23 |
| [[BOARD/tensoes_abertas/B29_condicao_taleb_alpha_edge_A\|B29]] | Condição Taleb — alpha Edge A após 1º trimestre | após 1º trimestre paper | 2026-03-23 |
| [[BOARD/tensoes_abertas/B30_tune_v2_mascara_reflect\|B30]] | TUNE v2.0 — máscara REFLECT e estratégias alternativas | após 1º trimestre paper | 2026-03-23 |
| [[BOARD/tensoes_abertas/B31_calmar_ratio_alavancas\|B31]] | Calmar ratio — alavancas mapeadas | múltiplos gatilhos | 2026-03-23 |
| [[BOARD/tensoes_abertas/B34_ITUB4_monitoramento\|B34]] | ITUB4 — rerrodar GATE set/2026 | setembro 2026 | 2026-03-23 |
| [[BOARD/tensoes_abertas/B35_REFLECT_backtest\|B35]] | REFLECT no backtest — sequência obrigatória pré-capital real | pré-capital real | 2026-03-23 |
| [[BOARD/tensoes_abertas/B36_PETR4_adverso_2025\|B36]] | PETR4 adverso em 2025 — estrutural ou cíclico? | monitorar paper / TUNE v2.0 | 2026-03-23 |
| [[BOARD/tensoes_abertas/B37_BOVA11_baseline_superior\|B37]] | BOVA11 baseline com P&L absoluto superior | TUNE v2.0 após 1º trimestre | 2026-03-23 |
| [[BOARD/tensoes_abertas/B38_BOVA11_NEUTRO_TRANSICAO\|B38]] | BOVA11 NEUTRO_TRANSICAO sem estratégia | definição de estratégia | 2026-03-23 |
| [[BOARD/tensoes_abertas/B39_inconsistencia_liquidez_backtest_paper\|B39]] | Inconsistência filtro liquidez backtest vs paper | após 1º trimestre paper | 2026-03-23 |
| [[BOARD/tensoes_abertas/B40_vol_financeiro_nao_mapeado\|B40]] | Vol. Financeiro não mapeado no tape_paper | revisão após 1º mês paper | 2026-03-23 |
| [[BOARD/tensoes_abertas/B41_delta_alvo_fixo\|B41]] | Delta alvo fixo — calibração Fase 2 | Fase 2 com API de vol | 2026-03-23 |
| [[BOARD/tensoes_abertas/B42_TUNE_v2\|B42]] | TUNE v2.0 — desenvolvimento pendente | após 1º trimestre paper | 2026-03-23 |
| [[BOARD/tensoes_abertas/B43_streamlit_fase2\|B43]] | Streamlit — front end Fase 2 | final 1º trimestre paper | 2026-03-23 |
| [[BOARD/tensoes_abertas/B44_preferencia_mensal_FIRE\|B44]] | Preferência mensal no FIRE | BOARD_REVIEW_REQUIRED | 2026-03-23 |
| [[BOARD/tensoes_abertas/B45_exercicio_antecipado\|B45]] | Exercício antecipado não modelado | BOARD_REVIEW_REQUIRED | 2026-03-23 |
| [[BOARD/tensoes_abertas/Q02b_vol_financeiro_minimo_provisorio\|Q2b]] | volume_financeiro_minimo provisório — calibrar | após 1º mês paper | 2026-03-23 |
| [[BOARD/tensoes_abertas/Q09_separar_data_decisao_execucao\|Q9]] | Separar data_decisao de data_execucao | antes de capital real | 2026-03-23 |
| [[BOARD/tensoes_abertas/Q10_S6_VALE3_congelado\|Q10]] | S6 VALE3 congelado 2024-Q1 | investigação imediata | 2026-03-23 |
| [[BOARD/tensoes_abertas/Q11_TUNE_VALE3_afetado_Q10\|Q11]] | TUNE v1.1 VALE3 afetado por Q10 | resolução de Q10 | 2026-03-23 |
| [[BOARD/tensoes_abertas/B46_advantage_integracao_dados_externos\|B46]] | ADVANTAGE — integração de dados externos ao Delta Chaos | fim do 1º trimestre paper | 2026-04-11 |

---

## Tensões fechadas

| uid | título | resolução resumida | fechada em |
|-----|---------|-------------------|-----------|
| [[BOARD/decisoes/C01_iron_condor_indeferido\|C1]] | Iron Condor indeferido permanentemente | liquidez insuficiente B3 | 2026-03-22 |
| [[BOARD/decisoes/C02-C66_tensoes_fechadas_consolidado\|C2–C66]] | Tensões fechadas sessões 2026-03-22 e 2026-03-23 | ver arquivo consolidado | 2026-03-23 |
