"""
Entry point de produção do Data Layer.
Rodar como: python -m src.data_layer.scheduler
NÃO depende de VS Code — processo autônomo de background.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime
import sys
import os
import math

# Adicionar o caminho do projeto ao sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Importar coletores
try:
    from .collectors.preco_volume import coletar as coletar_preco_volume
    from .collectors.macro_brasil import coletar as coletar_macro_brasil
    from .collectors.macro_global import coletar as coletar_macro_global
    from .collectors.alternativo import coletar as coletar_alternativo
    from .collectors.noticias import coletar as coletar_noticias
    from .collectors.polymarket import coletar as coletar_polymarket
except ImportError:
    # Fallback para importação alternativa
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from src.data_layer.collectors.preco_volume import coletar as coletar_preco_volume
    from src.data_layer.collectors.macro_brasil import coletar as coletar_macro_brasil
    from src.data_layer.collectors.macro_global import coletar as coletar_macro_global
    from src.data_layer.collectors.alternativo import coletar as coletar_alternativo
    from src.data_layer.collectors.noticias import coletar as coletar_noticias
    from src.data_layer.collectors.polymarket import coletar as coletar_polymarket

# Variável global para o scheduler - acessível aos handlers
cscheduler = None

def calcular_indicadores() -> int:
    """
    Calcula indicadores técnicos sobre dados de preço e volume.
    Lê da tabela preco_volume e escreve em indicadores_compartilhados.
    Retorna número de registros processados.
    """
    try:
        from .db.connection import get_connection
        import pandas as pd
        import pandas_ta as ta

        conn = get_connection("preco_volume")

        # Ler dados mais recentes da tabela preco_volume
        df = pd.read_sql("""
        SELECT ticker, data, abertura, maxima, minima, fechamento, volume
        FROM preco_volume
        WHERE flag_qualidade = 1
        ORDER BY data DESC
        LIMIT 1000
        """, conn)

        if df.empty:
            print(f"[{datetime.now()}] [calcular_indicadores] Nenhum dado disponível")
            return 0

        registros_processados = 0

        # Calcular indicadores para cada ticker
        tickers = df['ticker'].unique()
        for ticker in tickers:
            try:
                # Filtrar dados do ticker específico
                df_ticker = df[df['ticker'] == ticker].sort_values('data')

                if len(df_ticker) < 20:  # Mínimo de dados para calcular indicadores
                    continue

# Calcular indicadores técnicos
    # SMA (Simple Moving Average)
    sma_20 = ta.sma(df_ticker['fechamento'], length=20)
    sma_50 = ta.sma(df_ticker['fechamento'], length=50)
    sma_200 = ta.sma(df_ticker['fechamento'], length=200)

    # EMA (Exponential Moving Average)
    ema_9 = ta.ema(df_ticker['fechamento'], length=9)
    ema_21 = ta.ema(df_ticker['fechamento'], length=21)

    # RSI (Relative Strength Index)
    rsi_14 = ta.rsi(df_ticker['fechamento'], length=14)

    # MACD
    macd_result = ta.macd(df_ticker['fechamento'])

    # ATR (Average True Range)
    atr_14 = ta.atr(df_ticker['maxima'], df_ticker['minima'], df_ticker['fechamento'], length=14)
    atr_60 = ta.atr(df_ticker['maxima'], df_ticker['minima'], df_ticker['fechamento'], length=60)

    # Bollinger Bands
    bb_result = ta.bbands(df_ticker['fechamento'], length=20)

    # VWAP (Volume Weighted Average Price)
    vwap = ta.vwap(df_ticker['maxima'], df_ticker['minima'], df_ticker['fechamento'], df_ticker['volume'])

    # OBV (On-Balance Volume)
    obv = ta.obv(df_ticker['fechamento'], df_ticker['volume'])

    # Calcular distância da SMA200
    dist_sma200_pct = (df_ticker['fechamento'] - sma_200) / sma_200

    # Verificar se está acima do VWAP
    acima_vwap = (df_ticker['fechamento'] > vwap).astype(int)

    # Volume médio
    vol_media_20 = df_ticker['volume'].rolling(window=20).mean()
    vol_media_60 = df_ticker['volume'].rolling(window=60).mean()

    # Máximas e mínimas
    maxima_52s = df_ticker['fechamento'].rolling(window=252).max()
    minima_52s = df_ticker['fechamento'].rolling(window=252).min()
    maxima_3a = df_ticker['fechamento'].rolling(window=756).max()
    minima_3a = df_ticker['fechamento'].rolling(window=756).min()

# Inserir indicadores calculados
    for idx, row in df_ticker.iterrows():
        if pd.notna(sma_20.iloc[idx]) and pd.notna(rsi_14.iloc[idx]):
            conn.execute("""INSERT OR IGNORE INTO indicadores_compartilhados
            (ticker, data, sma_20, sma_50, sma_200, ema_9, ema_21, 
            rsi_14, macd, macd_signal, macd_hist, atr_14, atr_60,
            bb_upper, bb_lower, bb_width, vwap, obv, 
            dist_sma200_pct, acima_vwap, vol_media_20, vol_media_60,
            maxima_52s, minima_52s, maxima_3a, minima_3a, parametros_ver, data_calculo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                ticker,
                row['data'],
                float(sma_20.iloc[idx]) if pd.notna(sma_20.iloc[idx]) else None,
                float(sma_50.iloc[idx]) if pd.notna(sma_50.iloc[idx]) else None,
                float(sma_200.iloc[idx]) if pd.notna(sma_200.iloc[idx]) else None,
                float(ema_9.iloc[idx]) if pd.notna(ema_9.iloc[idx]) else None,
                float(ema_21.iloc[idx]) if pd.notna(ema_21.iloc[idx]) else None,
                float(rsi_14.iloc[idx]) if pd.notna(rsi_14.iloc[idx]) else None,
                float(macd_result['MACD_12_26_9'].iloc[idx]) if pd.notna(macd_result['MACD_12_26_9'].iloc[idx]) else None,
                float(macd_result['MACDs_12_26_9'].iloc[idx]) if pd.notna(macd_result['MACDs_12_26_9'].iloc[idx]) else None,
                float(macd_result['MACDh_12_26_9'].iloc[idx]) if pd.notna(macd_result['MACDh_12_26_9'].iloc[idx]) else None,
                float(atr_14.iloc[idx]) if pd.notna(atr_14.iloc[idx]) else None,
                float(atr_60.iloc[idx]) if pd.notna(atr_60.iloc[idx]) else None,
                float(bb_result['BBU_20_2.0'].iloc[idx]) if pd.notna(bb_result['BBU_20_2.0'].iloc[idx]) else None,
                float(bb_result['BBL_20_2.0'].iloc[idx]) if pd.notna(bb_result['BBL_20_2.0'].iloc[idx]) else None,
                float(bb_result['BBW_20_2.0'].iloc[idx]) if pd.notna(bb_result['BBW_20_2.0'].iloc[idx]) else None,
                float(vwap.iloc[idx]) if pd.notna(vwap.iloc[idx]) else None,
                float(obv.iloc[idx]) if pd.notna(obv.iloc[idx]) else None,
                float(dist_sma200_pct.iloc[idx]) if pd.notna(dist_sma200_pct.iloc[idx]) else None,
                int(acima_vwap.iloc[idx]) if pd.notna(acima_vwap.iloc[idx]) else None,
                float(vol_media_20.iloc[idx]) if pd.notna(vol_media_20.iloc[idx]) else None,
                float(vol_media_60.iloc[idx]) if pd.notna(vol_media_60.iloc[idx]) else None,
                float(maxima_52s.iloc[idx]) if pd.notna(maxima_52s.iloc[idx]) else None,
                float(minima_52s.iloc[idx]) if pd.notna(minima_52s.iloc[idx]) else None,
                float(maxima_3a.iloc[idx]) if pd.notna(maxima_3a.iloc[idx]) else None,
                float(minima_3a.iloc[idx]) if pd.notna(minima_3a.iloc[idx]) else None,
                "v1.0",  # parametros_ver
                datetime.now()
            ))
            registros_processados += conn.rowcount
            
            # Calcular retornos históricos
            if idx > 0:  # Não calcula para o primeiro registro
                # Retorno diário
                retorno_diario = (row['fechamento'] / df_ticker.iloc[idx-1]['fechamento']) - 1
                
                # Retorno logarítmico
                retorno_log = math.log(row['fechamento'] / df_ticker.iloc[idx-1]['fechamento'])
                
                # Inserir retornos históricos
                conn.execute("""INSERT OR IGNORE INTO retornos_historicos
                (ticker, data, retorno_diario, retorno_log, data_calculo)
                VALUES (?, ?, ?, ?, ?)""", (
                    ticker,
                    row['data'],
                    float(retorno_diario) if pd.notna(retorno_diario) else None,
                    float(retorno_log) if pd.notna(retorno_log) else None,
                    datetime.now()
                ))
                registros_processados += conn.rowcount

            except Exception as e:
                print(f"[{datetime.now()}] [calcular_indicadores] Erro no ticker {ticker}: {e}")
                continue

        conn.commit()
        print(f"[{datetime.now()}] [calcular_indicadores] Processados {registros_processados} registros")
        return registros_processados

    except Exception as e:
        print(f"[{datetime.now()}] [calcular_indicadores] Erro geral: {e}")
        return 0
    finally:
        if 'conn' in locals():
            conn.close()

