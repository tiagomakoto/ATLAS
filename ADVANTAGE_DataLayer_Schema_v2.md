# ADVANTAGE — DATA LAYER SCHEMA COMPLETO (VERSÃO 2.0)

## PRINCÍPIOS DE ARQUITETURA

O ADVANTAGE opera com quatro camadas funcionais.

```
DATA LAYER — fonte única de verdade
      ↓ dados brutos para todas as camadas
CAMADA 1 — CAUSA — processamento e scoring
      ↓ score + dados brutos
CAMADA 2 — EXPRESSÃO — confirmação de fluxo
      ↓ confirmação de expressão
CAMADA 3 — EXTRAÇÃO — decisão de sizing
```

**Regras invioláveis:**
- Nenhuma camada acessa fonte externa diretamente
- Todo dado bruto passa pelo Data Layer
- Indicadores básicos compartilhados calculados pelo Data Layer com parâmetros fixos versionados
- Indicadores específicos de cada camada calculados pela própria camada sobre dados brutos
- Score de CAUSA passado intacto à Camada 3 sem reinterpretação da Camada 2
- Tabelas com slot futuro existem desde o início — vazias mas estruturadas

---

## TABELAS CORE DE MERCADO

### TABELA 1: PRECO_VOLUME
| Campo | Tipo | Descrição |
|---|---|---|
| ticker | TEXT | Código do ativo na B3 |
| data | DATE | Data do pregão |
| abertura | FLOAT | Preço de abertura |
| maxima | FLOAT | Preço máximo |
| minima | FLOAT | Preço mínimo |
| fechamento | FLOAT | Preço de fechamento |
| fechamento_adj | FLOAT | Fechamento ajustado por dividendos e splits |
| volume | INTEGER | Volume financeiro |
| fonte | TEXT | Fonte do dado |
| data_coleta | TIMESTAMP | Momento da coleta |
| flag_qualidade | BOOLEAN | True se dado validado |

**Fonte:** yfinance + brapi.dev (complementar para fundamentals B3)
**Frequência:** Diária — Universo inicial: Ibovespa

---

### TABELA 2: FUNDAMENTALS
| Campo | Tipo | Descrição |
|---|---|---|
| ticker | TEXT | Código do ativo |
| data_referencia | DATE | Data de referência |
| periodo | TEXT | Identificador do período (ex: 2024Q3) |
| receita_liquida | FLOAT | Receita líquida |
| lucro_liquido | FLOAT | Lucro líquido |
| margem_liquida | FLOAT | Margem líquida (%) |
| roe | FLOAT | Retorno sobre patrimônio (%) |
| divida_liquida | FLOAT | Dívida líquida |
| ebitda | FLOAT | EBITDA |
| earnings_surprise | FLOAT | Desvio resultado real vs estimativa (%) |
| fonte | TEXT | Fonte |
| data_coleta | TIMESTAMP | Momento da coleta |

**Fonte:** yfinance + brapi.dev
**Frequência:** Trimestral

---

### TABELA 3: INDICADORES_COMPARTILHADOS
| Campo | Tipo | Descrição |
|---|---|---|
| ticker | TEXT | Código do ativo |
| data | DATE | Data de referência |
| atr_10 | FLOAT | ATR 10 dias |
| atr_60 | FLOAT | ATR 60 dias |
| mm_20 | FLOAT | Média móvel simples 20 dias |
| mm_50 | FLOAT | Média móvel simples 50 dias |
| mm_200 | FLOAT | Média móvel simples 200 dias |
| mme_9 | FLOAT | Média móvel exponencial 9 dias |
| mme_21 | FLOAT | Média móvel exponencial 21 dias |
| vol_media_20 | FLOAT | Volume médio 20 dias |
| vol_media_60 | FLOAT | Volume médio 60 dias |
| maxima_52s | FLOAT | Máxima 52 semanas — dinâmica |
| minima_52s | FLOAT | Mínima 52 semanas — dinâmica |
| maxima_3a | FLOAT | Máxima 3 anos — dinâmica |
| minima_3a | FLOAT | Mínima 3 anos — dinâmica |
| parametros_ver | TEXT | Versão dos parâmetros |

