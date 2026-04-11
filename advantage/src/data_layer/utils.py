import pandas as pd
from datetime import datetime
import time
import functools
from typing import Callable, Any

def validar_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Valida que OHLCV tem: abertura <= maxima, minima <= fechamento,
    volume >= 0, sem NaN em campos obrigatórios.
    Seta flag_qualidade=0 para linhas suspeitas — não descarta.
    """
    if df.empty:
        return df
    
    # Criar cópia para não modificar o original
    df_validado = df.copy()
    
    # Verificar campos obrigatórios
    campos_obrigatorios = ['abertura', 'maxima', 'minima', 'fechamento', 'volume']
    
    # Adicionar coluna de flag_qualidade se não existir
    if 'flag_qualidade' not in df_validado.columns:
        df_validado['flag_qualidade'] = 1
    
    # Validar cada linha
    for idx, row in df_validado.iterrows():
        try:
            # Verificar campos obrigatórios
            for campo in campos_obrigatorios:
                if campo in row and pd.isna(row[campo]):
                    df_validado.loc[idx, 'flag_qualidade'] = 0
                    break
            
            # Verificar relações de preço
            if 'abertura' in row and 'maxima' in row:
                if row['abertura'] > row['maxima']:
                    df_validado.loc[idx, 'flag_qualidade'] = 0
            
            if 'minima' in row and 'fechamento' in row:
                if row['minima'] > row['fechamento']:
                    df_validado.loc[idx, 'flag_qualidade'] = 0
            
            # Verificar volume
            if 'volume' in row and row['volume'] < 0:
                df_validado.loc[idx, 'flag_qualidade'] = 0
                
        except Exception as e:
            # Em caso de erro na validação, marcar como suspeito
            df_validado.loc[idx, 'flag_qualidade'] = 0
    
    return df_validado

def log_coleta(fonte: str, registros: int, erro: str | None = None) -> None:
    """
    Loga resultado de cada coleta em stdout estruturado:
    [TIMESTAMP] [FONTE] registros=N status=OK|ERRO erro=MSG
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status = "ERRO" if erro else "OK"
    
    msg = f"[{timestamp}] [{fonte}] registros={registros} status={status}"
    if erro:
        msg += f" erro={erro}"
    
    print(msg)

def retry(tentativas: int = 3, espera_s: float = 5.0):
    """
    Decorator/wrapper para retry com backoff linear.
    Loga cada tentativa falhada antes de re-tentar.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            ultimo_erro = None
            
            for tentativa in range(tentativas):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    ultimo_erro = e
                    
                    if tentativa < tentativas - 1:  # Não logar na última tentativa
                        log_coleta(
                            fonte=func.__name__,
                            registros=0,
                            erro=f"Tentativa {tentativa + 1}/{tentativas} falhou: {str(e)}"
                        )
                        
                        # Aguardar antes da próxima tentativa
                        time.sleep(espera_s)
                    else:
                        # Última tentativa falhou
                        log_coleta(
                            fonte=func.__name__,
                            registros=0,
                            erro=f"Todas as {tentativas} tentativas falharam: {str(e)}"
                        )
            
            # Se chegou aqui, todas as tentativas falharam
            raise ultimo_erro
        
        return wrapper
    return decorator

def validar_data(data_str: str) -> bool:
    """Valida se uma string é uma data válida no formato YYYY-MM-DD"""
    try:
        datetime.strptime(data_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validar_ticker(ticker: str) -> bool:
    """Valida se um ticker tem formato válido (4-6 caracteres alfanuméricos)"""
    import re
    return bool(re.match(r"^[A-Z0-9]{4,6}$", ticker))

def formatar_moeda(valor: float) -> str:
    """Formata valor monetário para exibição"""
    if valor is None:
        return "N/A"
    return f"R$ {valor:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')

def calcular_variacao_percentual(valor_atual: float, valor_anterior: float) -> float:
    """Calcula variação percentual entre dois valores"""
    if valor_anterior is None or valor_anterior == 0:
        return 0.0
    return ((valor_atual - valor_anterior) / valor_anterior) * 100