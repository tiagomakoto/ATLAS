# ════════════════════════════════════════════════════════════════════
import json
import os
# DELTA CHAOS — TUNE v3.0
# Eleição competitiva de estratégia por regime via Optuna.
# Para cada regime admissível, roda um study Optuna por candidato
# (lidos de config.tune.candidatos_por_regime — nunca hardcoded)
# com máscara REFLECT idêntica entre candidatos do mesmo regime.
# Ranking gravado atomicamente no JSON do ativo. Confirmação por regime
# exige ação explícita do CEO no ATLAS antes de gravar estrategias[regime].
# Removido: executar_tune (Optuna global), tune_aplicar_estrategias.
# Mantido: tune_diagnostico_estrategia (análise retrospectiva BOOK).
# ════════════════════════════════════════════════════════════════════

from delta_chaos.init import (
    CONFIG_PATH,
    carregar_config, ATIVOS_DIR, DRIVE_BASE, BOOK_DIR,
)
from delta_chaos.tape import (
    tape_ativo_carregar, tape_historico_carregar, tape_externas_carregar,
    _obter_selic,
)
from delta_chaos.orbit import ORBIT

# ── Logging ATLAS (graceful fallback) ─────────────────────────────────
def emit_log(msg, level="info"): print(f"[{level.upper()}] {msg}", flush=True)
def emit_error(e): print(f"[ERROR] {e}", flush=True)
_atlas_disponivel = False

from atlas_backend.core.event_bus import emit_dc_event

# ── Aliases de estratégia (defensive read do config) ──────────────────
_ALIAS_ESTRATEGIA = {"BPS": "BULL_PUT_SPREAD", "BCS": "BEAR_CALL_SPREAD"}

def _normalizar_estrategia(e: str) -> str:
    return _ALIAS_ESTRATEGIA.get(e, e) if e else e


# ── Helpers de escrita atômica ─────────────────────────────────────────

def _escrever_ativo_atomico(path_ativo: str, patch: dict) -> dict:
    """Lê JSON do ativo, aplica patch, escreve atomicamente. Retorna dados atualizados."""
    import tempfile
    from datetime import datetime
    with open(path_ativo, encoding="utf-8") as f:
        dados = json.load(f)
    dados.update(patch)
    dados["atualizado_em"] = str(datetime.now())[:19]
    dir_ = os.path.dirname(path_ativo)
    with tempfile.NamedTemporaryFile(
            "w", dir=dir_, suffix=".tmp", delete=False, encoding="utf-8") as tf:
        json.dump(dados, tf, indent=2, ensure_ascii=False, default=str)
        tmp_path = tf.name
    os.replace(tmp_path, path_ativo)
    return dados


def _escrever_regime_atomico(path_ativo: str, regime: str, entrada_regime: dict) -> None:
    """Atualiza atomicamente tune_ranking_estrategia[regime] no JSON do ativo."""
    import tempfile
    from datetime import datetime
    with open(path_ativo, encoding="utf-8") as f:
        dados = json.load(f)
    ranking = dados.setdefault("tune_ranking_estrategia", {})
    ranking[regime] = entrada_regime
    dados["atualizado_em"] = str(datetime.now())[:19]
    dir_ = os.path.dirname(path_ativo)
    with tempfile.NamedTemporaryFile(
            "w", dir=dir_, suffix=".tmp", delete=False, encoding="utf-8") as tf:
        json.dump(dados, tf, indent=2, ensure_ascii=False, default=str)
        tmp_path = tf.name
    os.replace(tmp_path, path_ativo)


def _rodar_optuna_candidato(
    regime: str,
    candidato: str,
    n_trials: int,
    seed: int,
    startup: int,
    min_delta: float,
    patience: int,
    tp_min: float, tp_max: float, tp_step: float,
    stop_min: float, stop_max: float, stop_step: float,
    janela_min: int, janela_max: int,
    simular_fn,
    ticker: str,
) -> tuple:
    """
    Roda um study Optuna para regime × candidato.
    Retorna (tp, stop, ir, trials_rodados).
    """
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def objective(trial):
        tp          = trial.suggest_float("tp",   tp_min,   tp_max,   step=tp_step)
        stop        = trial.suggest_float("stop", stop_min, stop_max, step=stop_step)
        janela_anos = trial.suggest_int("janela_anos", janela_min, janela_max)
        res = simular_fn(tp, stop, janela_anos, candidato, regime)
        for k, v in res.items():
            if k not in ("ano_teste_ini",):
                trial.set_user_attr(k, v)
        try:
            best_ir = round(float(study.best_value if study.trials else res["ir_valido"]), 3)
        except Exception:
            best_ir = 0.0
        emit_dc_event(
            "dc_tune_progress", "TUNE", "running",
            ticker=ticker, regime=regime, estrategia=candidato,
            trial=trial.number + 1, total=n_trials,
            ir=best_ir,
            best_tp=round(tp, 2),
            best_stop=round(stop, 2),
        )
        return res["ir_valido"]

    sampler = optuna.samplers.TPESampler(n_startup_trials=startup, seed=seed)
    study = optuna.create_study(storage=None, direction="maximize", sampler=sampler)

    _sem_melhoria = [0]
    _melhor = [-999.0]

    def _early_stop_cb(study, trial):
        if trial.number < startup:
            return
        if study.best_value > _melhor[0] + min_delta:
            _melhor[0] = study.best_value
            _sem_melhoria[0] = 0
        else:
            _sem_melhoria[0] += 1
        if _sem_melhoria[0] >= patience:
            study.stop()

    study.optimize(objective, n_trials=n_trials, callbacks=[_early_stop_cb])

    if not study.trials:
        return None, None, 0.0, 0

    melhor = study.best_trial
    return (
        round(float(melhor.params["tp"]), 2),
        round(float(melhor.params["stop"]), 2),
        float(study.best_value),
        len(study.trials),
    )