**Calculado por:** Data Layer sobre Tabela 1
**Frequência:** Diária

---

### TABELA 9: PORTFOLIO_ESTADO
| Campo | Tipo | Descrição |
|---|---|---|
| id_posicao | INTEGER | Identificador único |
| ticker | TEXT | Código do ativo |
| data_entrada | DATE | Data de abertura |
| preco_entrada | FLOAT | Preço de entrada |
| sizing_inicial | FLOAT | Sizing na entrada (% portfólio) |
| sizing_atual | FLOAT | Sizing atual após ajustes |
| stop_atual | FLOAT | Stop corrente |
| target_atual | FLOAT | Target corrente |
| score_causa_entrada | FLOAT | Score de CAUSA na entrada |
| classificacao_entrada | TEXT | risco_calculavel / incerteza_genuina |
| estilo | TEXT | swing / trend / hold |
| causa_alternativa_compartilhada | TEXT | Dados alternativos driver da CAUSA — para alerta de concentração oculta de portfólio (Dalio) |
| status | TEXT | aberta / fechada |
| data_saida | DATE | null se aberta |
| preco_saida | FLOAT | null se aberta |
| resultado_pct | FLOAT | null se aberta |
| motivo_saida | TEXT | stop / target / deterioracao_causa / deterioracao_expressao / temperatura_noticias / polymarket_evento / manual |

---

### TABELA 10: RETORNOS_HISTORICOS
| Campo | Tipo | Descrição |
|---|---|---|
| ticker | TEXT | Código do ativo |
| data | DATE | Data |
| retorno_diario | FLOAT | Retorno simples (%) |
| retorno_log | FLOAT | Retorno logarítmico |

---

### TABELA 11: TAXA_CONVERSAO
| Campo | Tipo | Descrição |
|---|---|---|
| ticker | TEXT | Código do ativo |
| data_avaliacao | DATE | Data |
| total_sinais_causa | INTEGER | Total de sinais gerados |
| confirmados_expressao | INTEGER | Confirmados pela Camada 2 |
| nao_confirmados | INTEGER | Não confirmados |
| taxa_conversao | FLOAT | null até N mínimo |
| n_minimo_valido | INTEGER | N mínimo para validade |
| status | TEXT | insuficiente / valido |

---

### TABELA 12: INTRADAY_SLOT
| Campo | Tipo | Descrição |
|---|---|---|
| ticker | TEXT | Código do ativo |
| timestamp | TIMESTAMP | Timestamp da operação |
| preco | FLOAT | Preço |
| volume | INTEGER | Volume |
| lado | TEXT | compra / venda |
| tipo_agente | TEXT | institucional / varejo |
| fonte_api | TEXT | Nome da API |
| status | TEXT | vazio_fase_atual / ativo |

---

## TABELAS DE CICLO MACRO

### TABELA 4: CICLO_GLOBAL
| Campo | Tipo | Descrição |
|---|---|---|
| data | DATE | Data |
| juros_real_eua | FLOAT | TIPS 10Y |
| vix | FLOAT | Volatilidade implícita S&P500 |
| spread_hy_eua | FLOAT | Spread crédito high yield |
| bdi | FLOAT | Baltic Dry Index |
| cobre_lme | FLOAT | Cotação cobre LME (USD/ton) |
| ouro_comex | FLOAT | Cotação ouro COMEX (USD/oz) |
| petroleo_brent | FLOAT | Cotação Brent ICE (USD/barril) |
| bitcoin_usd | FLOAT | Cotação BTC/USD — experimental |
| fonte | TEXT | Fonte dos dados |
| data_coleta | TIMESTAMP | Momento da coleta |

