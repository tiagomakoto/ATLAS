import requests
import pandas as pd
from typing import List, Optional
import sqlite3
from datetime import datetime, timedelta
import time
import traceback
import re
from src.data_layer.db.connection import get_connection
from pytrends.request import TrendReq
import pdfplumber
from bs4 import BeautifulSoup
import tempfile
import os

# Lista de termos para monitorar no Google Trends
# 20 ativos de maior liquidez do Ibovespa + termos macroeconômicos
GOOGLE_TRENDS_TERMOS = [
    "Vale", "Petrobras", "Itaú", "Bradesco", "Banco do Brasil",
    "Ambev", "Weg", "Itaúsa", "Cielo", "Braskem",
    "Selic", "inflação Brasil", "dólar real", "IBOV", "Bolsa",
    "Magazine Luiza", "Vivo", "TIM", "Oi", "Lojas Renner"
]

def extrair_producao_papel_celulose(texto_pdf: str) -> dict:
    """
    Extrai dados de produção de papel e celulose do texto do PDF.
    Retorna dict com producao_ton e variacao_12m se encontrados.
    """
    resultado = {
        'producao_ton': None,
        'variacao_12m': None
    }
    
    # Padrões comuns em relatórios da ABPO
    # Produção total de papel - captura número e unidade separadamente
    # Nota: ordem importante - milhão antes de mil para evitar match parcial
    padroes_producao = [
        r'produção\s+de\s+papel[:\s]*([\d,\.]+)\s*(milhões?|milhoes|mil|toneladas|t)',
        r'produção\s+total[:\s]*([\d,\.]+)\s*(milhões?|milhoes|mil|toneladas|t)',
        r'papel\s+produzido[:\s]*([\d,\.]+)\s*(milhões?|milhoes|mil|toneladas|t)',
        r'produção\s+de\s+celulose[:\s]*([\d,\.]+)\s*(milhões?|milhoes|mil|toneladas|t)',
        r'celulose\s+produzida[:\s]*([\d,\.]+)\s*(milhões?|milhoes|mil|toneladas|t)'
    ]
    
    # Variação percentual
    padroes_variacao = [
        r'variação\s+de\s+[\d\.]+\s*%[:\s]*([+-]?[\d\.]+)\s*%',
        r'crescimento\s+de\s+[\d\.]+\s*%[:\s]*([+-]?[\d\.]+)\s*%',
        r'queda\s+de\s+[\d\.]+\s*%[:\s]*([+-]?[\d\.]+)\s*%',
        r'[\d\.]+\s*%\s*(?:vs\.?|versus)\s*[\d\.]+\s*%[:\s]*([+-]?[\d\.]+)\s*%',
        r'variação\s+em\s+12\s+meses[:\s]*([+-]?[\d,\.]+)\s*%',
        r'[\d\.]+\s*%\s*\(12\s+meses\)',
        # Padrões simples: "Crescimento de X%" ou "Variação de X%"
        r'crescimento\s+de\s+([+-]?[\d,\.]+)\s*%',
        r'variação\s+de\s+([+-]?[\d,\.]+)\s*%',
        r'queda\s+de\s+([+-]?[\d,\.]+)\s*%'
    ]
    
    texto_lower = texto_pdf.lower()
    
    # Buscar produção
    for padrao in padroes_producao:
        match = re.search(padrao, texto_lower, re.IGNORECASE)
        if match:
            valor_str = match.group(1)
            unidade = match.group(2).lower() if len(match.groups()) >= 2 else ''
            try:
                # Limpar o valor
                valor_str_limpo = valor_str.strip()
                # Se unidade é 'mil' (milhar), remover pontos (separadores de milhar) e substituir vírgula por ponto
                if unidade == 'mil':
                    valor_str_limpo = valor_str_limpo.replace('.', '').replace(',', '.')
                else:
                    # Para 'milhão' ou 'toneladas', apenas substituir vírgula por ponto (decimal)
                    valor_str_limpo = valor_str_limpo.replace(',', '.')
                
                valor = float(valor_str_limpo)
                # Converter para toneladas conforme unidade
                if unidade.startswith('milh') or 'milhoes' in unidade:
                    valor *= 1_000_000
                elif unidade == 'mil':
                    valor *= 1_000
                # Se já está em toneladas, mantém
                resultado['producao_ton'] = valor
                break
            except:
                continue
    
    # Buscar variação
    for padrao in padroes_variacao:
        match = re.search(padrao, texto_lower, re.IGNORECASE)
        if match:
            try:
                valor_str = match.group(1).replace(',', '.')
                valor = float(valor_str)
                resultado['variacao_12m'] = valor
                break
            except:
                continue
    
    return resultado