def log_job_execution(job_name: str, registros: int, erro: str = None):
    """Loga execução de jobs do scheduler"""
    status = "ERRO" if erro else "OK"
    msg = f"[{datetime.now()}] [SCHEDULER] {job_name} registros={registros} status={status}"
    if erro:
        msg += f" erro={erro}"
    print(msg)

def verificar_jobs_perdidos():
    """
    Verifica e loga jobs que foram perdidos durante período offline.
    Executa automaticamente jobs dentro da janela de 2 meses.
    """
    from apscheduler.job import Job

    # Verificar se scheduler foi inicializado
    if cscheduler is None:
        return

    try:
        jobs = cscheduler.get_jobs()
        jobs_perdidos = []
        
        for job in jobs:
            next_run_time = job.next_run_time
            if next_run_time and next_run_time < datetime.now():
                jobs_perdidos.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': next_run_time
                })
        
        if jobs_perdidos:
            print(f"[{datetime.now()}] [SCHEDULER] ═══════════════════════════════════════════")
            print(f"[{datetime.now()}] [SCHEDULER] ⚠️ JOBS PERDIDOS DETECTADOS")
            print(f"[{datetime.now()}] [SCHEDULER] ═══════════════════════════════════════════")
            
            for job_info in jobs_perdidos:
                print(f"[{datetime.now()}] [SCHEDULER] 📋 Job: {job_info['name']}")
                print(f"[{datetime.now()}] [SCHEDULER] 📅 Deveria executar: {job_info['next_run_time']}")
                print(f"[{datetime.now()}] [SCHEDULER] 🔄 Status: Será executado automaticamente")
            
            print(f"[{datetime.now()}] [SCHEDULER] ═══════════════════════════════════════════")
            
    except Exception as e:
        print(f"[{datetime.now()}] [SCHEDULER] Erro ao verificar jobs perdidos: {e}")

