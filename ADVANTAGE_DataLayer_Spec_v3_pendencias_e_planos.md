# ADVANTAGE — Especificação: Data Layer v3 — Pendências e Planos de Execução

**Versão:** 3.1
**Data:** Sat Apr 11 2026
**Autor:** BUILD Agent

---

## RELATÓRIO DE ESTADO — ADVANTAGE Data Layer v1

### ESTADO v1 (Herdado da Spec v1):

| Item | Status | Observação |
|------|--------|------------|
| `data/raw/` com quatro arquivos `.db` | [ ] | **AUSENTE** — pasta não existe |
| `schema.py` — `create_all_tables()` | [x] | Funcional — cria tabelas básicas |
| `connection.py` — `get_connection(domain)` | [x] | Funcional — 4 domínios suportados |
| `collectors/preco_volume.py` — OHLCV | [x] | Funcional — yfinance + brapi fallback |
| `collectors/macro_brasil.py` — Selic, IPCA, câmbio, Focus | [x] | Funcional — BCB/SGS + Focus BCB |
| `collectors/macro_global.py` — DXY, S&P500, WTI, BDI, soja, cobre | [~] | **PARCIAL** — BDI omitido, faltam níquel, alumínio, lítio, celulose |
| `collectors/alternativo.py` — Google Trends | [x] | Funcional — com ABPO scraping |
| `collectors/noticias.py` — RSS + Gemini | [x] | Funcional — classifica sentimento |
| `scheduler.py` — autônomo | [x] | Funcional — BlockingScheduler |
| `calcular_indicadores` — SMA, EMA, RSI, MACD, ATR, VWAP, OBV | [x] | Funcional |
| Append-only verificado | [x] | Usa INSERT OR IGNORE |

---

## PENDÊNCIAS IDENTIFICADAS — Spec v3

### PENDÊNCIA 1: Tabelas Novas Ausentes no Schema

**Arquivos afetados:** `advantage/src/data_layer/db/schema.py`

**Tabelas faltando:**
1. `retornos_historicos` → `preco_volume.db`
2. `taxa_conversao` → `portfolio.db`
3. `scores_causa` → `portfolio.db`
4. `documentos_qualitativos` → `alternativo.db`
5. `polymarket_eventos` → `alternativo.db`
6. `intraday_slot` → `preco_volume.db`
7. `fluxo_investidores` → `macro.db`
8. `dados_setoriais_br` → `alternativo.db`
9. `commodities_setoriais` → `macro.db`

---

### PENDÊNCIA 2: Campos Adicionais em Tabelas Existentes

**Arquivos afetados:** `advantage/src/data_layer/db/schema.py`, `advantage/src/data_layer/utils.py`

**Tabelas com campos faltando:**
1. `portfolio_estado` — 10 campos novos (sizing_inicial, sizing_atual, etc.)
2. `temperatura_noticias` — 11 campos novos (escopo, referencia, polaridade, etc.)
3. `indicadores_compartilhados` — 9 campos novos (atr_10, atr_60, vol_media_20, etc.)
4. `google_trends` — 4 campos novos (ticker_relacionado, setor_relacionado, etc.)

---

### PENDÊNCIA 3: Funções de Temperatura em utils.py

**Arquivo afetado:** `advantage/src/data_layer/utils.py`

**Funções faltando:**
- `calcular_temperatura(polaridade, intensidade, volume_atual, volume_tipico)`
- `calcular_temperatura_zscore(temperatura, media_historica, desvpad_historico)`
- `alter_table_if_column_missing(conn, tabela, coluna, tipo)`

---

### PENDÊNCIA 4: Coletor Polymarket

**Arquivo a criar:** `advantage/src/data_layer/collectors/polymarket.py`

**Requisitos:**
- API: `https://gamma-api.polymarket.com/markets`
- Filtros: categorias copom, fed, politica_brasil, recessao_global, commodity
- Liquidez mínima: USD 10.000
- Frequência: diária

---

### PENDÊNCIA 5: Expansão do Coletor Alternativo

**Arquivo afetado:** `advantage/src/data_layer/collectors/alternativo.py`

