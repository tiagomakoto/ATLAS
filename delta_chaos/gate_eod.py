# ════════════════════════════════════════════════════════════════════
# DELTA CHAOS — GATE EOD v2.0
# Alterações em relação à v1.0:
# MIGRADO (P2): imports explícitos de init e tape — sem escopo global
# MIGRADO (P5): prints de inicialização sob if __name__ == "__main__"
# MANTIDO: 3 checks, retorno OPERAR/MONITORAR/BLOQUEADO/GATE VENCIDO
# ════════════════════════════════════════════════════════════════════

from delta_chaos.init import carregar_config, ATIVOS_DIR
from delta_chaos.tape import tape_ativo_carregar

# ── Emit events para ATLAS (JSONL) ───────────────────────────────────────
try:
    from delta_chaos.edge import emit_event
except ImportError:
    # Fallback se edge.py não disponível
    def emit_event(modulo, status, **kwargs):
        print(f"[EVENT] {modulo}: {status}")

# ── Logging ATLAS (graceful fallback) ─────────────────────────────────
try:
    from atlas_backend.core.terminal_stream import emit_log, emit_error
    _atlas_disponivel = True
except ImportError:
    def emit_log(msg, level="info"): print(f"[{level.upper()}] {msg}")
    def emit_error(e): print(f"[ERROR] {e}")
    _atlas_disponivel = False

# ════════════════════════════════════════════════════════════════════
# DELTA CHAOS — GATE EOD v1.0
# Verificação leve diária — sem backtest
# ════════════════════════════════════════════════════════════════════

import shutil
from datetime import date, datetime, timedelta

GATE_EOD_VALIDADE_DIAS  = 30
GATE_EOD_VALIDADE_AVISO = 20
REFLECT_BLOCK_STATES    = ("D", "E")
REFLECT_AVISO_STATES    = ("C",)
IR_MINIMO_EOD           = 0.10

def _dias_corridos(data_str: str) -> int:
    try:
        d = datetime.strptime(data_str[:10], "%Y-%m-%d").date()
        return (date.today() - d).days
    except Exception:
        return 9999

def _emoji(parecer: str) -> str:
    return {"OPERAR": "✓", "MONITORAR": "~",
            "BLOQUEADO": "✗", "GATE VENCIDO": "⚠"}.get(parecer, "?")