# ═══════════════════════════════════════════════════════════════════════
# TUNE v3.0 — Eleição competitiva
# ═══════════════════════════════════════════════════════════════════════

def tune_eleicao_competitiva(ticker: str) -> dict:
    """
    TUNE v3.0 — Eleição competitiva de estratégia por regime.

    Para cada regime:
      - candidatos = [] → bloqueado (nenhum Optuna, nenhuma gravação)
      - N < estrategia_n_minimo → estrutural_fixo (PE-008): usa
        tune.estrategia_estrutural_fixo[regime] do config.json
      - N >= threshold → competitiva: Optuna separado por candidato,
        máscara REFLECT idêntica entre candidatos do mesmo regime

    PE-008 — valor empírico provisório. Threshold N≥15 e tabela de
    candidatos definidos em sessão board 2026-04-25. Revisão condicionada
    a expansão do histórico de paper trading.
    Ref: vault/BOARD/tensoes_abertas/B59_tune_estrategia_selecao_competitiva.md

    Persistência:
      - tune_ranking_estrategia gravado atomicamente por regime, imediato.
      - estrategias[regime] NÃO é atualizado aqui — requer confirmação
        explícita do CEO via POST /delta-chaos/tune/confirmar-regime.

    Retorna dict com ticker, run_id e tune_ranking_estrategia completo.
    """
    TICKER = ticker.strip().upper()

    import pandas as pd
    import numpy as np
    import uuid
    from datetime import datetime

    # ── Parâmetros Optuna ──────────────────────────────────────────────
    OPTUNA_SEED     = 42
    OPTUNA_MIN_DELTA = 0.001
    TP_MIN,   TP_MAX,   TP_STEP   = 0.40, 0.95, 0.05
    STOP_MIN, STOP_MAX, STOP_STEP = 1.0,  3.0,  0.25
    JANELA_MIN, JANELA_MAX        = 3, 10
    REFLECT_ESTADOS_BLOQUEADOS    = {"C", "D", "E", "T"}

    # ── Config v3.0 — lido do config.json (zero hardcode)
    # PE-008 — valor empírico provisório. Threshold N≥15 definido em sessão
    # board 2026-04-25. Revisão condicionada a expansão do histórico.
    # Ref: vault/BOARD/tensoes_abertas/B59_tune_estrategia_selecao_competitiva.md
    _cfg_tune      = carregar_config()["tune"]
    N_MINIMO       = int(_cfg_tune["estrategia_n_minimo"])       # PE-008
    TRIALS_POR_CAND = int(_cfg_tune.get("trials_por_candidato", 150))
    PATIENCE       = int(_cfg_tune.get("early_stop_patience", 40))
    # PE-008 — tabela de candidatos por regime lida do config.json.
    # Ref: vault/BOARD/tensoes_abertas/B59_tune_estrategia_selecao_competitiva.md
    CANDIDATOS     = _cfg_tune["candidatos_por_regime"]          # PE-008
    ESTRUTURAL_FIXO = _cfg_tune["estrategia_estrutural_fixo"]   # PE-008

    STARTUP = int(_cfg_tune.get("startup_trials", 30))
    STARTUP = max(10, min(STARTUP, TRIALS_POR_CAND))

    # ── ETAPA 1 — pré-computação única ────────────────────────────────
    ANO_WARMUP = 2004
    ano_atual  = datetime.now().year
    ANOS       = list(range(2002, ano_atual + 1))

    emit_log(f"TUNE v3.0 [{TICKER}] Etapa 1: carregando TAPE/ORBIT/REFLECT...", level="info")
    print("=" * 60)
    print(f"  TUNE v3.0 — {TICKER}")
    print(f"  Eleição competitiva por regime (PE-008: N_min={N_MINIMO})")
    print(f"  Trials por candidato: {TRIALS_POR_CAND} (early stop patience={PATIENCE})")
    print("=" * 60)

    print(f"\n  [1/4] TAPE...")
    df_tape_c = tape_historico_carregar(ativos=[TICKER], anos=ANOS, forcar=False)
    print(f"  ✓ {len(df_tape_c):,} registros carregados")

    print(f"\n  [2/4] SELIC...")
    _obter_selic(min(ANOS), max(ANOS))
    print(f"  ✓ SELIC carregada")

    print(f"\n  [3/4] Config ativo...")
    cfg_ativo = tape_ativo_carregar(TICKER)
    print(f"  ✓ {TICKER} config carregado")

    datas = sorted(df_tape_c["data"].unique())
    print(f"  ✓ {len(datas):,} pregões")

    print(f"\n  [4/4] Regimes ORBIT + REFLECT...")
    path_ativo = os.path.join(ATIVOS_DIR, f"{TICKER}.json")
    with open(path_ativo, encoding="utf-8") as f:
        dados_ativo = json.load(f)

    historico_c = pd.DataFrame(dados_ativo.get("historico", []))
    if len(historico_c) == 0:
        print(f"  ~ Histórico ORBIT vazio — calculando agora...")
        _orbit_tune = ORBIT(universo={TICKER: {}})
        externas = tape_externas_carregar([TICKER], ANOS)
        _orbit_tune.orbit_rodar(df_tape_c, ANOS, modo="cache", externas_dict=externas)
        with open(path_ativo, encoding="utf-8") as f:
            dados_ativo = json.load(f)
        historico_c = pd.DataFrame(dados_ativo.get("historico", []))
        if len(historico_c) == 0:
            raise ValueError(f"TUNE v3.0 bloqueado em {TICKER}: ORBIT não gerou histórico")
        print(f"  ✓ ORBIT calculado — {len(historico_c)} ciclos")

    historico_c["ciclo_id"] = historico_c["ciclo_id"].astype(str)
    n_antes = len(historico_c)
    historico_c = historico_c[
        pd.to_datetime(historico_c["data_ref"]).dt.year >= ANO_WARMUP
    ].copy()
    historico_c = historico_c.drop_duplicates(subset="ciclo_id", keep="last")
    regime_idx_c = historico_c.set_index("ciclo_id").to_dict("index")
    print(f"  ✓ Warmup: {n_antes} → {len(historico_c)} ciclos em uso")

    reflect_cycle_hist = dados_ativo.get("reflect_cycle_history", {})

    # N por regime (contagem de ciclos históricos — proxy para N_trades esperados)
    n_por_regime: dict[str, int] = {}
    if "regime" in historico_c.columns:
        for r, grp in historico_c.groupby("regime"):
            n_por_regime[str(r)] = len(grp)

    # Máscara REFLECT por regime: calculada UMA VEZ por regime,
    # idêntica entre candidatos do mesmo regime — SPEC §4
    mask_reflect_por_regime: dict[str, dict[str, bool]] = {}
    if "regime" in historico_c.columns:
        for r, grp in historico_c.groupby("regime"):
            mask_reflect_por_regime[str(r)] = {
                cid: reflect_cycle_hist.get(cid, {}).get("reflect_state", "B")
                     in REFLECT_ESTADOS_BLOQUEADOS
                for cid in grp["ciclo_id"]
            }

    n_mask_total = sum(sum(m.values()) for m in mask_reflect_por_regime.values())
    print(f"  ✓ REFLECT masks: {n_mask_total} ciclos bloqueados (Edge C/D/E) em todos os regimes")

    # ── Pré-computação df_dias e tape_lookup (uma vez, para todos os studies) ──
    emit_log(f"TUNE v3.0 [{TICKER}] pré-computando {len(datas):,} dias...", level="info")
    emit_dc_event("dc_tune_index_start", "TUNE", "running", ticker=TICKER, total=len(datas))
    df_dias = {}
    for i, data in enumerate(datas):
        df_dias[str(data)[:10]] = df_tape_c[df_tape_c["data"] == data].copy()
        if (i + 1) % 100 == 0 or (i + 1) == len(datas):
            emit_dc_event("dc_tune_index_progress", "TUNE", "running",
                          ticker=TICKER, current=i + 1, total=len(datas))
    emit_log(f"TUNE v3.0 [{TICKER}] pré-cômputo concluído — iniciando eleição", level="info")
    emit_dc_event("dc_tune_index_complete", "TUNE", "ok", ticker=TICKER)

    df_ops_idx = df_tape_c[df_tape_c["tipo"].isin(["CALL", "PUT"])].copy()
    df_ops_idx["data_str"] = df_ops_idx["data"].astype(str).str[:10]
    tape_lookup = df_ops_idx.groupby(
        ["data_str", "ticker"])[["fechamento", "minimo", "maximo"]].first()

    # Constantes de config (uma vez)
    _cfg_book = carregar_config()["book"]
    _RT = _cfg_book["risco_trade"]
    _FM = _cfg_book["fator_margem"]
    _NM = _cfg_book["n_contratos_minimo"]

    _cfg_f      = carregar_config()["fire"]
    DIAS_MIN    = _cfg_f["dias_min"]
    DIAS_MAX    = _cfg_f["dias_max"]
    PREMIO_MIN  = _cfg_f["premio_minimo"]
    COOLING_OFF = _cfg_f["cooling_off_dias"]
    IV_MINIMO   = _cfg_f["iv_minimo"]

    _delta_alvo_cfg = _cfg_f["delta_alvo"]
    DELTA_ALVO_TUNE = {
        "CSP":              {"PUT":  _delta_alvo_cfg["CSP"]["put_vendida"]},
        "BULL_PUT_SPREAD":  {"PUT":  _delta_alvo_cfg["BULL_PUT_SPREAD"]["put_vendida"]},
        "BEAR_CALL_SPREAD": {"CALL": _delta_alvo_cfg["BEAR_CALL_SPREAD"]["call_vendida"]},
    }

    _reg_sizing = cfg_ativo.get("regimes_sizing", {})

    def _get_regime(ciclo_id):
        raw = regime_idx_c.get(ciclo_id, {})
        return {
            "regime": raw.get("regime", "DESCONHECIDO"),
            "ir":     float(raw.get("ir", 0.0)),
            "sizing": float(raw.get("sizing", 0.0)),
        }

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

    def _simular_para_candidato(
        tp: float, stop: float, janela_anos: int,
        estrategia_fixa: str, regime_alvo: str,
    ) -> dict:
        """
        Simula ciclos do regime_alvo com estrategia_fixa.
        Usa df_dias, tape_lookup, mask_reflect_por_regime pré-computados.
        """
        ano_teste_ini  = ano_atual - janela_anos
        posicao_aberta = None
        ultimo_stop_dt = None
        trades         = []
        mask_regime    = mask_reflect_por_regime.get(regime_alvo, {})

        for data in datas:
            data_str = str(data)[:10]
            ciclo_id = data_str[:7]
            df_dia   = df_dias[data_str]

            if posicao_aberta is not None:
                leg        = posicao_aberta["leg"]
                ticker_op  = leg["ticker"]
                premio_ref = leg["premio_entrada"]
                venc_dt    = pd.Timestamp(leg["vencimento"])
                data_ts    = pd.Timestamp(data_str)
                dias_rest  = (venc_dt - data_ts).days

                key = (data_str, ticker_op)
                if key in tape_lookup.index:
                    row_op = tape_lookup.loc[key]
                    if isinstance(row_op, pd.DataFrame):
                        row_op = row_op.iloc[0]
                    p_min_op = float(row_op["minimo"])
                    p_max_op = float(row_op["maximo"])
                else:
                    p_min_op = premio_ref
                    p_max_op = premio_ref

                fechou = False

                if dias_rest <= 0:
                    strike   = leg["strike"]
                    tipo_leg = leg["tipo"]
                    acao = df_dia[
                        (df_dia["ativo_base"] == TICKER) &
                        (df_dia["tipo"] == "ACAO")
                    ]["fechamento"]
                    preco_acao = float(acao.iloc[0]) if not acao.empty else 0.0
                    p_saida = (max(0, strike - preco_acao) if tipo_leg == "PUT"
                               else max(0, preco_acao - strike))
                    pnl = (premio_ref - p_saida) * posicao_aberta["n"]
                    trades.append({
                        "data_entrada": posicao_aberta["data_entrada"],
                        "data_saida":   data_str,
                        "motivo":       "VENCIMENTO",
                        "pnl":          round(pnl, 4),
                    })
                    posicao_aberta = None
                    fechou = True

                if not fechou:
                    pnl_pct_stop = (premio_ref - p_max_op) / (premio_ref + 1e-10)
                    if pnl_pct_stop <= -stop:
                        pnl = (premio_ref - p_max_op) * posicao_aberta["n"]
                        trades.append({
                            "data_entrada": posicao_aberta["data_entrada"],
                            "data_saida":   data_str,
                            "motivo":       "STOP",
                            "pnl":          round(pnl, 4),
                        })
                        ultimo_stop_dt = pd.Timestamp(data_str)
                        posicao_aberta = None
                        fechou = True

                if not fechou:
                    pnl_pct_tp = (premio_ref - p_min_op) / (premio_ref + 1e-10)
                    if pnl_pct_tp >= tp:
                        pnl = (premio_ref - p_min_op) * posicao_aberta["n"]
                        trades.append({
                            "data_entrada": posicao_aberta["data_entrada"],
                            "data_saida":   data_str,
                            "motivo":       "TP",
                            "pnl":          round(pnl, 4),
                        })
                        posicao_aberta = None

            if posicao_aberta is None:
                # Máscara REFLECT — usa lookup pré-computado por regime (idêntico entre candidatos)
                if mask_regime.get(ciclo_id, False):
                    continue

                orbit  = _get_regime(ciclo_id)
                regime = orbit["regime"]

                if regime != regime_alvo:
                    continue

                if ultimo_stop_dt is not None:
                    if (pd.Timestamp(data_str) - ultimo_stop_dt).days < COOLING_OFF:
                        continue

                sizing_config = float(_reg_sizing.get(regime, 0.0))
                sizing_orbit  = orbit["sizing"]
                if sizing_config <= 0.0 or sizing_orbit <= 0.0:
                    continue

                estrategia = estrategia_fixa

                if estrategia in ("CSP", "BULL_PUT_SPREAD"):
                    tipo_op    = "PUT"
                    delta_alvo = DELTA_ALVO_TUNE[estrategia]["PUT"]
                elif estrategia == "BEAR_CALL_SPREAD":
                    tipo_op    = "CALL"
                    delta_alvo = DELTA_ALVO_TUNE[estrategia]["CALL"]
                else:
                    continue

                melhor = _melhor_opcao(df_dia, TICKER, tipo_op, delta_alvo)
                if melhor is None:
                    continue

                premio_liq = float(melhor["fechamento"])
                if premio_liq < PREMIO_MIN:
                    continue

                n = max(int(10_000 * _RT * sizing_orbit * sizing_config /
                            (premio_liq * _FM + 1e-10)), _NM)

                posicao_aberta = {
                    "data_entrada": data_str,
                    "n":            n,
                    "leg": {
                        "ticker":         str(melhor["ticker"]),
                        "tipo":           tipo_op,
                        "strike":         float(melhor["strike"]),
                        "vencimento":     str(melhor["vencimento"])[:10],
                        "premio_entrada": premio_liq,
                    }
                }

        if not trades:
            return {"ir_valido": 0.0, "pnl_valido": 0.0, "trades_valido": 0,
                    "tp": tp, "stop": stop, "janela_anos": janela_anos,
                    "ano_teste_ini": ano_teste_ini, "n_stops": 0}

        df_tr  = pd.DataFrame(trades)
        valido = df_tr[pd.to_datetime(df_tr["data_entrada"]).dt.year >= ano_teste_ini]
        pnls_v = valido["pnl"].values if len(valido) > 0 else np.array([])
        _std_v    = float(np.std(pnls_v))
        _mean_v   = float(np.mean(pnls_v))
        # Floor relativo: max(std, |mean| * 0.1) evita IR > ~35 por baixa
        # dispersão em séries de alta taxa de win (ex: NEUTRO_BEAR IR=264).
        # PE-009 — valor empírico provisório; revisão após 24 ciclos paper.
        _std_floor = max(_std_v, abs(_mean_v) * 0.10, 1e-6)
        ir_valido = (float(_mean_v / _std_floor *
                     np.sqrt(252 / 21)) if len(pnls_v) > 5 else 0.0)

        return {
            "ir_valido":     ir_valido,
            "pnl_valido":    float(valido["pnl"].sum()) if len(valido) > 0 else 0.0,
            "trades_valido": len(valido),
            "tp":            tp,
            "stop":          stop,
            "janela_anos":   janela_anos,
            "ano_teste_ini": ano_teste_ini,
            "n_stops":       int((df_tr["motivo"] == "STOP").sum()),
        }

    # ── ETAPA 2 — Inicializa ranking com run_id ────────────────────────
    run_id = (f"tune-eleicao-{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}"
              f"-{uuid.uuid4().hex[:8]}")

    todos_regimes = set(CANDIDATOS.keys())

    ranking_inicial: dict = {
        "_meta": {
            "run_id":              run_id,
            "iniciado_em":         datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "concluido_em":        None,
            "versao":              "3.0",
            "trials_por_candidato": TRIALS_POR_CAND,
            "early_stop_patience": PATIENCE,
            "startup_trials":      STARTUP,
        }
    }
    for regime in todos_regimes:
        ranking_inicial[regime] = {
            "eleicao_status":    "in_progress",
            "confirmado":        False,
            "estrategia_eleita": None,
            "ranking":           [],
        }

    _escrever_ativo_atomico(path_ativo, {
        "tune_ranking_estrategia": ranking_inicial,
        "tune_versao":             "3.0",
        "tune_versao_pendente":    False,
    })

    emit_dc_event("dc_tune_eleicao_start", "TUNE", "running",
                  ticker=TICKER, run_id=run_id,
                  regimes_planejados=sorted(todos_regimes))

    emit_log(f"TUNE v3.0 [{TICKER}] Etapa 2: eleição competitiva por regime...", level="info")
    print(f"\n{'=' * 60}")
    print(f"  Etapa 2 — Eleição competitiva ({len(todos_regimes)} regimes)")
    print(f"{'=' * 60}")

    # ── ETAPA 3 — Eleição por regime ──────────────────────────────────
    # PE-008 — candidatos_por_regime lidos do config.json.
    # Ref: vault/BOARD/tensoes_abertas/B59_tune_estrategia_selecao_competitiva.md
    for regime in sorted(todos_regimes):
        candidatos_raw = CANDIDATOS.get(regime, [])
        candidatos = [_normalizar_estrategia(c) for c in candidatos_raw]
        n_trades   = n_por_regime.get(regime, 0)

        emit_dc_event("dc_tune_eleicao_regime_start", "TUNE", "running",
                      ticker=TICKER, regime=regime, candidatos=candidatos,
                      n_trades=n_trades)

        print(f"\n  {regime} — N={n_trades} | candidatos={candidatos or '[]'}")

        # Caso 1: regime bloqueado
        if not candidatos:
            entrada = {
                "eleicao_status":    "bloqueado",
                "n_trades":          n_trades,
                "data_eleicao":      datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "confirmado":        False,
                "estrategia_eleita": None,
                "ranking":           [],
            }
            _escrever_regime_atomico(path_ativo, regime, entrada)
            emit_dc_event("dc_tune_eleicao_regime_complete", "TUNE", "running",
                          ticker=TICKER, regime=regime, eleicao_status="bloqueado",
                          ranking=[])
            emit_log(f"TUNE v3.0 [{TICKER}] {regime}: BLOQUEADO", level="info")
            print(f"    → BLOQUEADO (candidatos=[])")
            continue

        # Caso 2: N < N_MINIMO → estrutural_fixo (PE-008)
        # PE-008 — N<15 usa estrategia_estrutural_fixo do config.json.
        # Ref: vault/BOARD/tensoes_abertas/B59_tune_estrategia_selecao_competitiva.md
        if n_trades < N_MINIMO:
            estrategia_fixa_raw = ESTRUTURAL_FIXO.get(regime)
            estrategia_fixa = _normalizar_estrategia(estrategia_fixa_raw) if estrategia_fixa_raw else None

            tp_fixo, stop_fixo, ir_fixo, trials_fixo = None, None, 0.0, 0
            if estrategia_fixa and estrategia_fixa in DELTA_ALVO_TUNE:
                emit_log(f"TUNE v3.0 [{TICKER}] {regime}: estrutural_fixo={estrategia_fixa}, rodando Optuna...", level="info")
                tp_fixo, stop_fixo, ir_fixo, trials_fixo = _rodar_optuna_candidato(
                    regime, estrategia_fixa, TRIALS_POR_CAND, OPTUNA_SEED,
                    STARTUP, OPTUNA_MIN_DELTA, PATIENCE,
                    TP_MIN, TP_MAX, TP_STEP,
                    STOP_MIN, STOP_MAX, STOP_STEP,
                    JANELA_MIN, JANELA_MAX,
                    _simular_para_candidato, TICKER,
                )

            ranking_fixo = ([{
                "estrategia": estrategia_fixa,
                "ir":         round(ir_fixo, 4),
                "n_trades":   n_trades,
                "tp":         tp_fixo,
                "stop":       stop_fixo,
                "trials":     trials_fixo,
                "seed":       OPTUNA_SEED,
            }] if estrategia_fixa else [])

            entrada = {
                "eleicao_status":    "estrutural_fixo",
                "n_trades":          n_trades,
                "data_eleicao":      datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "confirmado":        False,
                "estrategia_eleita": estrategia_fixa,
                "ranking":           ranking_fixo,
            }
            _escrever_regime_atomico(path_ativo, regime, entrada)
            emit_dc_event("dc_tune_eleicao_regime_complete", "TUNE", "running",
                          ticker=TICKER, regime=regime, eleicao_status="estrutural_fixo",
                          ranking=ranking_fixo)
            emit_log(f"TUNE v3.0 [{TICKER}] {regime}: ESTRUTURAL_FIXO "
                     f"(N={n_trades} < {N_MINIMO}) → {estrategia_fixa}", level="info")
            print(f"    → ESTRUTURAL_FIXO: {estrategia_fixa} "
                  f"(N={n_trades} < {N_MINIMO})")
            continue

        # Caso 3: Eleição competitiva
        ranking_regime = []
        for candidato in candidatos:
            # Seed único por candidato para diversidade de warmup (D9)
            seed_cand = OPTUNA_SEED + (hash(candidato) % 10000)
            emit_log(f"TUNE v3.0 [{TICKER}] {regime} × {candidato}: "
                     f"{TRIALS_POR_CAND} trials (seed={seed_cand})...", level="info")
            print(f"    {candidato}: rodando {TRIALS_POR_CAND} trials...")

            tp_c, stop_c, ir_c, trials_c = _rodar_optuna_candidato(
                regime, candidato, TRIALS_POR_CAND, seed_cand,
                STARTUP, OPTUNA_MIN_DELTA, PATIENCE,
                TP_MIN, TP_MAX, TP_STEP,
                STOP_MIN, STOP_MAX, STOP_STEP,
                JANELA_MIN, JANELA_MAX,
                _simular_para_candidato, TICKER,
            )
            ranking_regime.append({
                "estrategia": candidato,
                "ir":         round(ir_c, 4),
                "n_trades":   n_trades,
                "tp":         tp_c,
                "stop":       stop_c,
                "trials":     trials_c,
                "seed":       seed_cand,
            })
            print(f"      ✓ IR={ir_c:+.3f} TP={tp_c} STOP={stop_c} ({trials_c} trials)")

        ranking_regime.sort(key=lambda x: x["ir"], reverse=True)

        entrada = {
            "eleicao_status":    "competitiva",
            "n_trades":          n_trades,
            "data_eleicao":      datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "confirmado":        False,
            "estrategia_eleita": None,
            "ranking":           ranking_regime,
        }
        _escrever_regime_atomico(path_ativo, regime, entrada)
        emit_dc_event("dc_tune_eleicao_regime_complete", "TUNE", "running",
                      ticker=TICKER, regime=regime, eleicao_status="competitiva",
                      ranking=ranking_regime)
        vencedora = ranking_regime[0]
        emit_log(f"TUNE v3.0 [{TICKER}] {regime}: COMPETITIVA — "
                 f"vencedora={vencedora['estrategia']} IR={vencedora['ir']:+.3f}", level="info")
        print(f"    → VENCEDORA: {vencedora['estrategia']} "
              f"IR={vencedora['ir']:+.3f} TP={vencedora['tp']} STOP={vencedora['stop']}")

    # ── ETAPA 4 — Finaliza meta ────────────────────────────────────────
    with open(path_ativo, encoding="utf-8") as f:
        dados_pre = json.load(f)
    ranking_final = dados_pre.get("tune_ranking_estrategia", {})
    ranking_final.setdefault("_meta", {})["concluido_em"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    _escrever_ativo_atomico(path_ativo, {"tune_ranking_estrategia": ranking_final})

    emit_dc_event("dc_tune_eleicao_complete", "TUNE", "ok",
                  ticker=TICKER, run_id=run_id)

    print(f"\n{'=' * 60}")
    print(f"  TUNE v3.0 [{TICKER}] — Eleição concluída")
    print(f"  run_id: {run_id}")
    print(f"  Aguardando confirmação CEO por regime no ATLAS.")
    print(f"{'=' * 60}")

    with open(path_ativo, encoding="utf-8") as f:
        dados_final = json.load(f)

    return {
        "ticker":                    TICKER,
        "run_id":                    run_id,
        "tune_ranking_estrategia":   dados_final.get("tune_ranking_estrategia", {}),
    }


# ═══════════════════════════════════════════════════════════════════════
# Diagnóstico retrospectivo (mantido — análise complementar do BOOK)
# ═══════════════════════════════════════════════════════════════════════

def tune_diagnostico_estrategia(ticker: str) -> dict:
    """
    Fase 4 de B42 — Diagnóstico de estratégia vencedora por regime.

    Analisa o histórico completo de trades do BOOK (backtest) agrupado
    por regime × estratégia e identifica qual estratégia tem melhor
    P&L médio, acerto e IR em cada regime.

    Nível 2 da hierarquia doutrinária: precede TUNE global de TP/STOP.
    Não altera JSON automaticamente — exige confirmação do CEO.
    Células com N < 20 marcadas como 'amostra_insuficiente' (PE-001).

    Retorna:
        dict com chave por regime, valor com estratégia vencedora e métricas.
    """
    import json, os
    import pandas as pd
    import numpy as np
    from datetime import datetime

    TICKER = ticker.strip().upper()

    emit_log(f"TUNE DIAG [{TICKER}] iniciando diagnóstico de estratégia por regime",
             level="info")

    # ── Carrega BOOK backtest ─────────────────────────────────────────
    book_path = os.path.join(BOOK_DIR, "book_backtest.json")

    if not os.path.exists(book_path):
        raise FileNotFoundError(
            f"book_backtest.json não encontrado em {BOOK_DIR}. "
            f"Execute EDGE backtest antes do diagnóstico.")

    with open(book_path, encoding="utf-8") as f:
        book_raw = json.load(f)

    ops = book_raw.get("ops", [])
    if not ops:
        raise ValueError(f"BOOK backtest vazio para {TICKER}.")

    # ── Monta DataFrame de trades fechados do ativo ───────────────────
    rows = []
    for op in ops:
        core  = op.get("core", {})
        orbit = op.get("orbit", {})

        if core.get("motivo_nao_entrada"):
            continue
        if core.get("motivo_saida") is None:
            continue
        if core.get("ativo") != TICKER:
            continue

        rows.append({
            "regime":     orbit.get("regime_entrada", "DESCONHECIDO"),
            "estrategia": core.get("estrategia", "DESCONHECIDO"),
            "pnl":        float(core.get("pnl") or 0.0),
            "motivo":     core.get("motivo_saida", ""),
            "data":       core.get("data_entrada", ""),
        })

    if not rows:
        raise ValueError(f"Nenhum trade fechado encontrado para {TICKER} no BOOK.")

    df = pd.DataFrame(rows)

    # ── Agrega por regime × estratégia ───────────────────────────────
    resultado = {}
    aviso_n_baixo = []

    for regime in sorted(df["regime"].unique()):
        df_reg = df[df["regime"] == regime]
        estrategias_no_regime = df_reg["estrategia"].unique()

        celulas = {}
        for estrategia in estrategias_no_regime:
            df_cel = df_reg[df_reg["estrategia"] == estrategia]
            n      = len(df_cel)
            pnls   = df_cel["pnl"].values

            # PE-001: sistema graduado de confiança por N
            if n >= 50:
                confianca = "alta"
            elif n >= 20:
                confianca = "baixa"
                aviso_n_baixo.append(f"{regime} × {estrategia} (N={n})")
            else:
                confianca = "amostra_insuficiente"
                aviso_n_baixo.append(f"{regime} × {estrategia} (N={n} < 20)")

            ir = (float(np.mean(pnls) / (np.std(pnls) + 1e-10) *
                  np.sqrt(252/21)) if n > 5 else 0.0)

            celulas[estrategia] = {
                "n":          n,
                "pnl_medio":  round(float(np.mean(pnls)), 4),
                "pnl_total":  round(float(np.sum(pnls)), 4),
                "acerto_pct": round(float((pnls > 0).mean() * 100), 1),
                "ir":         round(ir, 4),
                "confianca":  confianca,
            }

        candidatas = {
            e: v for e, v in celulas.items()
            if v["confianca"] != "amostra_insuficiente"
        }

        if candidatas:
            vencedora = max(candidatas, key=lambda e: candidatas[e]["ir"])
            status    = "ok"
        else:
            vencedora = max(celulas, key=lambda e: celulas[e]["n"]) if celulas else None
            status    = "amostra_insuficiente"

        resultado[regime] = {
            "vencedora": vencedora,
            "status":    status,
            "celulas":   celulas,
        }

    # ── Relatório ─────────────────────────────────────────────────────
    print(f"\n{'═' * 60}")
    print(f"  {TICKER} — Diagnóstico de Estratégia por Regime (retrospectivo)")
    print(f"{'═' * 60}")
    print(f"  {'Regime':20} {'Vencedora':18} {'N':>5} "
          f"{'P&L méd':>10} {'Acerto':>8} {'IR':>8} {'Conf':>10}")
    print(f"  {'─' * 80}")

    for regime, dados in sorted(resultado.items()):
        venc = dados["vencedora"]
        if venc and venc in dados["celulas"]:
            cel = dados["celulas"][venc]
            print(f"  {regime:20} {venc:18} {cel['n']:>5} "
                  f"R${cel['pnl_medio']:>8,.2f} "
                  f"{cel['acerto_pct']:>7.1f}% "
                  f"{cel['ir']:>+8.3f} "
                  f"{cel['confianca']:>10}")
        else:
            print(f"  {regime:20} {'SEM DADOS':18}")

    if aviso_n_baixo:
        print(f"\n  ⚠ Células com amostra baixa ou insuficiente:")
        for av in aviso_n_baixo:
            print(f"    • {av}")

    print(f"\n  Diagnóstico retrospectivo — não aplica automaticamente.")
    print(f"  Para eleição competitiva via Optuna, use tune_eleicao_competitiva().")
    print(f"{'═' * 60}")

    return {
        "ticker":    TICKER,
        "resultado": resultado,
        "avisos":    aviso_n_baixo,
    }


if __name__ == "__main__":
    import sys
    t = (sys.argv[1] if len(sys.argv) > 1
         else input("Ticker para TUNE v3.0: ").strip().upper())
    resultado = tune_eleicao_competitiva(t)
    print(f"\n  run_id: {resultado['run_id']}")
    print(f"  Aguardando confirmação CEO no ATLAS.")
