#!/usr/bin/env python3
"""
Verification script to test that the 'bool' object has no attribute 'append' bug is fixed.
This script tests the exact scenario described in the bug report.
"""

import json
import os
import tempfile
from unittest.mock import patch, mock_open
from fastapi.testclient import TestClient
from atlas_backend.main import app

client = TestClient(app)


def test_vale3_confirmation_scenario():
    """
    Test the exact scenario from the bug report:
    - User clicks on 'gestao' and adds a new asset for calibration (VALE3)
    - Goes to the 2nd card (TUNE) 
    - After Optuna identifies optimized combinations, clicks confirm button
    - Should NOT get: 'bool' object has no attribute 'append'
    """
    print("Testing VALE3 confirmation scenario...")
    
    ticker = "VALE3"
    run_id = "test_run_12345"
    regime = "ALTA"
    
    # Simulate the state of a newly added asset (like VALE3)
    # Initially, historico_config would be an empty list []
    # After first successful confirmation, it becomes a list with one item [{...}]
    # The bug occurs when somehow historico_config becomes a boolean True/False
    
    # Test Case 1: historico_config is corrupted to boolean True (simulating the bug condition)
    print("  Test 1: historico_config corrupted to boolean True")
    mock_data_corrupted_true = {
        "ticker": ticker,
        "historico_config": True,  # This is the corruption that causes the bug
        "tune_ranking_estrategia": {
            "_meta": {
                "run_id": run_id
            },
            regime: {
                "confirmado": False,
                "eleicao_status": "competitiva",
                "ranking": [
                    {"estrategia": "CSP", "score": 0.95}
                ],
                "estrategia_eleita": "CSP"
            }
        },
        "estrategias": {}
    }
    
    # Test Case 2: historico_config is corrupted to boolean False
    print("  Test 2: historico_config corrupted to boolean False")
    mock_data_corrupted_false = {
        "ticker": ticker,
        "historico_config": False,  # Another form of corruption
        "tune_ranking_estrategia": {
            "_meta": {
                "run_id": run_id
            },
            regime: {
                "confirmado": False,
                "eleicao_status": "competitiva",
                "ranking": [
                    {"estrategia": "CSP", "score": 0.95}
                ],
                "estrategia_eleita": "CSP"
            }
        },
        "estrategias": {}
    }
    
    # Test Case 3: historico_config is missing entirely
    print("  Test 3: historico_config missing")
    mock_data_missing = {
        "ticker": ticker,
        # historico_config key is missing entirely
        "tune_ranking_estrategia": {
            "_meta": {
                "run_id": run_id
            },
            regime: {
                "confirmado": False,
                "eleicao_status": "competitiva",
                "ranking": [
                    {"estrategia": "CSP", "score": 0.95}
                ],
                "estrategia_eleita": "CSP"
            }
        },
        "estrategias": {}
    }
    
    # Test Case 4: historico_config is proper list (normal case)
    print("  Test 4: historico_config is proper list (normal)")
    mock_data_normal = {
        "ticker": ticker,
        "historico_config": [],  # Normal empty list
        "tune_ranking_estrategia": {
            "_meta": {
                "run_id": run_id
            },
            regime: {
                "confirmado": False,
                "eleicao_status": "competitiva",
                "ranking": [
                    {"estrategia": "CSP", "score": 0.95}
                ],
                "estrategia_eleita": "CSP"
            }
        },
        "estrategias": {}
    }
    
    test_cases = [
        ("corrupted_true", mock_data_corrupted_true),
        ("corrupted_false", mock_data_corrupted_false),
        ("missing", mock_data_missing),
        ("normal", mock_data_normal)
    ]
    
    for case_name, mock_data in test_cases:
        print(f"    Testing {case_name}...")
        
        with patch("atlas_backend.api.routes.delta_chaos.get_paths") as mock_get_paths, \
             patch("builtins.open", mock_open(read_data=json.dumps(mock_data))) as mock_file, \
             patch("atlas_backend.core.terminal_stream.emit_log"), \
             patch("tempfile.mkstemp") as mock_mkstemp, \
             patch("os.fdopen"), \
             patch("os.replace"), \
             patch("os.unlink"):
            
            # Setup mock for tempfile.mkstemp to return a fake file descriptor and path
            mock_mkstemp.return_value = (100, "/tmp/fake.tmp")
            
            # Make the request to confirmar-regime endpoint
            response = client.post(
                "/tune/confirmar-regime",
                json={
                    "ticker": ticker,
                    "regime": regime,
                    "run_id": run_id,
                    "confirm": True,
                    "description": "Test confirmation for bug verification"
                }
            )
            
            # The key assertion: we should NOT get a 500 error from the bool append bug
            # We might get other error codes (400, 404, 409) based on business logic validation
            # but NOT 500 from AttributeError: 'bool' object has no attribute 'append'
            assert response.status_code != 500, \
                f"Endpoint returned 500 for {case_name} - indicates the bug is NOT fixed: {response.json()}"
            
            print(f"      OK Status code: {response.status_code} (not 500, so no bool append error)")
    
    print("OK All test cases passed - the 'bool' object has no attribute 'append' bug appears to be FIXED!")