def main():
    """Função principal do scheduler"""
    print(f"[{datetime.now()}] [SCHEDULER] Iniciando ADVANTAGE Data Layer Scheduler")
    
    # Criar diretório para persistência de jobs
    os.makedirs('data', exist_ok=True)

    # Configurar jobstore persistente
    jobstores = {
        'default': SQLAlchemyJobStore(
            url='sqlite:///data/jobs.sqlite',
            tablename='scheduled_jobs'
        )
    }

    # Configurar executores
    executors = {
        'default': ThreadPoolExecutor(20)
    }

    # Configurar padrões de job
    job_defaults = {
        'coalesce': True, # Executa apenas uma vez se múltiplos jobs perdidos
        'max_instances': 1, # Evita execução paralela
        'misfire_grace_time': 5184000 # 60 dias (2 meses) em segundos
    }

# Criar scheduler persistente
global cscheduler
cscheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone="America/Sao_Paulo"
)

# Configurar executores
executors = {
    'default': ThreadPoolExecutor(20)
}

# Configurar padrões de job
job_defaults = {
    'coalesce': True, # Executa apenas uma vez se múltiplos jobs perdidos
    'max_instances': 1, # Evita execução paralela
    'misfire_grace_time': 5184000 # 60 dias (2 meses) em segundos
}

