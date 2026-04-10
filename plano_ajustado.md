# Plano de Implementação do Data Layer - Versão Ajustada

## BLOCO 1 - Mudanças visíveis no sistema

1. Vai existir um Data Layer completo com todas as tabelas estruturadas no SQLite
2. O sistema vai coletar dados de múltiplas fontes (yfinance, BCB, IBGE, etc.) diariamente
3. O sistema terá processos automatizados de coleta e cálculo de indicadores
4. Tudo será orquestrado pelo APScheduler com jobs específicos para cada fonte de dados
5. O sistema vai calcular automaticamente scores de causa e indicadores técnicos
6. Haverá monitoramento e logs para garantir a qualidade e atualização dos dados

## BLOCO 2 - Plano técnico

### 1. Estrutura de pastas

```
advantage/
├── data/
│   └── raw/
│       ├── preco_volume.db
│       ├── macro.db
│       ├── alternativo.db
│       └── portfolio.db
├── src/
│   └── data_layer/
│       ├── __init__.py
│       ├── db/
│       │   ├── __init__.py
│       │   ├── schema.py          # CREATE TABLE statements
│       │   └── connection.py      # get_connection() por domínio
│       ├── collectors/
│       │   ├── __init__.py
│       │   ├── preco_volume.py    # yfinance + brapi
│       │   ├── macro_global.py    # FRED, CME, BDI
│       │   ├── macro_brasil.py    # BCB/SGS, IBGE, Focus
│       │   ├── alternativo.py     # Google Trends, ANEEL, CAGED, ABPO (stub)
│       │   └── noticias.py        # RSS + Gemini 2.5 (temperatura)
│       ├── scheduler.py           # APScheduler — entry point de produção
│       └── utils.py               # validação de schema, log, retry
└── tests/
    └── data_layer/
        ├── test_schema.py
        ├── test_collectors.py
        └── test_scheduler.py
```

### 2. Implementação do banco de dados

#### 2.1. Módulo `db/connection.py`
- Implementar conexão com SQLite para os quatro domínios
- Criar função `get_connection(domain)` que retorna conexão SQLite
- Configurar WAL mode e foreign keys

#### 2.2. Módulo `db/schema.py`
- Implementar função `create_all_tables()` que cria todas as tabelas
- Usar `CREATE TABLE IF NOT EXISTS` para idempotência
- Criar todas as tabelas conforme especificado no documento

### 3. Implementação dos coletores

#### 3.1. `collectors/preco_volume.py`
- Fonte primária: `yfinance` — `yf.download(tickers, period, interval)`
- Fonte secundária: `brapi.dev` — endpoint `/api/quote/{ticker}`
- Fallback: se yfinance falhar para um ticker, tenta brapi
- Universo padrão: lista de tickers do Ibovespa (~80 ativos)
- Frequência de chamada: diária, após fechamento B3 (18h30)

#### 3.2. `collectors/macro_brasil.py`
- BCB/SGS via `requests` — endpoint `https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados`
- Séries obrigatórias:
  - 432: Selic meta
  - 11: Selic efetiva
  - 433: IPCA mensal
  - 13522: IPCA acumulado 12m
  - 189: IGP-M mensal
  - 1: USD/BRL
- Focus BCB via endpoint `https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/`
  - Coletar: `ExpectativasMercadoAnuais` para Selic, IPCA, Câmbio, PIB
  - Registrar mediana, desvio padrão, mínimo, máximo por indicador/horizonte

#### 3.3. `collectors/macro_global.py`
- FRED API: `pip install fredapi` — séries DFF (fed funds), T10Y2Y (yield)
- yfinance para: DX-Y.NYB (DXY), ^GSPC (S&P500), CL=F (WTI), BZ=F (Brent)
- BDI: scraping ou API pública (documentar fonte escolhida)
- Commodities agrícolas: yfinance ZS=F (soja), ZC=F (milho)
- Minério de ferro: yfinance ou scraping (documentar)

#### 3.4. `collectors/alternativo.py`
- Google Trends: `pip install pytrends` — termos configuráveis por ativo
- ANEEL: API pública de consumo industrial (stub aceitável se API indisponível)
- ABPO: **stub** — retornar `0` e logar aviso. Pipeline de PDF é Pendência 6.
- IIE-FGV: scraping do portal FGV (documentar URL)

#### 3.5. `collectors/noticias.py`
- RSS: `pip install feedparser` — feeds configuráveis (Valor Econômico, Infomoney, Reuters Brasil)
- Temperatura: chamada à API Gemini 2.5 Flash para classificar manchetes em score -1.0 a +1.0
- Frequência: a cada 30 minutos
- Persistir em `temperatura_noticias` com `hora_coleta` como parte da PK

### 4. Implementação do scheduler

#### 4.1. `scheduler.py`
- Entry point de produção do Data Layer
- Rodar como: `python -m src.data_layer.scheduler`
- NÃO depende de VS Code — processo autônomo de background
- Agendamento obrigatório:
  - `preco_volume.coletar` - `cron(hour=18, minute=30)` - Diário após fechamento B3
  - `macro_brasil.coletar` - `cron(hour=19, minute=0)` - Diário
  - `macro_global.coletar` - `cron(hour=19, minute=30)` - Diário
  - `alternativo.coletar` - `cron(day_of_week='mon', hour=8)` - Semanal
  - `noticias.coletar` - `interval(minutes=30)` - Contínuo
  - `calcular_indicadores` - `cron(hour=20, minute=0)` - Diário após preco_volume

### 5. Implementação dos utilitários

#### 5.1. `utils.py`
- Função `validar_ohlcv(df: pd.DataFrame)` - Valida dados OHLCV
- Função `log_coleta(fonte: str, registros: int, erro: str | None = None)` - Log estruturado
- Função `retry(func, tentativas: int = 3, espera_s: float = 5.0)` - Decorator para retry

### 6. Dependências

```
apscheduler>=3.10.0
yfinance>=0.2.36
requests>=2.31.0
pandas>=2.0.0
pandas-ta>=0.3.14b
feedparser>=6.0.10
pytrends>=4.9.2
fredapi>=0.5.0
google-generativeai>=0.8.0
```

### 7. Critérios de aceitação

- [ ] `data/raw/` criado com os quatro arquivos `.db`
- [ ] `schema.py` — `create_all_tables()` cria todas as tabelas sem erro
- [ ] `connection.py` — `get_connection(domain)` funciona para os quatro domínios
- [ ] `collectors/preco_volume.py` — coleta OHLCV para lista de tickers e persiste
- [ ] `collectors/macro_brasil.py` — coleta Selic, IPCA, câmbio e Focus BCB
- [ ] `collectors/macro_global.py` — coleta DXY, S&P500, WTI, BDI, soja, cobre
- [ ] `collectors/alternativo.py` — Google Trends funcional; ABPO é stub documentado
- [ ] `collectors/noticias.py` — RSS + Gemini classifica manchetes e persiste score
- [ ] `scheduler.py` — roda `python -m src.data_layer.scheduler` sem VS Code aberto
- [ ] `calcular_indicadores` — calcula e persiste SMA, EMA, RSI, MACD, ATR, VWAP, OBV
- [ ] Append-only verificado: segundo `coletar()` no mesmo dia não duplica registros
- [ ] `tests/data_layer/` — ao menos um teste por módulo passando

Critérios de rejeição imediato:
- Qualquer UPDATE em dados históricos (série temporal é imutável)
- Qualquer dependência de API REST para acesso interno ao banco
- Uso de PostgreSQL, Airflow ou Docker nesta fase
- Scheduler que exige VS Code aberto para rodar