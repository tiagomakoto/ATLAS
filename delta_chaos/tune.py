# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
import json
import os
# DELTA CHAOS â€” TUNE v2.0
# AlteraÃ§Ãµes em relaÃ§Ã£o Ã  v1.1:
# MIGRADO (P2): imports explÃ­citos de init e tape â€” sem escopo global
# MIGRADO (P3): TICKER=input() â†’ executar_tune(ticker: str) -> dict
# MIGRADO (P4): raise SystemExit â†’ raise ValueError
# MIGRADO (P5): prints de inicializaÃ§Ã£o sob if __name__ == "__main__"
# MANTIDO: OpÃ§Ã£o B SCAN, 6 combinaÃ§Ãµes, proxy intradiÃ¡rio, registro historico_config
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

from delta_chaos.init import (
    CONFIG_PATH,
    CONFIG_PATH,
    CONFIG_PATH,
    carregar_config, ATIVOS_DIR, DRIVE_BASE, CONFIG_PATH,
)
from delta_chaos.tape import (
    tape_carregar_ativo, tape_backtest,
    _obter_selic,
)
from delta_chaos.orbit import ORBIT

# â”€â”€ Logging ATLAS (graceful fallback) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    from atlas_backend.core.terminal_stream import emit_log, emit_error
    _atlas_disponivel = True
except ImportError:
    def emit_log(msg, level="info"): print(f"[{level.upper()}] {msg}")
    def emit_error(e): print(f"[ERROR] {e}")
    _atlas_disponivel = False