import requests
import pandas as pd
from typing import List, Optional
import sqlite3
from datetime import datetime, timedelta
import time
import traceback
import re
from src.data_layer.db.connection import get_connection
from pytrends.request import TrendReq
import pdfplumber
from bs4 import BeautifulSoup
import tempfile
import os

# Lista de termos para monitorar no Google Trends
# 20 ativos de maior liquidez do Ibovespa + termos macroeconômicos
GOOGLE_TRENDS_TERMOS = [
    "Vale", "Petrobras", "Itaú", "Bradesco", "Banco do Brasil",
    "Ambev", "Weg", "Itaúsa", "Cielo", "Braskem",
    "Selic", "inflação Brasil", "dólar real", "IBOV", "Bolsa",
    "Magazine Luiza", "Vivo", "TIM", "Oi", "Lojas Renner"
]

def extrair_producao_papel_celulose(texto_pdf: str) -> dict:
    """
    Extrai dados de produção de papel e celulose do texto do PDF.
    Retorna dict com producao_ton e variacao_12m se encontrados.
    """
    resultado = {
        'producao_ton': None,
        'variacao_12m': None
    }

    # Padrões comuns em relatórios da ABPO
    # Produção total de papel - captura número e unidade separadamente
    # Nota: ordem importante - milhão antes de mil para evitar match parcial
    padroes_producao = [
        r'produção\s+de\s+papel[:\s]*([\d,\.]+)\s*(milhões?|milhoes|mil|toneladas|t)',
        r'produção\s+total[:\s]*([\d,\.]+)\s*(milhões?|milhoes|mil|toneladas|t)',
        r'papel\s+produzido[:\s]*([\d,\.]+)\s*(milhões?|milhoes|mil|toneladas|t)',
        r'produção\s+de\s+celulose[:\s]*([\d,\.]+)\s*(milhões?|milhoes|mil|toneladas|t)',
        r'celulose\s+produzida[:\s]*([\d,\.]+)\s*(milhões?|milhoes|mil|toneladas|t)'
    ]

    # Variação percentual
    padroes_variacao = [
        r'variação\s+de\s+[\d\.]+\s*%[:\s]*([+-]?[\d\.]+)\s*%',
        r'crescimento\s+de\s+[\d\.]+\s*%[:\s]*([+-]?[\d\.]+)\s*%',
        r'queda\s+de\s+[\d\.]+\s*%[:\s]*([+-]?[\d\.]+)\s*%',
        r'[\d\.]+\s*%\s*(?:vs\.?|versus)\s*[\d\.]+\s*%[:\s]*([+-]?[\d\.]+)\s*%',
        r'variação\s+em\s+12\s+meses[:\s]*([+-]?[\d,\.]+)\s*%',
        r'[\d\.]+\s*%\s*\(12\s+meses\)',
        # Padrões simples: "Crescimento de X%" ou "Variação de X%"
        r'crescimento\s+de\s+([+-]?[\d,\.]+)\s*%',
        r'variação\s+de\s+([+-]?[\d,\.]+)\s*%',
        r'queda\s+de\s+([+-]?[\d,\.]+)\s*%'
    ]

    texto_lower = texto_pdf.lower()

    # Buscar produção
    for padrao in padroes_producao:
        match = re.search(padrao, texto_lower, re.IGNORECASE)
        if match:
            valor_str = match.group(1)
            unidade = match.group(2).lower() if len(match.groups()) >= 2 else ''
            try:
                # Limpar o valor
                valor_str_limpo = valor_str.strip()
                # Se unidade é 'mil' (milhar), remover pontos (separadores de milhar) e substituir vírgula por ponto
                if unidade == 'mil':
                    valor_str_limpo = valor_str_limpo.replace('.', '').replace(',', '.')
                else:
                    # Para 'milhão' ou 'toneladas', apenas substituir vírgula por ponto (decimal)
                    valor_str_limpo = valor_str_limpo.replace(',', '.')

                valor = float(valor_str_limpo)
                # Converter para toneladas conforme unidade
                if unidade.startswith('milh') or 'milhoes' in unidade:
                    valor *= 1_000_000
                elif unidade == 'mil':
                    valor *= 1_000
                # Se já está em toneladas, mantém
                resultado['producao_ton'] = valor
                break
            except:
                continue

    # Buscar variação
    for padrao in padroes_variacao:
        match = re.search(padrao, texto_lower, re.IGNORECASE)
        if match:
            try:
                valor_str = match.group(1).replace(',', '.')
                valor = float(valor_str)
                resultado['variacao_12m'] = valor
                break
            except:
                continue

    return resultado

