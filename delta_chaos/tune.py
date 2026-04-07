# ════════════════════════════════════════════════════════════════════
import json
import os
# DELTA CHAOS — TUNE v2.0
# Alterações em relação à v1.1:
# MIGRADO (P2): imports explícitos de init e tape — sem escopo global
# MIGRADO (P3): TICKER=input() → executar_tune(ticker: str) -> dict
# MIGRADO (P4): raise SystemExit → raise ValueError
# MIGRADO (P5): prints de inicialização sob if __name__ == "__main__"
# MANTIDO: Opção B SCAN, 6 combinações, proxy intradiário, registro historico_config
# ════════════════════════════════════════════════════════════════════

from delta_chaos.init import (
    CONFIG_PATH,
    CONFIG_PATH,
    CONFIG_PATH,
    carregar_config, ATIVOS_DIR, DRIVE_BASE, CONFIG_PATH,
)
from delta_chaos.tape import (
    tape_carregar_ativo, tape_backtest, tape_externas,
    _obter_selic,
)
from delta_chaos.orbit import ORBIT

# ── Logging ATLAS (graceful fallback) ─────────────────────────────────
try:
    from atlas_backend.core.terminal_stream import emit_log, emit_error
    _atlas_disponivel = True
except ImportError:
    def emit_log(msg, level="info"): print(f"[{level.upper()}] {msg}")
    def emit_error(e): print(f"[ERROR] {e}")
    _atlas_disponivel = False