**Funções a adicionar:**
- `coletar_ibge_sidra_embalagens()` — Tabela 8889 (substitui ABPO)
- `coletar_ibge_sidra_atividade()` — PMC, PMS, PIM
- `coletar_mdic_balanca()` — Balança comercial

---

### PENDÊNCIA 6: Expansão do Coletor Macro Global

**Arquivo afetado:** `advantage/src/data_layer/collectors/macro_global.py`

**Commodities faltando:**
- Níquel LME: `LNGG.L`
- Alumínio LME: `ALI=F`
- Lítio spot: stub (sem API gratuita)
- Celulose FOEX: stub (sem API gratuita)
- Boi gordo: `GF=F`
- Açúcar: `SB=F`
- Café: `KC=F`

---

### PENDÊNCIA 7: Expansão do calcular_indicadores

**Arquivo afetado:** `advantage/src/data_layer/scheduler.py`

**Indicadores novos a calcular:**
- ATR 10 e ATR 60
- Volume médio 20 e 60
- Máxima/mínima 52 semanas
- Máxima/mínima 3 anos
- Retornos históricos (diário e log)
- Persistir em `retornos_historicos`

---

### PENDÊNCIA 8: Jobs Novos no Scheduler

**Arquivo afetado:** `advantage/src/data_layer/scheduler.py`

**Jobs a adicionar:**
- `polymarket_diario` — 19h45
- `ibge_embalagens_mensal` — dia 1, 08h00
- `ibge_atividade_mensal` — dia 1, 08h15

---

### PENDÊNCIA 9: Requirements — python-dotenv

**Arquivo afetado:** `advantage/requirements.txt`

**Dependência a adicionar:**
- `python-dotenv>=1.0.0`

---

### PENDÊNCIA 10: Testes para Novos Módulos

**Arquivos a criar:**
- `advantage/tests/data_layer/collectors/test_polymarket.py`
- `advantage/tests/data_layer/test_utils_temperatura.py`

---

## PLANOS DE EXECUÇÃO POR PENDÊNCIA

### PLANO PENDÊNCIA 1: Tabelas Novas no Schema

**BLOCO 1 — PARA APROVAÇÃO (Negócio)**

Esta mudança adiciona 9 novas tabelas ao banco de dados para suportar:
- Retornos históricos calculados automaticamente
- Taxa de conversão de sinais (slot para Camada 2)
- Scores de causa (slot para Camada 1)
- Documentos qualitativos processados por LLM
- Eventos de predição do Polymarket
- Slot para dados intraday (futuro)
- Fluxo de investidores na B3
- Dados setoriais brasileiros (IBGE, MDIC)
- Commodities setoriais expandidas

Nenhuma tabela existente será alterada. As tabelas de slot (taxa_conversao, scores_causa, intraday_slot) serão criadas vazias, sem coletor.

**BLOCO 2 — PARA O BUILD (Técnico)**

```
TAREFA 1.1
Arquivo : advantage/src/data_layer/db/schema.py
Ação : modificar
Escopo : função create_all_tables(), bloco preco_volume.db
Detalhe : adicionar CREATE TABLE IF NOT EXISTS para:
- retornos_historicos
- intraday_slot
Constraints: não alterar tabelas existentes
Depende de: nenhuma

TAREFA 1.2
Arquivo : advantage/src/data_layer/db/schema.py
Ação : modificar
Escopo : função create_all_tables(), bloco macro.db
Detalhe : adicionar CREATE TABLE IF NOT EXISTS para:
- fluxo_investidores
- commodities_setoriais
Constraints: não alterar tabelas existentes
Depende de: nenhuma

TAREFA 1.3
Arquivo : advantage/src/data_layer/db/schema.py
Ação : modificar
Escopo : função create_all_tables(), bloco alternativo.db
Detalhe : adicionar CREATE TABLE IF NOT EXISTS para:
- documentos_qualitativos
- polymarket_eventos
- dados_setoriais_br
Constraints: não alterar tabelas existentes
Depende de: nenhuma

TAREFA 1.4
Arquivo : advantage/src/data_layer/db/schema.py
Ação : modificar
Escopo : função create_all_tables(), bloco portfolio.db
Detalhe : adicionar CREATE TABLE IF NOT EXISTS para:
- taxa_conversao
- scores_causa
Constraints: não alterar tabelas existentes
Depende de: nenhuma

TAREFA 1.5
Arquivo : advantage/tests/data_layer/db/test_schema.py
Ação : modificar
Escopo : testes existentes
Detalhe : adicionar testes para verificar criação das 9 novas tabelas
Constraints: não alterar código de produção
Depende de: TAREFA 1.4
```