def test_bulk_confirmation_scenario():
    """
    Test the bulk confirmation scenario (confirmar-todos) which also had the same bug.
    """
    print("\nTesting bulk confirmation scenario...")
    
    ticker = "VALE3"
    run_id = "test_run_12345"
    
    # Test with corrupted historico_config
    mock_data_corrupted = {
        "ticker": ticker,
        "historico_config": True,  # Corrupted to bool
        "tune_ranking_estrategia": {
            "_meta": {
                "run_id": run_id
            },
            "ALTA": {
                "confirmado": False,
                "eleicao_status": "competitiva",
                "ranking": [
                    {"estrategia": "CSP", "score": 0.95}
                ],
                "estrategia_eleita": "CSP"
            },
            "BAIXA": {
                "confirmado": False,
                "eleicao_status": "competitiva",
                "ranking": [
                    {"estrategia": "BC", "score": 0.90}
                ],
                "estrategia_eleita": "BC"
            }
        },
        "estrategias": {}
    }
    
    with patch("atlas_backend.api.routes.delta_chaos.get_paths") as mock_get_paths, \
         patch("builtins.open", mock_open(read_data=json.dumps(mock_data_corrupted))) as mock_file, \
         patch("atlas_backend.core.terminal_stream.emit_log"), \
         patch("tempfile.mkstemp") as mock_mkstemp, \
         patch("os.fdopen"), \
         patch("os.replace"), \
         patch("os.unlink"):
        
        # Setup mock for tempfile.mkstemp to return a fake file descriptor and path
        mock_mkstemp.return_value = (100, "/tmp/fake.tmp")
        
        # Make the request to confirmar-todos endpoint
        response = client.post(
            "/tune/confirmar-todos",
            json={
                "ticker": ticker,
                "run_id": run_id,
                "confirm": True,
                "description": "Test bulk confirmation for bug verification"
            }
        )
        
        # Should not get 500 from bool append error
        assert response.status_code != 500, \
            f"Bulk endpoint returned 500 - indicates the bug is NOT fixed: {response.json()}"
        
        print(f"OK Bulk confirmation test passed - status code: {response.status_code}")


if __name__ == "__main__":
    print("=" * 60)
    print("BUG FIX VERIFICATION: 'bool' object has no attribute 'append'")
    print("=" * 60)
    
    try:
        test_vale3_confirmation_scenario()
        test_bulk_confirmation_scenario()
        
        print("\n" + "=" * 60)
        print("*** ALL TESTS PASSED - BUG APPEARS TO BE FIXED! ***")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n!!! TEST FAILED: {e}")
        print("The bug may not be completely fixed.")
        raise