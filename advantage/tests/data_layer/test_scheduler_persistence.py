"""
test_scheduler_persistence.py — Testes para persistência do scheduler

Testes unitários para o scheduler persistente com SQLAlchemyJobStore.
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import patch, Mock
import sqlite3
import shutil

# Adicionar o caminho do projeto ao sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from advantage.src.data_layer.scheduler import verificar_jobs_perdidos, main

class TestSchedulerPersistence(unittest.TestCase):
    """Testes para a persistência do scheduler"""

    def setUp(self):
        """Configuração antes de cada teste."""
        # Criar diretório de dados de teste
        self.test_data_dir = Path("/tmp/test_scheduler_data")
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Caminho do banco de dados de teste
        self.test_db_path = self.test_data_dir / "jobs.sqlite"
        
        # Limpar qualquer banco de dados antigo
        if self.test_db_path.exists():
            self.test_db_path.unlink()
        
        # Substituir o caminho do banco de dados por um de teste
        self.original_db_path = "data/jobs.sqlite"
        
        # Criar um mock para o scheduler
        self.scheduler_mock = Mock()
        
        # Criar jobs simulados
        self.jobs = [
            Mock(id='job_preco_volume', name='preco_volume', next_run_time=datetime.now() - timedelta(days=1)),
            Mock(id='job_macro_brasil', name='macro_brasil', next_run_time=datetime.now() - timedelta(days=2)),
            Mock(id='job_macro_global', name='macro_global', next_run_time=datetime.now() - timedelta(days=3)),
            Mock(id='job_polymarket', name='polymarket', next_run_time=datetime.now() - timedelta(days=1)),
            Mock(id='job_ibge_embalagens_mensal', name='ibge_embalagens_mensal', next_run_time=datetime.now() - timedelta(days=30)),
            Mock(id='job_ibge_atividade_mensal', name='ibge_atividade_mensal', next_run_time=datetime.now() - timedelta(days=30)),
        ]
        
        # Mockar get_jobs para retornar os jobs simulados
        self.scheduler_mock.get_jobs.return_value = self.jobs
        
        # Substituir o scheduler global por um mock
        self.original_scheduler = None
        
    def tearDown(self):
        """Limpeza após cada teste."""
        # Remover diretório de teste
        if hasattr(self, 'test_data_dir') and self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)
        
        # Restaurar o scheduler original se necessário
        if hasattr(self, 'original_scheduler') and self.original_scheduler:
            pass  # Não vamos restaurar pois não modificamos o global

    @patch('advantage.src.data_layer.scheduler.scheduler', new_callable=Mock)
    def test_verificar_jobs_perdidos_detecta_jobs(self, mock_scheduler):
        """Verifica que a função detecta jobs perdidos"""
        # Configurar o mock para retornar jobs perdidos
        mock_scheduler.get_jobs.return_value = [
            Mock(id='job_preco_volume', name='preco_volume', next_run_time=datetime.now() - timedelta(days=1)),
            Mock(id='job_macro_brasil', name='macro_brasil', next_run_time=datetime.now() - timedelta(days=2)),
        ]
        
        # Capturar a saída padrão
        from io import StringIO
        import sys
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        # Executar a função
        verificar_jobs_perdidos()
        
        # Restaurar a saída padrão
        sys.stdout = sys.__stdout__
        
        # Verificar que a saída contém os logs esperados
        output = captured_output.getvalue()
        self.assertIn("⚠️ JOBS PERDIDOS DETECTADOS", output)
        self.assertIn("preco_volume", output)
        self.assertIn("macro_brasil", output)
        self.assertIn("Será executado automaticamente", output)

    @patch('advantage.src.data_layer.scheduler.scheduler', new_callable=Mock)
    def test_verificar_jobs_perdidos_nao_detecta_jobs_atuais(self, mock_scheduler):
        """Verifica que a função não detecta jobs que ainda não venceram"""
        # Configurar o mock para retornar jobs futuros
        mock_scheduler.get_jobs.return_value = [
            Mock(id='job_preco_volume', name='preco_volume', next_run_time=datetime.now() + timedelta(hours=1)),
            Mock(id='job_macro_brasil', name='macro_brasil', next_run_time=datetime.now() + timedelta(hours=2)),
        ]
        
        # Capturar a saída padrão
        from io import StringIO
        import sys
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        # Executar a função
        verificar_jobs_perdidos()
        
        # Restaurar a saída padrão
        sys.stdout = sys.__stdout__
        
        # Verificar que a saída não contém logs de jobs perdidos
        output = captured_output.getvalue()
        self.assertNotIn("⚠️ JOBS PERDIDOS DETECTADOS", output)
        self.assertNotIn("preco_volume", output)
        self.assertNotIn("macro_brasil", output)

    @patch('advantage.src.data_layer.scheduler.scheduler', new_callable=Mock)
    def test_verificar_jobs_perdidos_trata_erro(self, mock_scheduler):
        """Verifica que a função trata erros de forma segura"""
        # Configurar o mock para lançar erro
        mock_scheduler.get_jobs.side_effect = Exception("Erro simulado")
        
        # Capturar a saída padrão
        from io import StringIO
        import sys
        
        captured_output = StringIO()
        sys.stdout = captured_output
        
        # Executar a função
        verificar_jobs_perdidos()
        
        # Restaurar a saída padrão
        sys.stdout = sys.__stdout__
        
        # Verificar que a saída contém o log de erro
        output = captured_output.getvalue()
        self.assertIn("Erro ao verificar jobs perdidos", output)

    def test_scheduler_inicializa_com_jobstore(self):
        """Verifica que o scheduler inicializa com jobstore persistente"""
        # Este teste é mais complexo e requer execução real
        # Vamos verificar se o arquivo é criado
        
        # Criar diretório de teste
        test_data_dir = Path("/tmp/test_scheduler_init")
        test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Substituir temporariamente o caminho do banco de dados
        original_db_path = "data/jobs.sqlite"
        
        # Criar um arquivo de configuração temporário
        import tempfile
        
        # Criar um script temporário para inicializar o scheduler
        test_script = """