**Fonte:** Yahoo Finance, FRED API
**Frequência:** Diária
**Nota BDI:** Validado academicamente como preditor de retornos de ações com poder preditivo in-sample e out-of-sample documentado.
**Nota Bitcoin:** Experimental — peso mínimo inicial. Removido se correlação não persiste out-of-sample em 6 meses.

---

### TABELA 5: CICLO_LOCAL_BRASIL
| Campo | Tipo | Descrição |
|---|---|---|
| data | DATE | Data |
| selic_meta | FLOAT | Taxa Selic meta (% a.a.) |
| selic_real | FLOAT | Selic real deflacionada pelo IPCA |
| ipca_12m | FLOAT | IPCA acumulado 12 meses |
| usdbrl | FLOAT | Câmbio dólar/real |
| earnings_yield_ibov | FLOAT | Earnings yield do Ibovespa |
| spread_selic_ey | FLOAT | Spread Selic real vs earnings yield |
| fluxo_estrang_acum | FLOAT | Fluxo estrangeiro líquido acumulado no mês |
| ibc_br | FLOAT | IBC-Br — proxy mensal de PIB |
| iie_fgv | FLOAT | Índice de Incerteza Econômica FGV |
| capacidade_utilizada | FLOAT | Utilização da capacidade industrial FGV/CNI |
| fonte | TEXT | Fonte |
| data_coleta | TIMESTAMP | Momento da coleta |

**Fonte:** BCB API SGS, IBGE SIDRA, FGV/IBRE
**Frequência:** Diária (Selic, câmbio) / Mensal (demais)
**Nota IBC-Br:** Validado como variável com impacto estatisticamente significativo no Ibovespa em modelos VAR.
**Nota IIE-FGV:** Três componentes — mídia, dispersão de expectativas BCB, volatilidade Ibovespa. Trigger de Barbell quando alto.

---

### TABELA 6: FLUXO_INVESTIDORES
| Campo | Tipo | Descrição |
|---|---|---|
| data | DATE | Data |
| fluxo_estrangeiro | FLOAT | Fluxo líquido estrangeiro (R$ mi) |
| fluxo_local_inst | FLOAT | Fluxo líquido institucional local |
| fluxo_pf | FLOAT | Fluxo líquido pessoa física |
| saldo_liquido | FLOAT | Saldo líquido total |
| tesouro_direto_liquido | FLOAT | Aplicações menos resgates Tesouro Direto |
| fonte | TEXT | B3 IR + Tesouro Nacional |
| data_coleta | TIMESTAMP | Momento da coleta |

**Nota Tesouro Direto:** Proxy de apetite por risco do investidor individual brasileiro. Migração de TD para renda variável detectável antes de aparecer nos dados B3 IR.

---

### TABELA 13: FOCUS_BCB
Expectativas de mercado coletadas semanalmente pelo BCB.

| Campo | Tipo | Descrição |
|---|---|---|
| data | DATE | Data da publicação |
| pib_mediana | FLOAT | Mediana expectativa PIB |
| pib_desvpad | FLOAT | Dispersão expectativa PIB |
| ipca_mediana | FLOAT | Mediana expectativa IPCA |
| ipca_desvpad | FLOAT | Dispersão expectativa IPCA |
| selic_mediana | FLOAT | Mediana expectativa Selic fim ano |
| selic_desvpad | FLOAT | Dispersão expectativa Selic |
| cambio_mediana | FLOAT | Mediana expectativa câmbio |
| cambio_desvpad | FLOAT | Dispersão expectativa câmbio |
| dispersao_agregada | FLOAT | Média das dispersões — trigger de Barbell |
| fonte | TEXT | BCB Focus API |
| data_coleta | TIMESTAMP | Momento da coleta |

**Frequência:** Semanal
**Campo crítico:** dispersao_agregada — alta dispersão = incerteza genuína = Barbell obrigatório na Camada 3.

---

## TABELAS DE DADOS SETORIAIS BRASILEIROS

### TABELA 14: DADOS_SETORIAIS_BR
Dados de atividade setorial de fontes governamentais e associações.