---

### PLANO PENDÊNCIA 2: Campos Adicionais em Tabelas Existentes

**BLOCO 1 — PARA APROVAÇÃO (Negócio)**

Esta mudança adiciona campos novos a 4 tabelas existentes:
- `portfolio_estado`: campos para rastrear sizing, score de entrada, classificação, causa alternativa, dados de saída (preço, resultado, motivo)
- `temperatura_noticias`: campos para fórmula completa de temperatura (polaridade, intensidade, urgência, z-score)
- `indicadores_compartilhados`: ATR 10/60, volumes médios, máximas/mínimas 52s e 3a
- `google_trends`: relacionamento com ticker/setor, variação vs média

Nenhum dado existente será perdido. A abordagem é idempotente — segura para executar múltiplas vezes.

**BLOCO 2 — PARA O BUILD (Técnico)**

```
TAREFA 2.1
Arquivo : advantage/src/data_layer/utils.py
Ação : modificar
Escopo : final do arquivo
Detalhe : adicionar função alter_table_if_column_missing(conn, tabela, coluna, tipo) que verifica se coluna existe antes de adicionar (idempotente)
Constraints: não alterar funções existentes
Depende de: nenhuma

TAREFA 2.2
Arquivo : advantage/src/data_layer/db/schema.py
Ação : modificar
Escopo : função create_all_tables(), após criação de portfolio_estado
Detalhe : adicionar ALTER TABLE IF NOT EXISTS para 10 campos novos: sizing_inicial, sizing_atual, score_causa_entrada, classificacao_entrada, causa_alternativa_compartilhada, data_saida, preco_saida, resultado_pct, motivo_saida
Constraints: usar alter_table_if_column_missing para idempotência
Depende de: TAREFA 2.1

TAREFA 2.3
Arquivo : advantage/src/data_layer/db/schema.py
Ação : modificar
Escopo : função create_all_tables(), após criação de temperatura_noticias
Detalhe : adicionar ALTER TABLE IF NOT EXISTS para 11 campos novos: escopo, referencia, polaridade, intensidade, urgencia, volume_tipico, temperatura, temperatura_zscore, fontes_rss, modelo_llm
Constraints: usar alter_table_if_column_missing para idempotência
Depende de: TAREFA 2.1

TAREFA 2.4
Arquivo : advantage/src/data_layer/db/schema.py
Ação : modificar
Escopo : função create_all_tables(), após criação de indicadores_compartilhados
Detalhe : adicionar ALTER TABLE IF NOT EXISTS para 9 campos novos: atr_10, atr_60, vol_media_20, vol_media_60, maxima_52s, minima_52s, maxima_3a, minima_3a, parametros_ver
Constraints: usar alter_table_if_column_missing para idempotência
Depende de: TAREFA 2.1

TAREFA 2.5
Arquivo : advantage/src/data_layer/db/schema.py
Ação : modificar
Escopo : função create_all_tables(), após criação de google_trends
Detalhe : adicionar ALTER TABLE IF NOT EXISTS para 4 campos novos: ticker_relacionado, setor_relacionado, variacao_vs_media, tipo
Constraints: usar alter_table_if_column_missing para idempotência
Depende de: TAREFA 2.1

TAREFA 2.6
Arquivo : advantage/tests/data_layer/test_utils.py
Ação : modificar
Escopo : testes existentes
Detalhe : adicionar teste para alter_table_if_column_missing verificando que não duplica colunas em execuções múltiplas
Constraints: não alterar código de produção
Depende de: TAREFA 2.1
```

---

### PLANO PENDÊNCIA 3: Funções de Temperatura

**BLOCO 1 — PARA APROVAÇÃO (Negócio)**

Esta mudança adiciona funções matemáticas para calcular "temperatura" de notícias:
- `calcular_temperatura`: mede intensidade de sentimento ajustada pelo volume de notícias
- `calcular_temperatura_zscore`: normaliza temperatura em relação ao histórico

