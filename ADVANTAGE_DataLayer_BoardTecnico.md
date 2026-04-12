# ADVANTAGE — Data Layer: Visão Técnica

---

## O que é

O Data Layer é a camada de infraestrutura de dados do sistema ADVANTAGE.
Ele funciona como **fonte única de verdade** para todos os processos que
operam no ecossistema — nenhum sistema acessa fonte externa diretamente.
Todo dado bruto passa pelo Data Layer antes de qualquer processamento.

---

## Arquitetura

O Data Layer é implementado em **Python 3.10+** com **SQLite** como
storage (migração para PostgreSQL prevista em fase futura). Roda como
processo autônomo de background via **APScheduler**, independente de
qualquer IDE ou sessão interativa.

A estrutura física é composta por quatro bancos separados por domínio:

| Banco | Conteúdo |
|---|---|
| `preco_volume.db` | OHLCV, fundamentals, indicadores técnicos, retornos, intraday (slot futuro) |
| `macro.db` | Ciclo global, ciclo local Brasil, Focus BCB, fluxo de investidores, commodities setoriais |
| `alternativo.db` | Google Trends, temperatura de notícias, dados setoriais brasileiros, Polymarket, documentos qualitativos |
| `portfolio.db` | Estado de portfólio, scores de CAUSA, taxa de conversão C1→C2 |

Todos os bancos operam em **modo WAL** (Write-Ahead Logging), que permite
múltiplos leitores simultâneos sem bloqueio — requisito para o ecossistema
multi-processo.

---

## Fontes de dados e cadência

| Frequência | Fontes |
|---|---|
| **30 minutos** | RSS financeiros (InfoMoney, Valor, Reuters, Bloomberg Línea) → temperatura de notícias via Gemini 2.5 Flash |
| **Diária** | yfinance (OHLCV Ibovespa), BCB SGS (Selic, câmbio, IPCA), FRED API (macro EUA), Yahoo Finance (commodities, VIX, DXY), Polymarket, Google Trends |
| **Semanal** | brapi.dev (fundamentals B3), Focus BCB (dispersão de expectativas) |
| **Mensal** | IBGE SIDRA 8889 (produção industrial / embalagens), MDIC (balança comercial), ANEEL, CAGED |

---

## Os três níveis de dado

O Data Layer organiza seus dados em três níveis com semânticas distintas:

**Nível 1 — Brutos**
Dados coletados diretamente das fontes sem transformação analítica.
OHLCV, séries macro, dados alternativos, notícias. Append-only —
nenhum registro histórico é sobrescrito.

**Nível 2 — Calculados**
Indicadores derivados dos brutos com parâmetros fixos e versionados,
calculados pelo próprio Data Layer. SMA 20/50/200, EMA 9/21, ATR 10/14/60,
RSI 14, MACD, VWAP, OBV, Bollinger Bands, retornos diários e logarítmicos,
máximas e mínimas dinâmicas 52 semanas e 3 anos, volume relativo.

A responsabilidade de calcular esses indicadores é do Data Layer — não
das camadas de análise — para garantir consistência de parâmetros entre
todos os processos que os consomem.

**Nível 3 — Interpretados**
Output das camadas analíticas armazenado no Data Layer para persistência
e auditoria. Scores de CAUSA (Camada 1), estado de portfólio, taxa de
conversão C1→C2, triggers de Barbell. Esses dados são escritos pelas
camadas de análise, não pelo pipeline de coleta.

---

## Interface de acesso

O acesso ao Data Layer é feito por **query SQL direta via Python**,
sem API REST intermediária. A interface é um módulo compartilhado:

```python
from src.data_layer.db.connection import get_connection_readonly

with get_connection_readonly("macro") as conn:
    df = pd.read_sql("SELECT * FROM macro_brasil WHERE data >= '2025-01-01'", conn)
```

Dois modos de conexão:

- `get_connection(domain)` — leitura e escrita. Uso exclusivo do scheduler
  e dos coletores do ADVANTAGE.
- `get_connection_readonly(domain)` — somente leitura. Interface oficial
  para todos os processos externos. Enforced a nível de driver SQLite
  via URI `?mode=ro` — não é convenção, é restrição técnica.

Processos externos que importam o módulo `connection.py` herdam
automaticamente o path correto dos bancos — sem duplicação de configuração.

---

## Regras invioláveis

1. **Append-only**: série temporal nunca é sobrescrita. Apenas INSERT,
   nunca UPDATE em dados históricos. Duplicatas são tratadas via
   `INSERT OR IGNORE`.

2. **Fonte única**: nenhum processo externo acessa APIs de dados
   diretamente. Todo dado passa pelo pipeline de coleta do Data Layer.

3. **Parâmetros versionados**: indicadores do Nível 2 são calculados
   com parâmetros registrados no campo `parametros_ver`. Mudança de
   parâmetro gera nova versão — não reprocessamento silencioso.

4. **Isolamento de escrita**: processos externos têm acesso somente
   leitura. Escrita é exclusiva do scheduler do ADVANTAGE e das camadas
   de análise nos seus respectivos domínios de output.

5. **Score de CAUSA intacto**: o score produzido pela Camada 1 passa
   para a Camada 3 sem reinterpretação pela Camada 2. A Camada 2
   confirma ou nega EXPRESSÃO — não altera CAUSA.

---

## Relevância para o Delta Chaos

O Delta Chaos pode consumir o Data Layer em dois níveis:

**Nível 1 e 2 — dados de mercado e indicadores técnicos**: volatilidade
realizada (ATR), VWAP, retornos, dados macro. Inputs diretos para
modelos de pricing de opções sem dependência do scoring do ADVANTAGE.

**Nível 3 — contexto de regime**: `score_causa`, `trigger_barbell`,
`classificacao` (risco_calculavel / incerteza_genuina). Permite que o
Delta Chaos ajuste exposição ou estratégia com base no regime
identificado pelo ADVANTAGE — sem replicar a lógica de scoring.

Em ambos os casos a interface é `get_connection_readonly` e o acesso
é local, sem latência de rede, sem autenticação, sem servidor intermediário.

---

*ADVANTAGE — Data Layer v3.1*
*Documento técnico para alinhamento de board*
