def create_all_tables() -> None:
    """
    Inicializa todos os bancos e cria todas as tabelas se não existirem.
    Idempotente — seguro chamar múltiplas vezes.
    """
    # Importações necessárias
    from .connection import get_connection
    import sqlite3
    
    # Criar tabelas para preco_volume.db
    conn = get_connection("preco_volume")
    try:
        # Tabela preco_volume
        conn.execute("""
        CREATE TABLE IF NOT EXISTS preco_volume (
            ticker          TEXT NOT NULL,
            data            DATE NOT NULL,
            abertura        REAL,
            maxima          REAL,
            minima          REAL,
            fechamento      REAL,
            fechamento_adj  REAL,
            volume          INTEGER,
            fonte           TEXT NOT NULL,
            data_coleta     TIMESTAMP NOT NULL,
            flag_qualidade  INTEGER DEFAULT 1,
            PRIMARY KEY (ticker, data)
        )
        """)
        
        # Tabela indicadores_compartilhados
        conn.execute("""
        CREATE TABLE IF NOT EXISTS indicadores_compartilhados (
            ticker          TEXT NOT NULL,
            data            DATE NOT NULL,
            sma_20          REAL,
            sma_50          REAL,
            sma_200         REAL,
            ema_9           REAL,
            ema_21          REAL,
            rsi_14          REAL,
            macd            REAL,
            macd_signal     REAL,
            macd_hist       REAL,
            atr_14          REAL,
            bb_upper        REAL,
            bb_lower        REAL,
            bb_width        REAL,
            vwap            REAL,
            obv             REAL,
            dist_sma200_pct REAL,
            acima_vwap      INTEGER,
            data_calculo    TIMESTAMP NOT NULL,
            PRIMARY KEY (ticker, data)
        )
        """)
        
        # Tabela fundamentals
        conn.execute("""
        CREATE TABLE IF NOT EXISTS fundamentals (
            ticker              TEXT NOT NULL,
            data_referencia     DATE NOT NULL,
            periodo             TEXT,
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
        )
        """)
        
        conn.commit()
    finally:
        conn.close()
    
    # Criar tabelas para macro.db
    conn = get_connection("macro")
    try:
        # Tabela macro_brasil
        conn.execute("""
        CREATE TABLE IF NOT EXISTS macro_brasil (
            data            DATE NOT NULL,
            selic_meta      REAL,
            selic_efetiva   REAL,
            ipca_mensal     REAL,
            ipca_acum_12m   REAL,
            igpm_mensal     REAL,
            cambio_usd_brl  REAL,
            focus_selic_fin REAL,
            focus_ipca_ano  REAL,
            focus_dispersao_selic REAL,
            focus_dispersao_ipca  REAL,
            ibc_br          REAL,
            pib_trim        REAL,
            caged_saldo     INTEGER,
            fonte           TEXT NOT NULL,
            data_coleta     TIMESTAMP NOT NULL,
            PRIMARY KEY (data)
        )
        """)
        
        # Tabela macro_global
        conn.execute("""
        CREATE TABLE IF NOT EXISTS macro_global (
            data            DATE NOT NULL,
            fed_funds_rate  REAL,
            us_10y_yield    REAL,
            dxy             REAL,
            sp500           REAL,
            petroleo_wti    REAL,
            petroleo_brent  REAL,
            minério_ferro   REAL,
            cobre_lme       REAL,
            soja_cbot       REAL,
            milho_cbot      REAL,
            bdi             REAL,
            fonte           TEXT NOT NULL,
            data_coleta     TIMESTAMP NOT NULL,
            PRIMARY KEY (data)
        )
        """)
        
        # Tabela focus_bcb_historico
        conn.execute("""
        CREATE TABLE IF NOT EXISTS focus_bcb_historico (
            data_referencia DATE NOT NULL,
            indicador       TEXT NOT NULL,
            horizonte       TEXT NOT NULL,
            mediana         REAL,
            media           REAL,
            desvio_padrao   REAL,
            minimo          REAL,
            maximo          REAL,
            data_coleta     TIMESTAMP NOT NULL,
            PRIMARY KEY (data_referencia, indicador, horizonte)
        )
        """)
        
        conn.commit()
    finally:
        conn.close()
    
    # Criar tabelas para alternativo.db
    conn = get_connection("alternativo")
    try:
        # Tabela temperatura_noticias
        conn.execute("""
        CREATE TABLE IF NOT EXISTS temperatura_noticias (
            ticker          TEXT,
            data            DATE NOT NULL,
            hora_coleta     TIMESTAMP NOT NULL,
            score           REAL,
            volume_noticias INTEGER,
            manchetes_raw   TEXT,
            modelo          TEXT NOT NULL,
            PRIMARY KEY (ticker, hora_coleta)
        )
        """)
        
        # Tabela google_trends
        conn.execute("""
        CREATE TABLE IF NOT EXISTS google_trends (
            termo           TEXT NOT NULL,
            data            DATE NOT NULL,
            valor           REAL,
            data_coleta     TIMESTAMP NOT NULL,
            PRIMARY KEY (termo, data)
        )
        """)
        
        # Tabela aneel_energia
        conn.execute("""
        CREATE TABLE IF NOT EXISTS aneel_energia (
            data            DATE NOT NULL,
            consumo_mwh     REAL,
            variacao_12m    REAL,
            data_coleta     TIMESTAMP NOT NULL,
            PRIMARY KEY (data)
        )
        """)
        
        # Tabela abpo_papelao
        conn.execute("""
        CREATE TABLE IF NOT EXISTS abpo_papelao (
            data            DATE NOT NULL,
            producao_ton    REAL,
            variacao_12m    REAL,
            fonte_url       TEXT,
            data_coleta     TIMESTAMP NOT NULL,
            PRIMARY KEY (data)
        )
        """)
        
        # Tabela iie_fgv
        conn.execute("""
        CREATE TABLE IF NOT EXISTS iie_fgv (
            data            DATE NOT NULL,
            iie_total       REAL,
            iie_expectativa REAL,
            iie_situacao    REAL,
            desvio_historico REAL,
            data_coleta     TIMESTAMP NOT NULL,
            PRIMARY KEY (data)
        )
        """)
        
        conn.commit()
    finally:
        conn.close()
    
    # Criar tabelas para portfolio.db
    conn = get_connection("portfolio")
    try:
        # Tabela portfolio_estado
        conn.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_estado (
            id_posicao      TEXT PRIMARY KEY,
            ticker          TEXT NOT NULL,
            estilo          TEXT NOT NULL,
            data_entrada    DATE NOT NULL,
            preco_entrada   REAL NOT NULL,
            quantidade      INTEGER NOT NULL,
            stop_atual      REAL,
            target          REAL,
            status          TEXT NOT NULL,
            data_coleta     TIMESTAMP NOT NULL
        )
        """)
        
        # Tabela scores_historico
        conn.execute("""
        CREATE TABLE IF NOT EXISTS scores_historico (
            ticker          TEXT NOT NULL,
            data            DATE NOT NULL,
            score_causa     REAL,
            score_expressao REAL,
            score_extracao  REAL,
            trigger_barbell INTEGER DEFAULT 0,
            n_triggers      INTEGER DEFAULT 0,
            data_calculo    TIMESTAMP NOT NULL,
            PRIMARY KEY (ticker, data)
        )
        """)
        
        conn.commit()
    finally:
        conn.close()