Fórmula: `temperatura = polaridade × intensidade × log(volume / volume_típico)`

Essas funções serão usadas pelo coletor de notícias para enriquecer os dados de sentimento.

**BLOCO 2 — PARA O BUILD (Técnico)**

```
TAREFA 3.1
Arquivo : advantage/src/data_layer/utils.py
Ação : modificar
Escopo : final do arquivo
Detalhe : adicionar função calcular_temperatura(polaridade, intensidade, volume_atual, volume_tipico) retornando float
Implementar: polaridade * intensidade * math.log(volume_atual / volume_tipico)
Retornar 0.0 se volume_tipico == 0
Constraints: não alterar funções existentes
Depende de: nenhuma

TAREFA 3.2
Arquivo : advantage/src/data_layer/utils.py
Ação : modificar
Escopo : final do arquivo
Detalhe : adicionar função calcular_temperatura_zscore(temperatura, media_historica, desvpad_historico) retornando float
Implementar: (temperatura - media_historica) / desvpad_historico
Retornar 0.0 se desvpad_historico == 0
Constraints: não alterar funções existentes
Depende de: nenhuma

TAREFA 3.3
Arquivo : advantage/tests/data_layer/test_utils.py
Ação : modificar
Escopo : testes existentes
Detalhe : adicionar testes para:
- calcular_temperatura com valores normais
- calcular_temperatura com volume_tipico == 0
- calcular_temperatura_zscore com valores normais
- calcular_temperatura_zscore com desvpad == 0
Constraints: não alterar código de produção
Depende de: TAREFA 3.2
```

---

### PLANO PENDÊNCIA 4: Coletor Polymarket

**BLOCO 1 — PARA APROVAÇÃO (Negócio)**

Esta mudança cria um novo coletor para mercados de predição do Polymarket, permitindo capturar probabilidades de eventos relevantes para o mercado brasileiro:
- Decisões do COPOM
- Decisões do Fed
- Política brasileira
- Recessão global
- Commodities

O coletor filtra mercados com liquidez mínima de USD 10.000 para evitar ruído. Dados são coletados diariamente às 19h45.

**BLOCO 2 — PARA O BUILD (Técnico)**

```
TAREFA 4.1
Arquivo : advantage/src/data_layer/collectors/polymarket.py
Ação : criar
Escopo : arquivo novo
Detalhe : criar coletor com função coletar(tickers) que:
- Consome API https://gamma-api.polymarket.com/markets
- Filtra por categorias: copom, fed, politica_brasil, recessao_global, commodity
- Filtra liquidez >= USD 10.000
- Insere em polymarket_eventos
- Retorna número de registros inseridos
- Nunca lança exceção para o caller
Constraints: seguir padrão dos outros coletores
Depende de: TAREFA 1.3 (tabela polymarket_eventos)

TAREFA 4.2
Arquivo : advantage/src/data_layer/collectors/__init__.py
Ação : modificar
Escopo : imports
Detalhe : adicionar import de polymarket
Constraints: não remover imports existentes
Depende de: TAREFA 4.1

TAREFA 4.3
Arquivo : advantage/tests/data_layer/collectors/test_polymarket.py
Ação : criar
Escopo : arquivo novo
Detalhe : criar testes para:
- coletar retorna int >= 0
- coletar não lança exceção mesmo com API indisponível
- dados são inseridos corretamente
Constraints: usar mock para API externa
Depende de: TAREFA 4.1
```

---

### PLANO PENDÊNCIA 5: Expansão do Coletor Alternativo

**BLOCO 1 — PARA APROVAÇÃO (Negócio)**

Esta mudança substitui o pipeline de PDFs da ABPO pela API oficial do IBGE SIDRA (Tabela 8889), que é a fonte primária dos dados de produção de embalagens. Também adiciona:
- Coleta de PMC (comércio), PMS (serviços), PIM (produção industrial)
- Coleta de balança comercial via MDIC

Benefícios:
- Dados estruturados via API (sem scraping de PDF)
- Série histórica completa desde 2012
- Sem perda de informação — ABPO deriva desta fonte

**BLOCO 2 — PARA O BUILD (Técnico)**