# Criar scheduler persistente
scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone="America/Sao_Paulo"
)

# Configurar executores
executors = {
    'default': ThreadPoolExecutor(20)
}

# Configurar padrões de job
job_defaults = {
    'coalesce': True, # Executa apenas uma vez se múltiplos jobs perdidos
    'max_instances': 1, # Evita execução paralela
    'misfire_grace_time': 5184000 # 60 dias (2 meses) em segundos
}

# Criar scheduler persistente
scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone="America/Sao_Paulo"
)

# Configurar executores
executors = {
    'default': ThreadPoolExecutor(20)
}

# Configurar padrões de job
job_defaults = {
    'coalesce': True, # Executa apenas uma vez se múltiplos jobs perdidos
    'max_instances': 1, # Evita execução paralela
    'misfire_grace_time': 5184000 # 60 dias (2 meses) em segundos
}

# Criar scheduler persistente
scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone="America/Sao_Paulo"
)

    # Agendar jobs conforme especificação

    # Preço e Volume - Diário após fechamento B3 (18h30)
    @scheduler.scheduled_job(CronTrigger(hour=18, minute=30))
    def job_preco_volume():
        try:
            registros = coletar_preco_volume()
            log_job_execution("preco_volume", registros)
        except Exception as e:
            log_job_execution("preco_volume", 0, str(e))

    # Macro Brasil - Diário (19h00)
    @scheduler.scheduled_job(CronTrigger(hour=19, minute=0))
    def job_macro_brasil():
        try:
            registros = coletar_macro_brasil()
            log_job_execution("macro_brasil", registros)
        except Exception as e:
            log_job_execution("macro_brasil", 0, str(e))

    # Macro Global - Diário (19h30)
    @scheduler.scheduled_job(CronTrigger(hour=19, minute=30))
    def job_macro_global():
        try:
            registros = coletar_macro_global()
            log_job_execution("macro_global", registros)
        except Exception as e:
            log_job_execution("macro_global", 0, str(e))

    # Alternativo - Semanal (segunda-feira 08h00)
    @scheduler.scheduled_job(CronTrigger(day_of_week='mon', hour=8))
    def job_alternativo():
        try:
            registros = coletar_alternativo()
            log_job_execution("alternativo", registros)
        except Exception as e:
            log_job_execution("alternativo", 0, str(e))

    # Notícias - Contínuo (a cada 30 minutos)
    @scheduler.scheduled_job(IntervalTrigger(minutes=30))
    def job_noticias():
        try:
            registros = coletar_noticias()
            log_job_execution("noticias", registros)
        except Exception as e:
            log_job_execution("noticias", 0, str(e))

    # Calcular Indicadores - Diário após preco_volume (20h00)
    @scheduler.scheduled_job(CronTrigger(hour=20, minute=0))
    def job_calcular_indicadores():
        try:
            registros = calcular_indicadores()
            log_job_execution("calcular_indicadores", registros)
        except Exception as e:
            log_job_execution("calcular_indicadores", 0, str(e))

    # Polymarket Diário - Diário (19h45) após macro_global
    @scheduler.scheduled_job(CronTrigger(hour=19, minute=45))
    def job_polymarket():
        try:
            registros = coletar_polymarket()
            log_job_execution("polymarket", registros)
        except Exception as e:
            log_job_execution("polymarket", 0, str(e))

    # IBGE Embalagens Mensal - Mensal (dia 1, 08h00)
    @scheduler.scheduled_job(CronTrigger(day=1, hour=8, minute=0))
    def job_ibge_embalagens_mensal():
        try:
            registros = coletar_alternativo()  # Esta função já inclui a coleta de embalagens
            log_job_execution("ibge_embalagens_mensal", registros)
        except Exception as e:
            log_job_execution("ibge_embalagens_mensal", 0, str(e))

    # IBGE Atividade Mensal - Mensal (dia 1, 08h15)
    @scheduler.scheduled_job(CronTrigger(day=1, hour=8, minute=15))
    def job_ibge_atividade_mensal():
        try:
            registros = coletar_alternativo()  # Esta função já inclui a coleta de atividade
            log_job_execution("ibge_atividade_mensal", registros)
        except Exception as e:
            log_job_execution("ibge_atividade_mensal", 0, str(e))

