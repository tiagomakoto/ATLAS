#!/usr/bin/env python
# test_concorrencia.py
import asyncio
import json
from pathlib import Path
import sys

# Adicionar raiz do ATLAS ao path
ATLAS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ATLAS_ROOT))

from atlas_backend.core.dc_runner import run_orbit_update

async def main():
    tickers = ["VALE3", "PETR4"]  # ativos do universo para teste
    print(f"Testando concorrência com tickers: {tickers}")
    
    # Verificar estado do tmp antes
    tmp_dir = ATLAS_ROOT / "tmp"
    print(f"TMP_DIR: {tmp_dir.resolve()}")
    if tmp_dir.exists():
        before = list(tmp_dir.iterdir())
        print(f"Arquivos no tmp antes: {[f.name for f in before]}")
    else:
        print("Tmp não existe antes")
    
    # Executar em paralelo (cada um gera seu próprio run_id)
    tasks = [run_orbit_update(ticker, anos=[2025]) for ticker in tickers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for ticker, result in zip(tickers, results):
        if isinstance(result, Exception):
            print(f"[FAIL] {ticker} falhou: {result}")
        else:
            print(f"[OK] {ticker} concluído: status={result.get('status')}")
    
    # Verificar arquivos de eventos gerados
    tmp_dir = ATLAS_ROOT / "tmp"
    print(f"TMP_DIR: {tmp_dir.resolve()}")
    if not tmp_dir.exists():
        print(f"Diretório tmp não encontrado: {tmp_dir}")
        return
    
    # Aguardar um momento para garantir que os arquivos foram escritos
    import time
    time.sleep(1)
    
    # Listar arquivos events_*.jsonl no tmp
    event_files = list(tmp_dir.glob("events_*.jsonl"))
    print(f"Arquivos de eventos no tmp: {[f.name for f in event_files]}")
    print(f"\nArquivos de eventos criados: {len(event_files)}")
    
    # Agrupar por run_id
    run_files = {}
    for f in event_files:
        run_id = f.stem.replace("events_", "")
        run_files.setdefault(run_id, []).append(f)
    
    print(f"Run IDs distintos: {len(run_files)}")
    for run_id, files in run_files.items():
        print(f"  • {run_id}: {len(files)} arquivo(s)")
        # Verificar consistência de run_id dentro de cada arquivo
        for f in files:
            with open(f, "r", encoding="utf-8") as file:
                lines = file.readlines()
            file_run_ids = set()
            for line in lines[:10]:  # apenas primeiras 10 linhas
                if line.strip():
                    try:
                        event = json.loads(line)
                        file_run_ids.add(event.get("run_id"))
                    except json.JSONDecodeError:
                        pass
            if len(file_run_ids) > 1:
                print(f"    ⚠️ {f.name}: múltiplos run_ids detectados: {file_run_ids}")
            elif file_run_ids:
                print(f"    ✓ {f.name}: run_id={list(file_run_ids)[0]}")
    
    # Se temos 2 tickers, esperamos pelo menos 2 arquivos distintos
    expected = len(tickers)
    if len(run_files) >= expected:
        print(f"\n[PASS] Teste passou: {len(run_files)} run(s) distinto(s) para {expected} ticker(s)")
    else:
        print(f"\n[FAIL] Teste falhou: esperado pelo menos {expected} run(s) distinto(s), mas encontrado {len(run_files)}")

if __name__ == "__main__":
    asyncio.run(main())