```
TAREFA 5.1
Arquivo : advantage/src/data_layer/collectors/alternativo.py
Ação : modificar
Escopo : final do arquivo, antes de coletar()
Detalhe : adicionar função coletar_ibge_sidra_embalagens() que:
- Consome API IBGE SIDRA agregado 8889
- Coleta séries: '3' (Total), '3.4' (Papel/papelão), '3.5' (Plástico)
- Insere em dados_setoriais_br com fonte='IBGE_SIDRA_8889'
- Retorna número de registros inseridos
Constraints: não alterar função coletar() existente
Depende de: TAREFA 1.3 (tabela dados_setoriais_br)

TAREFA 5.2
Arquivo : advantage/src/data_layer/collectors/alternativo.py
Ação : modificar
Escopo : final do arquivo, após coletar_ibge_sidra_embalagens()
Detalhe : adicionar função coletar_ibge_sidra_atividade() que:
- Consome API SIDRA para PMC, PMS, PIM (agregados distintos)
- Insere em dados_setoriais_br com fonte='IBGE_SIDRA'
- Retorna número de registros inseridos
Constraints: não alterar funções existentes
Depende de: TAREFA 5.1

TAREFA 5.3
Arquivo : advantage/src/data_layer/collectors/alternativo.py
Ação : modificar
Escopo : final do arquivo, após coletar_ibge_sidra_atividade()
Detalhe : adicionar função coletar_mdic_balanca() que:
- Consome API MDIC/dados.gov.br
- Insere em dados_setoriais_br com fonte='MDIC'
- Retorna número de registros inseridos
- Se API indisponível, loga aviso e retorna 0
Constraints: não alterar funções existentes
Depende de: TAREFA 5.2

TAREFA 5.4
Arquivo : advantage/tests/data_layer/collectors/test_alternativo.py
Ação : modificar
Escopo : testes existentes
Detalhe : adicionar testes para:
- coletar_ibge_sidra_embalagens retorna int >= 0
- coletar_ibge_sidra_atividade retorna int >= 0
- coletar_mdic_balanca retorna int >= 0
Constraints: usar mock para APIs externas
Depende de: TAREFA 5.3
```

---

### PLANO PENDÊNCIA 6: Expansão do Coletor Macro Global

**BLOCO 1 — PARA APROVAÇÃO (Negócio)**

Esta mudança expande o coletor de dados macro globais para incluir:
- Níquel LME (via yfinance)
- Alumínio LME (via yfinance)
- Boi gordo B3 (via yfinance)
- Açúcar NYBOT (via yfinance)
- Café NYBOT (via yfinance)

Lítio e celulose serão mantidos como stubs documentados (sem API gratuita disponível).

**BLOCO 2 — PARA O BUILD (Técnico)**

```
TAREFA 6.1
Arquivo : advantage/src/data_layer/collectors/macro_global.py
Ação : modificar
Escopo : dicionário simbolos_yf
Detalhe : adicionar mapeamentos para:
- 'NIQUEL': 'LNGG.L'
- 'ALUMINIO': 'ALI=F'
- 'BOI_GORDO': 'GF=F'
- 'ACUCAR': 'SB=F'
- 'CAFE': 'KC=F'
Constraints: não remover mapeamentos existentes
Depende de: TAREFA 1.2 (tabela commodities_setoriais)

TAREFA 6.2
Arquivo : advantage/src/data_layer/collectors/macro_global.py
Ação : modificar
Escopo : mapeamento_colunas
Detalhe : adicionar mapeamentos para novas commodities:
- 'NIQUEL': 'niquel_lme'
- 'ALUMINIO': 'aluminio_lme'
- 'BOI_GORDO': 'boi_gordo_b3'
- 'ACUCAR': 'acucar_nybot'
- 'CAFE': 'cafe_nybot'
Constraints: não remover mapeamentos existentes
Depende de: TAREFA 6.1

TAREFA 6.3
Arquivo : advantage/src/data_layer/collectors/macro_global.py
Ação : modificar
Escopo : após loop de coleta yfinance
Detalhe : adicionar stubs documentados para:
- Lítio spot: logar aviso "API não disponível"
- Celulose FOEX: logar aviso "API não disponível"
Constraints: não alterar lógica existente
Depende de: TAREFA 6.2

TAREFA 6.4
Arquivo : advantage/tests/data_layer/collectors/test_macro_global.py
Ação : modificar
Escopo : testes existentes
Detalhe : adicionar testes para verificar coleta das novas commodities
Constraints: usar mock para yfinance
Depende de: TAREFA 6.3
```

