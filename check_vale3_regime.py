import json, os
from delta_chaos.init import ATIVOS_DIR
import tempfile

ativos = ["VALE3", "PETR4", "BOVA11", "BBAS3"]

for ticker in ativos:
    path = os.path.join(ATIVOS_DIR, f"{ticker}.json")
    with open(path, encoding="utf-8") as f:
        dados = json.load(f)

    alterados = 0
    for ciclo in dados["historico"]:
        if ciclo.get("regime_estrategia") is None:
            ciclo["regime_estrategia"] = ciclo.get("regime")
            alterados += 1

    # Escrita atômica
    dir_ = os.path.dirname(path)
    with tempfile.NamedTemporaryFile("w", dir=dir_, suffix=".tmp",
                                     delete=False, encoding="utf-8") as tf:
        json.dump(dados, tf, indent=2, ensure_ascii=False, default=str)
        tmp_path = tf.name
    os.replace(tmp_path, path)

    print(f"{ticker}: {alterados} ciclos migrados")