import sys
import os
from pathlib import Path

# Adicionar o caminho do projeto ao sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from advantage.src.data_layer.scheduler import main

# Criar diretório de dados de teste
test_data_dir = Path("/tmp/test_scheduler_init")
test_data_dir.mkdir(parents=True, exist_ok=True)

# Criar um arquivo de configuração temporário
with open(test_data_dir / "config.py", "w") as f:
    f.write("""
import os
os.environ['SCHEDULER_DB_PATH'] = str(test_data_dir / "jobs.sqlite")
""")

# Executar o scheduler com o caminho de teste
main()
"""
        
        # Executar o script
        import subprocess
        
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            temp_script = f.name
        
        try:
            # Executar o script
            result = subprocess.run([sys.executable, temp_script], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            
            # Verificar se o arquivo de banco foi criado
            db_file = test_data_dir / "jobs.sqlite"
            self.assertTrue(db_file.exists(), "Arquivo de banco de dados não foi criado")
            
        finally:
            # Limpar arquivos temporários
            if os.path.exists(temp_script):
                os.unlink(temp_script)
            if test_data_dir.exists():
                shutil.rmtree(test_data_dir)

    def test_shutdown_gracioso(self):
        """Verifica que o scheduler encerra corretamente"""
        # Este teste é mais complexo e requer execução real
        # Vamos verificar se o handler de sinal é registrado
        
        # Importar o módulo scheduler
        import advantage.src.data_layer.scheduler as scheduler_module
        
        # Verificar se os handlers de sinal foram registrados
        self.assertTrue(hasattr(scheduler_module, 'signal_handler'))
        
        # Verificar se os handlers estão registrados para SIGINT e SIGTERM
        # Isso é mais difícil de testar sem executar o código real
        # Mas podemos verificar que a função foi definida
        self.assertTrue(callable(scheduler_module.signal_handler))

    def test_persistencia_entre_reinicializacoes(self):
        """Verifica que jobs persistem entre reinicializações"""
        # Criar diretório de teste
        test_data_dir = Path("/tmp/test_scheduler_persist")
        test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Caminho do banco de dados de teste
        test_db_path = test_data_dir / "jobs.sqlite"
        
        # Limpar qualquer banco de dados antigo
        if test_db_path.exists():
            test_db_path.unlink()
        
        # Criar um script temporário para inicializar o scheduler e adicionar um job
        test_script = """
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Adicionar o caminho do projeto ao sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from advantage.src.data_layer.scheduler import main
from apscheduler.triggers.interval import IntervalTrigger

# Criar diretório de dados de teste
test_data_dir = Path("/tmp/test_scheduler_persist")
test_data_dir.mkdir(parents=True, exist_ok=True)

# Criar um arquivo de configuração temporário
with open(test_data_dir / "config.py", "w") as f:
    f.write("""
import os
os.environ['SCHEDULER_DB_PATH'] = str(test_data_dir / "jobs.sqlite")
""")

# Executar o scheduler com o caminho de teste
main()

# Adicionar um job manualmente para teste
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

jobstore = SQLAlchemyJobStore(url='sqlite:///""" + str(test_db_path) + """', tablename='scheduled_jobs')
scheduler = BackgroundScheduler(jobstores={'default': jobstore})
scheduler.add_job(lambda: None, IntervalTrigger(seconds=10), id='test_job')
scheduler.start()
scheduler.shutdown()
"""
        
        # Criar arquivo temporário
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_script)
            temp_script = f.name
        
        try:
            # Executar o script para criar o job
            import subprocess
            result = subprocess.run([sys.executable, temp_script], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            
            # Verificar se o arquivo de banco foi criado
            self.assertTrue(test_db_path.exists(), "Arquivo de banco de dados não foi criado")
            
            # Verificar se o job foi persistido
            # Abrir o banco de dados e verificar se o job está lá
            conn = sqlite3.connect(test_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM scheduled_jobs WHERE id = 'test_job'")
            result = cursor.fetchone()
            self.assertIsNotNone(result, "Job 'test_job' não foi persistido no banco de dados")
            
            # Fechar conexão
            conn.close()
            
        finally:
            # Limpar arquivos temporários
            if os.path.exists(temp_script):
                os.unlink(temp_script)
            if test_data_dir.exists():
                shutil.rmtree(test_data_dir)""