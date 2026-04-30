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
| [[BOARD/tensoes_abertas/B11_pesos_reflect_optuna\|B11]] | Pesos REFLECT 0.33/0.33/0.33 — Optuna stack compartilhado TUNE+REFLECT | 24 ciclos com 3 componentes ativos | 2026-03-22 |
| [[BOARD/tensoes_abertas/B14_pilares_pre_paper\|B14]] | Seis pilares pré-paper — capital segregado e protocolo | BOARD_REVIEW_REQUIRED | 2026-03-22 |
| [[BOARD/tensoes_abertas/B15_documentacao_sistema\|B15]] | Documentação técnica e executiva | BOARD_REVIEW_REQUIRED | 2026-03-22 |
| [[BOARD/tensoes_abertas/B17_proximos_ativos\|B17]] | Próximos ativos — expansão do universo | BBAS3: Edge B por 2-3 ciclos | 2026-03-22 |
| [[BOARD/tensoes_abertas/B18_reconciliacao_corretora\|B18]] | Reconciliação diária com corretora | BOARD_REVIEW_REQUIRED | 2026-03-22 |
| [[BOARD/tensoes_abertas/B19_versionamento_modulos\|B19]] | Versionamento de código — delta_chaos_versions.json | BOARD_REVIEW_REQUIRED | 2026-03-22 |
| [[BOARD/tensoes_abertas/B21_anos_validos_dinamico\|B21]] | anos_validos dinâmico no GATE v2.0 | GATE v2.0 | 2026-03-22 |
| [[BOARD/tensoes_abertas/B22_gate_v2_duas_janelas\|B22]] | GATE v2.0 — duas janelas de validação | BOARD_REVIEW_REQUIRED | 2026-03-22 |
| [[BOARD/tensoes_abertas/B27_BBAS3_edge_nao_testado\|B27]] | BBAS3 ALTA e NEUTRO_BEAR — edge não testado | REFLECT Edge B por 2-3 ciclos | 2026-03-22 |
| [[BOARD/tensoes_abertas/B28_bootstrap_ciclos_reflect\|B28]] | Bootstrap ciclos 1–3 REFLECT — exclusão backtest | antes de publicar backtest | 2026-03-23 |
| [[BOARD/tensoes_abertas/B29_condicao_taleb_alpha_edge_A\|B29]] | Condição Taleb — alpha Edge A após 1º trimestre | após 1º trimestre paper | 2026-03-23 |
| [[BOARD/tensoes_abertas/B31_calmar_ratio_alavancas\|B31]] | Calmar ratio — alavancas mapeadas | múltiplos gatilhos | 2026-03-23 |
| [[BOARD/tensoes_abertas/B34_ITUB4_monitoramento\|B34]] | ITUB4 — rerrodar GATE set/2026 | setembro 2026 | 2026-03-23 |
| [[BOARD/tensoes_abertas/B35_REFLECT_backtest\|B35]] | REFLECT no backtest — sequência obrigatória pré-capital real | pré-capital real | 2026-03-23 |
| [[BOARD/tensoes_abertas/B36_PETR4_adverso_2025\|B36]] | PETR4 adverso em 2025 — estrutural ou cíclico? | monitorar paper / TUNE v2.0 | 2026-03-23 |
| [[BOARD/tensoes_abertas/B37_BOVA11_baseline_superior\|B37]] | BOVA11 baseline com P&L absoluto superior | TUNE v2.0 após 1º trimestre | 2026-03-23 |
| [[BOARD/tensoes_abertas/B38_BOVA11_NEUTRO_TRANSICAO\|B38]] | BOVA11 NEUTRO_TRANSICAO sem estratégia | definição de estratégia | 2026-03-23 |
| [[BOARD/tensoes_abertas/B39_inconsistencia_liquidez_backtest_paper\|B39]] | Inconsistência filtro liquidez backtest vs paper | após 1º trimestre paper | 2026-03-23 |
| [[BOARD/tensoes_abertas/B40_vol_financeiro_nao_mapeado\|B40]] | Vol. Financeiro não mapeado no tape_paper | revisão após 1º mês paper | 2026-03-23 |
| [[BOARD/tensoes_abertas/B41_delta_alvo_fixo\|B41]] | Delta alvo fixo — calibração Fase 2 | Fase 2 com API de vol | 2026-03-23 |
| [[BOARD/tensoes_abertas/B43_streamlit_fase2\|B43]] | Streamlit — front end Fase 2 | final 1º trimestre paper | 2026-03-23 |
| [[BOARD/tensoes_abertas/B44_preferencia_mensal_FIRE\|B44]] | Preferência mensal no FIRE | BOARD_REVIEW_REQUIRED | 2026-03-23 |
| [[BOARD/tensoes_abertas/B45_exercicio_antecipado\|B45]] | Exercício antecipado não modelado | BOARD_REVIEW_REQUIRED | 2026-03-23 |
| [[BOARD/tensoes_abertas/Q02b_vol_financeiro_minimo_provisorio\|Q2b]] | volume_financeiro_minimo provisório — calibrar | após 1º mês paper | 2026-03-23 |
| [[BOARD/tensoes_abertas/Q09_separar_data_decisao_execucao\|Q9]] | Separar data_decisao de data_execucao | antes de capital real | 2026-03-23 |
| [[BOARD/tensoes_abertas/B46_advantage_integracao_dados_externos\|B46]] | ADVANTAGE — integração de dados externos ao Delta Chaos | fim do 1º trimestre paper | 2026-04-11 |
| [[BOARD/tensoes_abertas/B49_slippage_revisao_paper\|B49]] | Slippage 10% — revisão após dados reais de paper trading | fim 1º trimestre paper | 2026-04-12 |
| [[BOARD/tensoes_abertas/B50_drawer_onboarding_estado_persistido\|B50]] | Drawer onboarding — estado persistido no master JSON + watchdog | implementação PLAN | 2026-04-13 |
| [[BOARD/tensoes_abertas/B51_nav_relatorio_tune_exportavel\|B51]] | Nav "Relatório" na aba Ativo — relatório de TUNE exportável em .md | implementação PLAN | 2026-04-13 |
| [[BOARD/tensoes_abertas/B52_tp_stop_ativos_table\|B52]] | TP/STOP visível na AtivosTable (Visão Geral) | implementação PLAN | 2026-04-13 |


