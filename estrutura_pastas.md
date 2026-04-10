# Estrutura de pastas do Data Layer

Esta é a estrutura de pastas que será criada para o Data Layer do ADVANTAGE, conforme especificado na v1:

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

Esta estrutura será criada no diretório C:\Users\tiago\OneDrive\Documentos\ATLAS\advantage