| Campo | Tipo | Descrição |
|---|---|---|
| data_referencia | DATE | Mês de referência |
| indicador | TEXT | Nome do indicador |
| valor | FLOAT | Valor do indicador |
| variacao_mensal | FLOAT | Variação vs mês anterior (%) |
| variacao_anual | FLOAT | Variação vs mesmo mês ano anterior (%) |
| setor_primario | TEXT | Setor mais afetado em B3 |
| fonte | TEXT | Fonte do dado |
| defasagem_dias | INTEGER | Dias típicos entre referência e publicação |
| data_publicacao | DATE | Data efetiva de publicação |
| data_coleta | TIMESTAMP | Momento da coleta |

**Indicadores mapeados por fonte:**

```
IBGE SIDRA:
- PMC: Pesquisa Mensal de Comércio (varejo)
- PMS: Pesquisa Mensal de Serviços
- PIM: Produção Industrial Mensal
- PNAD: Desemprego trimestral

Ministério da Fazenda:
- Arrecadação IRPJ (proxy lucro corporativo)
- Arrecadação CSLL (proxy lucro corporativo)
- Arrecadação IPI (proxy produção industrial)
- Arrecadação IOF (proxy operações financeiras)
- Resultado primário governo federal

MDIC:
- Balança comercial total
- Exportações por produto
- Importações por produto

ANP:
- Produção petróleo e gás
- Vendas combustíveis por estado

ANEEL:
- Consumo energia elétrica industrial
- Consumo energia elétrica comercial

ANFAVEA:
- Produção de veículos
- Licenciamentos de veículos

ABECIP:
- Volume crédito imobiliário
- Número de financiamentos

ABPO:
- Produção papelão ondulado
- Vendas papelão ondulado
```

**Nota ABPO:** Validado por Greenspan e Fed de St. Louis como proxy de atividade industrial universal. Alpha elevado por baixa cobertura de mercado. Coleta via scraping de PDF — sem API estruturada.

**Nota ANEEL consumo industrial:** Um dos melhores proxies de atividade econômica real disponíveis. Consumo industrial de energia é contemporâneo à atividade — sem defasagem significativa.

---

### TABELA 15: COMMODITIES_SETORIAIS
Commodities com impacto direto em setores específicos de B3.

| Campo | Tipo | Descrição |
|---|---|---|
| data | DATE | Data |
| minerio_ferro_usd | FLOAT | Minério de ferro CME/SGX (USD/ton) |
| niquel_lme | FLOAT | Níquel LME (USD/ton) |
| aluminio_lme | FLOAT | Alumínio LME (USD/ton) |
| litio_spot | FLOAT | Lítio spot índice de referência |
| celulose_foex | FLOAT | Celulose FOEX (USD/ton) |
| milho_cbot | FLOAT | Milho CBOT (USD/bushel) |
| soja_cbot | FLOAT | Soja CBOT (USD/bushel) |
| boi_gordo_b3 | FLOAT | Boi gordo futuro B3 (R$/arroba) |
| acucar_nybot | FLOAT | Açúcar NYBOT (USD/lb) |
| cafe_nybot | FLOAT | Café NYBOT (USD/lb) |
| fonte | TEXT | Fonte |
| data_coleta | TIMESTAMP | Momento da coleta |

**Fonte:** Yahoo Finance, CME Group, FOEX, B3
**Frequência:** Diária

**Mapeamento setor-commodity:**
```
Minerio ferro → Vale, CSN, Usiminas
Celulose → Suzano, Klabin
Milho/Soja → BRF, JBS, Marfrig, usinas de etanol
Boi gordo → JBS, Marfrig, Minerva
Açúcar/Café → São Martinho, Raízen
Níquel/Lítio → Vale (metais básicos)
Alumínio → CBA, custos industriais amplos
```

---

## TABELAS DE DADOS ALTERNATIVOS DIGITAIS

### TABELA 16: GOOGLE_TRENDS
| Campo | Tipo | Descrição |
|---|---|---|
| data | DATE | Data |
| termo | TEXT | Termo buscado |
| ticker_relacionado | TEXT | Ativo relacionado (se aplicável) |
| setor_relacionado | TEXT | Setor relacionado (se aplicável) |
| interesse_relativo | FLOAT | Score 0-100 do Google Trends |
| variacao_vs_media | FLOAT | Desvios padrão vs média histórica |
| tipo | TEXT | empresa / setor / macro / produto |
| fonte | TEXT | Google Trends API |
| data_coleta | TIMESTAMP | Momento da coleta |

**Frequência:** Diária
**Uso primário:** Camada 1 — atenção de varejo antecede fluxo de varejo. Validado academicamente como preditor de retornos anormais.
**Uso secundário Camada 2:** Spike anormal de buscas = alerta de saída — varejo entrando = potencial exaustão de movimento.

---

### TABELA 17: TEMPERATURA_NOTICIAS
Score de temperatura de notícias calculado pelo Gemini 2.5 sobre RSS de portais financeiros.

| Campo | Tipo | Descrição |
|---|---|---|
| timestamp | TIMESTAMP | Momento do cálculo |
| escopo | TEXT | ticker / setor / macro |
| referencia | TEXT | Ticker, nome do setor ou "macro_brasil" |
| polaridade | FLOAT | -1 (muito negativo) a +1 (muito positivo) |
| intensidade | FLOAT | 1 (baixa) a 5 (crítica) |
| urgencia | TEXT | rotineiro / relevante / critico |
| volume_noticias | INTEGER | Número de notícias nas últimas 6h |
| volume_tipico | FLOAT | Volume médio histórico em 6h |
| temperatura | FLOAT | polaridade × intensidade × log(vol/vol_tipico) |
| temperatura_zscore | FLOAT | Desvios padrão vs média histórica |
| fontes_rss | TEXT | Portais que geraram as notícias |
| modelo_llm | TEXT | Modelo usado |
| data_coleta | TIMESTAMP | Momento da coleta |

**Frequência:** A cada 30 minutos
**Fontes RSS:**
- InfoMoney
- Valor Econômico
- Exame Invest
- Bloomberg Línea Brasil
- Reuters Brasil
- Agência Brasil

**Fórmula de temperatura:**
```
temperatura = polaridade_média × intensidade_média × 
              log(volume_últimas_6h / volume_típico_6h)

temperatura_zscore = (temperatura - média_histórica) / 
                     desvpad_histórico
```

**Uso Camada 2:** Temperatura anormalmente negativa com preço subindo = divergência = alerta de falso positivo de EXPRESSÃO.
**Uso Camada 3:** Temperatura anormalmente negativa com posição aberta = trigger de redução parcial por Hite antes do stop técnico.

---

### TABELA 18: POLYMARKET_EVENTOS
Probabilidades de eventos precificadas por mercado de predição com skin in the game.

| Campo | Tipo | Descrição |
|---|---|---|
| data | DATE | Data |
| timestamp | TIMESTAMP | Momento da coleta |
| market_id | TEXT | ID do mercado no Polymarket |
| descricao_evento | TEXT | Descrição do evento |
| categoria | TEXT | copom / fed / politica_brasil / recessao_global / commodity / outro |
| probabilidade | FLOAT | Probabilidade atual precificada (0 a 1) |
| variacao_24h | FLOAT | Variação da probabilidade nas últimas 24h |
| liquidez_usd | FLOAT | Liquidez do mercado em USD |
| data_resolucao | DATE | Data de resolução do evento |
| impacto_b3 | TEXT | Descrição do impacto esperado em B3 |
| ticker_afetado | TEXT | Ticker mais diretamente afetado (se aplicável) |
| fonte | TEXT | Polymarket API |
| data_coleta | TIMESTAMP | Momento da coleta |

**Fonte:** Polymarket API pública — gratuita
**Frequência:** Diária (ou tempo real para eventos críticos)

**Categorias prioritárias para B3:**
```
copom → decisão de Selic — impacto direto em 
        todos os ativos
fed → decisão do Fed — impacto em câmbio e 
      fluxo estrangeiro
politica_brasil → risco fiscal, eleições, 
                  reformas regulatórias
recessao_global → impacto em exportadores 
                  e commodities
commodity → direção de petróleo, minério, 
            grãos para setores específicos
```

**Uso Camada 1:** Probabilidade de evento Polymarket como componente de Mauboussin — causa futura precificada com skin in the game.
**Uso Camada 3:** Probabilidade acima de 40% de evento disruptivo = incerteza genuína = Barbell obrigatório (Taleb + Thorp).

---

## TABELAS DE DOCUMENTOS QUALITATIVOS

### TABELA 7: DOCUMENTOS_QUALITATIVOS
| Campo | Tipo | Descrição |
|---|---|---|
| ticker | TEXT | Código do ativo |
| data_publicacao | DATE | Data de publicação |
| tipo_documento | TEXT | fato_relevante / release_resultado / call_earnings / ata_copom / pronunciamento_bcb / nota_cmn / noticia_setorial |
| texto_extraido | TEXT | Texto completo |
| score_sentimento | FLOAT | Score geral (-1 a +1) |
| score_guidance | FLOAT | Score de guidance (-1 a +1) |
| score_risco | FLOAT | Score de risco (-1 a 0) |
| score_narrativa | FLOAT | Score de consistência narrativa (-1 a +1) |
| peso_confianca | FLOAT | Peso conservador até validação empírica |
| modelo_llm | TEXT | Modelo usado |
| prompt_versao | TEXT | Versão do prompt |
| data_processamento | TIMESTAMP | Momento do processamento |
| fonte_original | TEXT | URL ou caminho do arquivo |

**Tipos adicionais vs v1:** ata_copom, pronunciamento_bcb, nota_cmn — processados via Gemini 2.5 para análise de hawkish/dovish e mudança de direção de política monetária.

---

### TABELA 8: SCORES_CAUSA
| Campo | Tipo | Descrição |
|---|---|---|
| ticker | TEXT | Código do ativo |
| data | DATE | Data do cálculo |
| score_fluxo | FLOAT | Componente fluxo observável (0-1) |
| score_ciclo_global | FLOAT | Componente ciclo global — Marks (0-1) |
| score_ciclo_local | FLOAT | Componente ciclo local — Fraga (0-1) |
| score_fundamentals | FLOAT | Componente fundamentalista quantitativo (0-1) |
| score_qualitativo | FLOAT | Componente qualitativo Gemini 2.5 (0-1) |
| score_dados_alt | FLOAT | Componente dados alternativos (0-1) |
| score_temperatura | FLOAT | Componente temperatura de notícias (0-1) |
| score_polymarket | FLOAT | Componente probabilidade Polymarket (0-1) |
| score_google_trends | FLOAT | Componente Google Trends (0-1) |
| score_composto | FLOAT | Score composto ponderado final (0-1) |
| intervalo_conf_inf | FLOAT | Limite inferior intervalo de confiança |
| intervalo_conf_sup | FLOAT | Limite superior intervalo de confiança |
| classificacao | TEXT | risco_calculavel / incerteza_genuina |
| trigger_barbell | BOOLEAN | True se qualquer trigger de Barbell ativo |
| trigger_barbell_motivo | TEXT | focus_dispersao / iie_fgv / polymarket / intervalo_largo |
| estilo_candidato | TEXT | swing / trend / hold / multiplo |
| threshold_atingido | BOOLEAN | True se score acima do threshold |
| pesos_versao | TEXT | Versão dos pesos usados |
| versao_modelo | TEXT | Versão do modelo de scoring |
| data_calculo | TIMESTAMP | Momento do cálculo |

**Novo vs v1:** score_dados_alt, score_temperatura, score_polymarket, score_google_trends, trigger_barbell, trigger_barbell_motivo.