---

### PLANO PENDÊNCIA 7: Expansão do calcular_indicadores

**BLOCO 1 — PARA APROVAÇÃO (Negócio)**

Esta mudança expande o cálculo de indicadores técnicos para incluir:
- ATR de 10 e 60 períodos (volatilidade de curto e médio prazo)
- Volume médio de 20 e 60 períodos
- Máxima e mínima de 52 semanas
- Máxima e mínima de 3 anos
- Retornos diários e logarítmicos

Esses indicadores enriquecem a análise técnica e permitem identificar extremos de preço e volume.

**BLOCO 2 — PARA O BUILD (Técnico)**

```
TAREFA 7.1
Arquivo : advantage/src/data_layer/scheduler.py
Ação : modificar
Escopo : função calcular_indicadores(), bloco de cálculos
Detalhe : adicionar cálculos:
- atr_10 = ta.atr(...)
- atr_60 = ta.atr(...)
- vol_media_20 = df_ticker['volume'].rolling(20).mean()
- vol_media_60 = df_ticker['volume'].rolling(60).mean()
- maxima_52s = df_ticker['fechamento'].rolling(252).max()
- minima_52s = df_ticker['fechamento'].rolling(252).min()
- maxima_3a = df_ticker['fechamento'].rolling(756).max()
- minima_3a = df_ticker['fechamento'].rolling(756).min()
Constraints: não alterar cálculos existentes
Depende de: TAREFA 2.4 (campos em indicadores_compartilhados)

TAREFA 7.2
Arquivo : advantage/src/data_layer/scheduler.py
Ação : modificar
Escopo : função calcular_indicadores(), INSERT
Detalhe : adicionar novos campos ao INSERT em indicadores_compartilhados: atr_10, atr_60, vol_media_20, vol_media_60, maxima_52s, minima_52s, maxima_3a, minima_3a, parametros_ver
Constraints: não alterar INSERT existente
Depende de: TAREFA 7.1

TAREFA 7.3
Arquivo : advantage/src/data_layer/scheduler.py
Ação : modificar
Escopo : função calcular_indicadores(), após INSERT em indicadores
Detalhe : adicionar cálculo e INSERT em retornos_historicos:
- retorno_diario = (fechamento_adj / fechamento_adj_anterior) - 1
- retorno_log = ln(fechamento_adj / fechamento_adj_anterior)
- Inserir em retornos_historicos
Constraints: usar INSERT OR IGNORE para evitar duplicatas
Depende de: TAREFA 1.1 (tabela retornos_historicos)

TAREFA 7.4
Arquivo : advantage/tests/data_layer/test_scheduler.py
Ação : modificar
Escopo : testes existentes
Detalhe : adicionar testes para verificar cálculo dos novos indicadores
Constraints: não alterar código de produção
Depende de: TAREFA 7.3
```

---

### PLANO PENDÊNCIA 8: Jobs Novos no Scheduler

**BLOCO 1 — PARA APROVAÇÃO (Negócio)**

Esta mudança adiciona 3 novos jobs ao scheduler:
- Polymarket diário às 19h45 (após macro_global)
- IBGE embalagens mensal no dia 1 às 08h00
- IBGE atividade mensal no dia 1 às 08h15

**BLOCO 2 — PARA O BUILD (Técnico)**

