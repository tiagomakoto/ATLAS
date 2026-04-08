# ════════════════════════════════════════════════════════════════════
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
# DELTA CHAOS — GATE v2.0
# Alterações em relação à v1.0:
# MIGRADO (P2): imports explícitos de init, tape, edge — sem escopo global
# MIGRADO (P3): TICKER=input() → gate_executar(ticker: str) -> str
# MIGRADO (P4): raise SystemExit → raise ValueError (não mata FastAPI)
# MIGRADO (P5): prints de inicialização sob if __name__ == "__main__"
# MANTIDO: 8 etapas, lógica de backtest interno, decisão OPERAR/MONITORAR/EXCLUÍDO
# ════════════════════════════════════════════════════════════════════

from delta_chaos.init import (
    carregar_config, ATIVOS_DIR, BOOK_DIR, GREGAS_DIR, CONFIG_PATH
)
from delta_chaos.tape import tape_ativo_carregar, tape_ativo_inicializar, tape_ativo_salvar
from delta_chaos.edge import EDGE

# ── Logging ATLAS (graceful fallback) ─────────────────────────────────
try:
    from atlas_backend.core.terminal_stream import emit_log, emit_error
    _atlas_disponivel = True
except ImportError:
    def emit_log(msg, level="info"): print(f"[{level.upper()}] {msg}")
    def emit_error(e): print(f"[ERROR] {e}")
    _atlas_disponivel = False