---

## FONTES DE DADOS — RESUMO COMPLETO

| Fonte | Dados | Frequência | Tabelas |
|---|---|---|---|
| yfinance | OHLCV, fundamentals | Diária/Trimestral | 1, 2, 3, 10 |
| brapi.dev | Fundamentals B3 específicos | Trimestral | 2 |
| B3 IR | Fluxo de investidores | Diária | 6 |
| BCB API SGS | Selic, crédito, IBC-Br, Focus | Diária/Semanal/Mensal | 5, 13 |
| IBGE SIDRA | PMC, PMS, PIM, desemprego | Mensal | 14 |
| Ministério Fazenda | Arrecadação, resultado primário | Mensal | 14 |
| MDIC | Balança comercial | Semanal | 14 |
| ANP | Petróleo, combustíveis | Mensal | 14 |
| ANEEL | Consumo energia | Mensal | 14 |
| ANFAVEA | Produção veículos | Mensal | 14 |
| ABECIP | Crédito imobiliário | Mensal | 14 |
| ABPO | Papelão ondulado | Mensal | 14 |
| FGV/IBRE | IIE-FGV, capacidade utilizada | Mensal | 5 |
| Tesouro Nacional | Fluxo Tesouro Direto | Diária | 6 |
| Yahoo Finance | Commodities globais, BDI, VIX | Diária | 4, 15 |
| FRED API | Juros reais EUA, dados macro | Diária | 4 |
| CME/LME/FOEX | Commodities setoriais | Diária/Semanal | 15 |
| CVM | Fatos relevantes, documentos | Sob demanda | 7 |
| Gemini 2.5 API | Processamento qualitativo | Sob demanda/30min | 7, 17 |
| Google Trends API | Buscas por termos | Diária | 16 |
| Polymarket API | Probabilidades de eventos | Diária | 18 |
| RSS portais | Notícias financeiras | 30 minutos | 17 |
| APIs intraday | Tape e order flow | Intraday [futuro] | 12 |

---

## TRIGGERS DE BARBELL — CONSOLIDADOS

O Protocolo Barbell substitui Kelly padrão quando qualquer um dos triggers abaixo está ativo:

```
TRIGGER 1 — Focus BCB dispersao_agregada
Acima de threshold configurável = incerteza 
genuína de mercado

TRIGGER 2 — IIE-FGV
Acima de 2 desvios padrão da média histórica = 
incerteza econômica elevada

TRIGGER 3 — Polymarket evento crítico
Probabilidade > 40% de evento disruptivo 
para o ativo/setor

TRIGGER 4 — Intervalo de confiança do score
intervalo_conf_sup - intervalo_conf_inf > 
threshold configurável = parâmetros imprecisos

TRIGGER 5 — Classificação incerteza_genuina
Empresa < 8 trimestres de histórico ou 
evento binário pendente

Qualquer trigger ativo → trigger_barbell = True
Dois ou mais triggers → Barbell obrigatório, 
sizing mínimo
```

---

## NOTAS DE ARQUITETURA

1. Data Layer é fonte única de verdade.
2. Indicadores básicos compartilhados calculados pelo Data Layer com parâmetros versionados.
3. Score de CAUSA passa intacto à Camada 3 sem reinterpretação da Camada 2.
4. Tabelas 11, 12 existem desde o início — vazias mas estruturadas.
5. Histórico de scores imutável — série temporal preservada integralmente.
6. Todos os pesos são parâmetros configuráveis via YAML — nunca hardcoded.
7. Tabela 17 (Temperatura) atualizada a cada 30 minutos — dado mais frequente do sistema.
8. Tabela 18 (Polymarket) é categoria nova — probabilidade de evento, não proxy de atividade.
9. Bitcoin na Tabela 4 é experimental — removido se correlação não persiste out-of-sample em 6 meses.
10. ABPO (papelão) tem alpha elevado por baixa cobertura — prioridade alta apesar de ausência de API estruturada.
