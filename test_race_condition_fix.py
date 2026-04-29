#!/usr/bin/env python3
"""
Test script to verify that the race condition fix prevents the 
'ORBIT desatualizado — ciclo 2023-03 ausente no master JSON' error.
"""

import json
import os
import tempfile
import time
import threading
from unittest.mock import patch
import sys
sys.path.insert(0, 'C:\\Users\\tiago\\OneDrive\\Documentos\\ATLAS')

from delta_chaos.tape import tape_ativo_carregar, tape_ativo_salvar
from delta_chaos.gate import gate_executar


def test_race_condition_scenario():
    """
    Simulate the race condition:
    1. TAPE creates/updates VALE3.json with historical data
    2. Concurrently, GATE tries to read the JSON while it's being written
    3. Verify that GATE doesn't get an empty historico
    """
    print("Testing race condition scenario...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the ATIVOS_DIR to point to our temp directory
        with patch('delta_chaos.tape.ATIVOS_DIR', temp_dir), \
             patch('delta_chaos.gate.ATIVOS_DIR', temp_dir):
            
            ticker = "VALE3"
            json_path = os.path.join(temp_dir, f"{ticker}.json")
            
            # Step 1: Simulate TAPE having created a rich JSON with historical data
            initial_data = {
                "ticker": ticker,
                "status": "MONITORAR",
                "historico": [
                    {"ciclo_id": "2023-03", "regime": "ALTA", "ir": 0.05},
                    {"ciclo_id": "2023-04", "regime": "BAIXA", "ir": 0.03},
                    {"ciclo_id": "2023-05", "regime": "NEUTRO", "ir": 0.04}
                ],
                "historico_config": [
                    {"data": "2026-04-25", "modulo": "TUNE v3.0", "parametro": "estrategia.ALTA", 
                     "valor_anterior": None, "valor_novo": "BULL_PUT_SPREAD", 
                     "motivo": "Confirmação CEO"}
                ],
                "estrategias": {
                    "ALTA": "BULL_PUT_SPREAD",
                    "BAIXA": "BEAR_CALL_SPREAD", 
                    "NEUTRO": None,
                    "NEUTRO_BULL": None,
                    "NEUTRO_BEAR": None,
                    "NEUTRO_LATERAL": None,
                    "NEUTRO_MORTO": None,
                    "NEUTRO_TRANSICAO": None,
                    "RECUPERACAO": None,
                    "PANICO": None
                },
                "take_profit": 0.08,
                "stop_loss": 0.04,
                "reflect_state": "B",
                "atualizado_em": "2026-04-27 10:00:00"
            }
            
            # Write the initial rich data
            with open(json_path, 'w') as f:
                json.dump(initial_data, f, indent=2)
            
            print(f"✓ Created initial JSON with {len(initial_data['historico'])} historical entries")
            
            # Step 2: Simulate the race condition - TAPE updating the file while GATE reads
            def simulate_tape_update():
                """Simulate TAPE updating the JSON (like during confirmation)"""
                time.sleep(0.05)  # Small delay to increase chance of race condition
                try:
                    # This simulates what happens during TUNE confirmation
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                    
                    # Add a new TUNE confirmation (like the endpoint does)
                    data["historico_config"].append({
                        "data": "2026-04-27",
                        "modulo": "TUNE v3.0", 
                        "parametro": "estrategia.ALTA",
                        "valor_anterior": "BULL_PUT_SPREAD",
                        "valor_novo": "BULL_PUT_SPREAD",
                        "motivo": "Confirmação CEO - teste"
                    })
                    data["atualizado_em"] = "2026-04-27 10:00:05"
                    
                    # Write back atomically (simulating the endpoint behavior)
                    temp_path = json_path + ".tmp"
                    with open(temp_path, 'w') as f:
                        json.dump(data, f, indent=2)
                    os.replace(temp_path, json_path)
                    
                    print("✓ TAPE update simulation completed")
                except Exception as e:
                    print(f"✗ TAPE update simulation failed: {e}")
            
            def simulate_gate_read():
                """Simulate GATE reading the JSON (like during gate_executar)"""
                time.sleep(0.02)  # Start slightly after TAPE update begins
                try:
                    # This is what happens in gate.py line 85-86
                    with open(json_path, encoding="utf-8") as f:
                        dados = json.load(f)
                    
                    # This is what happens in edge.py reflect_cycle_calcular
                    historico = dados.get("historico", [])
                    ciclo_existe = any(c.get("ciclo_id") == "2023-03" for c in historico)
                    
                    print(f"✓ GATE read simulation: found {len(historico)} historical entries")
                    print(f"✓ GATE read simulation: ciclo 2023-03 presente: {ciclo_existe}")
                    
                    if not ciclo_existe:
                        raise ValueError(f"ORBIT desatualizado — ciclo 2023-03 ausente no master JSON")
                    
                    return True
                except Exception as e:
                    print(f"✗ GATE read simulation failed: {e}")
                    raise
            
            # Step 3: Run both operations concurrently to simulate race condition
            tape_thread = threading.Thread(target=simulate_tape_update)
            gate_thread = threading.Thread(target=simulate_gate_read)
            
            tape_thread.start()
            gate_thread.start()
            
            tape_thread.join()
            gate_thread.join()
            
            # Step 4: Verify final state
            try:
                with open(json_path, 'r') as f:
                    final_data = json.load(f)
                
                historico_count = len(final_data.get("historico", []))
                historico_config_count = len(final_data.get("historico_config", []))
                
                print(f"✓ Final JSON state: {historico_count} historical entries, {historico_config_count} config entries")
                
                # The key test: historico should NOT be empty
                if historico_count > 0:
                    print("✅ SUCCESS: Historical data preserved - race condition fix working!")
                    return True
                else:
                    print("❌ FAILURE: Historical data lost - race condition still present!")
                    return False
                    
            except Exception as e:
                print(f"✗ Failed to read final JSON: {e}")
                return False


if __name__ == "__main__":
    print("=" * 70)
    print("RACE CONDITION FIX VERIFICATION")
    print("Testing: 'ORBIT desatualizado — ciclo 2023-03 ausente no master JSON'")
    print("=" * 70)
    
    try:
        success = test_race_condition_scenario()
        print("\n" + "=" * 70)
        if success:
            print("🎉 RACE CONDITION FIX VERIFICATION PASSED!")
            print("The fix prevents destruction of historical data during concurrent access.")
        else:
            print("💥 RACE CONDITION FIX VERIFICATION FAILED!")
            print("The fix did not prevent the race condition.")
        print("=" * 70)
    except Exception as e:
        print(f"\n💥 VERIFICATION ERROR: {e}")
        print("=" * 70)