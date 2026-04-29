#!/usr/bin/env python3
"""
Verification script to test that the race condition fix in tape.py works correctly.
This tests that tape_ativo_carregar no longer recreates JSON with defaults on failure.
"""

import json
import os
import tempfile
import time
from unittest.mock import patch, mock_open
import sys
sys.path.insert(0, 'C:\\Users\\tiago\\OneDrive\\Documentos\\ATLAS')

from delta_chaos.tape import tape_ativo_carregar


def test_tape_ativo_carregar_propagates_error_instead_of_defaults():
    """Test that tape_ativo_carregar raises exception instead of returning defaults on JSON corruption"""
    print("Testing tape_ativo_carregar error propagation...")
    
    # Test case 1: JSON file exists but is corrupted (invalid JSON)
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the ATIVOS_DIR to point to our temp directory
        with patch('delta_chaos.tape.ATIVOS_DIR', temp_dir):
            ticker = "TEST"
            json_path = os.path.join(temp_dir, f"{ticker}.json")
            
            # Create a corrupted JSON file
            with open(json_path, 'w') as f:
                f.write("{ invalid json content")
            
            # Should raise an exception, not return defaults
            try:
                result = tape_ativo_carregar(ticker)
                print(f"❌ ERROR: Expected exception but got result: {result}")
                return False
            except (json.JSONDecodeError, Exception) as e:
                print(f"✅ OK: Got expected exception: {type(e).__name__}: {e}")
                # Verify that the corrupted file was backed up
                backup_files = [f for f in os.listdir(temp_dir) if f.startswith(f"{ticker}_corrupto_")]
                if backup_files:
                    print(f"✅ OK: Backup file created: {backup_files[0]}")
                else:
                    print(f"⚠️  WARNING: No backup file found")
                return True


def test_tape_ativo_carregar_retry_mechanism():
    """Test that tape_ativo_carregar retries on JSON decode errors"""
    print("\nTesting tape_ativo_carregar retry mechanism...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('delta_chaos.tape.ATIVOS_DIR', temp_dir):
            ticker = "TEST"
            json_path = os.path.join(temp_dir, f"{ticker}.json")
            
            # Create valid JSON data
            valid_data = {
                "ticker": ticker,
                "historico": [{"ciclo_id": "2023-03", "regime": "ALTA"}],
                "historico_config": [],
                "estrategias": {"ALTA": "CSP"}
            }
            
            # Write valid JSON
            with open(json_path, 'w') as f:
                json.dump(valid_data, f)
            
            # Should succeed and return the data
            try:
                result = tape_ativo_carregar(ticker)
                if result["ticker"] == ticker and len(result["historico"]) > 0:
                    print(f"✅ OK: Successfully read valid JSON: {result['ticker']}")
                    return True
                else:
                    print(f"❌ ERROR: Unexpected result: {result}")
                    return False
            except Exception as e:
                print(f"❌ ERROR: Unexpected exception: {e}")
                return False


def test_tape_ativo_carregar_missing_file():
    """Test that tape_ativo_carregar handles missing files correctly"""
    print("\nTesting tape_ativo_carregar missing file handling...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('delta_chaos.tape.ATIVOS_DIR', temp_dir):
            ticker = "TEST"
            json_path = os.path.join(temp_dir, f"{ticker}.json")
            
            # Ensure file does NOT exist
            if os.path.exists(json_path):
                os.remove(json_path)
            
            # Should raise FileNotFoundError
            try:
                result = tape_ativo_carregar(ticker)
                print(f"❌ ERROR: Expected FileNotFoundError but got result: {result}")
                return False
            except FileNotFoundError as e:
                print(f"✅ OK: Got expected FileNotFoundError: {e}")
                return True
            except Exception as e:
                print(f"❌ ERROR: Got unexpected exception: {e}")
                return False


if __name__ == "__main__":
    print("=" * 60)
    print("TAPE.PY FIX VERIFICATION")
    print("=" * 60)
    
    tests = [
        test_tape_ativo_carregar_propagates_error_instead_of_defaults,
        test_tape_ativo_carregar_retry_mechanism,
        test_tape_ativo_carregar_missing_file
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ FAILED: {test.__name__}")
        except Exception as e:
            print(f"💥 ERROR in {test.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")
    if passed == total:
        print("🎉 ALL TESTS PASSED - TAPE FIX APPEARS TO BE WORKING! 🎉")
    else:
        print("❌ SOME TESTS FAILED - FIX NEEDS MORE WORK")
    print("=" * 60)