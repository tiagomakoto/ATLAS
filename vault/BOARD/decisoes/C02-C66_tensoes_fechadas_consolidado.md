---
uid: C02-C26_C28-C66
title: Tensões fechadas — sessões 2026-03-22 e 2026-03-23
status: closed
closed_at: 2026-03-23
closed_in: [[BOARD/atas/2026-03-23_paper_trading]]
decided_by: Board
system: delta_chaos
---

# Tensões Fechadas — Registro Consolidado

## C2 — Druckenmiller no PRISM
Descartado. Sem fit com a dinâmica do PRISM atual.

## C3 — Lilian Weng como membro votante
Resolvido: consultora eventual, não membro votante.

## C4 — Chan como membro votante
Resolvido: codador permanente, sem voto no board.

## C5 — Soros entre board e PRISM
Resolvido: migrou definitivamente para PRISM.

## C6 — CDS/EMBI+ para PETR4
Descartado como série externa.

## C7 — CL=F para PETR4
Descartado: correlação 0.024, sem sinal.

## C8 — Baltic Dry Index
Descartado: indisponível via yfinance.

## C9 — Dalio como condutor
Resolvido: Howard Marks permanece CCO.

## C10 — UNIVERSO_PADRAO hardcoded
Resolvido: substituído pelos master JSONs por ativo.

## C11 — S6 como camadas S7/S8
Resolvido: S6 é camada única para séries externas.

## C12 — BBDC3 no universo
Removido: histórico insuficiente.

## C13 — Sinal de deterioração no ORBIT
Resolvido: substituído pelo REFLECT como metamodelo dedicado.

## C14 — Sizing A = 3.0 fixo
Resolvido: substituído por 1.0 + alpha dinâmico baseado no score do REFLECT.

## C15 — Estados com nomenclatura conceitual
Resolvido: substituído por letras A–E. Nome completo usado em dashboard, atas e discussões.

## C16 — Dalton como membro
Resolvido: filosofia de Value Area absorvida por Buffett.

## C17 — Kochuba e Karsan
Resolvido: GEX calculado por Chan internamente.

## C18 — McCandless e Rosling
Status: consultores de design futuro — sem função atual.

## C19 — REGIMES_SIZING_PADRAO hardcoded no TAPE
Resolvido: migrado para delta_chaos_config.json seção fire.

## C20 — _fallback_sizing no FIRE
Resolvido: removido — era código morto.

## C21 — TUNE v1.0 para VALE3
Resolvido: substituído por TUNE v1.1 TP=0.90 STOP=2.0.

## C22 — Bugs do GATE v1.0
Resolvido: múltiplos bugs corrigidos na sessão 2026-03-22.

## C23 — Protocolo de retomada após Edge E indefinido
Resolvido: cinco gates sequenciais definidos em A6.

## C24 — Fechamento de posição intraday vs EOD
Resolvido: sempre EOD, próximo pregão após cálculo do ciclo.

## C25 — Métrica função objetivo Optuna
Resolvido: Calmar ratio com fallback para métrica própria baseada em sequências de stops.

## C26 — tape_salvar_ciclo não-atômico
Resolvido: TAPE v1.2 usa tape_salvar_ativo() com os.replace().

## C28 — Alpha do Edge A acoplado ao IR do ORBIT
Resolvido: alpha baseado no score do REFLECT. alpha = clip((reflect_score - threshold_A) × alpha_factor, 0, max_cap). Validado: score=0.892 → mult=1.288.

## C29 — Persistência de dois ciclos consecutivos para Edge A
Resolvido: proposta rejeitada empiricamente. Nenhum ciclo Edge A consecutivo em VALE3/PETR4 — condição inutilizaria o Edge A.

## C30 — Bug contaminação REFLECT entre backtests
Resolvido: reflect_all_cycles_history limpo no início de _executar_backtest no EDGE v1.3.

## C31 — Imports entre módulos internos incompatíveis com Colab
Resolvido: removidos de ORBIT, BOOK, EDGE, FIRE. Funções via escopo global do notebook.

## C32 — regimes_sizing incompleto em BOVA11 e ITUB4
Resolvido: regimes_sizing completo configurado antes do GATE para todos os ativos novos.

## C33 — GATE lendo historico antes do backtest interno
Resolvido: master JSON recarregado após edge.executar() dentro do GATE.

## C34 — DELTA_ALVO conflito de escopo Colab
Resolvido: renomeado para DELTA_ALVO_TUNE no TUNE v1.1.

## C35 — ITUB4 na to-do list
Resolvido: removido. Status EXCLUÍDO por causa estrutural. Rerrodar GATE set/2026 (ver B34).

