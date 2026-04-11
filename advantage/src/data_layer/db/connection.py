# connection.py
import sqlite3
import os
from pathlib import Path
from typing import Literal, Optional

DB_ROOT = Path(__file__).resolve().parents[3] / "data" / "raw"

DB_MAP: dict[str, Path] = {
    "preco_volume": DB_ROOT / "preco_volume.db",
    "macro": DB_ROOT / "macro.db",
    "alternativo": DB_ROOT / "alternativo.db",
    "portfolio": DB_ROOT / "portfolio.db",
}

# Variável global para armazenar caminho de banco de teste
_test_db_path: Optional[str] = None


def set_test_db_path(path: Optional[str]) -> None:
    """
    Define o caminho do banco de dados para modo teste.
    
    Args:
        path: Caminho do arquivo SQLite de teste. None para desativar modo teste.
    
    Exemplo:
        >>> set_test_db_path("/tmp/test.db")
        >>> # Todos os get_connection subsequentes usarão o banco de teste
        >>> set_test_db_path(None)  # Voltar ao modo normal
    """
    global _test_db_path
    _test_db_path = path


def get_connection(
    domain: Literal["preco_volume", "macro", "alternativo", "portfolio"],
    test_db_path: Optional[str] = None
) -> sqlite3.Connection:
    """
    Retorna conexão SQLite para o domínio especificado.
    Cria o arquivo se não existir.
    row_factory = sqlite3.Row para acesso por nome de coluna.
    
    Args:
        domain: Domínio do banco de dados (preco_volume, macro, alternativo, portfolio)
        test_db_path: Caminho opcional para banco de dados de teste. 
                     Se fornecido, sobrescreve o caminho padrão.
                     Também pode ser definido globalmente via set_test_db_path().
    
    Returns:
        sqlite3.Connection: Conexão configurada com row_factory e WAL mode
    
    Exemplo:
        >>> conn = get_connection("alternativo")
        >>> conn = get_connection("alternativo", test_db_path="/tmp/test.db")
    """
    # Prioridade: argumento > variável global > padrão
    if test_db_path:
        path = Path(test_db_path)
    elif _test_db_path:
        path = Path(_test_db_path)
    else:
        path = DB_MAP[domain]
    
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn