# ADVANTAGE — Especificação: Data Layer
**Versão:** 1.0  
**Destino:** Agente `plan` — Qwen3 Coder 480B A35B  
**Autorização:** CEO Tiago  

---

## 1. CONTEXTO

O ADVANTAGE é um sistema de decisão para trading em B3 organizado em quatro camadas:

```
DATA LAYER → CAMADA 1 (CAUSA) → CAMADA 2 (EXPRESSÃO) → CAMADA 3 (EXTRAÇÃO)
```

O Data Layer é a **fonte única de verdade**. Nenhuma camada de análise acessa
fonte externa diretamente — tudo passa pelo Data Layer.

Esta especificação cobre exclusivamente a implementação do Data Layer.

---

## 2. DECISÕES ARQUITETURAIS — NÃO NEGOCIÁVEIS

O agente deve respeitar estas decisões já tomadas:

| Decisão | Valor |
|---|---|
| Banco de dados | **SQLite** (fase atual). PostgreSQL é fase futura — não implementar agora. |
| Scheduler | **APScheduler** rodando como processo background autônomo. Airflow não. |
| Acesso ao banco | **Direto via Python** — sem API REST, sem JWT, sem OAuth2 nesta fase. |
| Append-only | Série temporal **nunca sobrescrita** — apenas INSERT, nunca UPDATE de histórico. |
| Linguagem | **Python 3.10+** |
| Ambiente dev | VS Code. O scheduler roda fora do VS Code em produção. |

---

## 3. ESTRUTURA DE PASTAS

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

---

## 4. SCHEMA DO BANCO — TABELAS POR DOMÍNIO

### 4.1 `preco_volume.db`

```sql
CREATE TABLE IF NOT EXISTS preco_volume (
    ticker          TEXT NOT NULL,
    data            DATE NOT NULL,
    abertura        REAL,
    maxima          REAL,
    minima          REAL,
    fechamento      REAL,
    fechamento_adj  REAL,
    volume          INTEGER,
    fonte           TEXT NOT NULL,        -- 'yfinance' | 'brapi'
    data_coleta     TIMESTAMP NOT NULL,
    flag_qualidade  INTEGER DEFAULT 1,    -- 1=ok, 0=suspeito
    PRIMARY KEY (ticker, data)
);
```

```sql
CREATE TABLE IF NOT EXISTS indicadores_compartilhados (
    ticker          TEXT NOT NULL,
    data            DATE NOT NULL,
    -- Tendência
    sma_20          REAL,
    sma_50          REAL,
    sma_200         REAL,
    ema_9           REAL,
    ema_21          REAL,
    -- Momentum
    rsi_14          REAL,
    macd            REAL,
    macd_signal     REAL,
    macd_hist       REAL,
    -- Volatilidade
    atr_14          REAL,
    bb_upper        REAL,
    bb_lower        REAL,
    bb_width        REAL,
    -- Volume
    vwap            REAL,
    obv             REAL,
    -- Posição relativa
    dist_sma200_pct REAL,               -- (preco - sma200) / sma200
    acima_vwap      INTEGER,            -- 1=acima, 0=abaixo
    data_calculo    TIMESTAMP NOT NULL,
    PRIMARY KEY (ticker, data)
);
```

```sql
CREATE TABLE IF NOT EXISTS fundamentals (
    ticker              TEXT NOT NULL,
    data_referencia     DATE NOT NULL,
    periodo             TEXT,           -- 'T1-2024', 'A-2023' etc
    receita_liquida     REAL,
    lucro_liquido       REAL,
    margem_liquida      REAL,
    roe                 REAL,
    divida_liquida      REAL,
    ebitda              REAL,
    earnings_surprise   REAL,
    fonte               TEXT NOT NULL,
    data_coleta         TIMESTAMP NOT NULL,
    PRIMARY KEY (ticker, data_referencia)
);
```

### 4.2 `macro.db`

