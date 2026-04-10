# connection.py
import sqlite3
from pathlib import Path
from typing import Literal

DB_ROOT = Path(__file__).resolve().parents[3] / "data" / "raw"

DB_MAP: dict[str, Path] = {
    "preco_volume": DB_ROOT / "preco_volume.db",
    "macro":        DB_ROOT / "macro.db",
    "alternativo":  "alternativo.db",
    "portfolio":    "portfolio.db",
}

def get_connection(
    domain: Literal["preco_volume", "macro", "alternativo", "portfolio"]
) -> sqlite3.Connection:
    """
    Retorna conexão SQLite para o domínio especificado.
    Cria o arquivo se não existir.
    row_factory = sqlite3.Row para acesso por nome de coluna.
    """
    path = DB_MAP[domain]
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn