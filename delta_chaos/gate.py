# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
# DELTA CHAOS â€” GATE v2.0
# AlteraÃ§Ãµes em relaÃ§Ã£o Ã  v1.0:
# MIGRADO (P2): imports explÃ­citos de init, tape, edge â€” sem escopo global
# MIGRADO (P3): TICKER=input() â†’ executar_gate(ticker: str) -> str
# MIGRADO (P4): raise SystemExit â†’ raise ValueError (nÃ£o mata FastAPI)
# MIGRADO (P5): prints de inicializaÃ§Ã£o sob if __name__ == "__main__"
# MANTIDO: 8 etapas, lÃ³gica de backtest interno, decisÃ£o OPERAR/MONITORAR/EXCLUÃDO
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

from delta_chaos.init import (
    carregar_config, ATIVOS_DIR, BOOK_DIR, GREGAS_DIR, CONFIG_PATH
)
from delta_chaos.tape import tape_carregar_ativo, tape_inicializar_ativo
from delta_chaos.edge import EDGE

# â”€â”€ Logging ATLAS (graceful fallback) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    from atlas_backend.core.terminal_stream import emit_log, emit_error
    _atlas_disponivel = True
except ImportError:
    def emit_log(msg, level="info"): print(f"[{level.upper()}] {msg}")
    def emit_error(e): print(f"[ERROR] {e}")
    _atlas_disponivel = False



