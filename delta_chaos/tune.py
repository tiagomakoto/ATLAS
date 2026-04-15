# ════════════════════════════════════════════════════════════════════
import json
import os
# DELTA CHAOS — TUNE v2.0
# Alterações em relação à v1.1:
# MIGRADO (P2): imports explícitos de init e tape — sem escopo global
# MIGRADO (P3): TICKER=input() → executar_tune(ticker: str) -> dict
# MIGRADO (P4): raise SystemExit → raise ValueError
# MIGRADO (P5): prints de inicialização sob if __name__ == "__main__"
# FASE 2: grade fixa de 6 combinações → Optuna TPE 200 trials (B23)
#         espaço: TP [0.40,0.95] step 0.05 | STOP [1.0,3.0] step 0.25 | janela [3,10] anos
# FASE 3: máscara REFLECT exclui ciclos Edge C/D/E da simulação (B30)
#         lê reflect_state por ciclo de reflect_cycle_history[] — fallback permissivo 'B'
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
# tune.py roda como subprocess do dc_runner. emit_log deve usar print()
# com flush=True para que o dc_runner capture stdout linha a linha.
# Nao importar atlas_backend.terminal_stream aqui: o processo filho
# nao tem acesso ao event_bus/loop do uvicorn pai.
def emit_log(msg, level="info"): print(f"[{level.upper()}] {msg}", flush=True)
def emit_error(e): print(f"[ERROR] {e}", flush=True)
_atlas_disponivel = False

# ── IPC via JSONL (eventos estruturados) ──────────────────────────────
# Importa emit_event de edge.py para escrever no arquivo JSONL
# que o dc_runner consome e emite via WebSocket
try:
    from delta_chaos.edge import emit_event
except ImportError:
    def emit_event(modulo, status, **kwargs): pass


