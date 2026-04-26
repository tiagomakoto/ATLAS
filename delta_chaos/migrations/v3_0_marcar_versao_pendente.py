"""
Migration v3.0 — Marcar ativos v2.0 como pendentes de recalibração TUNE v3.0.

One-shot: executar uma única vez após deploy do TUNE v3.0.

Para cada JSON de ativo em ATIVOS_DIR que NÃO tem `tune_ranking_estrategia`,
adiciona:
  - tune_versao: "2.0"
  - tune_versao_pendente: true

Ativos que já têm `tune_ranking_estrategia` (i.e., já passaram pelo TUNE v3.0)
são ignorados.

Uso:
    python -m delta_chaos.migrations.v3_0_marcar_versao_pendente
    python -m delta_chaos.migrations.v3_0_marcar_versao_pendente --dry-run
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


def _carregar_ativos_dir() -> str:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from delta_chaos.init import ATIVOS_DIR
    return ATIVOS_DIR


def _patch_ativo(path: Path, dry_run: bool) -> str:
    """
    Lê o JSON do ativo e adiciona flags v2.0 se necessário.
    Retorna: "marcado" | "ja_v3" | "erro"
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as e:
        return f"erro:{e}"

    if "tune_ranking_estrategia" in cfg:
        return "ja_v3"

    cfg["tune_versao"] = "2.0"
    cfg["tune_versao_pendente"] = True

    if dry_run:
        return "marcado(dry)"

    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception as e:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        return f"erro:{e}"

    return "marcado"


def main():
    parser = argparse.ArgumentParser(description="Migration TUNE v3.0 — marcar ativos v2.0 como pendentes")
    parser.add_argument("--dry-run", action="store_true", help="Apenas exibe o que seria feito, sem gravar")
    args = parser.parse_args()

    ativos_dir = _carregar_ativos_dir()
    ativos_path = Path(ativos_dir)

    if not ativos_path.exists():
        print(f"[ERRO] ATIVOS_DIR não existe: {ativos_dir}")
        sys.exit(1)

    jsons = sorted(ativos_path.glob("*.json"))
    if not jsons:
        print(f"[AVISO] Nenhum arquivo .json encontrado em {ativos_dir}")
        sys.exit(0)

    contadores = {"marcado": 0, "ja_v3": 0, "erro": 0}

    for path in jsons:
        result = _patch_ativo(path, dry_run=args.dry_run)
        ticker = path.stem
        if result.startswith("marcado"):
            label = "PENDENTE (dry)" if args.dry_run else "MARCADO"
            print(f"  [{label}] {ticker}")
            contadores["marcado"] += 1
        elif result == "ja_v3":
            print(f"  [OK — v3.0] {ticker}")
            contadores["ja_v3"] += 1
        else:
            print(f"  [ERRO] {ticker}: {result}")
            contadores["erro"] += 1

    print()
    print(f"Total: {len(jsons)} ativos | "
          f"Marcados: {contadores['marcado']} | "
          f"Já v3.0: {contadores['ja_v3']} | "
          f"Erros: {contadores['erro']}")

    if args.dry_run:
        print("\n[DRY-RUN] Nenhuma alteração gravada.")

    if contadores["erro"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