# Iniciar scheduler
print(f"[{datetime.now()}] [SCHEDULER] Jobs agendados:")
print("- preco_volume: 18h30 diário")
print("- macro_brasil: 19h00 diário")
print("- macro_global: 19h30 diário")
print("- polymarket: 19h45 diário")
print("- alternativo: segunda-feira 08h00")
print("- ibge_embalagens_mensal: dia 1, 08h00")
print("- ibge_atividade_mensal: dia 1, 08h15")
print("- noticias: a cada 30 minutos")
print("- calcular_indicadores: 20h00 diário")
print(f"[{datetime.now()}] [SCHEDULER] Scheduler rodando...")

def signal_handler(signum, frame):
    """
    Handler para shutdown gracioso do scheduler.
    """
    # Verificar se scheduler foi inicializado
    if cscheduler is None:
        return

    print(f"[{datetime.now()}] [SCHEDULER] ═══════════════════════════════════════════")
    print(f"[{datetime.now()}] [SCHEDULER] 🛑 SINAL DE INTERRUPÇÃO RECEBIDO")
    print(f"[{datetime.now()}] [SCHEDULER] ═══════════════════════════════════════════")
    print(f"[{datetime.now()}] [SCHEDULER] 💾 Salvando estado dos jobs...")
    cscheduler.shutdown(wait=True)
    print(f"[{datetime.now()}] [SCHEDULER] ✅ Scheduler encerrado com segurança")
    sys.exit(0)

# Registrar handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

try:
    # Verificar jobs perdidos na inicialização
    verificar_jobs_perdidos()

    # Iniciar scheduler
    print(f"[{datetime.now()}] [SCHEDULER] ═════════════════════════════════════════════════════════")
    print(f"[{datetime.now()}] [SCHEDULER] 🚀 ADVANTAGE Data Layer Scheduler - MODO PERSISTENTE")
    print(f"[{datetime.now()}] [SCHEDULER] ═════════════════════════════════════════════════════════")
    print(f"[{datetime.now()}] [SCHEDULER] 📁 Jobstore: data/jobs.sqlite")
    print(f"[{datetime.now()}] [SCHEDULER] ⏰ Janela de recuperação: 2 meses")
    print(f"[{datetime.now()}] [SCHEDULER] 🔄 Jobs perdidos: Executados automaticamente")
    print(f"[{datetime.now()}] [SCHEDULER] ═════════════════════════════════════════════════════════")

    cscheduler.start()
except KeyboardInterrupt:
    print(f"[{datetime.now()}] [SCHEDULER] Scheduler interrompido")
except Exception as e:
    print(f"[{datetime.now()}] [SCHEDULER] Erro fatal: {e}")

if __name__ == "__main__":
    main()
