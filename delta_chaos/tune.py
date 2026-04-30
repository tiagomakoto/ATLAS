# ════════════════════════════════════════════════════════════════════
import json
import os
# DELTA CHAOS — TUNE v3.1
# Eleição em duas etapas: A (grid neutro fixo) → B (Optuna TP/Stop).
# Etapa A: elege estratégia por regime via 9 combinações fixas (3×3),
#   métrica = mediana do IR (ordinal). Sem Optuna nesta etapa.
# Etapa B: calibra TP/Stop com Optuna para regimes com estratégia
#   definida. janela_anos fixo do config — nunca livre no Optuna.
# Confirmação CEO via POST /tune/confirmar-regime grava o trio:
#   estrategias[regime] + tp_por_regime[regime] + stop_por_regime[regime].
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


def _avaliar_anomalia(regime_dados: dict, dados_ativo: dict, cfg_anomalia: dict) -> dict:
    """
    Avalia se um regime tem anomalia que impede aplicação automática.
    Retorna {"anomalo": bool, "motivos": List[str]}.

    Critérios fixos (não configuráveis):
      - status_fallback_global: fallback sempre é anomalia
      - mudanca_estrategia: mudança em relação ao ciclo anterior é anomalia
        (primeira execução sem estratégia anterior NÃO é anomalia)

    Critérios configuráveis (tune.anomalia no config):
      - ir_minimo: IR calibrado abaixo do limiar
      - variacao_tp_max: variação de tp_calibrado vs take_profit global
      - variacao_stop_max: variação de stop_calibrado vs stop_loss global
    """
    motivos = []

    # Fixo 1: fallback_global
    if regime_dados.get("status_calibracao") == "fallback_global":
        motivos.append("status_calibracao=fallback_global")

    # Fixo 2: mudança de estratégia (apenas se havia estratégia anterior)
    regime_key = regime_dados.get("_regime_key")  # injetado pelo chamador
    estrategia_nova = regime_dados.get("estrategia_eleita")
    estrategia_anterior = dados_ativo.get("estrategias", {}).get(regime_key)
    if estrategia_anterior is not None and estrategia_nova != estrategia_anterior:
        motivos.append(
            f"mudanca_estrategia: {estrategia_anterior} → {estrategia_nova}"
        )

    # Configuráveis — só avalia se calibrado (não fallback, que já captou acima)
    if regime_dados.get("status_calibracao") == "calibrado":
        ir_cal = regime_dados.get("ir_calibrado")
        ir_min = cfg_anomalia.get("ir_minimo", 0.5)
        if ir_cal is not None and ir_cal < ir_min:
            motivos.append(f"ir_calibrado={ir_cal:.3f} < ir_minimo={ir_min}")

        tp_cal  = regime_dados.get("tp_calibrado")
        tp_glob = dados_ativo.get("take_profit")
        variacao_tp_max = cfg_anomalia.get("variacao_tp_max", 0.30)
        if tp_cal is not None and tp_glob and tp_glob > 0:
            delta_tp_pct = abs(tp_cal - tp_glob) / tp_glob
            if delta_tp_pct > variacao_tp_max:
                motivos.append(
                    f"variacao_tp={delta_tp_pct:.1%} > max={variacao_tp_max:.1%}"
                )

        stop_cal  = regime_dados.get("stop_calibrado")
        stop_glob = dados_ativo.get("stop_loss")
        variacao_stop_max = cfg_anomalia.get("variacao_stop_max", 0.30)
        if stop_cal is not None and stop_glob and stop_glob > 0:
            delta_stop_pct = abs(stop_cal - stop_glob) / stop_glob
            if delta_stop_pct > variacao_stop_max:
                motivos.append(
                    f"variacao_stop={delta_stop_pct:.1%} > max={variacao_stop_max:.1%}"
                )

    return {"anomalo": len(motivos) > 0, "motivos": motivos}


