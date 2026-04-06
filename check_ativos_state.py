import sys
sys.stdout.reconfigure(encoding='utf-8')
import os, json

paths = {
    "config_dir": "G:\\Meu Drive\\Delta Chaos\\ativos",
    "ohlcv_dir": "G:\\Meu Drive\\Delta Chaos\\TAPE\\ohlcv",
    "history_dir": "G:\\Meu Drive\\Delta Chaos\\history",
    "book_dir": "G:\\Meu Drive\\Delta Chaos\\BOOK",
    "delta_chaos_base": "G:\\Meu Drive\\Delta Chaos",
}

for ticker in ["PETR4", "VALE3"]:
    fpath = os.path.join(paths["config_dir"], f"{ticker}.json")
    if os.path.exists(fpath):
        d = json.load(open(fpath, encoding="utf-8"))
        hist = d.get("historico", [])
        ultimo = hist[-1] if hist else {}
        hc = d.get("historico_config", [])
        tunes = [c for c in hc if "TUNE" in c.get("modulo", "")]
        last_tune = tunes[-1]["data"] if tunes else "nunca"
        print(f"{ticker}:")
        print(f"  ultimo_ciclo: {ultimo.get('ciclo_id', 'N/A')}")
        print(f"  regime: {ultimo.get('regime', 'N/A')}")
        print(f"  status: {d.get('status', 'N/A')}")
        print(f"  last_tune: {last_tune}")
        print(f"  historico len: {len(hist)}")
        
        # Check OHLCV parquet
        parquet_path = os.path.join(paths["ohlcv_dir"], f"{ticker}.parquet")
        if os.path.exists(parquet_path):
            import pandas as pd
            df = pd.read_parquet(parquet_path)
            print(f"  OHLCV last date: {df.index.max()}")
            print(f"  OHLCV month: {df.index.max().strftime('%Y-%m')}")
        else:
            print(f"  OHLCV parquet: NOT FOUND")
        print()
    else:
        print(f"{ticker}: arquivo nao encontrado")
        print()
