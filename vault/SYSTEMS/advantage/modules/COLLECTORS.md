---
uid: mod-adv-002
version: 1.0.6
status: validated
owner: Chan

function: Cinco coletores de dados externos — preco_volume, macro_brasil, macro_global, alternativo, noticias. Cada coletor expoe exatamente uma funcao publica coletar() que persiste no SQLite e retorna numero de registros inseridos.
file: advantage/src/data_layer/collectors/
role: Ingestao de dados externos — unica camada que conhece APIs e fontes externas

input:
  - tickers: list[str] | None — lista de ativos (quando aplicavel)

output:
  - int — numero de registros inseridos na execucao

depends_on:
  - [[SYSTEMS/advantage/modules/DATA_LAYER]]

depends_on_condition:

used_by:
  - [[SYSTEMS/advantage/modules/SCHEDULER]]

intent:
  - Nunca lanca excecao para o caller — captura internamente e loga.
  - Append-only: INSERT OR IGNORE — segundo coletar() no mesmo dia nao duplica registros.

constraints:
  - Interface obrigatoria: def coletar(tickers=None) -> int
  - Nunca faz UPDATE em registros existentes
  - Captura excecoes internamente — loga e retorna 0 em caso de falha
  - flag_qualidade=0 para linhas suspeitas — nao descarta dado
  - retry com backoff linear — 3 tentativas, 5s de espera

notes:
  - 2026-04-10: código modificado — utils.py
  - 2026-04-10: código modificado — macro_global.py
  - 2026-04-10: código modificado — utils.py
  - 2026-04-10: código modificado — macro_global.py
  - 2026-04-10: código modificado — utils.py
  - 2026-04-10: código modificado — macro_global.py >
  PRECO_VOLUME (preco_volume.py):
  - Fonte primaria: yfinance. Fallback: brapi.dev por ticker
  - Universo padrao: Ibovespa (~80 ativos)
  - Frequencia: diaria apos fechamento B3 (18h30)
  - Tabelas: preco_volume, fundamentals, indicadores_compartilhados, retornos_historicos

  MACRO_BRASIL (macro_brasil.py):
  - BCB/SGS — series 432 (Selic meta), 11 (Selic efetiva), 433 (IPCA mensal), 13522 (IPCA 12m), 189 (IGP-M), 1 (USD/BRL)
  - Focus BCB — ExpectativasMercadoAnuais: Selic, IPCA, Cambio, PIB
  - IBGE SIDRA — PMC, PMS, PIM, PNAD
  - Ministerio Fazenda — arrecadacao IRPJ, CSLL, IPI, IOF
  - Tabelas: macro_brasil, focus_bcb_historico, dados_setoriais_br, ciclo_local_brasil, fluxo_investidores

  MACRO_GLOBAL (macro_global.py — stub atual):
  - FRED API: fed funds (DFF), yield T10
  - yfinance: DXY, S&P500 (^GSPC), WTI (CL=F), Brent (BZ=F), soja (ZS=F), milho (ZC=F)
  - BDI: scraping ou API publica
  - Tabelas: macro_global, ciclo_global, commodities_setoriais

  ALTERNATIVO (alternativo.py):
  - Google Trends: pytrends — termos configuaveis por ativo
  - ANEEL: API publica consumo industrial (stub se indisponivel)
  - ABPO: stub — retorna 0 e loga aviso. Pipeline PDF e pendencia futura.
  - IIE-FGV: scraping portal FGV
  - Polymarket: API publica gratuita — probabilidades de eventos
  - Tabelas: google_trends, aneel_energia, abpo_papelao, iie_fgv, polymarket_eventos

  NOTICIAS (noticias.py):
  - RSS: feedparser — InfoMoney, Valor Economico, Exame Invest, Bloomberg Linea, Reuters Brasil, Agencia Brasil
  - Temperatura: Gemini 2.5 Flash — classifica manchetes em score -1.0 a +1.0
  - Frequencia: a cada 30 minutos
  - formula: temperatura = polaridade_media x intensidade_media x log(vol_6h / vol_tipico_6h)
  - temperatura_zscore = (temperatura - media_historica) / desvpad_historico
  - Tabela: temperatura_noticias, documentos_qualitativos
---