```sql
CREATE TABLE IF NOT EXISTS macro_brasil (
    data            DATE NOT NULL,
    -- BCB/SGS
    selic_meta      REAL,
    selic_efetiva   REAL,
    ipca_mensal     REAL,
    ipca_acum_12m   REAL,
    igpm_mensal     REAL,
    cambio_usd_brl  REAL,
    -- Focus BCB
    focus_selic_fin REAL,              -- mediana expectativa Selic fim ano
    focus_ipca_ano  REAL,              -- mediana expectativa IPCA
    focus_dispersao_selic REAL,        -- desvio padrão das expectativas
    focus_dispersao_ipca  REAL,
    -- IBC-Br
    ibc_br          REAL,
    -- IBGE
    pib_trim        REAL,
    caged_saldo     INTEGER,
    fonte           TEXT NOT NULL,
    data_coleta     TIMESTAMP NOT NULL,
    PRIMARY KEY (data)
);
```

```sql
CREATE TABLE IF NOT EXISTS macro_global (
    data            DATE NOT NULL,
    -- Fed / EUA
    fed_funds_rate  REAL,
    us_10y_yield    REAL,
    dxy             REAL,              -- Dollar Index
    sp500           REAL,
    -- Commodities
    petroleo_wti    REAL,
    petroleo_brent  REAL,
    minério_ferro   REAL,
    cobre_lme       REAL,
    soja_cbot       REAL,
    milho_cbot      REAL,
    -- Baltic Dry Index
    bdi             REAL,
    fonte           TEXT NOT NULL,
    data_coleta     TIMESTAMP NOT NULL,
    PRIMARY KEY (data)
);
```

```sql
CREATE TABLE IF NOT EXISTS focus_bcb_historico (
    data_referencia DATE NOT NULL,
    indicador       TEXT NOT NULL,     -- 'selic', 'ipca', 'cambio', 'pib'
    horizonte       TEXT NOT NULL,     -- 'ano_corrente', 'ano_seguinte'
    mediana         REAL,
    media           REAL,
    desvio_padrao   REAL,
    minimo          REAL,
    maximo          REAL,
    data_coleta     TIMESTAMP NOT NULL,
    PRIMARY KEY (data_referencia, indicador, horizonte)
);
```

### 4.3 `alternativo.db`

```sql
CREATE TABLE IF NOT EXISTS temperatura_noticias (
    ticker          TEXT,              -- NULL = mercado geral
    data            DATE NOT NULL,
    hora_coleta     TIMESTAMP NOT NULL,
    score           REAL,              -- -1.0 a +1.0
    volume_noticias INTEGER,
    manchetes_raw   TEXT,              -- JSON array de manchetes
    modelo          TEXT NOT NULL,     -- 'gemini-2.5-flash'
    PRIMARY KEY (ticker, hora_coleta)
);
```

```sql
CREATE TABLE IF NOT EXISTS google_trends (
    termo           TEXT NOT NULL,
    data            DATE NOT NULL,
    valor           REAL,              -- 0-100 (índice relativo Google)
    data_coleta     TIMESTAMP NOT NULL,
    PRIMARY KEY (termo, data)
);
```

```sql
CREATE TABLE IF NOT EXISTS aneel_energia (
    data            DATE NOT NULL,
    consumo_mwh     REAL,
    variacao_12m    REAL,
    data_coleta     TIMESTAMP NOT NULL,
    PRIMARY KEY (data)
);
```

```sql
CREATE TABLE IF NOT EXISTS abpo_papelao (
    data            DATE NOT NULL,     -- primeiro dia do mês de referência
    producao_ton    REAL,
    variacao_12m    REAL,
    fonte_url       TEXT,
    data_coleta     TIMESTAMP NOT NULL,
    PRIMARY KEY (data)
);
```