```
TAREFA 8.1
Arquivo : advantage/src/data_layer/scheduler.py
Ação : modificar
Escopo : imports
Detalhe : adicionar import de polymarket.coletar
Constraints: não remover imports existentes
Depende de: TAREFA 4.1 (coletor polymarket)

TAREFA 8.2
Arquivo : advantage/src/data_layer/scheduler.py
Ação : modificar
Escopo : função main(), após job_macro_global
Detalhe : adicionar job polymarket_diario:
@scheduler.scheduled_job(CronTrigger(hour=19, minute=45))
def job_polymarket():
    registros = polymarket.coletar()
    log_job_execution("polymarket", registros)
Constraints: não alterar jobs existentes
Depende de: TAREFA 8.1

TAREFA 8.3
Arquivo : advantage/src/data_layer/scheduler.py
Ação : modificar
Escopo : função main(), após jobs existentes
Detalhe : adicionar jobs mensais:
- ibge_embalagens_mensal: dia 1, 08h00
- ibge_atividade_mensal: dia 1, 08h15
Constraints: não alterar jobs existentes
Depende de: TAREFA 5.1, TAREFA 5.2 (funções IBGE)

TAREFA 8.4
Arquivo : advantage/src/data_layer/scheduler.py
Ação : modificar
Escopo : print de jobs agendados
Detalhe : adicionar linhas para os novos jobs no print de inicialização
Constraints: não alterar prints existentes
Depende de: TAREFA 8.3

TAREFA 8.5
Arquivo : advantage/tests/data_layer/test_scheduler.py
Ação : modificar
Escopo : testes existentes
Detalhe : adicionar testes para verificar que novos jobs são registrados
Constraints: não alterar código de produção
Depende de: TAREFA 8.4
```

---

### PLANO PENDÊNCIA 9: Requirements — python-dotenv

**BLOCO 1 — PARA APROVAÇÃO (Negócio)**

Esta mudança adiciona a dependência `python-dotenv>=1.0.0` ao requirements.txt, permitindo carregar variáveis de ambiente de arquivo `.env`.

**BLOCO 2 — PARA O BUILD (Técnico)**

```
TAREFA 9.1
Arquivo : advantage/requirements.txt
Ação : modificar
Escopo : final do arquivo
Detalhe : adicionar linha:
python-dotenv>=1.0.0
Constraints: não remover dependências existentes
Depende de: nenhuma
```

---

### PLANO PENDÊNCIA 10: Testes para Novos Módulos

**BLOCO 1 — PARA APROVAÇÃO (Negócio)**

Esta mudança garante cobertura de testes para os novos módulos implementados, validando comportamento esperado e edge cases.

**BLOCO 2 — PARA O BUILD (Técnico)**

```
TAREFA 10.1
Arquivo : advantage/tests/data_layer/collectors/test_polymarket.py
Ação : criar
Escopo : arquivo novo
Detalhe : criar testes para coletor polymarket:
- test_coletar_retorna_int
- test_coletar_nao_lanca_excecao
- test_dados_inseridos_corretamente
Constraints: usar mock para API externa
Depende de: TAREFA 4.1

TAREFA 10.2
Arquivo : advantage/tests/data_layer/test_utils_temperatura.py
Ação : criar
Escopo : arquivo novo
Detalhe : criar testes para funções de temperatura:
- test_calcular_temperatura_normal
- test_calcular_temperatura_volume_zero
- test_calcular_temperatura_zscore_normal
- test_calcular_temperatura_zscore_desvpad_zero
Constraints: não alterar código de produção
Depende de: TAREFA 3.2
```

---

## ORDEM DE EXECUÇÃO RECOMENDADA

1. **PENDÊNCIA 1** — Tabelas novas no schema (TAREFAS 1.1 a 1.5)
2. **PENDÊNCIA 2** — Campos adicionais (TAREFAS 2.1 a 2.6)
3. **PENDÊNCIA 3** — Funções de temperatura (TAREFAS 3.1 a 3.3)
4. **PENDÊNCIA 4** — Coletor Polymarket (TAREFAS 4.1 a 4.3)
5. **PENDÊNCIA 5** — Expansão Alternativo (TAREFAS 5.1 a 5.4)
6. **PENDÊNCIA 6** — Expansão Macro Global (TAREFAS 6.1 a 6.4)
7. **PENDÊNCIA 7** — Expansão calcular_indicadores (TAREFAS 7.1 a 7.4)
8. **PENDÊNCIA 8** — Jobs novos no scheduler (TAREFAS 8.1 a 8.5)
9. **PENDÊNCIA 9** — Requirements (TAREFA 9.1)
10. **PENDÊNCIA 10** — Testes finais (TAREFAS 10.1 a 10.2)

---

**Aguardando aprovação do BLOCO 1 de cada pendência para iniciar execução.**