def _aplicar_regime_no_ativo(
    dados: dict,
    regime: str,
    regime_dados: dict,
    run_id: str,
    modo: str,
) -> None:
    """
    Aplica estratégia + tp_por_regime + stop_por_regime no dict de dados do ativo.
    Modifica dados in-place. Não escreve em disco.
    modo: "automatica" | "anomalia_aprovada_ceo"
    """
    from datetime import datetime
    agora = str(datetime.now())[:19]
    versao_label = "TUNE v3.1"
    motivo_base = f"Aplicação {modo.replace('_', ' ')} — run_id={run_id}"

    estrategia = regime_dados.get("estrategia_eleita")
    status_calib = regime_dados.get("status_calibracao")

    if status_calib == "calibrado":
        tp_val   = regime_dados.get("tp_calibrado")
        stop_val = regime_dados.get("stop_calibrado")
    else:
        tp_val   = dados.get("take_profit")
        stop_val = dados.get("stop_loss")

    if not isinstance(dados.get("historico_config"), list):
        dados["historico_config"] = []
    if "estrategias" not in dados:
        dados["estrategias"] = {}

    estrategia_anterior = dados["estrategias"].get(regime)
    dados["estrategias"][regime] = estrategia

    tp_por_regime   = dados.setdefault("tp_por_regime", {})
    stop_por_regime = dados.setdefault("stop_por_regime", {})
    tp_ant   = tp_por_regime.get(regime)
    stop_ant = stop_por_regime.get(regime)
    tp_por_regime[regime]   = tp_val
    stop_por_regime[regime] = stop_val

    dados["historico_config"].append({
        "data":            agora[:10],
        "modulo":          versao_label,
        "parametro":       f"estrategia.{regime}",
        "valor_anterior":  estrategia_anterior,
        "valor_novo":      estrategia,
        "motivo":          motivo_base,
    })
    dados["historico_config"].append({
        "data":            agora[:10],
        "modulo":          versao_label,
        "parametro":       f"tp_por_regime.{regime}",
        "valor_anterior":  tp_ant,
        "valor_novo":      tp_val,
        "motivo":          motivo_base,
    })
    dados["historico_config"].append({
        "data":            agora[:10],
        "modulo":          versao_label,
        "parametro":       f"stop_por_regime.{regime}",
        "valor_anterior":  stop_ant,
        "valor_novo":      stop_val,
        "motivo":          motivo_base,
    })