```sql
CREATE TABLE IF NOT EXISTS iie_fgv (
    data            DATE NOT NULL,
    iie_total       REAL,
    iie_expectativa REAL,
    iie_situacao    REAL,
    desvio_historico REAL,             -- em quantos dp está do histórico
    data_coleta     TIMESTAMP NOT NULL,
    PRIMARY KEY (data)
);
```

### 4.4 `portfolio.db`

```sql
CREATE TABLE IF NOT EXISTS portfolio_estado (
    id_posicao      TEXT PRIMARY KEY,  -- UUID gerado na entrada
    ticker          TEXT NOT NULL,
    estilo          TEXT NOT NULL,     -- 'swing' | 'trend' | 'bnh'
    data_entrada    DATE NOT NULL,
    preco_entrada   REAL NOT NULL,
    quantidade      INTEGER NOT NULL,
    stop_atual      REAL,
    target          REAL,
    status          TEXT NOT NULL,     -- 'aberta' | 'fechada' | 'parcial'
    data_coleta     TIMESTAMP NOT NULL
);
```

```sql
CREATE TABLE IF NOT EXISTS scores_historico (
    ticker          TEXT NOT NULL,
    data            DATE NOT NULL,
    score_causa     REAL,              -- C1: -1.0 a +1.0
    score_expressao REAL,              -- C2: -1.0 a +1.0
    score_extracao  REAL,              -- C3: sizing sugerido
    trigger_barbell INTEGER DEFAULT 0, -- 0=não, 1=sim
    n_triggers      INTEGER DEFAULT 0, -- quantos triggers ativos
    data_calculo    TIMESTAMP NOT NULL,
    PRIMARY KEY (ticker, data)
);
```

---

## 5. MÓDULO `db/connection.py`

```python
# src/data_layer/db/connection.py

import sqlite3
from pathlib import Path
from typing import Literal

DB_ROOT = Path(__file__).resolve().parents[3] / "data" / "raw"

DB_MAP: dict[str, Path] = {
    "preco_volume": DB_ROOT / "preco_volume.db",
    "macro":        DB_ROOT / "macro.db",
    "alternativo":  DB_ROOT / "alternativo.db",
    "portfolio":    DB_ROOT / "portfolio.db",
}

def get_connection(
    domain: Literal["preco_volume", "macro", "alternativo", "portfolio"]
) -> sqlite3.Connection:
    """
    Retorna conexão SQLite para o domínio especificado.
    Cria o arquivo se não existir.
    row_factory = sqlite3.Row para acesso por nome de coluna.
    """
    path = DB_MAP[domain]
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
```

---

## 6. MÓDULO `db/schema.py`

Função única que cria todas as tabelas em todos os domínios:

```python
def create_all_tables() -> None:
    """
    Inicializa todos os bancos e cria todas as tabelas se não existirem.
    Idempotente — seguro chamar múltiplas vezes.
    """
    ...
```

Implementar usando `CREATE TABLE IF NOT EXISTS` com os schemas da Seção 4.

---

## 7. COLETORES — INTERFACE OBRIGATÓRIA

Cada arquivo em `collectors/` deve expor exatamente uma função pública:

```python
def coletar(tickers: list[str] | None = None) -> int:
    """
    Coleta dados da fonte correspondente e persiste no SQLite.
    Retorna número de registros inseridos.
    Nunca lança exceção para o caller — captura internamente e loga.
    Append-only: nunca faz UPDATE em registros existentes.
    Usa INSERT OR IGNORE para evitar duplicatas.
    """
```

### 7.1 `collectors/preco_volume.py`

- Fonte primária: `yfinance` — `yf.download(tickers, period, interval)`
- Fonte secundária: `brapi.dev` — endpoint `/api/quote/{ticker}`
- Fallback: se yfinance falhar para um ticker, tenta brapi
- Universo padrão: lista de tickers do Ibovespa (~80 ativos)
- Frequência de chamada: diária, após fechamento B3 (18h30)

### 7.2 `collectors/macro_brasil.py`

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

### 7.3 `collectors/macro_global.py`