def coletar(tickers: List[str] | None = None) -> int:
    """
    Coleta dados da fonte correspondente e persiste no SQLite.
    Retorna número de registros inseridos.
    Nunca lança exceção para o caller — captura internamente e loga.
    Append-only: nunca faz UPDATE em registros existentes.
    Usa INSERT OR IGNORE para evitar duplicatas.
    """
    # Contador de registros inseridos
    registros_inseridos = 0
    
    try:
        # Conectar ao banco de dados
        conn = get_connection("alternativo")
        
        # Coletar dados do Google Trends
        try:
            # Delay inicial mais longo para evitar rate limiting
            time.sleep(15)
            
            # Lista de proxies públicos (usar com cuidado)
            proxies = [
                'http://185.199.228.156:7492',
                'http://185.199.229.156:7492',
                'http://185.199.229.157:7492',
                'http://185.199.229.158:7492',
                'http://185.199.229.159:7492',
                'http://185.199.228.157:7492',
                'http://185.199.228.158:7492',
                'http://185.199.228.159:7492',
            ]
            
            # Inicializar pytrends com headers realistas
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            }
            
            # Período: últimos 30 dias
            timeframe = 'today 1-m'
            
            # Estratégia de retry com proxies rotativos e divisão em lotes
            max_tentativas = 5
            termos_divididos = [GOOGLE_TRENDS_TERMOS[i:i+5] for i in range(0, len(GOOGLE_TRENDS_TERMOS), 5)]
            
            for lote_idx, lote_termos in enumerate(termos_divididos):
                print(f"[{datetime.now()}] [Google Trends] Processando lote {lote_idx+1}/{len(termos_divididos)}")
                
                for tentativa in range(max_tentativas):
                    try:
                        proxy = proxies[tentativa % len(proxies)] if proxies else None
                        if proxy:
                            requests_args = {'headers': headers, 'proxies': {'http': proxy, 'https': proxy}}
                        else:
                            requests_args = {'headers': headers}
                        
                        pytrends = TrendReq(hl='pt-BR', tz=180, requests_args=requests_args)
                        pytrends.build_payload(lote_termos, timeframe=timeframe)
                        data = pytrends.interest_over_time()
                        
                        if not data.empty:
                            for date, row in data.iterrows():
                                data_date = date.date()
                                for termo in lote_termos:
                                    try:
                                        valor = row[termo]
                                        cursor = conn.execute("""INSERT OR IGNORE INTO google_trends
                                        (termo, data, valor, data_coleta)
                                        VALUES (?, ?, ?, ?)""", (termo, data_date, int(valor), datetime.now()))
                                        registros_inseridos += cursor.rowcount
                                    except KeyError:
                                        continue
                            print(f"[{datetime.now()}] [Google Trends] Lote {lote_idx+1} processado")
                            break
                    
                    except Exception as e:
                        if '429' in str(e) or 'TooManyRequests' in str(e):
                            espera = (tentativa + 1) * 15
                            print(f"[{datetime.now()}] [Google Trends] Rate limit. Esperando {espera}s")
                            time.sleep(espera)
                        else:
                            print(f"[{datetime.now()}] [Google Trends] Erro: {e}")
                            break
                
                time.sleep(5)
            
            time.sleep(10)
            
        except Exception as e:
            print(f"[{datetime.now()}] [Google Trends] Erro geral: {e}")
        
        # Coletar dados da ANEEL (stub)
        try:
            # Implementação futura com API da ANEEL
            # Por enquanto, apenas logar que a funcionalidade está em desenvolvimento
            print(f"[{datetime.now()}] [ANEEL] Funcionalidade em desenvolvimento")
        except Exception as e:
            print(f"[{datetime.now()}] [ANEEL] Erro ao coletar dados: {e}")
        
        # Coletar dados da ABPO (scraping de PDFs com Selenium)
        try:
            # Importar Selenium apenas se necessário (evita erro se não instalado)
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            # Configurar opções do Chrome
            chrome_options = Options()
            chrome_options.add_argument("--headless") # Executar em modo sem interface
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Iniciar o driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Anos para coletar: de 2025 até 2015
            anos = range(2025, 2014, -1)
            
            for ano in anos:
                try:
                    url_ano = f"https://www.abre.org.br/dados-do-setor/{ano}-2/"
                    print(f"[{datetime.now()}] [ABPO] Acessando {url_ano}")
                    
                    # Acessar a página com Selenium (carrega JavaScript)
                    driver.get(url_ano)
                    
                    # Esperar carregamento da página (até 30 segundos)
                    wait = WebDriverWait(driver, 30)
                    
                    # Esperar até que algum elemento da página seja carregado
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    
                    # Dar tempo extra para carregar conteúdo dinâmico
                    time.sleep(5)
                    
                    # Obter o HTML após carregamento JavaScript
                    html = driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Encontrar links de PDFs (procurar por tags <a> com href contendo .pdf)
                    pdf_links = []
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if '.pdf' in href.lower():
                            # Construir URL absoluta se necessário
                            if href.startswith('http'):
                                pdf_url = href
                            else:
                                pdf_url = f"https://www.abre.org.br{href}" if href.startswith('/') else f"https://www.abre.org.br/dados-do-setor/{href}"
                            pdf_links.append(pdf_url)
                    
                    # Se não encontrou, tentar buscar em <iframe> ou <embed>
                    if not pdf_links:
                        for iframe in soup.find_all(['iframe', 'embed'], src=True):
                            src = iframe['src']
                            if '.pdf' in src.lower():
                                pdf_url = src if src.startswith('http') else f"https://www.abre.org.br{src}"
                                pdf_links.append(pdf_url)
                    
                    if not pdf_links:
                        # Log mais detalhado para debug
                        print(f"[{datetime.now()}] [ABPO] Nenhum PDF encontrado para {ano}. Verificando conteúdo da página:")
                        # Logar os primeiros 500 caracteres do HTML
                        page_content = soup.get_text()[:500]
                        print(f"[{datetime.now()}] [ABPO] Conteúdo da página: {page_content}...")
                        continue
                    
                    # Processar cada PDF encontrado
                    for pdf_url in pdf_links[:3]: # Limitar a 3 PDFs por ano para não sobrecarregar
                        try:
                            print(f"[{datetime.now()}] [ABPO] Baixando PDF: {pdf_url}")
                            
                            # Baixar PDF
                            pdf_response = requests.get(pdf_url, timeout=60)
                            if pdf_response.status_code != 200:
                                print(f"[{datetime.now()}] [ABPO] Erro ao baixar PDF: {pdf_response.status_code}")
                                continue
                            
                            # Salvar temporariamente
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                                tmp_file.write(pdf_response.content)
                                tmp_path = tmp_file.name
                            
                            # Extrair texto do PDF
                            texto_completo = ""
                            try:
                                with pdfplumber.open(tmp_path) as pdf:
                                    for pagina in pdf.pages:
                                        texto = pagina.extract_text()
                                        if texto:
                                            texto_completo += texto + "\n"
                            finally:
                                # Remover arquivo temporário
                                os.unlink(tmp_path)
                            
                            # Extrair dados de produção
                            dados = extrair_producao_papel_celulose(texto_completo)
                            
                            if dados['producao_ton'] is not None:
                                # Inserir no banco
                                cursor = conn.execute("""INSERT OR IGNORE INTO abpo_papelao
                                (data, producao_ton, variacao_12m, fonte_url, data_coleta)
                                VALUES (?, ?, ?, ?, ?)""", (
                                    datetime(ano, 1, 1).date(), # data do relatório (início do ano)
                                    dados['producao_ton'],
                                    dados['variacao_12m'],
                                    pdf_url,
                                    datetime.now()
                                ))
                                registros_inseridos += cursor.rowcount
                                print(f"[{datetime.now()}] [ABPO] Dados extraídos para {ano}: {dados}")
                            else:
                                print(f"[{datetime.now()}] [ABPO] Não foi possível extrair dados de produção de {pdf_url}")
                            
                        except Exception as e:
                            print(f"[{datetime.now()}] [ABPO] Erro ao processar PDF {pdf_url}: {e}")
                            continue
                    
                    # Delay entre anos
                    time.sleep(5)
                    
                except Exception as e:
                    print(f"[{datetime.now()}] [ABPO] Erro ao processar ano {ano}: {e}")
                    continue
            
            # Fechar o driver
            driver.quit()
            
        except Exception as e:
            print(f"[{datetime.now()}] [ABPO] Erro geral com Selenium: {e}")
            # Fallback: tentar com requests apenas se Selenium falhar
            try:
                # Anos para coletar: de 2025 até 2015
                anos = range(2025, 2014, -1)
                
                for ano in anos:
                    try:
                        url_ano = f"https://www.abre.org.br/dados-do-setor/{ano}-2/"
                        print(f"[{datetime.now()}] [ABPO] Fallback - Acessando {url_ano}")
                        
                        # Fazer requisição para a página do ano
                        response = requests.get(url_ano, timeout=30)
                        if response.status_code != 200:
                            print(f"[{datetime.now()}] [ABPO] Fallback - Erro ao acessar página {ano}: {response.status_code}")
                            continue
                        
                        # Parse do HTML
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Encontrar links de PDFs (procurar por tags <a> com href contendo .pdf)
                        pdf_links = []
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            if '.pdf' in href.lower():
                                # Construir URL absoluta se necessário
                                if href.startswith('http'):
                                    pdf_url = href
                                else:
                                    pdf_url = f"https://www.abre.org.br{href}" if href.startswith('/') else f"https://www.abre.org.br/dados-do-setor/{href}"
                                pdf_links.append(pdf_url)
                        
                        # Se não encontrou, tentar buscar em <iframe> ou <embed>
                        if not pdf_links:
                            for iframe in soup.find_all(['iframe', 'embed'], src=True):
                                src = iframe['src']
                                if '.pdf' in src.lower():
                                    pdf_url = src if src.startswith('http') else f"https://www.abre.org.br{src}"
                                    pdf_links.append(pdf_url)
                        
                        if not pdf_links:
                            # Log mais detalhado para debug
                            print(f"[{datetime.now()}] [ABPO] Fallback - Nenhum PDF encontrado para {ano}")
                            continue
                        
                        # Processar cada PDF encontrado
                        for pdf_url in pdf_links[:3]: # Limitar a 3 PDFs por ano para não sobrecarregar
                            try:
                                print(f"[{datetime.now()}] [ABPO] Fallback - Baixando PDF: {pdf_url}")
                                
                                # Baixar PDF
                                pdf_response = requests.get(pdf_url, timeout=60)
                                if pdf_response.status_code != 200:
                                    print(f"[{datetime.now()}] [ABPO] Fallback - Erro ao baixar PDF: {pdf_response.status_code}")
                                    continue
                                
                                # Salvar temporariamente
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                                    tmp_file.write(pdf_response.content)
                                    tmp_path = tmp_file.name
                                
                                # Extrair texto do PDF
                                texto_completo = ""
                                try:
                                    with pdfplumber.open(tmp_path) as pdf:
                                        for pagina in pdf.pages:
                                            texto = pagina.extract_text()
                                            if texto:
                                                texto_completo += texto + "\n"
                                finally:
                                    # Remover arquivo temporário
                                    os.unlink(tmp_path)
                                
                                # Extrair dados de produção
                                dados = extrair_producao_papel_celulose(texto_completo)
                                
                                if dados['producao_ton'] is not None:
                                    # Inserir no banco
                                    cursor = conn.execute("""INSERT OR IGNORE INTO abpo_papelao
                                    (data, producao_ton, variacao_12m, fonte_url, data_coleta)
                                    VALUES (?, ?, ?, ?, ?)""", (
                                        datetime(ano, 1, 1).date(), # data do relatório (início do ano)
                                        dados['producao_ton'],
                                        dados['variacao_12m'],
                                        pdf_url,
                                        datetime.now()
                                    ))
                                    registros_inseridos += cursor.rowcount
                                    print(f"[{datetime.now()}] [ABPO] Fallback - Dados extraídos para {ano}: {dados}")
                                else:
                                    print(f"[{datetime.now()}] [ABPO] Fallback - Não foi possível extrair dados de produção de {pdf_url}")
                                
                            except Exception as e:
                                print(f"[{datetime.now()}] [ABPO] Fallback - Erro ao processar PDF {pdf_url}: {e}")
                                continue
                        
                        # Delay entre anos
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"[{datetime.now()}] [ABPO] Fallback - Erro ao processar ano {ano}: {e}")
                        continue
                
            except Exception as e:
                print(f"[{datetime.now()}] [ABPO] Erro geral no fallback: {e}")
        
        # Coletar dados do IIE-FGV (stub)
        try:
            # Implementação futura com scraping do portal FGV
            # Por enquanto, apenas logar que a funcionalidade está em desenvolvimento
            print(f"[{datetime.now()}] [IIE-FGV] Funcionalidade em desenvolvimento")
        except Exception as e:
            print(f"[{datetime.now()}] [IIE-FGV] Erro ao coletar dados: {e}")
        
        conn.commit()
        
    except Exception as e:
        print(f"[{datetime.now()}] [alternativo] Erro geral: {e}")
        registros_inseridos = 0
        
    finally:
        if 'conn' in locals():
            conn.close()
    
    return registros_inseridos