def executar_tune(ticker: str) -> dict:
    """
    Executa calibração TUNE completa para o ticker informado.
    Retorna dict com resultados de todas as combinações e a melhor.
    Registra no historico_config[] do master JSON — não aplica automaticamente.
    Lança ValueError se ORBIT não gerou histórico.
    """
    TICKER = ticker.strip().upper()

    emit_log(f"TUNE PING — {TICKER} | conexão WebSocket ativa", level="debug")

    import json, os
    import pandas as pd
    import numpy as np
    from datetime import datetime

    # ═══════════════════════════════════════════════════════════════════
    # CONFIGURAÇÃO
    # ═══════════════════════════════════════════════════════════════════
    # ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ 


    # TICKER recebido como argumento de executar_tune()
    ANO_WARMUP    = 2004
    ANO_TESTE_INI = 2019
    ano_atual     = datetime.now().year
    ANOS          = list(range(2002, ano_atual + 1))

    COMBINACOES = [
        {"tp": 0.50, "stop": 2.0, "label": "baseline"},
        {"tp": 0.50, "stop": 1.5, "label": "TP=0.50 STOP=1.5"},
        {"tp": 0.75, "stop": 1.0, "label": "TP=0.75 STOP=1.0"},
        {"tp": 0.75, "stop": 1.5, "label": "TP=0.75 STOP=1.5"},
        {"tp": 0.90, "stop": 1.5, "label": "TP=0.90 STOP=1.5"},
        {"tp": 0.90, "stop": 2.0, "label": "TP=0.90 STOP=2.0"},
    ]

    # ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ 
    # ETAPA 1 — carrega tudo uma vez
    # ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ 
    
    emit_log(f"TUNE [{TICKER}] Etapa 1/4: carregando TAPE/SELIC/ORBIT", level="info")
    
    print("=" * 60)
    print(f"  TUNE v1.1 — {TICKER}")
    print(f"  Opção B SCAN: proxy intradiário via mínimo/máximo")
    print(f"  Warmup:       descartar ciclos < {ANO_WARMUP}")
    print(f"  Período teste: {ANO_TESTE_INI}–{ano_atual} (7 anos)")
    print("=" * 60)

    # TAPE — uma vez
    print(f"\n  [1/4] TAPE...")
    df_tape_c = tape_backtest(
        ativos = [TICKER],
        anos   = ANOS,
        forcar = False)
    print(f"  ✓ {len(df_tape_c):,} registros carregados")

    # SELIC — uma vez
    print(f"\n  [2/4] SELIC...")
    df_selic_c = _obter_selic(min(ANOS), max(ANOS))
    print(f"  ✓ SELIC carregada")

    # Config do ativo — sem take_profit/stop_loss para não sobrescrever TUNE
    print(f"\n  [3/4] Config ativo...")
    cfg_ativo = tape_carregar_ativo(TICKER)
    cfg_ativo.pop("take_profit", None)
    cfg_ativo.pop("stop_loss",   None)
    print(f"  ✓ {TICKER} config carregado (take_profit/stop_loss removidos para TUNE)")

    # Datas únicas — uma vez
    datas = sorted(df_tape_c["data"].unique())
    print(f"  ✓ {len(datas):,} pregões")

    # Regimes do ORBIT — uma vez
    print(f"\n  [4/4] Regimes ORBIT...")
    path_ativo = os.path.join(ATIVOS_DIR, f"{TICKER}.json")
    with open(path_ativo) as f:
        dados_ativo = json.load(f)

    historico_c = pd.DataFrame(dados_ativo["historico"])
    if len(historico_c) == 0:
        print(f"  ~ Histórico ORBIT vazio — calculando agora...")
        _orbit_tune = ORBIT(universo={TICKER: {}})
        externas = tape_externas([TICKER], ANOS)
        _orbit_tune.rodar(df_tape_c, ANOS, modo="cache", externas_dict=externas)
        with open(path_ativo) as f:
            dados_ativo = json.load(f)
        historico_c = pd.DataFrame(dados_ativo["historico"])
        if len(historico_c) == 0:
            print(f"  ✗ ORBIT não gerou histórico para {TICKER} — verifique os dados do TAPE")
            raise ValueError(f"TUNE bloqueado em {TICKER}: ORBIT não gerou histórico")
        print(f"  ✓ ORBIT calculado — {len(historico_c)} ciclos")

    historico_c["ciclo_id"] = historico_c["ciclo_id"].astype(str)

    # Filtro de warmup
    n_antes = len(historico_c)
    historico_c = historico_c[
        pd.to_datetime(historico_c["data_ref"]).dt.year >= ANO_WARMUP
    ].copy()
    n_depois = len(historico_c)
    print(f"  ✓ Warmup: {n_antes} → {n_depois} ciclos "
          f"(descartados {n_antes - n_depois} ciclos < {ANO_WARMUP})")

    regime_idx_c = historico_c.set_index("ciclo_id").to_dict("index")
    print(f"  ✓ {len(historico_c)} ciclos em uso")

    # Lê baseline para restaurar ao final
    with open(CONFIG_PATH) as f:
        _cfg_baseline = json.load(f)
    tp_baseline_ant   = _cfg_baseline["fire"]["take_profit"]
    stop_baseline_ant = _cfg_baseline["fire"]["stop_loss"]

    print(f"\n  ✓ Etapa 1 concluída — tudo em memória")

    # ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ 
    # ETAPA 2 — simulação intradiária com mínimo/máximo
    # ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ 
    # Lógica Opção B (SCAN — Sarah Hamilton):
    #   — Para cada posição aberta, em cada pregão:
    #     — Usa mínimo da opção vendida como proxy do menor prêmio do dia
    #     — Se minimo <= premio_entrada * (1 - TP) → TP atingido intraday
    #     — Usa maximo da opção vendida como proxy do maior prêmio do dia
    #     — Se maximo >= premio_entrada * (1 + STOP) → STOP atingido intraday
    #   — Ordem de verificação: STOP primeiro (conservador), depois TP
    #     (na prática o dia ruim bate STOP antes do TP)
    # ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ ═ 


    emit_log(f"TUNE [{TICKER}] Etapa 2/4: simulando {len(COMBINACOES)} combinações...", level="info")
    print(f"\n{'=' * 60}")
    print(f"  Etapa 2 — Simulação intradiária: {len(COMBINACOES)} combinações")
    print(f"{'=' * 60}")

    # Pré-processa df_tape indexado por data e ticker para lookup O(1)
    df_ops_idx = df_tape_c[
        df_tape_c["tipo"].isin(["CALL", "PUT"])
    ].copy()
    df_ops_idx["data_str"] = df_ops_idx["data"].astype(str).str[:10]

    # à ndice: (data_str, ticker) → row
    tape_lookup = df_ops_idx.groupby(
        ["data_str", "ticker"])[["fechamento", "minimo", "maximo"]].first()

    # Ã ndice de regime por ciclo
    def _get_regime(ciclo_id):
        raw = regime_idx_c.get(ciclo_id, {})
        return {
            "regime":  raw.get("regime", "DESCONHECIDO"),
            "ir":      float(raw.get("ir", 0.0)),
            "sizing":  float(raw.get("sizing", 0.0)),
        }

    # Constantes do FIRE para filtros de entrada
    _cfg_f       = carregar_config()["fire"]
    DIAS_MIN     = _cfg_f["dias_min"]
    DIAS_MAX     = _cfg_f["dias_max"]
    PREMIO_MIN   = _cfg_f["premio_minimo"]
    COOLING_OFF  = _cfg_f["cooling_off_dias"]
    IV_MINIMO    = _cfg_f["iv_minimo"]

    # Estratégias por regime — lê do master JSON
    _estrategias = cfg_ativo.get("estrategias", {})
    _reg_sizing  = cfg_ativo.get("regimes_sizing", {})

    _delta_alvo_cfg = carregar_config()["fire"]["delta_alvo"]
    DELTA_ALVO_TUNE = {
        "CSP":             {"PUT":  _delta_alvo_cfg["CSP"]["put_vendida"]},
        "BULL_PUT_SPREAD": {"PUT":  _delta_alvo_cfg["BULL_PUT_SPREAD"]["put_vendida"]},
        "BEAR_CALL_SPREAD":{"CALL": _delta_alvo_cfg["BEAR_CALL_SPREAD"]["call_vendida"]},
    }

    # S6 — espelho intencional de FIRE._melhor()
    # Mantidas separadas por diferença de contexto:
    # TUNE não usa iv_rank, FIRE usa.
    # Se FIRE._melhor() for alterada, atualizar aqui também.
    def _melhor_opcao(df_dia, ativo, tipo, delta_alvo):
        cands = df_dia[
            (df_dia["ativo_base"] == ativo) &
            (df_dia["tipo"] == tipo) &
            (df_dia["delta"].notna()) &
            (df_dia["T"] * 252 >= DIAS_MIN) &
            (df_dia["T"] * 252 <= DIAS_MAX) &
            (df_dia["volume"] > 0) &
            (df_dia["iv"].notna()) &
            (df_dia["iv"] >= IV_MINIMO)
        ].copy()
        if cands.empty:
            return None
        cands["dist"] = (cands["delta"] - delta_alvo).abs()
        return cands.nsmallest(1, "dist").iloc[0]

    resultados = {}

    for combo in COMBINACOES:
        label   = combo["label"]
        TP      = combo["tp"]
        STOP    = combo["stop"]
        print(f"\n  Testando {label} (TP={TP} STOP={STOP})...")

        # Estado da simulação
        posicao_aberta  = None   # dict com dados da posição
        ultimo_stop_dt  = None   # data do último stop
        trades          = []     # lista de trades fechados

        from tqdm.auto import tqdm as _tqdm
        with _tqdm(total=len(datas), desc=f"  {label}",
                   unit="pregão", ncols=None) as pbar:

            for data in datas:
                data_str = str(data)[:10]
                ciclo_id = data_str[:7]
                df_dia   = df_tape_c[df_tape_c["data"] == data].copy()

                # ── Verifica posição aberta ───────────────────────────
                if posicao_aberta is not None:
                    leg        = posicao_aberta["leg"]
                    ticker_op  = leg["ticker"]
                    premio_ref = leg["premio_entrada"]
                    venc_dt    = pd.Timestamp(leg["vencimento"])
                    data_ts    = pd.Timestamp(data_str)
                    dias_rest  = (venc_dt - data_ts).days

                    # Busca preços do dia via lookup
                    key = (data_str, ticker_op)
                    if key in tape_lookup.index:
                        row_op = tape_lookup.loc[key]
                        if isinstance(row_op, pd.DataFrame):
                            row_op = row_op.iloc[0]
                        p_fech   = float(row_op["fechamento"])
                        p_min_op = float(row_op["minimo"])
                        p_max_op = float(row_op["maximo"])
                    else:
                        p_fech   = premio_ref
                        p_min_op = premio_ref
                        p_max_op = premio_ref

                    # Preço ação para vencimento
                    acao = df_dia[
                        (df_dia["ativo_base"] == TICKER) &
                        (df_dia["tipo"] == "ACAO")
                    ]["fechamento"]
                    preco_acao = float(acao.iloc[0]) if not acao.empty else 0.0

                    fechou = False

                    # Vencimento
                    if dias_rest <= 0:
                      strike   = leg["strike"]
                      tipo_leg = leg["tipo"]

                      acao = df_dia[
                          (df_dia["ativo_base"] == TICKER) &
                          (df_dia["tipo"] == "ACAO")
                      ]["fechamento"]

                      if acao.empty:
                          p_saida = 0.0  # sem preço — assume OTM
                      else:
                          preco_acao = float(acao.iloc[0])
                          if tipo_leg == "PUT":
                              p_saida = max(0, strike - preco_acao)
                          else:
                              p_saida = max(0, preco_acao - strike)

                      pnl = (premio_ref - p_saida) * posicao_aberta["n"]
                      trades.append({
                          "data_entrada": posicao_aberta["data_entrada"],
                          "data_saida":   data_str,
                          "motivo":       "VENCIMENTO",
                          "pnl":          round(pnl, 4),
                          "premio_ref":   premio_ref,
                      })
                      posicao_aberta = None
                      fechou = True

                    # STOP — usa máximo do dia (proxy intraday)
                    # pnl_pct = (entrada - maximo) / entrada
                    # se maximo >> entrada → pnl_pct muito negativo → STOP
                    if not fechou:
                        pnl_pct_stop = (premio_ref - p_max_op) / (premio_ref + 1e-10)
                        if pnl_pct_stop <= -STOP:
                            pnl = (premio_ref - p_max_op) * posicao_aberta["n"]
                            trades.append({
                                "data_entrada": posicao_aberta["data_entrada"],
                                "data_saida":   data_str,
                                "motivo":       "STOP",
                                "pnl":          round(pnl, 4),
                                "premio_ref":   premio_ref,
                            })
                            ultimo_stop_dt = pd.Timestamp(data_str)
                            posicao_aberta = None
                            fechou = True

                    # TP — usa mínimo do dia (proxy intraday)
                    # pnl_pct = (entrada - minimo) / entrada
                    # se minimo << entrada → pnl_pct positivo → TP
                    if not fechou:
                        pnl_pct_tp = (premio_ref - p_min_op) / (premio_ref + 1e-10)
                        if pnl_pct_tp >= TP:
                            pnl = (premio_ref - p_min_op) * posicao_aberta["n"]
                            trades.append({
                                "data_entrada": posicao_aberta["data_entrada"],
                                "data_saida":   data_str,
                                "motivo":       "TP",
                                "pnl":          round(pnl, 4),
                                "premio_ref":   premio_ref,
                            })
                            posicao_aberta = None
                            fechou = True

                # ── Tenta abrir posição ───────────────────────────
                if posicao_aberta is None:
                    orbit = _get_regime(ciclo_id)
                    regime = orbit["regime"]

                    # Cooling off
                    if ultimo_stop_dt is not None:
                        dias_desde_stop = (
                            pd.Timestamp(data_str) - ultimo_stop_dt).days
                        if dias_desde_stop < COOLING_OFF:
                            pbar.update(1)
                            continue

                    # Sizing
                    sizing_config = float(_reg_sizing.get(regime, 0.0))
                    sizing_orbit  = orbit["sizing"]
                    if sizing_config <= 0.0 or sizing_orbit <= 0.0:
                        pbar.update(1)
                        continue

                    # Estratégia
                    estrategia = _estrategias.get(regime)
                    if not estrategia:
                        pbar.update(1)
                        continue

                    # Seleciona opção
                    if estrategia in ("CSP", "BULL_PUT_SPREAD"):
                        tipo_op     = "PUT"
                        delta_alvo  = DELTA_ALVO_TUNE[estrategia]["PUT"]
                    elif estrategia == "BEAR_CALL_SPREAD":
                        tipo_op     = "CALL"
                        delta_alvo  = DELTA_ALVO_TUNE[estrategia]["CALL"]
                    else:
                        pbar.update(1)
                        continue

                    melhor = _melhor_opcao(df_dia, TICKER, tipo_op, delta_alvo)
                    if melhor is None:
                        pbar.update(1)
                        continue

                    premio_liq = float(melhor["fechamento"])
                    if premio_liq < PREMIO_MIN:
                        pbar.update(1)
                        continue

                    # Contratos
                    _rt     = carregar_config()["book"]["risco_trade"]
                    _fm     = carregar_config()["book"]["fator_margem"]
                    _nm     = carregar_config()["book"]["n_contratos_minimo"]
                    capital = 10_000
                    n = max(int(capital * _rt * sizing_orbit * sizing_config /
                                (premio_liq * _fm + 1e-10)), _nm)

                    posicao_aberta = {
                        "data_entrada": data_str,
                        "n":            n,
                        "leg": {
                            "ticker":        str(melhor["ticker"]),
                            "tipo":          tipo_op,
                            "strike":        float(melhor["strike"]),
                            "vencimento":    str(melhor["vencimento"])[:10],
                            "premio_entrada": premio_liq,
                        }
                    }

                pbar.update(1)
                pbar.set_postfix(
                    aberta   = 1 if posicao_aberta else 0,
                    fechados = len(trades))

        # ── Coleta resultados ─────────────────────────────────────────
        df_tr = pd.DataFrame(trades)

        if df_tr.empty:
            print(f"  ✗ {label} — nenhum trade")
            resultados[label] = {k: 0 for k in [
                "tp","stop","trades","pnl","acerto","ir",
                "n_tp","ganho_medio","n_venc","venc_medio",
                "n_stops","perda_media","pnl_valido",
                "trades_valido","acerto_valido","ir_valido",
                "n_tp_valido","n_venc_valido","n_stops_valido",
                "perda_media_valido"]}
            resultados[label]["tp"]   = TP
            resultados[label]["stop"] = STOP
            continue

        fechadas = df_tr.copy()
        valido   = fechadas[
            pd.to_datetime(fechadas["data_entrada"])
            .dt.year >= ANO_TESTE_INI
        ]

        pnls   = fechadas["pnl"].values
        pnls_v = valido["pnl"].values if len(valido) > 0 else np.array([])

        ir = (float(np.mean(pnls) / (np.std(pnls) + 1e-10) *
              np.sqrt(252/21)) if len(pnls) > 5 else 0.0)
        ir_valido = (float(np.mean(pnls_v) / (np.std(pnls_v) + 1e-10) *
                     np.sqrt(252/21)) if len(pnls_v) > 5 else 0.0)

        tp_t   = fechadas[fechadas["motivo"] == "TP"]
        venc_t = fechadas[fechadas["motivo"] == "VENCIMENTO"]
        stop_t = fechadas[fechadas["motivo"] == "STOP"]
        tp_v   = valido[valido["motivo"] == "TP"]
        venc_v = valido[valido["motivo"] == "VENCIMENTO"]
        stop_v = valido[valido["motivo"] == "STOP"]

        resultados[label] = {
            "tp":              TP,
            "stop":            STOP,
            "trades":          len(fechadas),
            "pnl":             fechadas["pnl"].sum(),
            "acerto":          (fechadas["pnl"] > 0).mean() * 100,
            "ir":              ir,
            "n_tp":            len(tp_t),
            "ganho_medio":     tp_t["pnl"].mean()   if len(tp_t)   > 0 else 0,
            "n_venc":          len(venc_t),
            "venc_medio":      venc_t["pnl"].mean() if len(venc_t) > 0 else 0,
            "n_stops":         len(stop_t),
            "perda_media":     stop_t["pnl"].mean() if len(stop_t) > 0 else 0,
            "pnl_valido":      valido["pnl"].sum()  if len(valido) > 0 else 0,
            "trades_valido":   len(valido),
            "acerto_valido":   (valido["pnl"] > 0).mean() * 100
                               if len(valido) > 0 else 0,
            "ir_valido":       ir_valido,
            "n_tp_valido":     len(tp_v),
            "n_venc_valido":   len(venc_v),
            "n_stops_valido":  len(stop_v),
            "perda_media_valido": stop_v["pnl"].mean()
                                  if len(stop_v) > 0 else 0,
        }

        print(f"  ✓ {label:22} "
              f"IR={ir:+.3f}  "
              f"IR válido={ir_valido:+.3f}  "
              f"P&L válido=R${valido['pnl'].sum():+,.0f}  "
              f"trades={len(fechadas)}  "
              f"stops={len(stop_t)}")

    # =====================================
    # ETAPA 3 — tabela comparativa
    # =====================================
    print(f"\n{'═ ' * 88}")
    print(f"  {TICKER} — TUNE v1.1 — TP e STOP screening (proxy intradiário)")
    print(f"  Warmup: < {ANO_WARMUP} | Teste: {ANO_TESTE_INI}–{ano_atual} (7 anos)")
    print(f"{'═ ' * 88}")

    colunas = list(resultados.keys())
    col_w   = 17

    print(f"  {'Métrica':28}", end="")
    for label in colunas:
        print(f"  {label:>{col_w}}", end="")
    print()
    print(f"  {'─' * (28 + (col_w + 2) * len(colunas))}")

    metricas = [
        ("TP",                   "tp",                "{:.2f}"),
        ("STOP",                 "stop",              "{:.1f}x"),
        ("─" * 26,               None,                None),
        ("── HISTÓRICO COMPLETO",None,                None),
        ("Trades totais",         "trades",            "{:.0f}"),
        ("P&L total",             "pnl",               "R${:,.0f}"),
        ("Acerto %",              "acerto",            "{:.1f}%"),
        ("IR realizado",          "ir",                "{:+.3f}"),
        ("n TP",                  "n_tp",              "{:.0f}"),
        ("Ganho médio (TP)",      "ganho_medio",       "R${:,.0f}"),
        ("n VENCIMENTO",          "n_venc",            "{:.0f}"),
        ("Venc médio",            "venc_medio",        "R${:,.0f}"),
        ("n STOP",                "n_stops",           "{:.0f}"),
        ("Perda média",           "perda_media",       "R${:,.0f}"),
        ("─" * 26,               None,                None),
        (f"── TESTE {ANO_TESTE_INI}–{ano_atual}",None,        None),
        ("Trades válidos",        "trades_valido",     "{:.0f}"),
        ("P&L válido",            "pnl_valido",        "R${:,.0f}"),
        ("Acerto válido %",       "acerto_valido",     "{:.1f}%"),
        ("IR válido",             "ir_valido",         "{:+.3f}"),
        ("n TP válido",           "n_tp_valido",       "{:.0f}"),
        ("n VENC válido",         "n_venc_valido",     "{:.0f}"),
        ("n STOP válido",         "n_stops_valido",    "{:.0f}"),
        ("Perda média válida",    "perda_media_valido","R${:,.0f}"),
    ]

    for nome, chave, fmt in metricas:
        if chave is None:
            if "─" in nome:
                print(f"  {'─' * 26}", end="")
                for _ in colunas:
                    print(f"  {'─' * col_w}", end="")
                print()
            else:
                print(f"\n  {nome}")
            continue
        print(f"  {nome:28}", end="")
        for label in colunas:
            val = resultados[label][chave]
            print(f"  {fmt.format(val):>{col_w}}", end="")
        print()

    print(f"\n  {'─' * 50}")
    melhor_ir   = max(resultados.items(), key=lambda x: x[1]["ir"])
    melhor_ir_v = max(resultados.items(), key=lambda x: x[1]["ir_valido"])
    melhor_pnl  = max(resultados.items(), key=lambda x: x[1]["pnl"])
    melhor_pnl_v= max(resultados.items(), key=lambda x: x[1]["pnl_valido"])

    print(f"  Melhor IR total:    {melhor_ir[0]:24} IR={melhor_ir[1]['ir']:+.3f}")
    print(f"  Melhor IR válido:   {melhor_ir_v[0]:24} IR={melhor_ir_v[1]['ir_valido']:+.3f}")
    print(f"  Melhor P&L total:   {melhor_pnl[0]:24} R${melhor_pnl[1]['pnl']:,.0f}")
    print(f"  Melhor P&L válido:  {melhor_pnl_v[0]:24} R${melhor_pnl_v[1]['pnl_valido']:,.0f}")
    print(f"\n  ⚠ Métrica de decisão: IR válido e P&L válido")
    print(f"    (período {ANO_TESTE_INI}–{ano_atual} — proxy intradiário via mínimo/máximo)")
    print(f"\n{'═ ' * 88}")

    # ==========================================
    # ETAPA 4 registro no historico_config
    # ===========================================
    melhor = melhor_ir_v

    with open(path_ativo) as f:
        dados = json.load(f)

    if "historico_config" not in dados:
        dados["historico_config"] = []

    dados["historico_config"].append({
        "data":          str(datetime.now())[:10],
        "modulo":        "TUNE v1.1",
        "parametro":     "take_profit / stop_loss",
        "valor_ant":     f"TP={tp_baseline_ant} STOP={stop_baseline_ant}",
        "valor_novo":    f"TP={melhor[1]['tp']} STOP={melhor[1]['stop']}",
        "motivo":        (f"TUNE v1.1 — IR válido ({ANO_TESTE_INI}–{ano_atual}) "
                         f"IR={melhor[1]['ir_valido']:+.3f} "
                         f"P&L=R${melhor[1]['pnl_valido']:,.0f} "
                         f"trades={melhor[1]['trades_valido']} "
                         f"proxy=intraday_min_max"),
        "combinacao":    melhor[0],
        "warmup":        ANO_WARMUP,
        "periodo_teste": f"{ANO_TESTE_INI}-{ano_atual}",
        "metodo":        "proxy_intraday_min_max",
    })
    dados["atualizado_em"] = str(datetime.now())[:19]

    with open(path_ativo, "w") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False, default=str)

    print(f"  ✓ Resultado registrado no master JSON de {TICKER}")
    print(f"    Melhor: {melhor[0]} — "
          f"IR válido={melhor[1]['ir_valido']:+.3f} "
          f"P&L válido=R${melhor[1]['pnl_valido']:,.0f}")

    _tp_aplicar   = melhor[1]['tp']
    _stop_aplicar = melhor[1]['stop']

    print(f"{'=' * 52}")  
    print(f"  ⚠ Aplicar requer decisão explícita do CEO")
    print(f"  Para aplicar, cole e execute a célula abaixo:")
    print(f"{'=' * 52}")  
    print(f"""
    # Aplicar TUNE v1.1 — {TICKER}
    # TP={_tp_aplicar} STOP={_stop_aplicar} — IR válido={melhor[1]['ir_valido']:+.3f}
    import json
    _path = f"{{ATIVOS_DIR}}/{TICKER}.json"
    with open(_path) as f:
        _cfg = json.load(f)
    _cfg["take_profit"] = {_tp_aplicar}
    _cfg["stop_loss"]   = {_stop_aplicar}
    with open(_path, "w") as f:
        json.dump(_cfg, f, indent=2, ensure_ascii=False)
    print("✓ TP={_tp_aplicar} STOP={_stop_aplicar} aplicado em {TICKER}")
    """)
    print(f"{'=' * 52}")  

    # RETORNO DA FUNÇÃO
    return {
        "ticker":      TICKER,
        "resultados":  resultados,
        "melhor_ir_valido": {
            "label": melhor_ir_v[0],
            "tp":    melhor_ir_v[1]["tp"],
            "stop":  melhor_ir_v[1]["stop"],
            "ir_valido": melhor_ir_v[1]["ir_valido"],
            "pnl_valido": melhor_ir_v[1]["pnl_valido"],
        },
        "melhor_pnl_valido": {
            "label": melhor_pnl_v[0],
            "tp":    melhor_pnl_v[1]["tp"],
            "stop":  melhor_pnl_v[1]["stop"],
            "pnl_valido": melhor_pnl_v[1]["pnl_valido"],
        },
    }


if __name__ == "__main__":
    import sys
    t = (sys.argv[1] if len(sys.argv) > 1
         else input("Ticker para TUNE: ").strip().upper())
    resultado = executar_tune(t)
    melhor = resultado["melhor_ir_valido"]
    print(f"\n  Melhor IR válido: {melhor['label']} "
          f"TP={melhor['tp']} STOP={melhor['stop']} "
          f"IR={melhor['ir_valido']:+.3f}")