def _rodar_optuna_tpstop(
    regime: str,
    candidato: str,
    janela_anos: int,
    n_trials: int,
    seed: int,
    startup: int,
    min_delta: float,
    patience: int,
    tp_min: float, tp_max: float, tp_step: float,
    stop_min: float, stop_max: float, stop_step: float,
    simular_fn,
    ticker: str,
) -> tuple:
    """
    Etapa B — Optuna varia apenas TP e Stop. janela_anos fixo.
    Retorna (tp, stop, ir, trials_rodados).
    """
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def objective(trial):
        tp   = trial.suggest_float("tp",   tp_min,   tp_max,   step=tp_step)
        stop = trial.suggest_float("stop", stop_min, stop_max, step=stop_step)
        res  = simular_fn(tp, stop, janela_anos, candidato, regime)
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
            etapa="B",
        )
        return res["ir_valido"]

    sampler = optuna.samplers.TPESampler(n_startup_trials=startup, seed=seed)
    study   = optuna.create_study(storage=None, direction="maximize", sampler=sampler)

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
    TUNE v3.1 — Eleição em duas etapas: A (grid neutro) → B (Optuna TP/Stop).

    Etapa A — Eleição de estratégia (sem Optuna):
      - candidatos=[] → bloqueado.
      - Simulação-piloto com ESTRUTURAL_FIXO[regime] no ponto central do grid.
        N_trades_reais < N_MINIMO → estrutural_fixo (PE-008).
        N_trades_reais >= N_MINIMO → grid 3×3 (9 combinações por candidato),
        métrica=mediana IR (ordinal). Vencedora = maior mediana.
    Etapa B — Calibração TP/Stop (Optuna):
      - Apenas para regimes com eleicao_status competitiva ou estrutural_fixo
        E estrategia_eleita definida.
      - janela_anos fixo do config — nunca livre no Optuna.
      - N_trades_calibracao < n_minimo_calibracao → fallback_global.

    Persistência:
      - tune_ranking_estrategia gravado atomicamente por regime.
      - estrategias[regime] NÃO é atualizado aqui — requer confirmação CEO.

    Retorna dict com ticker, run_id e tune_ranking_estrategia completo.
    """
    TICKER = ticker.strip().upper()

    import pandas as pd
    import numpy as np
    import uuid
    from datetime import datetime

    # ── Config v3.1 — tudo lido do config.json (zero hardcode) ────────
    OPTUNA_SEED      = 42
    OPTUNA_MIN_DELTA = 0.001
    REFLECT_ESTADOS_BLOQUEADOS = {"C", "D", "E", "T"}

    # PE-008 — threshold N mínimo e tabelas de candidatos lidos do config.
    # Ref: vault/BOARD/tensoes_abertas/B59_tune_estrategia_selecao_competitiva.md
    _cfg_tune       = carregar_config()["tune"]
    N_MINIMO        = int(_cfg_tune["estrategia_n_minimo"])           # PE-008
    TRIALS_POR_CAND = int(_cfg_tune.get("trials_por_candidato", 100))
    PATIENCE        = int(_cfg_tune.get("early_stop_patience", 30))
    STARTUP         = int(_cfg_tune.get("startup_trials", 30))
    STARTUP         = max(10, min(STARTUP, TRIALS_POR_CAND))
    JANELA_ANOS     = int(_cfg_tune.get("janela_anos", 5))
    N_MINIMO_CALIB  = int(_cfg_tune.get("n_minimo_calibracao", 15))
    CANDIDATOS      = _cfg_tune["candidatos_por_regime"]               # PE-008
    ESTRUTURAL_FIXO = _cfg_tune["estrategia_estrutural_fixo"]          # PE-008

    _ref = _cfg_tune.get("referencia_eleicao", {})
    TP_VALUES   = _ref.get("tp_values",   [0.50, 0.75, 0.90])
    STOP_VALUES = _ref.get("stop_values", [1.50, 2.00, 2.50])
    TP_PILOTO   = TP_VALUES[len(TP_VALUES) // 2]    # ponto central do grid
    STOP_PILOTO = STOP_VALUES[len(STOP_VALUES) // 2]

    _cfg_calib        = _cfg_tune.get("calibracao", {})
    _tp_cfg           = _cfg_calib.get("tp",   {"min": 0.40, "max": 0.95, "step": 0.05})
    _stop_cfg         = _cfg_calib.get("stop", {"min": 1.0,  "max": 3.0,  "step": 0.25})
    TP_MIN, TP_MAX, TP_STEP         = _tp_cfg["min"],   _tp_cfg["max"],   _tp_cfg["step"]
    STOP_MIN, STOP_MAX, STOP_STEP   = _stop_cfg["min"], _stop_cfg["max"], _stop_cfg["step"]

    # ── ETAPA 1 — pré-computação única ────────────────────────────────
    ANO_WARMUP = 2004
    ano_atual  = datetime.now().year
    ANOS       = list(range(2002, ano_atual + 1))

    emit_log(f"TUNE v3.1 [{TICKER}] Etapa 1: carregando TAPE/ORBIT/REFLECT...", level="info")
    print("=" * 60)
    print(f"  TUNE v3.1 — {TICKER}")
    print(f"  Etapa A: grid {len(TP_VALUES)}×{len(STOP_VALUES)} | N_min={N_MINIMO}")
    print(f"  Etapa B: Optuna TP/Stop | janela_anos={JANELA_ANOS} | trials={TRIALS_POR_CAND}")
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
            raise ValueError(f"TUNE v3.1 bloqueado em {TICKER}: ORBIT não gerou histórico")
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

    # Máscara REFLECT por regime — pré-computada UMA VEZ, idêntica entre candidatos (SPEC §4)
    mask_reflect_por_regime: dict[str, dict[str, bool]] = {}
    if "regime" in historico_c.columns:
        for r, grp in historico_c.groupby("regime"):
            mask_reflect_por_regime[str(r)] = {
                cid: reflect_cycle_hist.get(cid, {}).get("reflect_state", "B")
                     in REFLECT_ESTADOS_BLOQUEADOS
                for cid in grp["ciclo_id"]
            }

    n_mask_total = sum(sum(m.values()) for m in mask_reflect_por_regime.values())
    print(f"  ✓ REFLECT masks: {n_mask_total} ciclos bloqueados (Edge C/D/E/T) em todos os regimes")

    # ── Pré-computação df_dias e tape_lookup (uma vez, para todos os studies) ──
    emit_log(f"TUNE v3.1 [{TICKER}] pré-computando {len(datas):,} dias...", level="info")
    emit_dc_event("dc_tune_index_start", "TUNE", "running", ticker=TICKER, total=len(datas))
    df_dias = {}
    for i, data in enumerate(datas):
        df_dias[str(data)[:10]] = df_tape_c[df_tape_c["data"] == data].copy()
        if (i + 1) % 100 == 0 or (i + 1) == len(datas):
            emit_dc_event("dc_tune_index_progress", "TUNE", "running",
                          ticker=TICKER, current=i + 1, total=len(datas))
    emit_log(f"TUNE v3.1 [{TICKER}] pré-cômputo concluído — iniciando Etapa A→B", level="info")
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

                sizing_orbit  = orbit["sizing"]
                if sizing_orbit <= 0.0:
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

                n = max(int(10_000 * _RT * sizing_orbit /
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
        # PE-009 provisório — revisão gatilhada por B62 após
        # 1 trimestre paper trading TUNE v3.1
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
            "run_id":               run_id,
            "iniciado_em":          datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "concluido_em":         None,
            "versao":               "3.1",
            "trials_por_candidato": TRIALS_POR_CAND,
            "early_stop_patience":  PATIENCE,
            "startup_trials":       STARTUP,
            "janela_anos":          JANELA_ANOS,
            "n_minimo_calibracao":  N_MINIMO_CALIB,
            "tp_values":            TP_VALUES,
            "stop_values":          STOP_VALUES,
        }
    }
    for regime in todos_regimes:
        ranking_inicial[regime] = {
            "eleicao_status":    "in_progress",
            "confirmado":        False,
            "estrategia_eleita": None,
            "ranking_eleicao":   [],
        }

    _escrever_ativo_atomico(path_ativo, {
        "tune_ranking_estrategia": ranking_inicial,
        "tune_versao":             "3.1",
        "tune_versao_pendente":    False,
    })

    emit_dc_event("dc_tune_eleicao_start", "TUNE", "running",
                  ticker=TICKER, run_id=run_id,
                  regimes_planejados=sorted(todos_regimes))

    # ── ETAPA 3A — Eleição por regime (grid neutro, sem Optuna) ───────
    # PE-008 — candidatos_por_regime lidos do config.json.
    # Ref: vault/BOARD/tensoes_abertas/B59_tune_estrategia_selecao_competitiva.md
    emit_log(f"TUNE v3.1 [{TICKER}] Etapa 3A: eleição por grid neutro...", level="info")
    print(f"\n{'=' * 60}")
    print(f"  Etapa 3A — Eleição (grid {len(TP_VALUES)}×{len(STOP_VALUES)}, {len(todos_regimes)} regimes)")
    print(f"{'=' * 60}")

    for regime in sorted(todos_regimes):
        candidatos_raw = CANDIDATOS.get(regime, [])
        candidatos = [_normalizar_estrategia(c) for c in candidatos_raw]

        emit_dc_event("dc_tune_eleicao_regime_start", "TUNE", "running",
                      ticker=TICKER, regime=regime, candidatos=candidatos,
                      n_trades=0)

        print(f"\n  {regime} — candidatos={candidatos or '[]'}")

        # Caso 1: regime bloqueado (sem candidatos)
        if not candidatos:
            entrada = {
                "eleicao_status":    "bloqueado",
                "n_trades_reais":    0,
                "ir_eleicao_mediana": None,
                "ranking_eleicao":   [],
                "estrategia_eleita": None,
                "data_eleicao":      datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "status_calibracao": None,
                "tp_calibrado":      None,
                "stop_calibrado":    None,
                "ir_calibrado":      None,
                "n_trades_calibracao": None,
                "janela_anos":       JANELA_ANOS,
                "trials_rodados":    None,
                "data_calibracao":   None,
                "confirmado":        False,
            }
            _escrever_regime_atomico(path_ativo, regime, entrada)
            emit_dc_event("dc_tune_eleicao_regime_complete", "TUNE", "running",
                          ticker=TICKER, regime=regime, eleicao_status="bloqueado",
                          ranking_eleicao=[])
            emit_log(f"TUNE v3.1 [{TICKER}] {regime}: BLOQUEADO", level="info")
            print(f"    → BLOQUEADO (candidatos=[])")
            continue

        # Simulação-piloto (Adenda 1): candidato=ESTRUTURAL_FIXO[regime], ponto central do grid
        # Determina N_trades_reais real antes de decidir estrutural_fixo vs competitiva.
        piloto_raw  = ESTRUTURAL_FIXO.get(regime)
        piloto      = _normalizar_estrategia(piloto_raw) if piloto_raw else None
        n_trades_reais = 0
        res_piloto     = None

        if piloto and piloto in DELTA_ALVO_TUNE:
            res_piloto     = _simular_para_candidato(TP_PILOTO, STOP_PILOTO, JANELA_ANOS, piloto, regime)
            n_trades_reais = res_piloto.get("trades_valido", 0)

        print(f"    Piloto={piloto} | N_trades_reais={n_trades_reais} (limiar={N_MINIMO})")

        # Caso 2: N < N_MINIMO → estrutural_fixo (PE-008)
        # PE-008 — N<N_MINIMO usa estrategia_estrutural_fixo do config.json.
        # Ref: vault/BOARD/tensoes_abertas/B59_tune_estrategia_selecao_competitiva.md
        if n_trades_reais < N_MINIMO:
            ranking_eleicao = []
            if res_piloto is not None:
                ranking_eleicao = [{
                    "estrategia":    piloto,
                    "ir_mediana":    round(res_piloto["ir_valido"], 4),
                    "n_trades_reais": n_trades_reais,
                }]

            entrada = {
                "eleicao_status":    "estrutural_fixo",
                "n_trades_reais":    n_trades_reais,
                "ir_eleicao_mediana": round(res_piloto["ir_valido"], 4) if res_piloto else None,
                "ranking_eleicao":   ranking_eleicao,
                "estrategia_eleita": piloto,
                "data_eleicao":      datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "status_calibracao": None,
                "tp_calibrado":      None,
                "stop_calibrado":    None,
                "ir_calibrado":      None,
                "n_trades_calibracao": None,
                "janela_anos":       JANELA_ANOS,
                "trials_rodados":    None,
                "data_calibracao":   None,
                "confirmado":        False,
            }
            _escrever_regime_atomico(path_ativo, regime, entrada)
            emit_dc_event("dc_tune_eleicao_regime_complete", "TUNE", "running",
                          ticker=TICKER, regime=regime, eleicao_status="estrutural_fixo",
                          ranking_eleicao=ranking_eleicao)
            emit_log(f"TUNE v3.1 [{TICKER}] {regime}: ESTRUTURAL_FIXO "
                     f"(N={n_trades_reais} < {N_MINIMO}) → {piloto}", level="info")
            print(f"    → ESTRUTURAL_FIXO: {piloto} (N={n_trades_reais} < {N_MINIMO})")
            continue

        # Caso 3: Eleição competitiva via grid neutro 3×3
        ranking_eleicao = []
        for candidato in candidatos:
            irs_grid = []
            for tp_g in TP_VALUES:
                for stop_g in STOP_VALUES:
                    # Reaproveita simulação-piloto quando candidato e ponto coincidem
                    if (candidato == piloto and
                            abs(tp_g - TP_PILOTO) < 1e-9 and
                            abs(stop_g - STOP_PILOTO) < 1e-9 and
                            res_piloto is not None):
                        res_g = res_piloto
                    else:
                        res_g = _simular_para_candidato(tp_g, stop_g, JANELA_ANOS, candidato, regime)
                    irs_grid.append(res_g["ir_valido"])
                    emit_dc_event(
                        "dc_tune_progress", "TUNE", "running",
                        ticker=TICKER, regime=regime, estrategia=candidato,
                        trial=len(irs_grid), total=len(TP_VALUES) * len(STOP_VALUES),
                        ir=round(res_g["ir_valido"], 3),
                        best_tp=round(tp_g, 2),
                        best_stop=round(stop_g, 2),
                        etapa="A",
                    )

            ir_mediana = float(np.median(irs_grid))
            ranking_eleicao.append({
                "estrategia":    candidato,
                "ir_mediana":    round(ir_mediana, 4),
                "n_trades_reais": n_trades_reais,
            })
            print(f"    {candidato}: IR_mediana={ir_mediana:+.3f} (grid {len(TP_VALUES)}×{len(STOP_VALUES)})")

        ranking_eleicao.sort(key=lambda x: x["ir_mediana"], reverse=True)
        vencedora      = ranking_eleicao[0]
        ir_venc_mediana = vencedora["ir_mediana"]

        entrada = {
            "eleicao_status":    "competitiva",
            "n_trades_reais":    n_trades_reais,
            "ir_eleicao_mediana": ir_venc_mediana,
            "ranking_eleicao":   ranking_eleicao,
            "estrategia_eleita": vencedora["estrategia"],
            "data_eleicao":      datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "status_calibracao": None,
            "tp_calibrado":      None,
            "stop_calibrado":    None,
            "ir_calibrado":      None,
            "n_trades_calibracao": None,
            "janela_anos":       JANELA_ANOS,
            "trials_rodados":    None,
            "data_calibracao":   None,
            "confirmado":        False,
        }
        _escrever_regime_atomico(path_ativo, regime, entrada)
        emit_dc_event("dc_tune_eleicao_regime_complete", "TUNE", "running",
                      ticker=TICKER, regime=regime, eleicao_status="competitiva",
                      ranking_eleicao=ranking_eleicao)
        emit_log(f"TUNE v3.1 [{TICKER}] {regime}: COMPETITIVA — "
                 f"vencedora={vencedora['estrategia']} IR_mediana={ir_venc_mediana:+.3f}", level="info")
        print(f"    → VENCEDORA: {vencedora['estrategia']} IR_mediana={ir_venc_mediana:+.3f} (ordinal)")

    # ── ETAPA 3B — Calibração TP/Stop por Optuna ──────────────────────
    emit_log(f"TUNE v3.1 [{TICKER}] Etapa 3B: calibração TP/Stop por Optuna...", level="info")
    print(f"\n{'=' * 60}")
    print(f"  Etapa 3B — Calibração TP/Stop (janela_anos={JANELA_ANOS})")
    print(f"{'=' * 60}")

    with open(path_ativo, encoding="utf-8") as f:
        dados_pos_a = json.load(f)
    ranking_pos_a = dados_pos_a.get("tune_ranking_estrategia", {})

    for regime in sorted(todos_regimes):
        regime_dados = ranking_pos_a.get(regime, {})
        eleicao_status   = regime_dados.get("eleicao_status")
        estrategia_eleita = regime_dados.get("estrategia_eleita")

        # Só calibra regimes com estratégia definida
        if eleicao_status not in ("competitiva", "estrutural_fixo") or not estrategia_eleita:
            continue

        print(f"\n  {regime} — estrategia={estrategia_eleita}")

        # Mede N_trades_calibracao: simula com estratégia eleita no ponto central
        res_calib_piloto = _simular_para_candidato(
            TP_PILOTO, STOP_PILOTO, JANELA_ANOS, estrategia_eleita, regime
        )
        n_trades_calib = res_calib_piloto.get("trades_valido", 0)

        if n_trades_calib < N_MINIMO_CALIB:
            # fallback: herda campos globais do JSON do ativo
            com_dados_ativo = dados_pos_a
            tp_fallback   = com_dados_ativo.get("take_profit")
            stop_fallback = com_dados_ativo.get("stop_loss")
            regime_dados["status_calibracao"]    = "fallback_global"
            regime_dados["tp_calibrado"]         = tp_fallback
            regime_dados["stop_calibrado"]       = stop_fallback
            regime_dados["ir_calibrado"]         = None
            regime_dados["n_trades_calibracao"]  = n_trades_calib
            regime_dados["trials_rodados"]       = 0
            regime_dados["data_calibracao"]      = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            _escrever_regime_atomico(path_ativo, regime, regime_dados)
            emit_log(f"TUNE v3.1 [{TICKER}] {regime}: FALLBACK_GLOBAL "
                     f"(N={n_trades_calib} < {N_MINIMO_CALIB})", level="info")
            print(f"    → FALLBACK_GLOBAL (N={n_trades_calib} < {N_MINIMO_CALIB})"
                  f" — tp={tp_fallback} stop={stop_fallback}")
            continue

        # Optuna: varia só TP e Stop (janela fixo)
        seed_b = OPTUNA_SEED + (hash(regime) % 10000)
        emit_log(f"TUNE v3.1 [{TICKER}] {regime}: Optuna TP/Stop "
                 f"({TRIALS_POR_CAND} trials, seed={seed_b})...", level="info")
        print(f"    Optuna {TRIALS_POR_CAND} trials (seed={seed_b})...")

        tp_b, stop_b, ir_b, trials_b = _rodar_optuna_tpstop(
            regime, estrategia_eleita, JANELA_ANOS,
            TRIALS_POR_CAND, seed_b, STARTUP, OPTUNA_MIN_DELTA, PATIENCE,
            TP_MIN, TP_MAX, TP_STEP,
            STOP_MIN, STOP_MAX, STOP_STEP,
            _simular_para_candidato, TICKER,
        )
        regime_dados["status_calibracao"]   = "calibrado"
        regime_dados["tp_calibrado"]        = tp_b
        regime_dados["stop_calibrado"]      = stop_b
        regime_dados["ir_calibrado"]        = round(ir_b, 4) if ir_b is not None else None
        regime_dados["n_trades_calibracao"] = n_trades_calib
        regime_dados["trials_rodados"]      = trials_b
        regime_dados["data_calibracao"]     = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        _escrever_regime_atomico(path_ativo, regime, regime_dados)
        emit_log(f"TUNE v3.1 [{TICKER}] {regime}: CALIBRADO — "
                 f"tp={tp_b} stop={stop_b} IR={ir_b:+.3f} ({trials_b} trials)", level="info")
        print(f"    → CALIBRADO: tp={tp_b} stop={stop_b} IR_calibrado={ir_b:+.3f} ({trials_b} trials)")

    # ── ETAPA C — Gate de Anomalia + Aplicação Automática ────────────
    emit_log(f"TUNE v3.1 [{TICKER}] Etapa C: gate de anomalia + aplicação automática...", level="info")
    print(f"\n{'=' * 60}")
    print(f"  Etapa C — Gate de Anomalia + Aplicação Automática")
    print(f"{'=' * 60}")

    _cfg_anomalia = _cfg_tune.get("anomalia", {})

    with open(path_ativo, encoding="utf-8") as f:
        dados_pos_b = json.load(f)
    ranking_pos_b = dados_pos_b.get("tune_ranking_estrategia", {})

    regimes_automaticos = []
    regimes_anomalos    = []

    for regime in sorted(todos_regimes):
        regime_dados = ranking_pos_b.get(regime, {})
        eleicao_status = regime_dados.get("eleicao_status")

        # Apenas regimes com estratégia definida passam pelo gate
        if eleicao_status not in ("competitiva", "estrutural_fixo"):
            continue
        if not regime_dados.get("estrategia_eleita"):
            continue

        # Injeta chave do regime para _avaliar_anomalia identificar estratégia anterior
        regime_dados["_regime_key"] = regime
        avaliacao = _avaliar_anomalia(regime_dados, dados_pos_b, _cfg_anomalia)
        del regime_dados["_regime_key"]

        if avaliacao["anomalo"]:
            regime_dados["anomalia"] = {"detectada": True, "motivos": avaliacao["motivos"]}
            regime_dados["aplicacao"] = "pendente_anomalia"
            regime_dados["confirmado"] = False
            ranking_pos_b[regime] = regime_dados
            regimes_anomalos.append(regime)
            emit_log(
                f"TUNE v3.1 [{TICKER}] {regime}: ANOMALIA — {avaliacao['motivos']}",
                level="warning",
            )
            emit_dc_event(
                "dc_tune_anomalia_detectada", "TUNE", "warning",
                ticker=TICKER, regime=regime, motivos=avaliacao["motivos"],
            )
            print(f"\n  {regime} → ANOMALIA")
            for m in avaliacao["motivos"]:
                print(f"    • {m}")
        else:
            regime_dados["anomalia"] = {"detectada": False, "motivos": []}
            regime_dados["aplicacao"] = "automatica"
            regime_dados["confirmado"] = True
            ranking_pos_b[regime] = regime_dados
            regimes_automaticos.append(regime)
            emit_log(f"TUNE v3.1 [{TICKER}] {regime}: aplicação automática OK", level="info")
            emit_dc_event(
                "dc_tune_aplicacao_automatica", "TUNE", "ok",
                ticker=TICKER, regime=regime,
            )
            print(f"\n  {regime} → aplicado automaticamente")

    # Escrita atômica única: ranking atualizado + aplicação dos regimes automáticos
    dados_pos_b["tune_ranking_estrategia"] = ranking_pos_b
    for regime in regimes_automaticos:
        regime_dados = ranking_pos_b[regime]
        _aplicar_regime_no_ativo(dados_pos_b, regime, regime_dados, run_id, "automatica")

    # ── ETAPA 4 — Finaliza meta ────────────────────────────────────────
    ranking_pos_b.setdefault("_meta", {})["concluido_em"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    dados_pos_b["tune_ranking_estrategia"] = ranking_pos_b
    _escrever_ativo_atomico(path_ativo, dados_pos_b)

    emit_dc_event("dc_tune_eleicao_complete", "TUNE", "ok",
                  ticker=TICKER, run_id=run_id,
                  regimes_automaticos=regimes_automaticos,
                  regimes_anomalos=regimes_anomalos)

    print(f"\n{'=' * 60}")
    print(f"  TUNE v3.1 [{TICKER}] — Eleição A→B→C concluída")
    print(f"  run_id: {run_id}")
    if regimes_automaticos:
        print(f"  Aplicados automaticamente: {', '.join(regimes_automaticos)}")
    if regimes_anomalos:
        print(f"  Anomalias pendentes CEO:   {', '.join(regimes_anomalos)}")
    if not regimes_anomalos:
        print(f"  Nenhuma anomalia detectada — todos os regimes aplicados.")
    print(f"{'=' * 60}")

    with open(path_ativo, encoding="utf-8") as f:
        dados_final = json.load(f)

    return {
        "ticker":                  TICKER,
        "run_id":                  run_id,
        "tune_ranking_estrategia": dados_final.get("tune_ranking_estrategia", {}),
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