def executar_tune(ticker: str) -> dict:
    """
    Executa calibração TUNE v2.0 para o ticker informado.
    Fase 2: Optuna substitui grade fixa de 6 combinações.
            Espaço: TP [0.40, 0.95] step 0.05 | STOP [1.0, 3.0] step 0.25 | janela [3, 10] anos.
            200 trials TPE | early stopping patience=50 min_delta=0.001.
    Fase 3: Máscara REFLECT exclui ciclos Edge C/D/E da simulação.
            Lê reflect_state por ciclo de reflect_cycle_history[] com fallback permissivo 'B'.
    Registra no historico_config[] do master JSON — não aplica automaticamente.
    Lança ValueError se ORBIT não gerou histórico.
    """
    TICKER = ticker.strip().upper()
    from pathlib import Path as _Path
    _TMP_DIR = _Path(__file__).resolve().parent.parent / "tmp"
    _TMP_DIR.mkdir(parents=True, exist_ok=True)
    _study_db = _TMP_DIR / f"tune_{TICKER}.db"

    emit_log(f"TUNE PING — {TICKER} | conexão WebSocket ativa", level="debug")

    import json, os, tempfile
    import pandas as pd
    import numpy as np
    from datetime import datetime
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    # ═══════════════════════════════════════════════════════════════════
    # CONFIGURAÇÃO
    # ═══════════════════════════════════════════════════════════════════

    ANO_WARMUP = 2004
    ano_atual  = datetime.now().year
    ANOS       = list(range(2002, ano_atual + 1))

    # Fase 2 — Optuna (B23 fechada)
    OPTUNA_N_TRIALS  = 200
    OPTUNA_STARTUP   = 50
    OPTUNA_PATIENCE  = 50
    OPTUNA_MIN_DELTA = 0.001
    OPTUNA_SEED      = 42
    TP_MIN,   TP_MAX,   TP_STEP   = 0.40, 0.95, 0.05
    STOP_MIN, STOP_MAX, STOP_STEP = 1.0,  3.0,  0.25
    JANELA_MIN, JANELA_MAX        = 3, 10

    # Fase 3 — Máscara REFLECT (B3 resolvido)
    REFLECT_ESTADOS_BLOQUEADOS = {"C", "D", "E"}

    # ═══════════════════════════════════════════════════════════════════
    # ETAPA 1 — carrega tudo uma vez
    # ═══════════════════════════════════════════════════════════════════

    emit_log(f"TUNE [{TICKER}] Etapa 1/3: carregando TAPE/SELIC/ORBIT/REFLECT", level="info")

    print("=" * 60)
    print(f"  TUNE v2.0 — {TICKER}")
    print(f"  Fase 2: Optuna TPE {OPTUNA_N_TRIALS} trials")
    print(f"  Fase 3: Máscara REFLECT (bloqueia Edge C/D/E)")
    print(f"  Warmup:       descartar ciclos < {ANO_WARMUP}")
    print(f"  Janela teste: hiperparâmetro Optuna [{JANELA_MIN}–{JANELA_MAX} anos]")
    print("=" * 60)

    print(f"\n  [1/4] TAPE...")
    df_tape_c = tape_historico_carregar(
        ativos=[TICKER], anos=ANOS, forcar=False)
    print(f"  ✓ {len(df_tape_c):,} registros carregados")

    print(f"\n  [2/4] SELIC...")
    # df_selic carregado para uso futuro (vencimento com preço de exercício)
    # Não usado na simulação Optuna atual — mantido para extensibilidade
    _obter_selic(min(ANOS), max(ANOS))
    print(f"  ✓ SELIC carregada")

    print(f"\n  [3/4] Config ativo...")
    cfg_ativo = tape_ativo_carregar(TICKER)
    cfg_ativo.pop("take_profit", None)
    cfg_ativo.pop("stop_loss",   None)
    print(f"  ✓ {TICKER} config carregado")

    datas = sorted(df_tape_c["data"].unique())
    print(f"  ✓ {len(datas):,} pregões")

    print(f"\n  [4/4] Regimes ORBIT + REFLECT...")
    path_ativo = os.path.join(ATIVOS_DIR, f"{TICKER}.json")
    with open(path_ativo) as f:
        dados_ativo = json.load(f)

    historico_c = pd.DataFrame(dados_ativo["historico"])
    if len(historico_c) == 0:
        print(f"  ~ Histórico ORBIT vazio — calculando agora...")
        _orbit_tune = ORBIT(universo={TICKER: {}})
        externas = tape_externas_carregar([TICKER], ANOS)
        _orbit_tune.orbit_rodar(df_tape_c, ANOS, modo="cache", externas_dict=externas)
        with open(path_ativo) as f:
            dados_ativo = json.load(f)
        historico_c = pd.DataFrame(dados_ativo["historico"])
        if len(historico_c) == 0:
            raise ValueError(f"TUNE bloqueado em {TICKER}: ORBIT não gerou histórico")
        print(f"  ✓ ORBIT calculado — {len(historico_c)} ciclos")

    historico_c["ciclo_id"] = historico_c["ciclo_id"].astype(str)

    # Warmup
    n_antes = len(historico_c)
    historico_c = historico_c[
        pd.to_datetime(historico_c["data_ref"]).dt.year >= ANO_WARMUP
    ].copy()
    historico_c = historico_c.drop_duplicates(subset="ciclo_id", keep="last")
    regime_idx_c = historico_c.set_index("ciclo_id").to_dict("index")
    print(f"  ✓ Warmup: {n_antes} → {len(historico_c)} ciclos em uso")

    # Fase 3 — carrega máscara REFLECT por ciclo
    # reflect_cycle_history: {ciclo_id: {reflect_state, score_reflect, ...}}
    # Fallback permissivo: ciclo ausente → estado 'B' (não bloqueia)
    reflect_cycle_hist = dados_ativo.get("reflect_cycle_history", {})
    n_mask = sum(
        1 for cid in historico_c["ciclo_id"]
        if reflect_cycle_hist.get(cid, {}).get("reflect_state", "B")
        in REFLECT_ESTADOS_BLOQUEADOS
    )
    print(f"  ✓ REFLECT mask: {n_mask}/{len(historico_c)} ciclos bloqueados (Edge C/D/E)")

    with open(CONFIG_PATH) as f:
        _cfg_baseline = json.load(f)
    tp_baseline_ant   = _cfg_baseline["fire"]["take_profit"]
    stop_baseline_ant = _cfg_baseline["fire"]["stop_loss"]

    print(f"\n  ✓ Etapa 1 concluída — tudo em memória")

    # ═══════════════════════════════════════════════════════════════════
    # ETAPA 2 — simulação intradiária via Optuna (Fases 2 + 3)
    # ═══════════════════════════════════════════════════════════════════
    # Lógica Opção B (SCAN — Sarah Hamilton):
    #   STOP primeiro (proxy: máximo do dia), depois TP (proxy: mínimo do dia)
    # Fase 3: antes de abrir posição, verifica reflect_state do ciclo.
    #   Edge C/D/E → pula abertura (ciclo mascarado).
    #   Edge A/B ou ausente → opera normalmente.
    # ═══════════════════════════════════════════════════════════════════

    emit_log(f"TUNE [{TICKER}] Etapa 2/3: Optuna {OPTUNA_N_TRIALS} trials...", level="info")
    print(f"\n{'=' * 60}")
    print(f"  Etapa 2 — Optuna Fases 2+3")
    print(f"{'=' * 60}")

    # Pré-computa lookup O(1): (data_str, ticker) → {fechamento, minimo, maximo}
    df_ops_idx = df_tape_c[df_tape_c["tipo"].isin(["CALL", "PUT"])].copy()
    df_ops_idx["data_str"] = df_ops_idx["data"].astype(str).str[:10]
    tape_lookup = df_ops_idx.groupby(
        ["data_str", "ticker"])[["fechamento", "minimo", "maximo"]].first()

    # C2 — pré-computa df_dia por data fora de _simular()
    # Evita filtrar df_tape_c 200x × N_datas dentro do loop Optuna
    # Loop com progresso a cada 500 datas para feedback visual
    emit_log(f"TUNE [{TICKER}] pré-computando {len(datas):,} dias...", level="info")
    emit_event("TUNE_INDEX", "start", ticker=TICKER, total=len(datas))
    df_dias = {}
    for i, data in enumerate(datas):
        df_dias[str(data)[:10]] = df_tape_c[df_tape_c["data"] == data].copy()
        if (i + 1) % 100 == 0 or (i + 1) == len(datas):
            emit_event("TUNE_INDEX", "progress", ticker=TICKER, current=i+1, total=len(datas))
        emit_log(f"TUNE [{TICKER}] pré-cômputo concluído — iniciando Optuna", level="info")
        emit_event("TUNE_INDEX", "done", ticker=TICKER)

    # C1 — constantes do BOOK extraídas uma vez fora de _simular()
    # Evita carregar_config() dentro do loop de 200 trials × N_pregões
    _cfg_book_tune = carregar_config()["book"]
    _RT = _cfg_book_tune["risco_trade"]
    _FM = _cfg_book_tune["fator_margem"]
    _NM = _cfg_book_tune["n_contratos_minimo"]

    def _get_regime(ciclo_id):
        raw = regime_idx_c.get(ciclo_id, {})
        return {
            "regime": raw.get("regime", "DESCONHECIDO"),
            "ir":     float(raw.get("ir", 0.0)),
            "sizing": float(raw.get("sizing", 0.0)),
        }

    def _reflect_bloqueado(ciclo_id):
        """Fase 3: retorna True se ciclo está em Edge C/D/E."""
        estado = reflect_cycle_hist.get(ciclo_id, {}).get("reflect_state", "B")
        return estado in REFLECT_ESTADOS_BLOQUEADOS

    _cfg_f      = carregar_config()["fire"]
    DIAS_MIN    = _cfg_f["dias_min"]
    DIAS_MAX    = _cfg_f["dias_max"]
    PREMIO_MIN  = _cfg_f["premio_minimo"]
    COOLING_OFF = _cfg_f["cooling_off_dias"]
    IV_MINIMO   = _cfg_f["iv_minimo"]

    _estrategias    = cfg_ativo.get("estrategias", {})
    _reg_sizing     = cfg_ativo.get("regimes_sizing", {})
    _delta_alvo_cfg = carregar_config()["fire"]["delta_alvo"]
    DELTA_ALVO_TUNE = {
        "CSP":              {"PUT":  _delta_alvo_cfg["CSP"]["put_vendida"]},
        "BULL_PUT_SPREAD":  {"PUT":  _delta_alvo_cfg["BULL_PUT_SPREAD"]["put_vendida"]},
        "BEAR_CALL_SPREAD": {"CALL": _delta_alvo_cfg["BEAR_CALL_SPREAD"]["call_vendida"]},
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

    def _simular(tp: float, stop: float, janela_anos: int) -> dict:
        """
        Roda simulação completa para um par (TP, STOP, janela_anos).
        Retorna dict com métricas. Chamado pelo Optuna a cada trial.
        Usa df_dias, tape_lookup, _RT/_FM/_NM pré-computados (C1+C2).
        """
        ano_teste_ini  = ano_atual - janela_anos
        posicao_aberta = None
        ultimo_stop_dt = None
        trades         = []

        for data in datas:
            data_str = str(data)[:10]
            ciclo_id = data_str[:7]
            df_dia   = df_dias[data_str]  # C2: lookup O(1), sem filtro

            # ── Verifica posição aberta ───────────────────────────────
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

                # Vencimento
                if dias_rest <= 0:
                    strike   = leg["strike"]
                    tipo_leg = leg["tipo"]
                    acao = df_dia[
                        (df_dia["ativo_base"] == TICKER) &
                        (df_dia["tipo"] == "ACAO")
                    ]["fechamento"]
                    if acao.empty:
                        p_saida = 0.0
                    else:
                        preco_acao = float(acao.iloc[0])
                        p_saida = max(0, strike - preco_acao) if tipo_leg == "PUT" \
                                  else max(0, preco_acao - strike)
                    pnl = (premio_ref - p_saida) * posicao_aberta["n"]
                    trades.append({
                        "data_entrada": posicao_aberta["data_entrada"],
                        "data_saida":   data_str,
                        "motivo":       "VENCIMENTO",
                        "pnl":          round(pnl, 4),
                    })
                    posicao_aberta = None
                    fechou = True

                # STOP — proxy: máximo do dia
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

                # TP — proxy: mínimo do dia
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

            # ── Tenta abrir posição ───────────────────────────────────
            if posicao_aberta is None:
                # Fase 3 — máscara REFLECT: bloqueia ciclos Edge C/D/E
                if _reflect_bloqueado(ciclo_id):
                    continue

                orbit  = _get_regime(ciclo_id)
                regime = orbit["regime"]

                # Cooling off
                if ultimo_stop_dt is not None:
                    if (pd.Timestamp(data_str) - ultimo_stop_dt).days < COOLING_OFF:
                        continue

                sizing_config = float(_reg_sizing.get(regime, 0.0))
                sizing_orbit  = orbit["sizing"]
                if sizing_config <= 0.0 or sizing_orbit <= 0.0:
                    continue

                estrategia = _estrategias.get(regime)
                if not estrategia:
                    continue

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

        # Métricas
        if not trades:
            return {"ir_valido": 0.0, "pnl_valido": 0.0, "trades_valido": 0,
                    "ir_total": 0.0, "trades_total": 0, "acerto_valido": 0.0,
                    "n_stops": 0, "tp": tp, "stop": stop, "janela_anos": janela_anos,
                    "ano_teste_ini": ano_teste_ini}

        df_tr   = pd.DataFrame(trades)
        valido  = df_tr[pd.to_datetime(df_tr["data_entrada"]).dt.year >= ano_teste_ini]

        pnls   = df_tr["pnl"].values
        pnls_v = valido["pnl"].values if len(valido) > 0 else np.array([])

        ir_total  = (float(np.mean(pnls) / (np.std(pnls) + 1e-10) *
                     np.sqrt(252/21)) if len(pnls) > 5 else 0.0)
        ir_valido = (float(np.mean(pnls_v) / (np.std(pnls_v) + 1e-10) *
                     np.sqrt(252/21)) if len(pnls_v) > 5 else 0.0)

        return {
            "ir_valido":     ir_valido,
            "pnl_valido":    float(valido["pnl"].sum()) if len(valido) > 0 else 0.0,
            "trades_valido": len(valido),
            "ir_total":      ir_total,
            "trades_total":  len(df_tr),
            "acerto_valido": float((valido["pnl"] > 0).mean() * 100) if len(valido) > 0 else 0.0,
            "n_stops":       int((df_tr["motivo"] == "STOP").sum()),
            "tp":            tp,
            "stop":          stop,
            "janela_anos":   janela_anos,
            "ano_teste_ini": ano_teste_ini,
        }

    # ── Função objetivo Optuna ────────────────────────────────────────
    def objective(trial):
        tp          = trial.suggest_float("tp",   TP_MIN,   TP_MAX,   step=TP_STEP)
        stop        = trial.suggest_float("stop", STOP_MIN, STOP_MAX, step=STOP_STEP)
        janela_anos = trial.suggest_int("janela_anos", JANELA_MIN, JANELA_MAX)
        res = _simular(tp, stop, janela_anos)
        # Reporta métricas como user_attrs para relatório final
        for k, v in res.items():
            trial.set_user_attr(k, v)
    # Print para terminal (stdout capturado pelo dc_runner)
        n = trial.number + 1
        fase = "warmup" if n <= OPTUNA_STARTUP else "TPE"
        emit_log(
            f"TUNE [{TICKER}] trial {n:>3}/{OPTUNA_N_TRIALS} [{fase}] "
            f"tp={tp:.2f} stop={stop:.2f} janela={janela_anos}a "
            f"ir={res['ir_valido']:+.3f}",
            level="info"
        )
        # IPC: emite evento estruturado para o frontend via WebSocket
        emit_event(
            "TUNE_TRIAL", "progress",
            ticker=TICKER,
            trial=n,
            total=OPTUNA_N_TRIALS,
            fase=fase,
            tp=tp,
            stop=stop,
            janela_anos=janela_anos,
            ir=res["ir_valido"],
            best_ir=study.best_value if study.trials else -999.0
        )
        return res["ir_valido"]

    # ── Executa estudo Optuna ─────────────────────────────────────────
    sampler = optuna.samplers.TPESampler(
        n_startup_trials=OPTUNA_STARTUP,
        seed=OPTUNA_SEED
    )
    # Apaga estudo anterior — cada TUNE é calibração nova, não retomada
    if _study_db.exists():
        _study_db.unlink()
        emit_log(f"TUNE [{TICKER}] estudo anterior removido — iniciando do zero", level="info")

    study = optuna.create_study(
        storage=f"sqlite:///{_study_db}",
        study_name=TICKER,
        load_if_exists=False,
        direction="maximize",
        sampler=sampler,
    )

    # Early stopping: patience=50 trials sem melhoria de min_delta
    _sem_melhoria = [0]
    _melhor_valor = [study.best_value if study.trials else -999.0]

    def _early_stop_cb(study, trial):
        # C3: não conta paciência durante warm-up do TPE
        # Evita early stop prematuro antes do surrogate model estar ativo
        if trial.number < OPTUNA_STARTUP:
            return
        # emit_log de progresso só no TPE — warmup já emite via objective()
        if study.best_value > _melhor_valor[0] + OPTUNA_MIN_DELTA:
            _melhor_valor[0] = study.best_value
            _sem_melhoria[0] = 0
        else:
            _sem_melhoria[0] += 1
        # NOVO — emite evento por trial para WebSocket/EventFeed do ATLAS
        emit_log(
            f"TUNE [{TICKER}] trial {trial.number + 1}/{OPTUNA_N_TRIALS} "
            f"best_ir={_melhor_valor[0]:+.4f} sem_melhoria={_sem_melhoria[0]}",
            level="info"
        )
        if _sem_melhoria[0] >= OPTUNA_PATIENCE:
            study.stop()

    print(f"  Rodando {OPTUNA_N_TRIALS} trials (early stop patience={OPTUNA_PATIENCE})...")
    study.optimize(objective, n_trials=OPTUNA_N_TRIALS, callbacks=[_early_stop_cb])

    trials_rodados = len(study.trials)
    melhor_trial   = study.best_trial
    melhor_attrs   = melhor_trial.user_attrs

    print(f"  ✓ Optuna concluído: {trials_rodados} trials rodados")
    print(f"  ✓ Melhor: TP={melhor_attrs['tp']:.2f} "
          f"STOP={melhor_attrs['stop']:.2f} "
          f"janela={melhor_attrs['janela_anos']}a "
          f"IR válido={melhor_attrs['ir_valido']:+.3f} "
          f"P&L=R${melhor_attrs['pnl_valido']:+,.0f} "
          f"trades={melhor_attrs['trades_valido']}")

    # ═══════════════════════════════════════════════════════════════════
    # ETAPA 3 — relatório e registro
    # ═══════════════════════════════════════════════════════════════════

    emit_log(f"TUNE [{TICKER}] Etapa 3/3: relatório e registro", level="info")

    ano_teste_ini = melhor_attrs["ano_teste_ini"]

    # Sistema graduado de confiança por N (PE-001)
    n_trades = melhor_attrs["trades_valido"]
    if n_trades >= 50:
        confianca = "alta"
    elif n_trades >= 20:
        confianca = "baixa"
    else:
        confianca = "amostra_insuficiente"

    print(f"\n{'═' * 60}")
    print(f"  {TICKER} — TUNE v2.0 — Resultado Optuna")
    print(f"{'═' * 60}")
    print(f"  TP:             {melhor_attrs['tp']:.2f}")
    print(f"  STOP:           {melhor_attrs['stop']:.2f}x")
    print(f"  Janela teste:   {melhor_attrs['janela_anos']} anos "
          f"({ano_teste_ini}–{ano_atual})")
    print(f"  IR válido:      {melhor_attrs['ir_valido']:+.3f}")
    print(f"  P&L válido:     R${melhor_attrs['pnl_valido']:+,.0f}")
    print(f"  Trades válidos: {n_trades}")
    print(f"  Acerto válido:  {melhor_attrs['acerto_valido']:.1f}%")
    print(f"  Stops totais:   {melhor_attrs['n_stops']}")
    print(f"  Confiança N:    {confianca} (PE-001)")
    print(f"  REFLECT mask:   {n_mask} ciclos excluídos (Edge C/D/E)")
    print(f"  Trials rodados: {trials_rodados}/{OPTUNA_N_TRIALS}")
    if confianca == "amostra_insuficiente":
        print(f"\n  ⚠ AMOSTRA INSUFICIENTE (N={n_trades} < 20)")
        print(f"    Resultado não confiável — TP/STOP default mantido")
    elif confianca == "baixa":
        print(f"\n  ⚠ CONFIANÇA BAIXA (N={n_trades}, 20–49) — interpretar com cautela")
    print(f"{'═' * 60}")

    # Registro no historico_config[]
    with open(path_ativo) as f:
        dados = json.load(f)

    if "historico_config" not in dados:
        dados["historico_config"] = []

    dados["historico_config"].append({
        "data":          str(datetime.now())[:10],
        "modulo":        "TUNE v2.0",
        "parametro":     "take_profit / stop_loss / janela_anos",
        "valor_ant":     f"TP={tp_baseline_ant} STOP={stop_baseline_ant}",
        "valor_novo":    f"TP={melhor_attrs['tp']} STOP={melhor_attrs['stop']}",
        "motivo":        (f"TUNE v2.0 Optuna — IR válido ({ano_teste_ini}–{ano_atual}) "
                         f"IR={melhor_attrs['ir_valido']:+.3f} "
                         f"P&L=R${melhor_attrs['pnl_valido']:,.0f} "
                         f"trades={n_trades} confianca={confianca} "
                         f"reflect_mask={n_mask}ciclos"),
        "janela_anos":   melhor_attrs["janela_anos"],
        "ano_teste_ini": ano_teste_ini,
        "trials":        trials_rodados,
        "confianca_n":   confianca,
        "reflect_mask":  n_mask,
        "metodo":        "optuna_v2",
    })
    dados["atualizado_em"] = str(datetime.now())[:19]

    dir_ = os.path.dirname(path_ativo)
    with tempfile.NamedTemporaryFile(
            "w", dir=dir_, suffix=".tmp",
            delete=False, encoding="utf-8") as tf:
        json.dump(dados, tf, indent=2, ensure_ascii=False, default=str)
        tmp_path = tf.name
    os.replace(tmp_path, path_ativo)

    print(f"  ✓ Resultado registrado no master JSON de {TICKER}")

    _tp_aplicar   = melhor_attrs["tp"]
    _stop_aplicar = melhor_attrs["stop"]

    if confianca != "amostra_insuficiente":
        print(f"\n{'=' * 52}")
        print(f"  ⚠ Aplicar requer decisão explícita do CEO")
        print(f"  Para aplicar, cole e execute a célula abaixo:")
        print(f"{'=' * 52}")
        print(f"""
    # Aplicar TUNE v2.0 — {TICKER}
    # TP={_tp_aplicar} STOP={_stop_aplicar} — IR válido={melhor_attrs['ir_valido']:+.3f}
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

    return {
        "ticker":   TICKER,
        "melhor": {
            "tp":            _tp_aplicar,
            "stop":          _stop_aplicar,
            "janela_anos":   melhor_attrs["janela_anos"],
            "ano_teste_ini": ano_teste_ini,
            "ir_valido":     melhor_attrs["ir_valido"],
            "pnl_valido":    melhor_attrs["pnl_valido"],
            "trades_valido": n_trades,
            "confianca_n":   confianca,
            "reflect_mask":  n_mask,
            "trials":        trials_rodados,
        },
    }


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

    with open(book_path) as f:
        book_raw = json.load(f)

    ops = book_raw.get("ops", [])
    if not ops:
        raise ValueError(f"BOOK backtest vazio para {TICKER}.")

    # ── Monta DataFrame de trades fechados do ativo ───────────────────
    rows = []
    for op in ops:
        core  = op.get("core", {})
        orbit = op.get("orbit", {})

        # Filtra: apenas fechadas, apenas o ativo, sem não-entradas
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

        # Vencedora: maior IR entre células com confianca != 'amostra_insuficiente'
        candidatas = {
            e: v for e, v in celulas.items()
            if v["confianca"] != "amostra_insuficiente"
        }

        if candidatas:
            vencedora = max(candidatas, key=lambda e: candidatas[e]["ir"])
            status    = "ok"
        else:
            # Todas as células com N insuficiente — usa maior N como fallback
            vencedora = max(celulas, key=lambda e: celulas[e]["n"]) if celulas else None
            status    = "amostra_insuficiente"

        resultado[regime] = {
            "vencedora": vencedora,
            "status":    status,
            "celulas":   celulas,
        }

    # ── Relatório ─────────────────────────────────────────────────────
    print(f"\n{'═' * 60}")
    print(f"  {TICKER} — Diagnóstico de Estratégia por Regime (Fase 4)")
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

    print(f"\n  Não aplicado automaticamente — requer confirmação do CEO.")
    print(f"  Para aplicar, use: tune_aplicar_estrategias('{TICKER}', resultado)")
    print(f"{'═' * 60}")

    return {
        "ticker":    TICKER,
        "resultado": resultado,
        "avisos":    aviso_n_baixo,
    }


def tune_aplicar_estrategias(ticker: str, diagnostico: dict) -> None:
    """
    Aplica resultado do tune_diagnostico_estrategia() no master JSON.
    Atualiza campo 'estrategias' por regime com a vencedora diagnosticada.
    Só aplica regimes com status == 'ok' — regimes com amostra_insuficiente
    mantêm a estratégia atual.
    Exige confirmação explícita do CEO antes de chamar.
    """
    import json, os, tempfile
    from datetime import datetime

    TICKER = ticker.strip().upper()
    path_ativo = os.path.join(ATIVOS_DIR, f"{TICKER}.json")

    with open(path_ativo) as f:
        dados = json.load(f)

    if "estrategias" not in dados:
        dados["estrategias"] = {}

    aplicados   = []
    ignorados   = []
    resultado   = diagnostico.get("resultado", {})

    for regime, dados_regime in resultado.items():
        if dados_regime["status"] != "ok":
            ignorados.append(f"{regime} (amostra_insuficiente)")
            continue
        vencedora = dados_regime["vencedora"]
        if vencedora is None:
            ignorados.append(f"{regime} (sem vencedora)")
            continue
        anterior = dados["estrategias"].get(regime, "N/A")
        dados["estrategias"][regime] = vencedora
        aplicados.append(f"{regime}: {anterior} → {vencedora}")

    # Registra no historico_config[]
    if "historico_config" not in dados:
        dados["historico_config"] = []
    dados["historico_config"].append({
        "data":     str(datetime.now())[:10],
        "modulo":   "TUNE v2.0 Fase 4",
        "parametro": "estrategias por regime",
        "aplicados": aplicados,
        "ignorados": ignorados,
        "metodo":   "diagnostico_pnl_regime",
    })
    dados["atualizado_em"] = str(datetime.now())[:19]

    # Escrita atômica
    dir_ = os.path.dirname(path_ativo)
    with tempfile.NamedTemporaryFile(
            "w", dir=dir_, suffix=".tmp",
            delete=False, encoding="utf-8") as tf:
        json.dump(dados, tf, indent=2, ensure_ascii=False, default=str)
        tmp_path = tf.name
    os.replace(tmp_path, path_ativo)

    print(f"\n  ✓ Estratégias aplicadas em {TICKER}:")
    for a in aplicados:
        print(f"    • {a}")
    if ignorados:
        print(f"  ~ Ignorados (amostra insuficiente):")
        for i in ignorados:
            print(f"    • {i}")


if __name__ == "__main__":
    import sys
    t = (sys.argv[1] if len(sys.argv) > 1
         else input("Ticker para TUNE: ").strip().upper())
    resultado = executar_tune(t)
    m = resultado["melhor"]
    print(f"\n  Melhor: TP={m['tp']} STOP={m['stop']} "
          f"janela={m['janela_anos']}a "
          f"IR={m['ir_valido']:+.3f} "
          f"confiança={m['confianca_n']}")