def coletar_ibge_sidra_embalagens() -> int:
    """
    Coleta Tabela 8889 do IBGE SIDRA — Produção Física Industrial, 
    Índices Especiais de Embalagens (PIM-PF).
    Substitui pipeline ABPO — dado primário confirmado.
    
    Séries coletadas:
    '3' → Total de Embalagens
    '3.4' → Embalagens de papel e papelão
    '3.5' → Embalagens de material plástico
    
    URL: https://servicodados.ibge.gov.br/api/v3/agregados/8889/
    periodos/all/variaveis/all
    Insere em dados_setoriais_br com fonte='IBGE_SIDRA_8889'.
    Histórico disponível: janeiro 2012 em diante.
    Frequência de chamada: mensal (job_mensal).
    """
    registros_inseridos = 0
    
    try:
        # URL da API do IBGE SIDRA
        url = "https://servicodados.ibge.gov.br/api/v3/agregados/8889/periodos/all/variaveis/all"
        
        # Fazer requisição à API
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"[{datetime.now()}] [IBGE_SIDRA_8889] Erro ao acessar API: {response.status_code}")
            return 0
        
        # Parse do JSON
        data = response.json()
        
        # Conectar ao banco de dados
        conn = get_connection("alternativo")
        
        # Processar os dados
        for item in data:
            try:
                # Extrair informações
                periodo = item.get("periodo", "")
                variavel = item.get("variavel", "")
                valor = item.get("resultado", "")
                
                # Mapear variáveis para os códigos esperados
                if variavel == "3":
                    indicador = "Total de Embalagens"
                elif variavel == "3.4":
                    indicador = "Embalagens de papel e papelão"
                elif variavel == "3.5":
                    indicador = "Embalagens de material plástico"
                else:
                    continue
                
                # Converter período para data
                # O período está no formato YYYYMM
                if len(periodo) == 6:
                    data_referencia = datetime.strptime(periodo, "%Y%m").date()
                else:
                    continue
                
                # Converter valor para float
                try:
                    valor_float = float(valor)
                except ValueError:
                    continue
                
                # Inserir no banco de dados
                conn.execute("""INSERT OR IGNORE INTO dados_setoriais_br (
                    data_referencia, 
                    indicador, 
                    valor, 
                    variacao_mensal, 
                    variacao_anual, 
                    setor_primario, 
                    fonte, 
                    defasagem_dias, 
                    data_publicacao, 
                    data_coleta
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                    data_referencia,
                    indicador,
                    valor_float,
                    None,  # variacao_mensal
                    None,  # variacao_anual
                    "Embalagens",  # setor_primario
                    "IBGE_SIDRA_8889",  # fonte
                    0,  # defasagem_dias
                    data_referencia,  # data_publicacao
                    datetime.now()
                ))
                
                registros_inseridos += conn.rowcount
                
            except Exception as e:
                print(f"[{datetime.now()}] [IBGE_SIDRA_8889] Erro ao processar item: {e}")
                continue
        
        conn.commit()
        
    except Exception as e:
        print(f"[{datetime.now()}] [IBGE_SIDRA_8889] Erro geral: {e}")
        registros_inseridos = 0
        
    finally:
        if 'conn' in locals():
            conn.close()
    
    return registros_inseridos

def coletar_ibge_sidra_atividade() -> int:
    """
    Coleta PMC, PMS e PIM via API SIDRA (agregados distintos do 8889).
    Insere em dados_setoriais_br com fonte='IBGE_SIDRA'.
    """
    registros_inseridos = 0
    
    try:
        # URLs da API do IBGE SIDRA para os diferentes agregados
        agregados = {
            "PMC": "8890",  # Pesquisa Mensal de Comércio
            "PMS": "8891",  # Pesquisa Mensal de Serviços
            "PIM": "8892"   # Pesquisa Industrial Mensal
        }
        
        # Conectar ao banco de dados
        conn = get_connection("alternativo")
        
        for nome_agregado, id_agregado in agregados.items():
            url = f"https://servicodados.ibge.gov.br/api/v3/agregados/{id_agregado}/periodos/all/variaveis/all"
            
            # Fazer requisição à API
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                print(f"[{datetime.now()}] [IBGE_SIDRA_{nome_agregado}] Erro ao acessar API: {response.status_code}")
                continue
            
            # Parse do JSON
            data = response.json()
            
            # Processar os dados
            for item in data:
                try:
                    # Extrair informações
                    periodo = item.get("periodo", "")
                    variavel = item.get("variavel", "")
                    valor = item.get("resultado", "")
                    
                    # Mapear variáveis para os indicadores esperados
                    # Para PMC, PMS e PIM, os indicadores são mais complexos
                    # Vamos usar o nome da variável como indicador
                    indicador = variavel
                    
                    # Converter período para data
                    # O período está no formato YYYYMM
                    if len(periodo) == 6:
                        data_referencia = datetime.strptime(periodo, "%Y%m").date()
                    else:
                        continue
                    
                    # Converter valor para float
                    try:
                        valor_float = float(valor)
                    except ValueError:
                        continue
                    
                    # Inserir no banco de dados
                    conn.execute("""INSERT OR IGNORE INTO dados_setoriais_br (
                        data_referencia, 
                        indicador, 
                        valor, 
                        variacao_mensal, 
                        variacao_anual, 
                        setor_primario, 
                        fonte, 
                        defasagem_dias, 
                        data_publicacao, 
                        data_coleta
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                        data_referencia,
                        indicador,
                        valor_float,
                        None,  # variacao_mensal
                        None,  # variacao_anual
                        nome_agregado,  # setor_primario
                        "IBGE_SIDRA",  # fonte
                        0,  # defasagem_dias
                        data_referencia,  # data_publicacao
                        datetime.now()
                    ))
                    
                    registros_inseridos += conn.rowcount
                    
                except Exception as e:
                    print(f"[{datetime.now()}] [IBGE_SIDRA_{nome_agregado}] Erro ao processar item: {e}")
                    continue
        
        conn.commit()
        
    except Exception as e:
        print(f"[{datetime.now()}] [IBGE_SIDRA_ATIVIDADE] Erro geral: {e}")
        registros_inseridos = 0
        
    finally:
        if 'conn' in locals():
            conn.close()
    
    return registros_inseridos