| [[BOARD/tensoes_abertas/B61_tune_v31_tp_stop_por_regime\|B61]] | TUNE v3.1 — TP/STOP por regime + migração FIRE/GATE/BOOK | TUNE v3.0 validado em paper trading | 2026-04-25 |
| [[BOARD/tensoes_abertas/B62_tune_grid_stop_range_revisao\|B62]] | Grid Etapa A — range Stop 1.5–2.5 amplo demais para vendedor de vol | 1 trimestre paper trading TUNE v3.1 | 2026-04-29 |
| [[BOARD/tensoes_abertas/B63_regimes_renomeacao_lateral\|B63]] | Renomeação NEUTRO_* → LATERAL_* + colapso MORTO + elimina TRANSICAO | CEO confirmado — aguarda SPEC | 2026-04-29 |
| [[BOARD/tensoes_abertas/B64_petr4_historico_duplicado_orbit\|B64]] | PETR4 historico[] duplicado 26x — origem bug orbit.py | imediato | 2026-04-29 |
| [[BOARD/tensoes_abertas/B65_timezone_utc_vs_gmt3_relatorios\|B65]] | Timezone UTC vs GMT-3 no gerador de relatórios | imediato | 2026-04-30 |

---

## Sessões registradas

| data | tema | tipo |
|------|------|------|
| [[BOARD/atas/2026-03-23_paper_trading\|2026-03-23]] | paper trading — início | board |
| [[BOARD/atas/2026-04-12_vault_scm_manutencao\|2026-04-12]] | vault SCM — manutenção e correções | off-ata |
| [[BOARD/atas/2026-04-12_tune_v2_escopo\|2026-04-12]] | TUNE v2.0 — escopo e gestão aba | board |
| [[BOARD/atas/2026-04-13_atlas_onboarding_drawer_relatorio_tune\|2026-04-13]] | ATLAS — drawer onboarding + relatório TUNE | board |
| [[BOARD/atas/2026-04-13_regime_padronizacao\|2026-04-13]] | regime_estrategia → regime — padronização e migração | off-ata |
| [[BOARD/atas/2026-04-14_atlas_websocket_onboarding_ux\|2026-04-14]] | ATLAS — WebSocket pipeline + OnboardingDrawer UX | board |
| [[BOARD/atas/2026-04-14_dc_runner_edge_fusao\|2026-04-14]] | dc_runner — eliminação de subprocess, import direto de edge.py | board |
| [[BOARD/atas/2026-04-24_reflect_estados_sizing\|2026-04-24]] | REFLECT — redesign estados A/B/C/D/X + sizing canônico por estado | board |
| [[BOARD/atas/2026-04-25_prio3_bloqueio_relatorio\|2026-04-25]] | PRIO3 bloqueio GATE + auditoria formato relatório | board |
| [[BOARD/atas/2026-04-25_tune_v3_eleicao_competitiva\|2026-04-25]] | TUNE v3.0 — eleição competitiva de estratégia por regime | board |
| [[BOARD/atas/2026-04-25_hardreset_ativos\|2026-04-25]] | Hard reset completo dos ativos + fechamento B60 | off-ata |
| [[BOARD/atas/2026-04-29_tune_v31_arquitetura\|2026-04-29]] | TUNE v3.1 — arquitetura duas etapas + gate anomalia | board |
| [[BOARD/atas/2026-04-29_regimes_nomenclatura_lateral\|2026-04-29]] | Regimes: NEUTRO_* → LATERAL_* + colapso + bug PETR4 | board |
| [[BOARD/atas/2026-04-29_tune_v31_implementacao_scan\|2026-04-29]] | TUNE v3.1 implementação + SCAN aprovado + SPEC frontend | board |
| [[BOARD/atas/2026-04-29_scan_frontend_tune_v31\|2026-04-29]] | SCAN frontend TUNE v3.1 — 4 adendas aprovadas + ressalva router | board |
| [[BOARD/atas/2026-04-29_auditoria_scan_b53_b54_b55_b56_b57\|2026-04-29]] | Auditoria SCAN estado real B53/B54/B55/B56/B57 | off-ata |
| [[BOARD/atas/2026-04-29_fechamento_b53_b54_b55_b56_b57\|2026-04-29]] | Fechamento B53/B54/B55/B56/B57 — SCAN aprovado | off-ata |
| [[BOARD/atas/2026-04-30_rastreabilidade_relatorio_calibracao\|2026-04-30]] | Rastreabilidade do relatório de calibração — SCAN + PE-010 + B65 | board |
---