- FRED API: `pip install fredapi` — séries DFF (fed funds), T10Y2Y (yield)
- yfinance para: DX-Y.NYB (DXY), ^GSPC (S&P500), CL=F (WTI), BZ=F (Brent)
- BDI: scraping ou API pública (documentar fonte escolhida)
- Commodities agrícolas: yfinance ZS=F (soja), ZC=F (milho)
- Minério de ferro: yfinance ou scraping (documentar)

### 7.4 `collectors/alternativo.py`

- Google Trends: `pip install pytrends` — termos configuráveis por ativo
- ANEEL: API pública de consumo industrial (stub aceitável se API indisponível)
- ABPO: **stub** — retornar `0` e logar aviso. Pipeline de PDF é Pendência 6.
- IIE-FGV: scraping do portal FGV (documentar URL)

### 7.5 `collectors/noticias.py`

- RSS: `pip install feedparser` — feeds configuráveis (Valor Econômico, Infomoney, Reuters Brasil)
- Temperatura: chamada à API Gemini 2.5 Flash para classificar manchetes em score -1.0 a +1.0
- Frequência: a cada 30 minutos
- Persistir em `temperatura_noticias` com `hora_coleta` como parte da PK

---

## 8. MÓDULO `scheduler.py`

```python
# src/data_layer/scheduler.py
"""
Entry point de produção do Data Layer.
Rodar como: python -m src.data_layer.scheduler
NÃO depende de VS Code — processo autônomo de background.
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BlockingScheduler(timezone="America/Sao_Paulo")
```

Agendamento obrigatório:

| Job | Trigger | Descrição |
|---|---|---|
| `preco_volume.coletar` | `cron(hour=18, minute=30)` | Diário após fechamento B3 |
| `macro_brasil.coletar` | `cron(hour=19, minute=0)` | Diário |
| `macro_global.coletar` | `cron(hour=19, minute=30)` | Diário |
| `alternativo.coletar` | `cron(day_of_week='mon', hour=8)` | Semanal |
| `noticias.coletar` | `interval(minutes=30)` | Contínuo |
| `calcular_indicadores` | `cron(hour=20, minute=0)` | Diário após preco_volume |

`calcular_indicadores` é uma função local no scheduler que lê `preco_volume`
e escreve em `indicadores_compartilhados` usando `pandas-ta` ou `ta-lib`.

---

## 9. MÓDULO `utils.py`

Funções obrigatórias:

```python
def validar_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Valida que OHLCV tem: abertura <= maxima, minima <= fechamento,
    volume >= 0, sem NaN em campos obrigatórios.
    Seta flag_qualidade=0 para linhas suspeitas — não descarta.
    """

def log_coleta(fonte: str, registros: int, erro: str | None = None) -> None:
    """
    Loga resultado de cada coleta em stdout estruturado:
    [TIMESTAMP] [FONTE] registros=N status=OK|ERRO erro=MSG
    """

def retry(func, tentativas: int = 3, espera_s: float = 5.0):
    """
    Decorator/wrapper para retry com backoff linear.
    Loga cada tentativa falhada antes de re-tentar.
    """
```

---

## 10. DEPENDÊNCIAS (`requirements.txt` — Data Layer)

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

---

## 11. DEFINIÇÃO DE PRONTO

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

**Critério de rejeição imediato:**
- Qualquer UPDATE em dados históricos (série temporal é imutável)
- Qualquer dependência de API REST para acesso interno ao banco
- Uso de PostgreSQL, Airflow ou Docker nesta fase
- Scheduler que exige VS Code aberto para rodar

---

*Especificação redigida para agente `plan` — Qwen3 Coder 480B A35B*  
*Base: decisões arquiteturais ADVANTAGE + api_plan.md (aproveitado: schema de tabelas e modelos Pydantic)*  
*Divergências do api_plan.md original: sem REST, sem JWT, sem Airflow, sem PostgreSQL*