def gate_eod_verificar(ticker: str, verbose: bool = True) -> str:
    ticker = ticker.replace(".SA", "").upper()
    
    # ═══ Emitir evento de início para ATLAS frontend ═══
    emit_event("GATE", "start", ticker=ticker, acao="gate_eod")
    
    dados  = tape_ativo_carregar(ticker)
    hoje   = date.today().strftime("%Y-%m-%d")
    avisos    = []
    bloqueios = []
    sep       = "─" * 52
    sep2      = "═" * 52

    if verbose:
        print(f"\n  {sep2}")
        print(f"  GATE EOD v1.0 — {ticker} — {hoje}")
        print(f"  {sep2}")

    # [1/3] Último GATE completo
    hcfg     = dados.get("historico_config", [])

    # Aceita três formatos de campo — compatibilidade total
    gates_ok = [
        c for c in hcfg
        if "GATE" in c.get("modulo", "")
        and (
            c.get("resultado")    in ("OPERAR", "MONITORAR", "EXCLUÍDO")
            or c.get("gate_decisao") in ("OPERAR", "MONITORAR", "EXCLUÍDO")
            or c.get("valor_novo")   in ("OPERAR", "MONITORAR", "EXCLUÍDO")
        )
    ]

    if not gates_ok:
        bloqueios.append(
            "GATE completo nunca executado — "
            "rode o GATE antes de operar")
        ug_resultado = "N/A"
        ug_data      = "N/A"
        dias_gate    = 9999
    else:
        ug           = sorted(
            gates_ok, key=lambda x: x["data"])[-1]
        ug_resultado = (ug.get("resultado")
                        or ug.get("gate_decisao")
                        or ug.get("valor_novo")
                        or "N/A")
        ug_data      = ug.get("data", "N/A")
        dias_gate    = _dias_corridos(ug_data)
        if ug_resultado == "EXCLUÍDO":
            bloqueios.append(
                f"GATE retornou EXCLUÍDO em {ug_data}")
        elif dias_gate > GATE_EOD_VALIDADE_DIAS:
            bloqueios.append(
                f"GATE vencido — {dias_gate} dias "
                f"(limite {GATE_EOD_VALIDADE_DIAS}d)")
        elif dias_gate > GATE_EOD_VALIDADE_AVISO:
            avisos.append(
                f"GATE com {dias_gate} dias — "
                f"revalidar em breve")
        elif ug_resultado == "MONITORAR":
            avisos.append(
                f"GATE retornou MONITORAR em {ug_data}")

    if verbose:
        print(f"\n  [1/3] GATE completo")
        print(f"  {sep}")
        print(f"  Último resultado : {ug_resultado}")
        print(f"  Data execução    : {ug_data}")
        if dias_gate < 9999:
            st = ("✓ válido"   if dias_gate <= GATE_EOD_VALIDADE_AVISO
                  else "~ atenção" if dias_gate <= GATE_EOD_VALIDADE_DIAS
                  else "✗ vencido")
            print(f"  Dias desde GATE  : {dias_gate}d  {st}")

    # [2/3] Regime atual
    historico = dados.get("historico", [])
    if not historico:
        bloqueios.append(
            "Sem histórico ORBIT — rode o backtest primeiro")
        regime_atual = "N/A"
        sizing_atual = 0.0
        ir_atual     = 0.0
        ciclo_atual  = "N/A"
        est_hoje     = "N/A"
        mes_corrente = date.today().strftime("%Y-%m")
        defasagem    = 99
    else:
        uc           = sorted(
            historico, key=lambda x: x["ciclo_id"])[-1]
        regime_atual = uc.get("regime", "DESCONHECIDO")
        sizing_atual = float(uc.get("sizing", 0.0))
        ir_atual     = float(uc.get("ir", 0.0))
        ciclo_atual  = uc.get("ciclo_id", "N/A")
        estrategias  = dados.get("estrategias", {})
        est_hoje     = estrategias.get(regime_atual)

        # Defasagem ORBIT
        mes_corrente = date.today().strftime("%Y-%m")
        defasagem    = 0
        if ciclo_atual != "N/A":
            ano_c, mes_c = int(ciclo_atual[:4]), int(ciclo_atual[5:])
            ano_m, mes_m = int(mes_corrente[:4]), int(mes_corrente[5:])
            defasagem    = (ano_m - ano_c) * 12 + (mes_m - mes_c)
        else:
            defasagem = 99

        if defasagem >= 1:
            bloqueios.append(
                f"ORBIT defasado {defasagem}m — "
                f"atualizar antes de operar")

        if sizing_atual <= 0.0:
            bloqueios.append(
                f"Regime {regime_atual} com sizing=0")
        elif est_hoje is None:
            bloqueios.append(
                f"Regime {regime_atual} sem estratégia (null)")
        elif ir_atual < IR_MINIMO_EOD:
            avisos.append(
                f"IR {ir_atual:+.3f} abaixo do mínimo "
                f"{IR_MINIMO_EOD}")

    if verbose:
        print(f"\n  [2/3] Regime atual")
        print(f"  {sep}")
        print(f"  Ciclo            : {ciclo_atual}")
        print(f"  Regime           : {regime_atual}")
        print(f"  Sizing           : {sizing_atual:.1f}")
        print(f"  IR               : {ir_atual:+.4f}")
        print(f"  Estratégia hoje  : "
              f"{est_hoje or 'não configurada'}")
        print(f"  Mês corrente     : {mes_corrente}")
        print(f"  Defasagem        : {defasagem}m  "
              f"{'✓' if defasagem == 0 else '⚠' if defasagem == 1 else '✗'}")

    # [3/3] REFLECT
    reflect_state         = dados.get("reflect_state", "B")
    reflect_score         = float(dados.get("reflect_score", 0.0))
    reflect_hist          = dados.get("reflect_history", [])
    reflect_cycle_history = dados.get("reflect_cycle_history", {})
    ultimos = [
        r.get("state", "?")
        for r in sorted(
            reflect_hist,
            key=lambda x: x.get("ciclo_id", ""))[-5:]
    ]

    if not reflect_cycle_history:
        bloqueios.append(
            "REFLECT sem histórico de ciclos — "
            "calibração incompleta ou dados corrompidos")
    elif reflect_state in REFLECT_BLOCK_STATES:
        bloqueios.append(
            f"REFLECT state={reflect_state} "
            f"score={reflect_score:+.3f} — sizing=0")
    elif reflect_state in REFLECT_AVISO_STATES:
        avisos.append(
            f"REFLECT state={reflect_state} "
            f"score={reflect_score:+.3f} — monitorar")

    if verbose:
        print(f"\n  [3/3] REFLECT")
        print(f"  {sep}")
        print(f"  State atual      : {reflect_state}")
        print(f"  Score atual      : {reflect_score:+.3f}")
        if ultimos:
            print(f"  Últimos states   : {' | '.join(ultimos)}")

    # Parecer final
    if bloqueios:
        parecer = (
            "GATE VENCIDO"
            if dias_gate > GATE_EOD_VALIDADE_DIAS
            and len(bloqueios) == 1
            and "vencido" in bloqueios[0]
            else "BLOQUEADO")
    elif avisos:
        parecer = "MONITORAR"
    else:
        parecer = "OPERAR"

    if verbose:
        print(f"\n  {sep2}")
        print(f"  {_emoji(parecer)}  PARECER: {parecer}")
        if bloqueios:
            print(f"\n  Bloqueios:")
            for b in bloqueios:
                print(f"    ✗ {b}")
        if avisos:
            print(f"\n  Avisos:")
            for a in avisos:
                print(f"    ~ {a}")
        print(f"  {sep2}\n")

    # ═══ Emitir evento de conclusão para ATLAS frontend ═══
    emit_event("GATE", "done", ticker=ticker, parecer=parecer)

    return parecer

if __name__ == "__main__":
    print("✓ gate_eod v1.0 carregado")
    print("  gate_eod_verificar(ticker) → OPERAR | MONITORAR | BLOQUEADO | GATE VENCIDO")
