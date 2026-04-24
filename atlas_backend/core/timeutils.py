"""
Utilitários de tempo para o backend do ATLAS.

Motivação:
    O frontend (CalibracaoDrawer.jsx) usa `new Date(isoStr)` para converter
    timestamps em objetos Date. Strings ISO 8601 sem offset (ex.
    "2026-04-23T23:48:11") são interpretadas como hora LOCAL do browser pelo
    ECMAScript 2015+. Misturar `datetime.now().isoformat()` (local naive) com
    `datetime.utcnow().isoformat()` (UTC naive) dentro do mesmo payload leva
    a horários e durações incorretos no display.

Regra:
    Qualquer timestamp que vá ser serializado em JSON (persistido em disco)
    ou emitido via WebSocket DEVE usar `iso_utc()`. O sufixo `+00:00` dá
    ao browser a informação necessária para converter para a hora local
    do usuário sem ambiguidade.
"""

from datetime import datetime, timezone


def iso_utc() -> str:
    """Retorna timestamp ISO 8601 em UTC com offset explícito (+00:00).

    Exemplo: "2026-04-23T23:48:11.123456+00:00"
    """
    return datetime.now(timezone.utc).isoformat()