def executar_tune(ticker: str) -> dict:
    """
    Executa calibraÃ§Ã£o TUNE completa para o ticker informado.
    Retorna dict com resultados de todas as combinaÃ§Ãµes e a melhor.
    Registra no historico_config[] do master JSON â€” nÃ£o aplica automaticamente.
    LanÃ§a ValueError se ORBIT nÃ£o gerou histÃ³rico.
    """
    TICKER = ticker.strip().upper()

    emit_log(f"TUNE PING — {TICKER} | conexão WebSocket ativa", level="debug")

    import json, os
    import pandas as pd
    import numpy as np
    from datetime import datetime

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # CONFIGURAÃ‡ÃƒO
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


    # TICKER recebido como argumento de executar_tune()
    ANO_WARMUP    = 2004
    ANO_TESTE_INI = 2019
    ANOS          = list(range(2002, 2027))

    COMBINACOES = [
        {"tp": 0.50, "stop": 2.0, "label": "baseline"},
        {"tp": 0.50, "stop": 1.5, "label": "TP=0.50 STOP=1.5"},
        {"tp": 0.75, "stop": 1.0, "label": "TP=0.75 STOP=1.0"},
        {"tp": 0.75, "stop": 1.5, "label": "TP=0.75 STOP=1.5"},
        {"tp": 0.90, "stop": 1.5, "label": "TP=0.90 STOP=1.5"},
        {"tp": 0.90, "stop": 2.0, "label": "TP=0.90 STOP=2.0"},
    ]

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # ETAPA 1 â€” carrega tudo uma vez
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    
    emit_log(f"TUNE [{TICKER}] Etapa 1/4: carregando TAPE/SELIC/ORBIT", level="info")
    
    print("=" * 60)
    print(f"  TUNE v1.1 â€” {TICKER}")
    print(f"  OpÃ§Ã£o B SCAN: proxy intradiÃ¡rio via mÃ­nimo/mÃ¡ximo")
    print(f"  Warmup:       descartar ciclos < {ANO_WARMUP}")
    print(f"  PerÃ­odo teste: {ANO_TESTE_INI}â€“2026 (7 anos)")
    print("=" * 60)

    # TAPE â€” uma vez
    print(f"\n  [1/4] TAPE...")
    df_tape_c = tape_backtest(
        ativos = [TICKER],
        anos   = ANOS,
        forcar = False)
    print(f"  âœ“ {len(df_tape_c):,} registros carregados")

    # SELIC â€” uma vez
    print(f"\n  [2/4] SELIC...")
    df_selic_c = _obter_selic(min(ANOS), max(ANOS))
    print(f"  âœ“ SELIC carregada")

    # Config do ativo â€” sem take_profit/stop_loss para nÃ£o sobrescrever TUNE
    print(f"\n  [3/4] Config ativo...")
    cfg_ativo = tape_carregar_ativo(TICKER)
    cfg_ativo.pop("take_profit", None)
    cfg_ativo.pop("stop_loss",   None)
    print(f"  âœ“ {TICKER} config carregado (take_profit/stop_loss removidos para TUNE)")

    # Datas Ãºnicas â€” uma vez
    datas = sorted(df_tape_c["data"].unique())
    print(f"  âœ“ {len(datas):,} pregÃµes")

    # Regimes do ORBIT â€” uma vez
    print(f"\n  [4/4] Regimes ORBIT...")
    path_ativo = os.path.join(ATIVOS_DIR, f"{TICKER}.json")
    with open(path_ativo) as f:
        dados_ativo = json.load(f)

    historico_c = pd.DataFrame(dados_ativo["historico"])
    if len(historico_c) == 0:
        print(f"  ~ HistÃ³rico ORBIT vazio â€” calculando agora...")
        _orbit_tune = ORBIT(universo={TICKER: {}})
        _orbit_tune.rodar(df_tape_c, ANOS, modo="cache")
        with open(path_ativo) as f:
            dados_ativo = json.load(f)
        historico_c = pd.DataFrame(dados_ativo["historico"])
        if len(historico_c) == 0:
            print(f"  âœ— ORBIT nÃ£o gerou histÃ³rico para {TICKER} â€” verifique os dados do TAPE")
            raise ValueError(f"TUNE bloqueado em {TICKER}: ORBIT nÃ£o gerou histÃ³rico")
        print(f"  âœ“ ORBIT calculado â€” {len(historico_c)} ciclos")

    historico_c["ciclo_id"] = historico_c["ciclo_id"].astype(str)

    # Filtro de warmup
    n_antes = len(historico_c)
    historico_c = historico_c[
        pd.to_datetime(historico_c["data_ref"]).dt.year >= ANO_WARMUP
    ].copy()
    n_depois = len(historico_c)
    print(f"  âœ“ Warmup: {n_antes} â†’ {n_depois} ciclos "
          f"(descartados {n_antes - n_depois} ciclos < {ANO_WARMUP})")

    regime_idx_c = historico_c.set_index("ciclo_id").to_dict("index")
    print(f"  âœ“ {len(historico_c)} ciclos em uso")

    # LÃª baseline para restaurar ao final
    with open(CONFIG_PATH) as f:
        _cfg_baseline = json.load(f)
    tp_baseline_ant   = _cfg_baseline["fire"]["take_profit"]
    stop_baseline_ant = _cfg_baseline["fire"]["stop_loss"]

    print(f"\n  âœ“ Etapa 1 concluÃ­da â€” tudo em memÃ³ria")

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # ETAPA 2 â€” simulaÃ§Ã£o intradiÃ¡ria com mÃ­nimo/mÃ¡ximo
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # LÃ³gica OpÃ§Ã£o B (SCAN â€” Sarah Hamilton):
    #   â€” Para cada posiÃ§Ã£o aberta, em cada pregÃ£o:
    #     â€” Usa mÃ­nimo da opÃ§Ã£o vendida como proxy do menor prÃªmio do dia
    #     â€” Se minimo <= premio_entrada * (1 - TP) â†’ TP atingido intraday
    #     â€” Usa maximo da opÃ§Ã£o vendida como proxy do maior prÃªmio do dia
    #     â€” Se maximo >= premio_entrada * (1 + STOP) â†’ STOP atingido intraday
    #   â€” Ordem de verificaÃ§Ã£o: STOP primeiro (conservador), depois TP
    #     (na prÃ¡tica o dia ruim bate STOP antes do TP)
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


    emit_log(f"TUNE [{TICKER}] Etapa 2/4: simulando {len(COMBINACOES)} combinações...", level="info")
    print(f"\n{'=' * 60}")
    print(f"  Etapa 2 â€” SimulaÃ§Ã£o intradiÃ¡ria: {len(COMBINACOES)} combinaÃ§Ãµes")
    print(f"{'=' * 60}")

    # PrÃ©-processa df_tape indexado por data e ticker para lookup O(1)
    df_ops_idx = df_tape_c[
        df_tape_c["tipo"].isin(["CALL", "PUT"])
    ].copy()
    df_ops_idx["data_str"] = df_ops_idx["data"].astype(str).str[:10]

    # Ãndice: (data_str, ticker) â†’ row
    tape_lookup = df_ops_idx.groupby(
        ["data_str", "ticker"])[["fechamento", "minimo", "maximo"]].first()

    # Ãndice de regime por ciclo
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

    # EstratÃ©gias por regime â€” lÃª do master JSON
    _estrategias = cfg_ativo.get("estrategias", {})
    _reg_sizing  = cfg_ativo.get("regimes_sizing", {})

    _delta_alvo_cfg = carregar_config()["fire"]["delta_alvo"]
    DELTA_ALVO_TUNE = {
        "CSP":             {"PUT":  _delta_alvo_cfg["CSP"]["put_vendida"]},
        "BULL_PUT_SPREAD": {"PUT":  _delta_alvo_cfg["BULL_PUT_SPREAD"]["put_vendida"]},
        "BEAR_CALL_SPREAD":{"CALL": _delta_alvo_cfg["BEAR_CALL_SPREAD"]["call_vendida"]},
    }

    # S6 â€” espelho intencional de FIRE._melhor()
    # Mantidas separadas por diferenÃ§a de contexto:
    # TUNE nÃ£o usa iv_rank, FIRE usa.
    # Se FIRE._melhor() for alterada, atualizar aqui tambÃ©m.
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

        # Estado da simulaÃ§Ã£o
        posicao_aberta  = None   # dict com dados da posiÃ§Ã£o
        ultimo_stop_dt  = None   # data do Ãºltimo stop
        trades          = []     # lista de trades fechados

        from tqdm.auto import tqdm as _tqdm
        with _tqdm(total=len(datas), desc=f"  {label}",
                   unit="pregÃ£o", ncols=None) as pbar:

            for data in datas:
                data_str = str(data)[:10]
                ciclo_id = data_str[:7]
                df_dia   = df_tape_c[df_tape_c["data"] == data].copy()

                # â”€â”€ Verifica posiÃ§Ã£o aberta â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
                if posicao_aberta is not None:
                    leg        = posicao_aberta["leg"]
                    ticker_op  = leg["ticker"]
                    premio_ref = leg["premio_entrada"]
                    venc_dt    = pd.Timestamp(leg["vencimento"])
                    data_ts    = pd.Timestamp(data_str)
                    dias_rest  = (venc_dt - data_ts).days

                    # Busca preÃ§os do dia via lookup
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

                    # PreÃ§o aÃ§Ã£o para vencimento
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
                          p_saida = 0.0  # sem preÃ§o â€” assume OTM
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

                    # STOP â€” usa mÃ¡ximo do dia (proxy intraday)
                    # pnl_pct = (entrada - maximo) / entrada
                    # se maximo >> entrada â†’ pnl_pct muito negativo â†’ STOP
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

                    # TP â€” usa mÃ­nimo do dia (proxy intraday)
                    # pnl_pct = (entrada - minimo) / entrada
                    # se minimo << entrada â†’ pnl_pct positivo â†’ TP
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

                # â”€â”€ Tenta abrir posiÃ§Ã£o â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

                    # EstratÃ©gia
                    estrategia = _estrategias.get(regime)
                    if not estrategia:
                        pbar.update(1)
                        continue

                    # Seleciona opÃ§Ã£o
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

        # â”€â”€ Coleta resultados â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        df_tr = pd.DataFrame(trades)

        if df_tr.empty:
            print(f"  âœ— {label} â€” nenhum trade")
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

        print(f"  âœ“ {label:22} "
              f"IR={ir:+.3f}  "
              f"IR vÃ¡lido={ir_valido:+.3f}  "
              f"P&L vÃ¡lido=R${valido['pnl'].sum():+,.0f}  "
              f"trades={len(fechadas)}  "
              f"stops={len(stop_t)}")

    # =====================================
    # ETAPA 3 â€” tabela comparativa
    # =====================================
    print(f"\n{'â•' * 88}")
    print(f"  {TICKER} â€” TUNE v1.1 â€” TP e STOP screening (proxy intradiÃ¡rio)")
    print(f"  Warmup: < {ANO_WARMUP} | Teste: {ANO_TESTE_INI}â€“2026 (7 anos)")
    print(f"{'â•' * 88}")

    colunas = list(resultados.keys())
    col_w   = 17

    print(f"  {'MÃ©trica':28}", end="")
    for label in colunas:
        print(f"  {label:>{col_w}}", end="")
    print()
    print(f"  {'â”€' * (28 + (col_w + 2) * len(colunas))}")

    metricas = [
        ("TP",                   "tp",                "{:.2f}"),
        ("STOP",                 "stop",              "{:.1f}x"),
        ("â”€" * 26,               None,                None),
        ("â”€â”€ HISTÃ“RICO COMPLETO",None,                None),
        ("Trades totais",         "trades",            "{:.0f}"),
        ("P&L total",             "pnl",               "R${:,.0f}"),
        ("Acerto %",              "acerto",            "{:.1f}%"),
        ("IR realizado",          "ir",                "{:+.3f}"),
        ("n TP",                  "n_tp",              "{:.0f}"),
        ("Ganho mÃ©dio (TP)",      "ganho_medio",       "R${:,.0f}"),
        ("n VENCIMENTO",          "n_venc",            "{:.0f}"),
        ("Venc mÃ©dio",            "venc_medio",        "R${:,.0f}"),
        ("n STOP",                "n_stops",           "{:.0f}"),
        ("Perda mÃ©dia",           "perda_media",       "R${:,.0f}"),
        ("â”€" * 26,               None,                None),
        (f"â”€â”€ TESTE {ANO_TESTE_INI}â€“2026",None,        None),
        ("Trades vÃ¡lidos",        "trades_valido",     "{:.0f}"),
        ("P&L vÃ¡lido",            "pnl_valido",        "R${:,.0f}"),
        ("Acerto vÃ¡lido %",       "acerto_valido",     "{:.1f}%"),
        ("IR vÃ¡lido",             "ir_valido",         "{:+.3f}"),
        ("n TP vÃ¡lido",           "n_tp_valido",       "{:.0f}"),
        ("n VENC vÃ¡lido",         "n_venc_valido",     "{:.0f}"),
        ("n STOP vÃ¡lido",         "n_stops_valido",    "{:.0f}"),
        ("Perda mÃ©dia vÃ¡lida",    "perda_media_valido","R${:,.0f}"),
    ]

    for nome, chave, fmt in metricas:
        if chave is None:
            if "â”€" in nome:
                print(f"  {'â”€' * 26}", end="")
                for _ in colunas:
                    print(f"  {'â”€' * col_w}", end="")
                print()
            else:
                print(f"\n  {nome}")
            continue
        print(f"  {nome:28}", end="")
        for label in colunas:
            val = resultados[label][chave]
            print(f"  {fmt.format(val):>{col_w}}", end="")
        print()

    print(f"\n  {'â”€' * 50}")
    melhor_ir   = max(resultados.items(), key=lambda x: x[1]["ir"])
    melhor_ir_v = max(resultados.items(), key=lambda x: x[1]["ir_valido"])
    melhor_pnl  = max(resultados.items(), key=lambda x: x[1]["pnl"])
    melhor_pnl_v= max(resultados.items(), key=lambda x: x[1]["pnl_valido"])

    print(f"  Melhor IR total:    {melhor_ir[0]:24} IR={melhor_ir[1]['ir']:+.3f}")
    print(f"  Melhor IR vÃ¡lido:   {melhor_ir_v[0]:24} IR={melhor_ir_v[1]['ir_valido']:+.3f}")
    print(f"  Melhor P&L total:   {melhor_pnl[0]:24} R${melhor_pnl[1]['pnl']:,.0f}")
    print(f"  Melhor P&L vÃ¡lido:  {melhor_pnl_v[0]:24} R${melhor_pnl_v[1]['pnl_valido']:,.0f}")
    print(f"\n  âš  MÃ©trica de decisÃ£o: IR vÃ¡lido e P&L vÃ¡lido")
    print(f"    (perÃ­odo {ANO_TESTE_INI}â€“2026 â€” proxy intradiÃ¡rio via mÃ­nimo/mÃ¡ximo)")
    print(f"\n{'â•' * 88}")

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
        "motivo":        (f"TUNE v1.1 â€” IR vÃ¡lido ({ANO_TESTE_INI}â€“2025) "
                         f"IR={melhor[1]['ir_valido']:+.3f} "
                         f"P&L=R${melhor[1]['pnl_valido']:,.0f} "
                         f"trades={melhor[1]['trades_valido']} "
                         f"proxy=intraday_min_max"),
        "combinacao":    melhor[0],
        "warmup":        ANO_WARMUP,
        "periodo_teste": f"{ANO_TESTE_INI}-2026",
        "metodo":        "proxy_intraday_min_max",
    })
    dados["atualizado_em"] = str(datetime.now())[:19]

    with open(path_ativo, "w") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False, default=str)

    print(f"  âœ“ Resultado registrado no master JSON de {TICKER}")
    print(f"    Melhor: {melhor[0]} â€” "
          f"IR vÃ¡lido={melhor[1]['ir_valido']:+.3f} "
          f"P&L vÃ¡lido=R${melhor[1]['pnl_valido']:,.0f}")

    _tp_aplicar   = melhor[1]['tp']
    _stop_aplicar = melhor[1]['stop']

    print(f"{'=' * 52}")  
    print(f"  âš  Aplicar requer decisÃ£o explÃ­cita do CEO")
    print(f"  Para aplicar, cole e execute a cÃ©lula abaixo:")
    print(f"{'=' * 52}")  
    print(f"""
    # Aplicar TUNE v1.1 â€” {TICKER}
    # TP={_tp_aplicar} STOP={_stop_aplicar} â€” IR vÃ¡lido={melhor[1]['ir_valido']:+.3f}
    import json
    _path = f"{{ATIVOS_DIR}}/{TICKER}.json"
    with open(_path) as f:
        _cfg = json.load(f)
    _cfg["take_profit"] = {_tp_aplicar}
    _cfg["stop_loss"]   = {_stop_aplicar}
    with open(_path, "w") as f:
        json.dump(_cfg, f, indent=2, ensure_ascii=False)
    print("âœ“ TP={_tp_aplicar} STOP={_stop_aplicar} aplicado em {TICKER}")
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
    print(f"\n  Melhor IR vÃ¡lido: {melhor['label']} "
          f"TP={melhor['tp']} STOP={melhor['stop']} "
          f"IR={melhor['ir_valido']:+.3f}")
