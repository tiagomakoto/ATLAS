import sys
import asyncio
import json
import os
import glob as glob_mod
import uvicorn

# ── Diretório dos ativos ──────────────────────────────────────────
ATIVOS_DIR = r"G:\Meu Drive\Delta Chaos\ativos"

# ── Reset de histórico (simula última parametrização há ~1 ano) ───
def reset_historico_ativos():
    """Remove ciclos de 2025-03 até 2026-04 do historico de cada ativo."""
    if not os.path.isdir(ATIVOS_DIR):
        print(f"[WARN]  Diretorio de ativos nao encontrado: {ATIVOS_DIR}")
        return

    json_files = glob_mod.glob(os.path.join(ATIVOS_DIR, "*.json"))
    if not json_files:
        print("[WARN]  Nenhum arquivo JSON encontrado no diretorio de ativos.")
        return

    ciclo_inicio = "2025-03"
    ciclo_fim    = "2026-04"
    total_resetados = 0

    for filepath in sorted(json_files):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                dados = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[ERRO] Erro ao ler {os.path.basename(filepath)}: {e}")
            continue

        historico = dados.get("historico", [])
        if not historico:
            print(f"[INFO] {os.path.basename(filepath)}: sem historico -- pulando.")
            continue

        original_len = len(historico)
        novo_historico = [
            c for c in historico
            if not (ciclo_inicio <= c.get("ciclo_id", "") <= ciclo_fim)
        ]
        removidos = original_len - len(novo_historico)

        if removidos == 0:
            print(f"[INFO] {os.path.basename(filepath)}: nenhum ciclo no periodo {ciclo_inicio}-{ciclo_fim} -- pulando.")
            continue

        dados["historico"] = novo_historico

        # Limpar reflect_cycle_history dos mesmos ciclos removidos
        reflect_hist = dados.get("reflect_cycle_history", {})
        if reflect_hist:
            dados["reflect_cycle_history"] = {
                k: v for k, v in reflect_hist.items()
                if not (ciclo_inicio <= k <= ciclo_fim)
            }

        total_resetados += removidos

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
            ultimo = novo_historico[-1]["ciclo_id"] if novo_historico else "vazio"
            print(f"[OK] {os.path.basename(filepath)}: {removidos} ciclos removidos -- ultimo ciclo: {ultimo}")
        except OSError as e:
            print(f"[ERRO] Erro ao salvar {os.path.basename(filepath)}: {e}")

    print(f"\n[RESET] Concluido -- {total_resetados} ciclos removidos no total.\n")


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if __name__ == "__main__":
    # Sempre resetar ciclos para 2025-02 — permite debugar bloco mensal indefinidamente
    ##reset_historico_ativos()

    print("🚀 Iniciando ATLAS Server com WindowsProactor (Suporte a Subprocessos AsyncHabilitado)")
    uvicorn.run("atlas_backend.main:app", host="0.0.0.0", port=8000, reload=True)