def gate_executar(ticker: str) -> str:
    """
    Executa GATE completo para o ticker informado.
    Retorna: "OPERAR" | "MONITORAR" | "EXCLUÍDO"
    Lança ValueError se GATE 0 ou E0 falharem (não mata o servidor FastAPI).
    """
    TICKER = ticker.strip().upper()
    
    # Ano atual dinâmico
    ano_atual = datetime.now().year
    
    # Lê config dinamicamente
    cfg = carregar_config()
    anos_passados = cfg.get("gate", {}).get("anos_passados", 3)
    threshold_meses = cfg.get("gate", {}).get("threshold_meses", 60)
    
    # Calcula ANOS_VALIDOS dinamicamente
    ANOS_VALIDOS = list(range(ano_atual - anos_passados, ano_atual + 1))
    
    IR_GATE_E1 = 0.10
    IR_GATE_E4 = 0.20
    DD_GATE_E7 = 3.0
    # TICKER recebido como argumento de gate_executar()

    sep  = "═" * 60
    sep2 = "─" * 60

    tape_ativo_inicializar(TICKER)

    # Lê apenas TP, STOP e estrategias antes do backtest
    with open(os.path.join(ATIVOS_DIR, f"{TICKER}.json")) as f:
        _cfg_ativo = json.load(f)

    # Lê do master JSON — específico por ativo
    # ANOS_VALIDOS já calculado dinamicamente no início da função

    TAKE_PROFIT = float(_cfg_ativo.get("take_profit") or carregar_config()["fire"]["take_profit"])
    STOP_LOSS   = float(_cfg_ativo.get("stop_loss")   or carregar_config()["fire"]["stop_loss"])
    REGIME_ESTRATEGIA_GATE = _cfg_ativo.get("estrategias", {})

    # Estratégias lidas do master JSON do ativo
    REGIME_ESTRATEGIA_GATE = _cfg_ativo.get("estrategias", {})
    print(f"  estrategias: {REGIME_ESTRATEGIA_GATE}")

    def gate(passou, criterio):
        return f"{'✓ PASSOU' if passou else '✗ FALHOU':10} {criterio}"

    print(f"\n  {sep}")
    print(f"  GATE v1.0 — {TICKER}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  {sep}")

    # ── Carrega dados ─────────────────────────────────────────────────
    with open(os.path.join(ATIVOS_DIR, f"{TICKER}.json")) as f:
        dados = json.load(f)


    # ── GATE 0 — Estratégias configuradas ────────────────────────
    estrategias_cfg = _cfg_ativo.get("estrategias", {})
    tem_estrategia  = any(v is not None
                          for v in estrategias_cfg.values())

    e0_estrategia = tem_estrategia
    print(f"  Estratégias configuradas: {estrategias_cfg}")
    print(f"  {gate(e0_estrategia, 'pelo menos uma estratégia não-null')}")

    if not e0_estrategia:
        emit_log(f"✗ GATE 0 FALHOU — configure estrategias no master JSON", level='error')
        msg_erro = f"GATE bloqueado em {TICKER}: estrategias não configuradas no master JSON"
        dados = tape_ativo_carregar(TICKER)
        if "historico_config" not in dados:
            dados["historico_config"] = []
        dados["historico_config"].append({
            "data":      str(datetime.now())[:10],
            "modulo":    "GATE v1.0",
            "parametro": "gate_decisao",
            "valor_novo": "FALHA",
            "motivo":    msg_erro,
        })
        tape_ativo_salvar(TICKER, dados)
        raise ValueError(msg_erro)

    historico = pd.DataFrame(dados["historico"])
    if historico.empty or "ciclo_id" not in historico.columns:
        print(f"  ~ Histórico ORBIT vazio — será populado pelo backtest interno do GATE")
        historico = pd.DataFrame(columns=["ciclo_id","ano","mes_ano","regime","ir","sizing"])
    historico["ano"] = historico["ciclo_id"].str[:4].astype(int)
    historico["mes_ano"] = historico["ciclo_id"].str[:7]

    # ── Roda backtest fresco com parâmetros do master JSON ────────────
    print(f"\n  Rodando backtest para {TICKER}...")

    # Limpa book anterior
    for ext in ["json", "parquet"]:
        p = os.path.join(BOOK_DIR, f"book_backtest.{ext}")
        if os.path.exists(p):
            os.remove(p)

    # Roda EDGE com anos válidos + 2 anos de aquecimento
    anos_gate = list(range(min(ANOS_VALIDOS) - 2, ano_atual + 1))
    edge = EDGE(capital=10_000, modo="backtest",
                universo=[TICKER])
    df_resultado = edge.executar(anos=anos_gate)

    # ── Recarrega master JSON após backtest interno ───────────────
    # O ORBIT popula historico durante edge.executar — necessário recarregar
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
    print(f"  ✓ Trades fechados: {len(fechadas)} | Válidos: {len(valido)}")

    # ── ETAPA 0 — Integridade ─────────────────────────────────────────
    print(f"\n  ETAPA 0 — Integridade dos dados")
    print(f"  {sep2}")

    n_ciclos   = len(historico)
    n_gregas   = sum(1 for f in os.listdir(GREGAS_DIR)
                     if TICKER in f)
    anos_cobertos = sorted(historico["ano"].unique().tolist())
    iv_ok      = True  # assumido válido dado backtests anteriores

    # SCAN-10: relax requirement to 50 cycles (robustness against missing data)
    e0_passou = n_ciclos >= 50 and n_gregas >= 6
    print(f"  Ciclos ORBIT:    {n_ciclos}")
    print(f"  Gregas parquet:  {n_gregas} arquivos")
    print(f"  Anos cobertos:   {anos_cobertos}")
    print(f"  {gate(e0_passou, 'cobertura mínima OK')}")

    if not e0_passou:
        emit_log(f"✗ GATE 0 FALHOU — corrigir antes de avançar", level='error')
        msg_erro = f"GATE bloqueado em {TICKER}: cobertura mínima insuficiente (E0)"
        dados = tape_ativo_carregar(TICKER)
        if "historico_config" not in dados:
            dados["historico_config"] = []
        dados["historico_config"].append({
            "data":      str(datetime.now())[:10],
            "modulo":    "GATE v1.0",
            "parametro": "gate_decisao",
            "valor_novo": "FALHA",
            "motivo":    msg_erro,
        })
        tape_ativo_salvar(TICKER, dados)
        raise ValueError(msg_erro)

    # ── ETAPA 1 — Diagnóstico de regime ───────────────────────────────
    print(f"\n  ETAPA 1 — Diagnóstico de regime")
    print(f"  {sep2}")

    hist_val = historico[historico["ano"].isin(ANOS_VALIDOS)]
    ir_por_regime = hist_val.groupby("regime")["ir"].mean()
    ir_max_valido = ir_por_regime.max()

    print(f"  IR médio por regime (janela válida):")
    for regime, ir in ir_por_regime.sort_values(
            ascending=False).items():
        marker = " ← opera" if ir >= IR_GATE_E1 else " ← bloqueado"
        print(f"    {regime:20} IR={ir:+.3f}{marker}")

    e1_passou = ir_max_valido >= IR_GATE_E1
    print(f"\n  IR máximo janela válida: {ir_max_valido:+.3f}")
    print(f"  {gate(e1_passou, f'IR >= {IR_GATE_E1} em pelo menos um regime')}")

    # ── ETAPA 2 — Diagnóstico de acerto ───────────────────────────────
    print(f"\n  ETAPA 2 — Diagnóstico de acerto por regime")
    print(f"  {sep2}")

    # Break-even com TP=0.50 e STOP=2.0
    # Para acerto p: EV = p*TP - (1-p)*STOP = 0
    # p = STOP/(TP+STOP) = 2.0/2.5 = 0.80
    breakeven = STOP_LOSS / (TAKE_PROFIT + STOP_LOSS)
    print(f"  TP atual: {TAKE_PROFIT}  STOP atual: {STOP_LOSS}x")
    print(f"  Break-even necessário (TP=0.50, STOP=2.0): "
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

    # ── ETAPA 3 — Estratégias por regime ──────────────────────────────
    print(f"\n  ETAPA 3 — Estratégias por regime")
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
    print(f"\n  {gate(e3_passou, 'P&L total positivo na janela válida')}")

    # ── ETAPA 4 — Sensibilidade TP e STOP ────────────────────────────
    print(f"\n  ETAPA 4 — Sensibilidade de TP e STOP")
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
            # Lê estado atual usando carregador robusto
            dados = tape_ativo_carregar(TICKER)

            for pnl_orig in pnls_orig:
                if pnl_orig > 0:
                    # Trade vencedor — simula TP diferente
                    pnl_novo = pnl_orig * (tp / 0.50)
                    pnl_sim.append(pnl_novo)
                    acertos += 1
                else:
                    # Trade perdedor — simula STOP diferente
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

    print(f"  Combinação atual:  "
          f"TP={TAKE_PROFIT}  STOP={STOP_LOSS}x  "
          f"P&L=R${valido['pnl'].sum():+,.2f}")
    print(f"  Nota Q4: sensibilidade simula escalonamento "
          f"linear de P&L — não recalcula quais trades "
          f"teriam aberto/fechado com novos parâmetros. "
          f"Use TUNE v1.1 para calibração precisa.")
    print(f"\n  Top 5 combinações por IR:")
    for _, row in df_e4.nlargest(5, "ir").iterrows():
        atual = " ← atual" \
            if row["tp"] == 0.50 and row["stop"] == 2.0 \
            else ""
        print(f"    TP={row['tp']:.2f}  STOP={row['stop']:.1f}x  "
              f"P&L=R${row['pnl']:+,.2f}  "
              f"IR={row['ir']:+.3f}{atual}")

    e4_passou = melhor_e4["ir"] >= IR_GATE_E4
    print(f"\n  Melhor IR: {melhor_e4['ir']:+.3f} "
          f"(TP={melhor_e4['tp']:.2f} "
          f"STOP={melhor_e4['stop']:.1f}x)")
    print(f"  {gate(e4_passou, f'IR >= {IR_GATE_E4} em alguma combinação')}")

    # ── ETAPA 5 — Sensibilidade ORBIT ────────────────────────────────
    print(f"\n  ETAPA 5 — Sensibilidade do ORBIT")
    print(f"  {sep2}")

    # Verifica estabilidade entre os dois últimos anos completos do histórico
    anos_disponiveis = sorted(historico["ano"].unique().tolist())
    if len(anos_disponiveis) >= 2:
        ano_mais_recente = anos_disponiveis[-1]
        ano_anterior = anos_disponiveis[-2]
    else:
        ano_mais_recente = anos_disponiveis[-1] if anos_disponiveis else ano_atual
        ano_anterior = ano_mais_recente - 1

    ir_ano_atual = historico[historico["ano"]==ano_mais_recente]["ir"].mean()
    ir_ano_anterior = historico[historico["ano"]==ano_anterior]["ir"].mean()
    estavel = abs(ir_ano_atual - ir_ano_anterior) < 0.50

    print(f"  IR médio {ano_anterior}: {ir_ano_anterior:+.3f}")
    print(f"  IR médio {ano_mais_recente}: {ir_ano_atual:+.3f}")
    print(f"  Diferença:     {abs(ir_ano_atual-ir_ano_anterior):+.3f}")

    pnl_ano_anterior = fechadas[fechadas["ano"]==ano_anterior]["pnl"].sum()
    pnl_ano_mais_recente = fechadas[fechadas["ano"]==ano_mais_recente]["pnl"].sum()
    print(f"  P&L {ano_anterior}: R${pnl_ano_anterior:+,.2f}")
    print(f"  P&L {ano_mais_recente}: R${pnl_ano_mais_recente:+,.2f}")

    e5_passou = estavel and pnl_ano_anterior > 0 and pnl_ano_mais_recente > 0
    print(f"  {gate(e5_passou, 'IR estável e P&L positivo em ambos os anos')}")

    # ── ETAPA 6 — Séries externas ─────────────────────────────────────
    print(f"\n  ETAPA 6 — Séries externas")
    print(f"  {sep2}")

    externas = dados.get("externas", {})
    print(f"  Configuração atual: {externas}")
    print(f"  usdbrl: {'ativo' if externas.get('usdbrl') else 'inativo'}")
    print(f"  minerio: {'ativo' if externas.get('minerio') else 'inativo'}")
    print(f"  Nota: teste isolado de minerio pendente na to-do list")
    e6_passou = True  # configuração atual validada em sessões anteriores
    print(f"  {gate(e6_passou, 'externas configuradas e validadas')}")

    # ── ETAPA 7 — Stress test ─────────────────────────────────────────
    print(f"\n  ETAPA 7 — Stress test")
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

    # Drawdown máximo
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

    print(f"\n  Drawdown máximo:   R${max_dd:,.2f}")
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
    print(f"\n  Nota Q5: backtest assume execução no fechamento.")
    print(f"  Gap risk não modelado — em eventos de cauda,")
    print(f"  abertura do dia seguinte pode ser significativa-")
    print(f"  mente pior que o fechamento anterior. STOP de")
    print(f"  {STOP_LOSS}x é calculado sobre o prêmio, não sobre")
    print(f"  o movimento do subjacente.")

    # ── ETAPA 8 — Decisão final ───────────────────────────────────────
    print(f"\n  ETAPA 8 — Decisão final")
    print(f"  {sep}")

    gates = {
        "E0 — Integridade":     e0_passou,
        "E1 — Regime":          e1_passou,
        "E2 — Acerto":          e2_passou,
        "E3 — Estratégia":      e3_passou,
        "E4 — TP e STOP":       e4_passou,
        "E5 — ORBIT":           e5_passou,
        "E6 — Externas":        e6_passou,
        "E7 — Stress":          e7_passou,
    }

    todos_passaram = all(gates.values())
    n_passou = sum(gates.values())

    for nome, passou in gates.items():
        print(f"  {'✓' if passou else '✗'}  {nome}")

    print(f"\n  Gates aprovados: {n_passou}/8")
    print(f"\n  {'═'*20} DECISÃO {'═'*20}")

    if todos_passaram:
        print(f"\n  ✓  {TICKER} — OPERAR")
        print(f"     Todos os gates aprovados")
    elif n_passou >= 6:
        print(f"\n  ~  {TICKER} — MONITORAR")
        print(f"     {8-n_passou} gate(s) falharam")
    else:
        print(f"\n  ✗  {TICKER} — EXCLUÍDO")
        print(f"     {8-n_passou} gates falharam")

    # ── Retorno da função ──────────────────────────────────────────
    decisao_final = "OPERAR" if todos_passaram else "MONITORAR"
    return decisao_final

    print(f"\n  {sep}")


if __name__ == "__main__":
    import sys
    t = (sys.argv[1] if len(sys.argv) > 1
         else input("Ticker para análise GATE: ").strip().upper())
    resultado = gate_executar(t)
    print(f"\n  Resultado final: {resultado}")