## C36 — DELTA_ALVO hardcoded no FIRE
Resolvido: migrado para delta_chaos_config.json. anos_validos também migrado.

## C37 — NEUTRO_BULL em BBAS3
Resolvido: ausência de edge no regime, não na estratégia. NEUTRO_BULL setado como null.

## C38 — B24: tape_salvar_ciclo atômico
Resolvido: tempfile + os.replace. Sessão 2026-03-23.

## C39 — S1: BOOK._salvar atômico em paper/real
Resolvido. Sessão 2026-03-23.

## C40 — S2: tape_carregar_ativo backup antes de sobrescrever JSON corrompido
Resolvido. Sessão 2026-03-23.

## C41 — S3: BOOK._carregar backup + audit_log antes de reiniciar vazio
Resolvido. Sessão 2026-03-23.

## C42 — Q7: GATE integrado ao EDGE.executar_eod() via gate_eod() leve
Resolvido. Sessão 2026-03-23.

## C43 — S4: FIRE carregar_config() cache no __init__ e abrir()
Resolvido. Sessão 2026-03-23.

## C44 — S5: FIRE verificar() configs_ativos como parâmetro opcional
Resolvido. Sessão 2026-03-23.

## C45 — Q1: BOOK fechar() aplica slippage_aplicado no P&L
Resolvido. Sessão 2026-03-23.

## C46 — Q2: filtro liquidez volume_financeiro_minimo=10000 provisório
Resolvido provisoriamente. Ver Q2b (aberto).

## C47 — Q3: tape_paper() valida freshness xlsx threshold 16h
Resolvido: cobre download 17h30 até abertura 09h00. Sessão 2026-03-23.

## C48 — Q4: GATE E4 print corrigido + nota limitação linear
Resolvido. Sessão 2026-03-23.

## C49 — Q5: gap risk documentado no GATE E7
Resolvido. Sessão 2026-03-23.

## C50 — Q6: séries externas VALE3 — ADF desnecessário
Resolvido: S6 média +0.32, nunca zero em 284 ciclos. Ridge valida sinal. Sessão 2026-03-23.

## C51 — Q8: timezones fire.py tz_localize(None)
Resolvido em verificar() e abrir(). Sessão 2026-03-23.

## C52 — S6: _melhor_opcao TUNE / _melhor FIRE — comentários de sincronização
Resolvido. Sessão 2026-03-23.

## C53 — S7: GATE E2 print TP/STOP hardcoded corrigido
Resolvido para variáveis reais. Sessão 2026-03-23.

## C54 — S8: TUNE printa célula pronta para aplicar TP/STOP
Resolvido. Sessão 2026-03-23.

## C55 — S9: ORBIT pbar.set_postfix movido para antes do continue
Resolvido. Sessão 2026-03-23.

## C56 — Bug TUNE delta_alvo_tune — variável inexistente
Resolvido: corrigido para parâmetro delta_alvo. Sessão 2026-03-23.

## C57 — Bug GATE anos_validos — _cfg_ativo usado antes de ser definido
Resolvido: bloco inicial reordenado. Sessão 2026-03-23.

## C58 — B25: TUNE v1.1 para PETR4
Resolvido: TP=0.90 STOP=2.0 aprovado. IR válido +2.931. Master JSON atualizado.

## C59 — GATE PETR4 pendente
Resolvido: 8/8 aprovado. Status OPERAR. Robustez confirmada mesmo com TP=0.50 provisório.

## C60 — VOL_FIN_MIN=10000 removido do _melhor no FIRE
Resolvido: substituído por volume > 0. Decisão CEO: liquidez estruturalmente baixa no Brasil.

## C61 — NEUTRO_BULL BOVA11 com BULL_PUT_SPREAD bloqueado
Resolvido: acerto 62.5% abaixo do break-even 66.7%. Edge ausente no regime.

## C62 — B24: tape_salvar_ciclo atômico via tape_salvar_ativo()
Resolvido: os.replace() implementado no TAPE v1.2.

## C63 — gate_eod filtro de GATE completo corrigido
Resolvido: aceita campos resultado, gate_decisao e valor_novo. Compatibilidade retroativa garantida.

## C64 — _montar_bear_call strike validation corrigida
Resolvido: >= substituído por >. Vendida deve ter strike MENOR que comprada em BEAR_CALL_SPREAD.

## C65 — _cache_ok corrigido — FileNotFoundError em arquivo inexistente
Resolvido: os.path.exists verificado antes de os.path.getsize.

## C66 — tape_paper() atualizado para formato opcoes.net.br
Resolvido: header=1, mapeamento de colunas com \xa0, strike e fechamento divididos por 100.