## Tensões fechadas

| uid | título | resolução resumida | fechada em |
|-----|---------|-------------------|-----------|
| [[BOARD/decisoes/C01_iron_condor_indeferido\|C1]] | Iron Condor indeferido permanentemente | liquidez insuficiente B3 | 2026-03-22 |
| [[BOARD/decisoes/C02-C66_tensoes_fechadas_consolidado\|C2–C66]] | Tensões fechadas sessões 2026-03-22 e 2026-03-23 | ver arquivo consolidado | 2026-03-23 |
| [[BOARD/tensoes_abertas/B48_entrada_close_d0_vs_open_d1\|B48]] | Entrada close d0 vs open d1 — campo premio_executado em Leg | fire.py + book.py corrigidos | 2026-04-12 |
| [[BOARD/tensoes_abertas/B23_criterio_parada_tune\|B23]] | Critério de parada do TUNE — Optuna 200 trials TPE | steps 0.05/0.25/1, patience=50 | 2026-04-13 |
| [[BOARD/decisoes/B60_neutro_consolidacao\|B60]] | NEUTRO legado — consolidação com subregimes NEUTRO_* | 0 ocorrências em todos os ativos — sem ação necessária | 2026-04-25 |
| [[BOARD/decisoes/B26_divergencia_gate_tune_vale3\|B26]] | Divergência GATE vs TUNE — TP/STOP em VALE3 | obsolescência — hardreset descartou TUNE v1.1; divergência E5 é questão distinta | 2026-04-25 |
| [[BOARD/decisoes/Q10_S6_VALE3_congelado\|Q10]] | regime_estrategia ausente em 518 ciclos históricos | migração retroativa + fix indentação orbit.py | 2026-04-12 |
| [[BOARD/decisoes/Q11_TUNE_VALE3_afetado_Q10\|Q11]] | TUNE v1.1 VALE3 potencialmente afetado por Q10 | hipótese não materializada — TUNE lê regime, não regime_estrategia | 2026-04-12 |
| [[BOARD/tensoes_abertas/B47_janela_teste_tune\|B47]] | Janela de teste TUNE — janela como hiperparâmetro Optuna | implementado em TUNE v2.0 Fase 2 | 2026-04-13 |
| [[BOARD/tensoes_abertas/B30_tune_v2_mascara_reflect\|B30]] | TUNE v2.0 máscara REFLECT + diagnóstico estratégia | Fases 3 e 4 implementadas e aprovadas por SCAN | 2026-04-13 |
| [[BOARD/tensoes_abertas/B42_TUNE_v2\|B42]] | TUNE v2.0 — 5 fases implementadas | Fases 1a/2/3/4/5 aprovadas por SCAN; Fase 1b aguarda B49 | 2026-04-13 |
| [[BOARD/decisoes/Q12_regime_estrategia_padronizado_regime\|Q12]] | regime_estrategia renomeado para regime — padronização global | orbit.py corrigido + 2119 ciclos migrados | 2026-04-13 |
| [[BOARD/tensoes_abertas/B59_tune_estrategia_selecao_competitiva\|B59]] | TUNE v3.0→3.1 — backend + frontend completos, SCAN aprovado | tune.py v3.1 + frontend adendas #1–#4 + fix body?.status_calibracao. Merge sem restrições. | 2026-04-29 |
| [[BOARD/decisoes/B53_onboarding_drawer_ux_melhorias\|B53]] | CalibaçãoDrawer v3.0 — reformulação estrutural completa | Renomeação + steps + GATE granular + FIRE + badge N<5 + import corrigido. SCAN aprovado. | 2026-04-29 |
| [[BOARD/decisoes/B54_dc_runner_edge_import_direto\|B54]] | dc_runner — subprocess eliminado, import direto implementado | 19 emit_dc_event removidos de edge.py. dc_runner único emissor. Suite 76/76. SCAN aprovado. | 2026-04-29 |
| [[BOARD/decisoes/B55_reflect_estados_ABCDX_redesign\|B55]] | REFLECT estados E→T implementado (etapa 1) | reflect_cycle_calcular e sizing_calcular usam T. TODO etapa 2 em B04. SCAN aprovado. | 2026-04-29 |
| [[BOARD/decisoes/B56_reflect_sizing_por_estado\|B56]] | REFLECT sizing por estado + regimes_sizing removido | Lookup A/B/C/D/T. TODOs no código. regimes_sizing zerado em tape.py. SCAN aprovado. | 2026-04-29 |
| [[BOARD/decisoes/B57_relatorio_calibracao_lacunas\|B57]] | Relatório calibração — 6 campos implementados | 5 seções novas em formatar_relatorio_markdown. Threshold campo 5 como PE provisório. SCAN aprovado. | 2026-04-29 |