def coletar_mdic_balanca() -> int:
    """
    Coleta balança comercial via API MDIC/dados.gov.br.
    Insere em dados_setoriais_br com fonte='MDIC'.
    """
    registros_inseridos = 0
    
    try:
        # URL da API do MDIC
        # A API do MDIC tem várias endpoints, vamos usar a principal de balança comercial
        url = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/balanca_comercial"
        
        # Fazer requisição à API
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"[{datetime.now()}] [MDIC_BALANCA] Erro ao acessar API: {response.status_code}")
            return 0
        
        # Parse do JSON
        data = response.json()
        
        # Conectar ao banco de dados
        conn = get_connection("alternativo")
        
        # Processar os dados
        for item in data.get("items", []):
            try:
                # Extrair informações
                mes = item.get("mes", "")
                ano = item.get("ano", "")
                exportacao = item.get("exportacao", None)
                importacao = item.get("importacao", None)
                
                # Converter para data
                if mes and ano:
                    data_referencia = datetime.strptime(f"{ano}-{mes}", "%Y-%m").date()
                else:
                    continue
                
                # Inserir exportação
                if exportacao is not None:
                    conn.execute("""INSERT OR IGNORE INTO dados_setoriais_br (
                        data_referencia, 
                        indicador, 
                        valor, 
                        variacao_mensal, 
                        variacao_anual, 
                        setor_primario, 
                        fonte, 
                        defasagem_dias, 
                        data_publicacao, 
                        data_coleta
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                        data_referencia,
                        "Exportação",
                        exportacao,
                        None,  # variacao_mensal
                        None,  # variacao_anual
                        "Balança Comercial",  # setor_primario
                        "MDIC",  # fonte
                        0,  # defasagem_dias
                        data_referencia,  # data_publicacao
                        datetime.now()
                    ))
                    registros_inseridos += conn.rowcount
                
                # Inserir importação
                if importacao is not None:
                    conn.execute("""INSERT OR IGNORE INTO dados_setoriais_br (
                        data_referencia, 
                        indicador, 
                        valor, 
                        variacao_mensal, 
                        variacao_anual, 
                        setor_primario, 
                        fonte, 
                        defasagem_dias, 
                        data_publicacao, 
                        data_coleta
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                        data_referencia,
                        "Importação",
                        importacao,
                        None,  # variacao_mensal
                        None,  # variacao_anual
                        "Balança Comercial",  # setor_primario
                        "MDIC",  # fonte
                        0,  # defasagem_dias
                        data_referencia,  # data_publicacao
                        datetime.now()
                    ))
                    registros_inseridos += conn.rowcount
                
            except Exception as e:
                print(f"[{datetime.now()}] [MDIC_BALANCA] Erro ao processar item: {e}")
                continue
        
        conn.commit()
        
    except Exception as e:
        print(f"[{datetime.now()}] [MDIC_BALANCA] Erro geral: {e}")
        registros_inseridos = 0
        
    finally:
        if 'conn' in locals():
            conn.close()
    
    return registros_inseridos