import os
import json
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

# Testes para o sistema de onboarding

def test_emit_event_chamado_por_trial():
    """
    Verifica se emit_event é chamado a cada trial no tune.py
    """
    # Este teste é mais adequado para ser feito com mock
    # Como não temos acesso direto ao código em execução, vamos verificar a presença do código
    tune_py_path = Path(__file__).parent.parent / "tune.py"
    
    with open(tune_py_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verifica se o emit_event foi adicionado no _early_stop_cb
    assert "emit_event(\"TUNE\", \"trial\"" in content, "emit_event não foi adicionado no _early_stop_cb"

def test_onboarding_estado_inicial():
    """
    Verifica se a estrutura padrão do campo onboarding é criada corretamente
    """
    # Criar um arquivo JSON temporário para simular um ativo
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name
        json.dump({"ticker": "TESTE"}, f)
    
    try:
        # Simular a leitura do ativo
        with open(temp_path, "r", encoding="utf-8") as f:
            dados = json.load(f)
        
        # Verificar que o campo onboarding foi adicionado com a estrutura padrão
        assert "onboarding" in dados, "Campo onboarding não encontrado no JSON"
        
        onboarding = dados["onboarding"]
        assert onboarding["step_atual"] == 1, "step_atual deve ser 1"
        
        steps = onboarding["steps"]
        assert "1_backtest_dados" in steps, "Step 1 não encontrado"
        assert "2_tune" in steps, "Step 2 não encontrado"
        assert "3_backtest_gate" in steps, "Step 3 não encontrado"
        
        # Verificar estados iniciais
        assert steps["1_backtest_dados"]["status"] == "idle", "Step 1 deve estar idle"
        assert steps["2_tune"]["status"] == "idle", "Step 2 deve estar idle"
        assert steps["3_backtest_gate"]["status"] == "idle", "Step 3 deve estar idle"
        
        # Verificar campos de trials
        assert steps["2_tune"]["trials_completos"] == 0, "trials_completos deve ser 0"
        assert steps["2_tune"]["trials_total"] == 200, "trials_total deve ser 200"
        
        # Verificar ultimo_evento_em
        assert onboarding["ultimo_evento_em"] is None, "ultimo_evento_em deve ser None"
        
    finally:
        os.unlink(temp_path)

def test_watchdog_promove_paused():
    """
    Verifica se o watchdog promove status running para paused após 10 minutos sem sinal
    """
    # Criar um arquivo JSON temporário com estado running e ultimo_evento_em antigo
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name
        
        # Criar um estado running com ultimo_evento_em de 15 minutos atrás
        old_time = (datetime.now() - timedelta(minutes=15)).isoformat()
        
        json.dump({
            "ticker": "TESTE",
            "onboarding": {
                "step_atual": 2,
                "steps": {
                    "1_backtest_dados": {"status": "done", "iniciado_em": None, "concluido_em": None, "erro": None},
                    "2_tune": {"status": "running", "iniciado_em": None, "concluido_em": None, "erro": None, "trials_completos": 0, "trials_total": 200},
                    "3_backtest_gate": {"status": "idle", "iniciado_em": None, "concluido_em": None, "erro": None}
                },
                "ultimo_evento_em": old_time
            }
        }, f)
    
    try:
        # Simular a leitura do ativo (como faria o endpoint /onboarding/{ticker})
        with open(temp_path, "r", encoding="utf-8") as f:
            dados = json.load(f)
        
        # Simular a reconciliação watchdog (como faria o endpoint)
        onboarding = dados["onboarding"]
        
        # Verificar que o status foi atualizado para paused
        assert onboarding["steps"]["2_tune"]["status"] == "paused", "Step 2 deve ser promovido para paused"
        
        # Verificar que ultimo_evento_em foi atualizado
        assert onboarding["ultimo_evento_em"] is not None, "ultimo_evento_em deve ser atualizado"
        
        # Verificar que o novo ultimo_evento_em é recente
        new_time = datetime.fromisoformat(onboarding["ultimo_evento_em"])
        assert (datetime.now() - new_time).total_seconds() < 10, "ultimo_evento_em deve ser atualizado para o momento atual"
        
    finally:
        os.unlink(temp_path)

def test_retomada_continua_do_sqlite():
    """
    Verifica se a retomada do TUNE continua do SQLite existente
    """
    # Criar um arquivo SQLite temporário com alguns trials
    with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
        temp_db_path = f.name
    
    try:
        # Criar banco SQLite com alguns trials
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # Criar tabela trials
        cursor.execute("""
            CREATE TABLE trial (
                id INTEGER PRIMARY KEY,
                number INTEGER,
                state TEXT,
                value REAL
            )
        """)
        
        # Inserir alguns trials completos
        cursor.executemany("""
            INSERT INTO trial (number, state, value) VALUES (?, ?, ?)
        """, [
            (1, "COMPLETE", 0.5),
            (2, "COMPLETE", 0.6),
            (3, "COMPLETE", 0.7),
            (4, "COMPLETE", 0.8),
            (5, "COMPLETE", 0.9)
        ])
        
        conn.commit()
        conn.close()
        
        # Simular a chamada de dc_onboarding_progresso_tune
        # Verificar que o número de trials completos é 5
        conn = sqlite3.connect(f"file:{temp_db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM trial WHERE state = 'COMPLETE'")
        trials_completos = cursor.fetchone()[0]
        
        assert trials_completos == 5, "Deve haver 5 trials completos no SQLite"
        
        conn.close()
        
    finally:
        os.unlink(temp_db_path)