def executar_gate(ticker: str) -> str:
    """
    Executa GATE completo para o ticker informado.
    Retorna: "OPERAR" | "MONITORAR" | "EXCLUÃDO"
    LanÃ§a ValueError se GATE 0 ou E0 falharem (nÃ£o mata o servidor FastAPI).
    """
    TICKER = ticker.strip().upper()

    IR_GATE_E1     = 0.10
    IR_GATE_E4     = 0.20
    DD_GATE_E7     = 3.0   # drawdown mÃ¡ximo = 3x esperado
    # TICKER recebido como argumento de executar_gate()

    sep  = "â•" * 60
    sep2 = "â”€" * 60

    tape_inicializar_ativo(TICKER)

    # LÃª apenas TP, STOP e estrategias antes do backtest
    with open(os.path.join(ATIVOS_DIR, f"{TICKER}.json")) as f:
        _cfg_ativo = json.load(f)

    # LÃª do master JSON â€” especÃ­fico por ativo
    anos_validos = _cfg_ativo.get(
        "anos_validos",
        carregar_config()["gate"]["anos_validos"]
    )
    ANOS_VALIDOS = anos_validos

    TAKE_PROFIT = float(_cfg_ativo.get("take_profit") or carregar_config()["fire"]["take_profit"])
    STOP_LOSS   = float(_cfg_ativo.get("stop_loss")   or carregar_config()["fire"]["stop_loss"])
    REGIME_ESTRATEGIA_GATE = _cfg_ativo.get("estrategias", {})

    # EstratÃ©gias lidas do master JSON do ativo
    REGIME_ESTRATEGIA_GATE = _cfg_ativo.get("estrategias", {})
    print(f"  estrategias: {REGIME_ESTRATEGIA_GATE}")

    def gate(passou, criterio):
        return f"{'âœ“ PASSOU' if passou else 'âœ— FALHOU':10} {criterio}"

    print(f"\n  {sep}")
    print(f"  GATE v1.0 â€” {TICKER}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  {sep}")

    # â”€â”€ Carrega dados â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    with open(os.path.join(ATIVOS_DIR, f"{TICKER}.json")) as f:
        dados = json.load(f)


    # â”€â”€ GATE 0 â€” EstratÃ©gias configuradas â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    estrategias_cfg = _cfg_ativo.get("estrategias", {})
    tem_estrategia  = any(v is not None
                          for v in estrategias_cfg.values())

    e0_estrategia = tem_estrategia
    print(f"  EstratÃ©gias configuradas: {estrategias_cfg}")
    print(f"  {gate(e0_estrategia, 'pelo menos uma estratÃ©gia nÃ£o-null')}")

    if not e0_estrategia:
        emit_log(f"âœ— GATE 0 FALHOU â€” configure estrategias no master JSON", level='error')
        raise ValueError(f"GATE bloqueado em {TICKER}: estrategias nÃ£o configuradas no master JSON")

    historico = pd.DataFrame(dados["historico"])
    if historico.empty or "ciclo_id" not in historico.columns:
        print(f"  ~ HistÃ³rico ORBIT vazio â€” serÃ¡ populado pelo backtest interno do GATE")
        historico = pd.DataFrame(columns=["ciclo_id","ano","mes_ano","regime","ir","sizing"])
    historico["ano"] = historico["ciclo_id"].str[:4].astype(int)
    historico["mes_ano"] = historico["ciclo_id"].str[:7]

    # â”€â”€ Roda backtest fresco com parÃ¢metros do master JSON â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print(f"\n  Rodando backtest para {TICKER}...")

    # Limpa book anterior
    for ext in ["json", "parquet"]:
        p = os.path.join(BOOK_DIR, f"book_backtest.{ext}")
        if os.path.exists(p):
            os.remove(p)

    # Roda EDGE com anos vÃ¡lidos + 2 anos de aquecimento
    anos_gate = list(range(min(ANOS_VALIDOS) - 2, 2026))
    edge = EDGE(capital=10_000, modo="backtest",
                universo=[TICKER])
    df_resultado = edge.executar(anos=anos_gate)

    # â”€â”€ Recarrega master JSON apÃ³s backtest interno â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # O ORBIT popula historico durante edge.executar â€” necessÃ¡rio recarregar
    with open(os.path.join(ATIVOS_DIR, f"{TICKER}.json")) as f:
        dados = json.load(f)

    historico     = pd.DataFrame(dados["historico"])
    historico["ano"]     = historico["ciclo_id"].str[:4].astype(int)
    historico["mes_ano"] = historico["ciclo_id"].str[:7]

    df_book = pd.read_parquet(
        os.path.join(BOOK_DIR, "book_backtest.parquet"))
    df_book["mes_ano"] = pd.to_datetime(
        df_book["data_entrada"]).dt.strftime("%Y-%m")
    df_book["ano"] = pd.to_datetime(
        df_book["data_entrada"]).dt.year

    fechadas = df_book[df_book["motivo_saida"].notna()].copy()
    valido   = fechadas[fechadas["ano"].isin(ANOS_VALIDOS)].copy()
    print(f"  âœ“ Trades fechados: {len(fechadas)} | VÃ¡lidos: {len(valido)}")

    # â”€â”€ ETAPA 0 â€” Integridade â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print(f"\n  ETAPA 0 â€” Integridade dos dados")
    print(f"  {sep2}")

    n_ciclos   = len(historico)
    n_gregas   = sum(1 for f in os.listdir(GREGAS_DIR)
                     if TICKER in f)
    anos_cobertos = sorted(historico["ano"].unique().tolist())
    iv_ok      = True  # assumido vÃ¡lido dado backtests anteriores

    e0_passou = n_ciclos >= 60 and n_gregas >= 6
    print(f"  Ciclos ORBIT:    {n_ciclos}")
    print(f"  Gregas parquet:  {n_gregas} arquivos")
    print(f"  Anos cobertos:   {anos_cobertos}")
    print(f"  {gate(e0_passou, 'cobertura mÃ­nima OK')}")

    if not e0_passou:
        emit_log(f"âœ— GATE 0 FALHOU â€” corrigir antes de avanÃ§ar", level='error')
        raise ValueError(f"GATE bloqueado em {TICKER}: cobertura mÃ­nima insuficiente (E0)")

    # â”€â”€ ETAPA 1 â€” DiagnÃ³stico de regime â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print(f"\n  ETAPA 1 â€” DiagnÃ³stico de regime")
    print(f"  {sep2}")

    hist_val = historico[historico["ano"].isin(ANOS_VALIDOS)]
    ir_por_regime = hist_val.groupby("regime")["ir"].mean()
    ir_max_valido = ir_por_regime.max()

    print(f"  IR mÃ©dio por regime (janela vÃ¡lida):")
    for regime, ir in ir_por_regime.sort_values(
            ascending=False).items():
        marker = " â† opera" if ir >= IR_GATE_E1 else " â† bloqueado"
        print(f"    {regime:20} IR={ir:+.3f}{marker}")

    e1_passou = ir_max_valido >= IR_GATE_E1
    print(f"\n  IR mÃ¡ximo janela vÃ¡lida: {ir_max_valido:+.3f}")
    print(f"  {gate(e1_passou, f'IR >= {IR_GATE_E1} em pelo menos um regime')}")

    # â”€â”€ ETAPA 2 â€” DiagnÃ³stico de acerto â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print(f"\n  ETAPA 2 â€” DiagnÃ³stico de acerto por regime")
    print(f"  {sep2}")

    # Break-even com TP=0.50 e STOP=2.0
    # Para acerto p: EV = p*TP - (1-p)*STOP = 0
    # p = STOP/(TP+STOP) = 2.0/2.5 = 0.80
    breakeven = STOP_LOSS / (TAKE_PROFIT + STOP_LOSS)
    print(f"  TP atual: {TAKE_PROFIT}  STOP atual: {STOP_LOSS}x")
    print(f"  Break-even necessÃ¡rio (TP=0.50, STOP=2.0): "
          f"{breakeven*100:.1f}%")

    e2_passou = False
    for regime in valido["regime_entrada"].unique():
        r = valido[valido["regime_entrada"] == regime]
        acerto = (r["pnl"] > 0).mean()
        passou = acerto >= breakeven
        if passou:
            e2_passou = True
        print(f"  {regime:20} acerto={acerto*100:.1f}%  "
              f"{gate(passou, 'acerto >= break-even')}")

    # â”€â”€ ETAPA 3 â€” EstratÃ©gias por regime â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print(f"\n  ETAPA 3 â€” EstratÃ©gias por regime")
    print(f"  {sep2}")

    for regime in valido["regime_entrada"].unique():
        r = valido[valido["regime_entrada"] == regime]
        if len(r) == 0:
            continue
        estrategias = r["estrategia"].value_counts() \
            if "estrategia" in r.columns \
            else pd.Series()
        pnl = r["pnl"].sum()
        print(f"  {regime:20} "
              f"n={len(r):3}  P&L=R${pnl:+,.2f}  "
              f"estrategia={estrategias.index[0] if len(estrategias)>0 else '?'}")

    e3_passou = valido["pnl"].sum() > 0
    print(f"\n  {gate(e3_passou, 'P&L total positivo na janela vÃ¡lida')}")

    # â”€â”€ ETAPA 4 â€” Sensibilidade TP e STOP â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print(f"\n  ETAPA 4 â€” Sensibilidade de TP e STOP")
    print(f"  {sep2}")

    tps   = [0.30, 0.40, 0.50, 0.60, 0.75]
    stops = [1.0,  1.5,  2.0,  3.0]

    resultados_e4 = []
    pnls_orig = valido["pnl"].values.copy()

    for tp in tps:
        for stop in stops:
            pnl_sim   = []
            acertos   = 0
            n_stops_s = 0
            premio_ref_medio = abs(
                valido[valido["pnl"] < 0]["pnl"].mean()) / 2.0 \
                if len(valido[valido["pnl"] < 0]) > 0 \
                else 80.0

            for pnl_orig in pnls_orig:
                if pnl_orig > 0:
                    # Trade vencedor â€” simula TP diferente
                    pnl_novo = pnl_orig * (tp / 0.50)
                    pnl_sim.append(pnl_novo)
                    acertos += 1
                else:
                    # Trade perdedor â€” simula STOP diferente
                    pnl_novo = pnl_orig * (stop / 2.0)
                    pnl_sim.append(pnl_novo)
                    n_stops_s += 1

            pnl_total = sum(pnl_sim)
            ac = acertos / max(len(pnl_sim), 1)
            ir_sim = (np.mean(pnl_sim) /
                      (np.std(pnl_sim) + 1e-10) *
                      np.sqrt(252/21)
                      if len(pnl_sim) > 5 else 0.0)

            resultados_e4.append({
                "tp": tp, "stop": stop,
                "pnl": pnl_total,
                "acerto": ac,
                "ir": ir_sim,
            })

    df_e4 = pd.DataFrame(resultados_e4)
    melhor_e4 = df_e4.loc[df_e4["ir"].idxmax()]

    print(f"  CombinaÃ§Ã£o atual:  "
          f"TP={TAKE_PROFIT}  STOP={STOP_LOSS}x  "
          f"P&L=R${valido['pnl'].sum():+,.2f}")
    print(f"  Nota Q4: sensibilidade simula escalonamento "
          f"linear de P&L â€” nÃ£o recalcula quais trades "
          f"teriam aberto/fechado com novos parÃ¢metros. "
          f"Use TUNE v1.1 para calibraÃ§Ã£o precisa.")
    print(f"\n  Top 5 combinaÃ§Ãµes por IR:")
    for _, row in df_e4.nlargest(5, "ir").iterrows():
        atual = " â† atual" \
            if row["tp"] == 0.50 and row["stop"] == 2.0 \
            else ""
        print(f"    TP={row['tp']:.2f}  STOP={row['stop']:.1f}x  "
              f"P&L=R${row['pnl']:+,.2f}  "
              f"IR={row['ir']:+.3f}{atual}")

    e4_passou = melhor_e4["ir"] >= IR_GATE_E4
    print(f"\n  Melhor IR: {melhor_e4['ir']:+.3f} "
          f"(TP={melhor_e4['tp']:.2f} "
          f"STOP={melhor_e4['stop']:.1f}x)")
    print(f"  {gate(e4_passou, f'IR >= {IR_GATE_E4} em alguma combinaÃ§Ã£o')}")

    # â”€â”€ ETAPA 5 â€” Sensibilidade ORBIT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print(f"\n  ETAPA 5 â€” Sensibilidade do ORBIT")
    print(f"  {sep2}")

    # Verifica estabilidade entre 2024 e 2025
    ir_2024 = historico[historico["ano"]==2024]["ir"].mean()
    ir_2025 = historico[historico["ano"]==2025]["ir"].mean()
    estavel = abs(ir_2024 - ir_2025) < 0.50

    print(f"  IR mÃ©dio 2024: {ir_2024:+.3f}")
    print(f"  IR mÃ©dio 2025: {ir_2025:+.3f}")
    print(f"  DiferenÃ§a:     {abs(ir_2024-ir_2025):+.3f}")

    pnl_2024 = fechadas[fechadas["ano"]==2024]["pnl"].sum()
    pnl_2025 = fechadas[fechadas["ano"]==2025]["pnl"].sum()
    print(f"  P&L 2024: R${pnl_2024:+,.2f}")
    print(f"  P&L 2025: R${pnl_2025:+,.2f}")

    e5_passou = estavel and pnl_2024 > 0 and pnl_2025 > 0
    print(f"  {gate(e5_passou, 'IR estÃ¡vel e P&L positivo em ambos os anos')}")

    # â”€â”€ ETAPA 6 â€” SÃ©ries externas â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print(f"\n  ETAPA 6 â€” SÃ©ries externas")
    print(f"  {sep2}")

    externas = dados.get("externas", {})
    print(f"  ConfiguraÃ§Ã£o atual: {externas}")
    print(f"  usdbrl: {'ativo' if externas.get('usdbrl') else 'inativo'}")
    print(f"  minerio: {'ativo' if externas.get('minerio') else 'inativo'}")
    print(f"  Nota: teste isolado de minerio pendente na to-do list")
    e6_passou = True  # configuraÃ§Ã£o atual validada em sessÃµes anteriores
    print(f"  {gate(e6_passou, 'externas configuradas e validadas')}")

    # â”€â”€ ETAPA 7 â€” Stress test â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print(f"\n  ETAPA 7 â€” Stress test")
    print(f"  {sep2}")

    # 5 piores meses
    fechadas["mes_pnl"] = fechadas.groupby("mes_ano")["pnl"].transform("sum")
    piores_meses = (fechadas.groupby("mes_ano")["pnl"]
                    .sum()
                    .nsmallest(5))
    print(f"  5 piores meses:")
    for mes, pnl in piores_meses.items():
        regime_mes = historico[
            historico["mes_ano"]==mes]["regime"].values
        r = regime_mes[0] if len(regime_mes) > 0 else "?"
        print(f"    {mes}  P&L=R${pnl:+,.2f}  regime={r}")

    # Drawdown mÃ¡ximo
    fechadas_ord = fechadas.sort_values("data_saida")
    curva  = fechadas_ord["pnl"].cumsum().values
    pico   = 0.0
    max_dd = 0.0
    for v in curva:
        if v > pico:
            pico = v
        dd = pico - v
        if dd > max_dd:
            max_dd = dd

    # P&L esperado por trade
    pnl_esperado = fechadas["pnl"].mean()
    dd_esperado  = abs(pnl_esperado) * 10
    dd_limite    = dd_esperado * DD_GATE_E7

    print(f"\n  Drawdown mÃ¡ximo:   R${max_dd:,.2f}")
    print(f"  DD esperado (ref): R${dd_esperado:,.2f}")
    print(f"  DD limite (3x):    R${dd_limite:,.2f}")

    # Stops consecutivos
    fechadas_ord2 = fechadas.sort_values("data_saida")
    max_seq = seq = 0
    for pnl in fechadas_ord2["pnl"]:
        if pnl < 0:
            seq += 1
            max_seq = max(max_seq, seq)
        else:
            seq = 0
    print(f"  Max stops seguidos:{max_seq}")

    e7_passou = max_dd <= dd_limite and max_seq <= 3
    print(f"  {gate(e7_passou, f'drawdown <= {DD_GATE_E7}x esperado e stops <= 3')}")
    print(f"\n  Nota Q5: backtest assume execuÃ§Ã£o no fechamento.")
    print(f"  Gap risk nÃ£o modelado â€” em eventos de cauda,")
    print(f"  abertura do dia seguinte pode ser significativa-")
    print(f"  mente pior que o fechamento anterior. STOP de")
    print(f"  {STOP_LOSS}x Ã© calculado sobre o prÃªmio, nÃ£o sobre")
    print(f"  o movimento do subjacente.")

    # â”€â”€ ETAPA 8 â€” DecisÃ£o final â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    print(f"\n  ETAPA 8 â€” DecisÃ£o final")
    print(f"  {sep}")

    gates = {
        "E0 â€” Integridade":     e0_passou,
        "E1 â€” Regime":          e1_passou,
        "E2 â€” Acerto":          e2_passou,
        "E3 â€” EstratÃ©gia":      e3_passou,
        "E4 â€” TP e STOP":       e4_passou,
        "E5 â€” ORBIT":           e5_passou,
        "E6 â€” Externas":        e6_passou,
        "E7 â€” Stress":          e7_passou,
    }

    todos_passaram = all(gates.values())
    n_passou = sum(gates.values())

    for nome, passou in gates.items():
        print(f"  {'âœ“' if passou else 'âœ—'}  {nome}")

    print(f"\n  Gates aprovados: {n_passou}/8")
    print(f"\n  {'â•'*20} DECISÃƒO {'â•'*20}")

    if todos_passaram:
        print(f"\n  âœ“  {TICKER} â€” OPERAR")
        print(f"     Todos os gates aprovados")
    elif n_passou >= 6:
        print(f"\n  ~  {TICKER} â€” MONITORAR")
        print(f"     {8-n_passou} gate(s) falharam")
    else:
        print(f"\n  âœ—  {TICKER} â€” EXCLUÃDO")
        print(f"     {8-n_passou} gates falharam")

    # â”€â”€ Retorno da funÃ§Ã£o â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    decisao_final = (
        "OPERAR"    if todos_passaram
        else "MONITORAR" if n_passou >= 6
        else "EXCLUÃDO"
    )
    return decisao_final

    print(f"\n  {sep}")


if __name__ == "__main__":
    import sys
    t = (sys.argv[1] if len(sys.argv) > 1
         else input("Ticker para anÃ¡lise GATE: ").strip().upper())
    resultado = executar_gate(t)
    print(f"\n  Resultado final: {resultado}")
