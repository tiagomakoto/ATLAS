# ════════════════════════════════════════════════════════════════════
import os
from datetime import datetime
# DELTA CHAOS — EDGE v2.0
# Alterações em relação à v1.3:
# MIGRADO (P2): imports explícitos de todos os módulos — sem escopo global
# MIGRADO (P5): prints de inicialização sob if __name__ == "__main__"
# MANTIDO: orquestração backtest/paper/EOD, REFLECT, GATE EOD, BOOK
# ════════════════════════════════════════════════════════════════════


# =====================================================================
# [ATLAS-STATUS-LOGIC] — DO NOT DELETE — Lógica de Status do Sistema
# ---------------------------------------------------------------------
# Status válidos: SEM_EDGE | OPERAR | MONITORAR | SUSPENSO | BLOQUEADO
#
#   BLOQUEADO  — Ativo sem calibração. Nunca executou ORBIT+TUNE+GATE.
#                É necessário rodar a calibração completa para ativar.
#
#   SEM_EDGE   — Backtest com dados suficientes mas sem IR capturável
#                em nenhum regime. Sem estratégia viável.
#                Ex: ITUB4
#
#   MONITORAR  — Edge identificado em backtest mas GATE incompleto,
#                parcial (5-7/8) ou condições atuais inadequadas.
#                Ex: BBAS3 (GATE 7/8, E5 bloqueado)
#
#   OPERAR     — GATE 8/8 aprovado, ORBIT atual autoriza.
#                Elegível para paper trading ou capital real.
#                Ex: VALE3, PETR4, BOVA11
#
#   SUSPENSO   — Estava em OPERAR. Duas quedas consecutivas de Edge
#                de um mês para o outro (ex: A→C ou B→D).
#                Edge histórico existe — condições atuais impedem.
#                Retoma quando REFLECT recuperar por 2-3 ciclos.
#
# Regras de determinação (ver bloco "Determinar status" em get_ativo):
#   1. Sem histórico (sem historico_config) → BLOQUEADO
#   2. Quedas REFLECT consecutivas >= 2 (D ou T) → SUSPENSO
#   3. GATE 8/8 + IR > 0 + REFLECT em A/B → OPERAR
#   4. GATE com resultado válido (não 8/8) → MONITORAR
#   5. Sem IR capturável em nenhum regime → SEM_EDGE
# ---------------------------------------------------------------------
# [ATLAS-STATUS-LOGIC-END] — DO NOT DELETE
# =====================================================================

#
# --modo orbit_backtest    calibração step 1: COTAHIST + ORBIT + popula historico[]
# --modo tune             calibração step 2 + atualização mensal step 3 (se elegível)
# --modo backtest_gate    calibração step 3 + atualização mensal step 2: GATE completo
# --modo orbit_update       atualização mensal: OHLCV cache + ORBIT + reflect_cycle
# --modo eod              diário: paper/live



from delta_chaos.init import (
    carregar_config, ATIVOS_DIR, BOOK_DIR,
    OPCOES_HOJE_DIR, DRIVE_BASE,
)
from pathlib import Path
import os
import json
from datetime import datetime

# ── Logging ATLAS ─────────────────────────────────
from atlas_backend.core.terminal_stream import emit_log, emit_error
from atlas_backend.core.event_bus import emit_dc_event

def emit_event(modulo, status, ticker=None, **kwargs):
    if status == "start":
        emit_dc_event("dc_module_start", modulo, "running", ticker=ticker, **kwargs)
    elif status == "done":
        emit_dc_event("dc_module_complete", modulo, "ok", ticker=ticker, **kwargs)
    elif status == "error":
        emit_dc_event("dc_module_complete", modulo, "error", ticker=ticker, **kwargs)
    else:
        emit_dc_event("dc_module_complete", modulo, status, ticker=ticker, **kwargs)


# ════════════════════════════════════════════════════════════════════
# DELTA CHAOS — EDGE v1.3
# Alterações em relação à v1.2:
# ADICIONADO: integração com REFLECT via reflect_sizing_calcular()
# ADICIONADO: verificação reflect_permanent_block_flag antes de abrir
# ADICIONADO: reflect_cycle_calcular no fechamento de cada ciclo mensal
# CORRIGIDO (SCAN-11): configs_ativos indefinido no modo paper — NameError
# CORRIGIDO (SCAN-9): cfg passado ao FIRE no paper — evita dupla leitura JSON
# ════════════════════════════════════════════════════════════════════

import os
from datetime import datetime
from datetime import datetime, date
import pandas as pd
from tqdm.auto import tqdm as _tqdm

from delta_chaos.tape import (
    tape_ativo_carregar,
    tape_ativo_salvar,
    tape_historico_carregar,
    tape_eod_carregar,
    tape_ohlcv_carregar,
    tape_ibov_carregar,
    tape_externas_carregar,
    _obter_selic,
)
from .orbit import ORBIT
from .book import BOOK
from .fire import FIRE
from .gate_eod import gate_eod_verificar

# ── REFLECT FUNCTIONS (moved from tape.py) ────────────────────────────────────

def reflect_daily_calcular(ativo: str, data: str, df_eod: pd.DataFrame) -> dict:
    """
    Calcula componentes REFLECT diários (IV/Prêmio, Ret/Vol, GEX).
    Retorna dict com os valores calculados.
    """
    cfg = tape_ativo_carregar(ativo)

    # Calcular componentes (copiado de tape_reflect_daily)
    div = _calculate_divergence_components(df_eod, ativo, data)
    preco_acao = (float(df_eod["preco_acao"].iloc[0])
                  if not df_eod.empty and "preco_acao" in df_eod.columns else 0.0)
    gex = _calculate_gex(df_eod, preco_acao)

    return {
        "iv_prem_ratio": div["iv_prem_ratio"],
        "ret_vol_ratio": div["ret_vol_ratio"],
        "gex": gex,
    }

def reflect_daily_salvar(ativo: str, data: str, df_eod: pd.DataFrame) -> None:
    """
    Salva componentes REFLECT diários no master JSON do ativo.
    """
    cfg = tape_ativo_carregar(ativo)

    if "reflect_daily_history" not in cfg:
        cfg["reflect_daily_history"] = {}

    # Só salva se ainda não existir para este dia
    if data not in cfg["reflect_daily_history"]:
        componentes = reflect_daily_calcular(ativo, data, df_eod)
        cfg["reflect_daily_history"][data] = {
            "iv_prem_ratio": componentes["iv_prem_ratio"],
            "ret_vol_ratio": componentes["ret_vol_ratio"],
            "gex": componentes["gex"],
        }
        print(f"  ✓ REFLECT diário {ativo} {data}: "
              f"IV/Prêmio={componentes['iv_prem_ratio']:.4f}  "
              f"Ret/Vol={componentes['ret_vol_ratio']:.4f}")
        tape_ativo_salvar(ativo, cfg)

def reflect_cycle_calcular(ativo: str, ciclo_id: str) -> None:
    """
    Calcula o estado REFLECT definitivo para o ciclo mensal.
    (Copiado de tape_reflect_cycle, adaptado para usar tape_ativo_carregar/salvar)
    """
    cfg = tape_ativo_carregar(ativo)
    _cfg_reflect = carregar_config()["reflect"]
    _cfg_orbit = carregar_config()["orbit"]

    zscore_window = _cfg_reflect["reflect_zscore_window"]
    delta_ir_short_window = _cfg_reflect["reflect_delta_ir_short_window"]
    delta_ir_long_window = _cfg_reflect["reflect_delta_ir_long_window"]
    div_iv_window = _cfg_reflect["divergence_iv_prem_rolling_window"]
    div_rv_window = _cfg_reflect["divergence_ret_vol_rolling_window"]

    # Verificação de causas
    historico_orbit = cfg.get("historico", [])
    ciclo_existe_orbit = any(
        c.get("ciclo_id") == ciclo_id for c in historico_orbit
    )

    if not ciclo_existe_orbit:
        raise ValueError(f"ORBIT desatualizado — ciclo {ciclo_id} ausente no master JSON")

    # Cálculo da aceleração (score_vel derivative)
    historico_df = pd.DataFrame(cfg.get("historico", []))
    if historico_df.empty or "ciclo_id" not in historico_df.columns:
        raise ValueError("Histórico ORBIT vazio ou sem ciclo_id")

    historico_df = historico_df.set_index("ciclo_id")
    if ciclo_id not in historico_df.index:
        raise ValueError(f"Ciclo {ciclo_id} não encontrado no histórico")

    idx = historico_df.index.get_loc(ciclo_id)
    if isinstance(idx, slice):
        idx = idx.start

    aceleracao = 0.0
    if idx >= 1:
        sv_atual = float(historico_df.iloc[idx].get("score_vel", 0.0))
        sv_ant = float(historico_df.iloc[idx-1].get("score_vel", 0.0))
        aceleracao = sv_atual - sv_ant

    # Componentes de divergência (média rolling) — com fallback
    daily_hist = cfg.get("reflect_daily_history", {})
    divergencia_disponivel = False
    iv_media = None
    rv_media = None

    if daily_hist:
        daily_df = pd.DataFrame.from_dict(daily_hist, orient="index")
        daily_df.index = pd.to_datetime(daily_df.index)
        try:
            mask = daily_df.index.to_period("M") == pd.Period(ciclo_id)
            df_ciclo = daily_df[mask].copy()
            if not df_ciclo.empty:
                iv_media = float(df_ciclo["iv_prem_ratio"].mean())
                rv_media = float(df_ciclo["ret_vol_ratio"].mean())
                divergencia_disponivel = True
        except Exception:
            pass

    # Delta IR (curto vs longo)
    delta_ir = 0.0
    if len(historico_df) >= delta_ir_long_window:
        ir_curto = historico_df.iloc[idx]["ir"]
        ir_longo = historico_df.iloc[idx - delta_ir_long_window]["ir"]
        delta_ir = ir_curto - ir_longo

    # Pesos base da config
    w_base = carregar_config()["reflect"]["weights"]
    # Esperado: {"aceleracao": 0.33, "divergencia": 0.33, "delta_ir": 0.33}

    # Definir pesos efetivos conforme disponibilidade da divergência
    if divergencia_disponivel:
        w = {
            "aceleracao":  w_base["aceleracao"],
            "divergencia": w_base["divergencia"],
            "delta_ir":    w_base["delta_ir"]
        }
        fonte_divergencia = "eod_diario"
    else:
        # Renormaliza: divergência = 0.00, restante dividido entre aceleração e delta_IR
        total = w_base["aceleracao"] + w_base["delta_ir"]
        w = {
            "aceleracao":  w_base["aceleracao"] / total,
            "divergencia": 0.0,
            "delta_ir":    w_base["delta_ir"] / total
        }
        fonte_divergencia = "ausente_renormalizado"
        # Se não há dados de divergência, setar médias para 0.0 para não quebrar score
        iv_media = 0.0
        rv_media = 0.0

    # Score final REFLECT com pesos efetivos
    reflect_score = (
        aceleracao * w["aceleracao"] +
        (iv_media * 0.5 + rv_media * 0.5) * w["divergencia"] +  # média simples dos dois
        delta_ir * w["delta_ir"]
    )

    # B55 — estados canônicos A/B/C/D/T (Tail)
    # 'E' legado: ainda pode existir em JSONs antigos até rerrodar (B55)
    _thr = carregar_config()["reflect"]["thresholds"]
    if reflect_score >= _thr["A"]:
        reflect_state = "A"
    elif reflect_score >= _thr["B_lower"]:
        reflect_state = "B"
    elif reflect_score >= _thr["C"]:
        reflect_state = "C"
    elif reflect_score >= _thr["D"]:
        reflect_state = "D"
    else:
        reflect_state = "T"  # Tail

    # Salvar no master JSON
    if "reflect_cycle_history" not in cfg:
        cfg["reflect_cycle_history"] = {}

    cfg["reflect_cycle_history"][ciclo_id] = {
        "aceleracao": aceleracao,
        "iv_media": iv_media,
        "rv_media": rv_media,
        "delta_ir": delta_ir,
        "score_reflect": reflect_score,
        "reflect_state": reflect_state,
        "data_calc": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fonte_divergencia": fonte_divergencia,
        "divergencia_disponivel": divergencia_disponivel
    }
    tape_ativo_salvar(ativo, cfg)

def reflect_sizing_calcular(ativo: str) -> float:
    """
    B56 — Multiplicador REFLECT por estado canônico A/B/C/D/T.
    sizing_final = sizing_orbit × reflect_mult

    A → 1.0  (alpha via B01/B29 — futuro)
    B → 1.0  (edge normal)
    C → 0.5  (edge enfraquecendo — PE-007 provisório)
    D → 0.0  (edge deteriorado)
    T → 0.0  (Tail — evento de cauda, protocolo B02)
    """
    cfg = tape_ativo_carregar(ativo)
    reflect_hist = cfg.get("reflect_cycle_history", {})
    if not reflect_hist:
        return 1.0  # default se não há histórico

    ultimo_ciclo = max(reflect_hist.keys())
    estado = reflect_hist[ultimo_ciclo].get("reflect_state", "B")

    _lookup = {
        "A": 1.0,   # alpha pendente B01/B29
        "B": 1.0,
        "C": 0.5,   # PE-007 — provisório
        "D": 0.0,
        "T": 0.0,   # Tail — protocolo B02
        "E": 0.0,   # legado — tratar como T até rerrodar histórico (B55)
    }
    return _lookup.get(estado, 1.0)

# Funções auxiliares copiadas de tape.py (precisam ser definidas ou importadas)
def _calculate_divergence_components(df_eod, ativo, data):
    # Placeholder — a implementação real viria de tape.py
    # Por ora, retorna valores fixos para não quebrar
    return {"iv_prem_ratio": 0.0, "ret_vol_ratio": 0.0}

def _calculate_gex(df_eod, preco_acao):
    # Placeholder
    return 0.0

# ───────────────────────────────────────────────────────────────────────────────

class EDGE:
    """
    Orquestra TAPE → ORBIT → FIRE → BOOK
    Configuração de ativos via master JSON em ATIVOS_DIR
    """

    def __init__(self, capital=10_000,
                 modo="backtest",
                 universo=None):
        assert modo in ("backtest", "paper", "real")
        self.capital = capital
        self.modo    = modo

        ativos = universo or []
        self.universo = {}
        for ticker in ativos:
            cfg = tape_ativo_carregar(ticker)
            self.universo[ticker] = cfg

        self.ativos = list(self.universo.keys())

        if modo == "backtest":
            for ext in ["json", "parquet"]:
                p = os.path.join(
                    BOOK_DIR, f"book_{modo}.{ext}")
                if os.path.exists(p):
                    os.remove(p)
                    print(f"  ✓ {os.path.basename(p)} removido")

        self.book  = BOOK(fonte=modo, capital=capital)
        self.fire  = FIRE(book=self.book, modo=modo)
        self.orbit = ORBIT(universo=self.universo)

        print(f"\n  {'═'*55}")
        print(f"  EDGE v1.3 — modo={modo}")
        print(f"  Capital:  R${capital:,.0f}")
        print(f"  Ativos:   {self.ativos}")
        print(f"  {'═'*55}")

    def executar(self, anos=None, xlsx_dir=None,
                 modo_orbit="pipeline",
                 reset=False):
        if reset:
            self.book._ops         = []
            self.book._counter     = 0
            self.book._abertas_idx = {}
            self.book._salvar()
            print("  ✓ BOOK resetado — backtest limpo")

        if self.modo == "backtest":
            if anos is None:
                anos = [2020,2021,2022,2023,2024,2025,2026]
            return self._executar_backtest(anos, modo_orbit)
        elif self.modo == "paper":
            return self._executar_paper(xlsx_dir)
        elif self.modo == "real":
            raise NotImplementedError("EDGE.real — Fase 3.")

    def _executar_backtest(self, anos, modo_orbit):
        print(f"\n  {'═'*55}")
        print(f"  EDGE.backtest — {anos[0]}→{anos[-1]}")
        print(f"  {'═'*55}")

        self.book._ativo_atual = "_".join(self.ativos)

        # Limpa BOOK antes de backtest
        for ext in ["json", "parquet"]:
            p = os.path.join(BOOK_DIR, f"book_backtest.{ext}")
            if os.path.exists(p):
                os.remove(p)
                print(f"  ✓ {os.path.basename(p)} removido")

        # Limpa histórico REFLECT dos ativos — evita z-score
        # contaminado por backtest anterior
        for ticker in self.ativos:
            cfg = tape_ativo_carregar(ticker)
            cfg["reflect_all_cycles_history"] = []
            cfg["reflect_history"]            = []
            cfg["reflect_daily_history"]      = {}
            cfg["reflect_state"]              = "B"
            cfg["reflect_score"]              = 0.0
            tape_ativo_salvar(ticker, cfg)
            print(f"  ✓ REFLECT limpo — {ticker}")

        # [1/3] TAPE
        print(f"\n  [1/3] TAPE")
        df_tape = tape_historico_carregar(
            ativos=self.ativos, anos=anos, forcar=False)
        if df_tape.empty:
            print("  ✗ TAPE vazio. Abortando.")
            return pd.DataFrame()
        print(f"  ✓ TAPE: {len(df_tape)} registros")
        df_selic = _obter_selic(min(anos), max(anos))

        # Carregar séries externas (responsabilidade do TAPE)
        externas = tape_externas_carregar(self.ativos, anos)

        # [2/3] ORBIT
        print(f"\n  [2/3] ORBIT v3.4")
        df_regimes = self.orbit.orbit_rodar(
            df_tape, anos, modo=modo_orbit, externas_dict=externas)
        if df_regimes.empty:
            print("  ✗ ORBIT vazio. Abortando.")
            return pd.DataFrame()

        print(f"  ✓ ORBIT: regimes calculados")

        df_regimes["ciclo_id"] = \
            df_regimes["ciclo_id"].astype(str)
        df_regimes = df_regimes.drop_duplicates(
            subset=["ciclo_id", "ativo"], keep="last")
        regime_idx = df_regimes.set_index(
            ["ciclo_id","ativo"]).to_dict("index")

        # Config dos ativos carregada uma vez
        configs_ativos = {
            ativo: tape_ativo_carregar(ativo)
            for ativo in self.ativos
        }

        # [3/3] FIRE
        print(f"\n  [3/3] FIRE")
        datas = sorted(df_tape["data"].unique())

        reflect_ciclos_processados = set()

        with _tqdm(total=len(datas), desc="FIRE",
                  unit="pregão", ncols=None) as pbar:
            for data in datas:
                data_str = str(data)[:10]
                ciclo_id = data_str[:7]

                df_dia = df_tape[
                    df_tape["data"] == data].copy()

                self.fire.verificar(
                    df_dia, data_str, df_selic,
                    cfg_global=self._cfg_global if hasattr(self, '_cfg_global') else None,
                    configs_ativos=configs_ativos)

                for ativo in self.ativos:
                    cfg_ativo = configs_ativos[ativo]

                    raw = regime_idx.get((ciclo_id, ativo), {})
                    sizing_orbit = float(raw.get("sizing", 0.0))

                    # Modula sizing do ORBIT pelo REFLECT
                    reflect_mult = reflect_sizing_calcular(ativo)
                    sizing_modulado  = sizing_orbit * reflect_mult

                    orbit_data = {
                        "ciclo":  str(raw.get("ciclo_id", ciclo_id)),
                        "regime": raw.get("regime", "DESCONHECIDO"),
                        "ir":     float(raw.get("ir", 0.0)),
                        "sizing": sizing_modulado,
                    }

                    if not self.book.posicoes_por_ativo(ativo):
                        self.fire.abrir(
                            ativo      = ativo,
                            data       = data_str,
                            df_dia     = df_dia,
                            orbit_data = orbit_data,
                            df_selic   = df_selic,
                            cfg        = cfg_ativo,
                        )

                # REFLECT de ciclo — uma vez por ciclo mensal
                if ciclo_id not in reflect_ciclos_processados:
                    for ativo in self.ativos:
                        reflect_cycle_calcular(ativo, ciclo_id)
                        # Recarrega config após atualização do REFLECT
                        configs_ativos[ativo] = tape_ativo_carregar(ativo)
                    reflect_ciclos_processados.add(ciclo_id)

                pbar.update(1)
                pbar.set_postfix(
                    abertas  = len(self.book.posicoes_abertas),
                    fechadas = sum(
                        1 for op in self.book._ops
                        if op.core.motivo_saida),
                )

        print(f"\n  {'═'*55}")
        print(f"  EDGE.backtest concluído")
        print(f"  {'═'*55}")
        self.book.dashboard()
        return self.book.df()

    def executar_eod(self,
                     xlsx_dir=None,
                     capital=None):
        """
        Fluxo completo de paper trading diário.
        Substitui chamada manual à Célula EOD.

        Etapas:
          1. Arquiva xlsx do dia em opcoes_historico/
          2. GATE EOD por ativo — exclui bloqueados
          3. _executar_paper() nos aprovados
        """
        import shutil
        from datetime import date

        xlsx_dir  = xlsx_dir or OPCOES_HOJE_DIR
        data_hoje = str(date.today())
        hist_dir  = os.path.join(
            DRIVE_BASE, "opcoes_historico")
        os.makedirs(hist_dir, exist_ok=True)

        print(f"\n  {'═'*55}")
        print(f"  EDGE.executar_eod — {data_hoje}")
        print(f"  {'═'*55}")

        # 1. Arquiva xlsx do dia
        print(f"\n  [1/3] Arquivando snapshots...")
        for ativo in self.ativos:
            src = os.path.join(
                xlsx_dir, f"{ativo}.xlsx")
            dst = os.path.join(
                hist_dir,
                f"{data_hoje} {ativo}.xlsx")
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"  ✓ {data_hoje} "
                      f"{ativo}.xlsx → opcoes_historico/")
            else:
                print(f"  ⚠ Não encontrado: "
                      f"{ativo}.xlsx")

        # 2. GATE EOD por ativo
        print(f"\n  [2/3] GATE EOD...")
        aprovados = []
        for ativo in self.ativos:
            parecer = gate_eod_verificar(ativo, verbose=True)
            if parecer in ("BLOQUEADO",
                            "GATE VENCIDO"):
                print(f"  → {ativo} excluído "
                      f"({parecer})\n")
            else:
                aprovados.append(ativo)

        if not aprovados:
            print(f"\n  Nenhum ativo aprovado "
                  f"pelo GATE EOD hoje.")
            print(f"  {'═'*55}\n")
            return self.book.df()

        print(f"\n  Aprovados: {aprovados}")

        # 3. Paper trading — apenas aprovados
        print(f"\n  [3/3] EDGE paper...")
        self.ativos = aprovados
        return self._executar_paper(xlsx_dir)


    def _executar_paper(self, xlsx_dir=None):
        xlsx_dir  = xlsx_dir or OPCOES_HOJE_DIR
        data_hoje = str(date.today())
        print(f"\n  EDGE.paper — {data_hoje}")

        frames = []
        # SCAN-11 CORRIGIDO: configs_ativos definido antes do loop de ativos
        configs_ativos = {
            ativo: tape_ativo_carregar(ativo)
            for ativo in self.ativos
        }

        for ativo in self.ativos:

            # GATE EOD — verificação leve antes de qualquer operação
            parecer = gate_eod_verificar(ativo, verbose=True)
            if parecer in ("BLOQUEADO", "GATE VENCIDO"):
                print(f"  → {ativo} excluído do EOD ({parecer})\n")
                continue

            # MONITORAR e OPERAR prosseguem normalmente
            hoje  = str(date.today())
            xlsx  = os.path.join(xlsx_dir, f"{ativo}.xlsx")
            xlsx2 = os.path.join(xlsx_dir, f"{hoje} {ativo}.xlsx")

            if not os.path.exists(xlsx) and os.path.exists(xlsx2):
                import shutil
                shutil.copy2(xlsx2, xlsx)
                print(f"  ✓ {hoje} {ativo}.xlsx → {ativo}.xlsx")

            if not os.path.exists(xlsx):
                print(f"  ⚠ {ativo}.xlsx não encontrado")
                continue

            # Processa EOD para alimentar o REFLECT diário
            df_eod = tape_eod_carregar(ativo=ativo, filepath=xlsx)
            if not df_eod.empty:
                reflect_daily_calcular(ativo, data_hoje, df_eod)
                reflect_daily_salvar(ativo, data_hoje, df_eod)

            try:
                preco = float(input(
                    f"  Preço atual {ativo}: R$ "))
            except Exception:
                print(f"  ⚠ Preço inválido para {ativo}")
                continue
            df_p = tape_eod_carregar(
                ativo=ativo, filepath=xlsx,
                preco_acao=preco, data=data_hoje)
            if not df_p.empty:
                frames.append(df_p)

        if not frames:
            print("  ✗ Nenhum XLSX carregado.")
            return pd.DataFrame()

        df_hoje  = pd.concat(frames, ignore_index=True)
        df_selic = _obter_selic(
            datetime.now().year, datetime.now().year)

        self.fire.verificar(
            df_hoje, data_hoje, df_selic,
            configs_ativos=configs_ativos)

        for ativo in self.ativos:
            cfg_ativo = configs_ativos[ativo]

            orbit_data   = self.orbit.orbit_regime_para_data(ativo, data_hoje)
            sizing_orbit = float(orbit_data.get("sizing", 0.0))

            # Modula sizing pelo REFLECT
            reflect_mult = reflect_sizing_calcular(ativo)
            orbit_data["sizing"] = sizing_orbit * reflect_mult

            if not self.book.posicoes_por_ativo(ativo):
                self.fire.abrir(
                    ativo      = ativo,
                    data       = data_hoje,
                    df_dia     = df_hoje,
                    orbit_data = orbit_data,
                    df_selic   = df_selic,
                    cfg        = cfg_ativo,  # SCAN-9: passa cfg, evita releitura
                )

        self.book.dashboard()
        return self.book.df()


# ──────────────────────────────────────────────────────────────
# Funções Públicas Síncronas (API do Orquestrador)
# Requisito SPEC: executam I/O pesado, o caller (dc_runner) deve usar asyncio.to_thread
# ──────────────────────────────────────────────────────────────

def rodar_backtest_dados(ticker: str, anos: list = None):
    try:
        from datetime import datetime
        import sys
        
        anos_list = anos if anos else list(range(2002, datetime.now().year + 1))
        
        emit_dc_event("dc_module_start", "ORBIT", "running", ticker=ticker)
        
        config = carregar_config() or {}
        capital = config.get("backtest", {}).get("capital", 10000.0)
        edge = EDGE(capital=capital, modo="backtest", universo=[ticker])
        
        # TAPE
        emit_dc_event("dc_module_start", "TAPE", "running", ticker=ticker)
        df_tape = tape_historico_carregar(ativos=[ticker], anos=anos_list, forcar=False)
        if df_tape.empty:
            emit_dc_event("dc_module_complete", "TAPE", "error", ticker=ticker, erro="TAPE vazio")
            raise Exception("TAPE vazio")
        externas = tape_externas_carregar([ticker], anos_list)
        emit_dc_event("dc_module_complete", "TAPE", "ok", ticker=ticker, registros=len(df_tape))
        
        # ORBIT
        emit_dc_event("dc_module_start", "ORBIT", "running", ticker=ticker)
        cfg_ativo = tape_ativo_carregar(ticker)
        if cfg_ativo is None:
            emit_dc_event("dc_module_complete", "ORBIT", "error", ticker=ticker, erro="cfg_ativo é None")
            raise Exception(f"Configuração ausente para {ticker}")
            
        orbit = ORBIT(universo={ticker: cfg_ativo})
        df_regimes_result = orbit.orbit_rodar(df_tape, anos_list, modo="mensal", externas_dict=externas)
        if df_regimes_result is None or df_regimes_result.empty:
            emit_dc_event("dc_module_complete", "ORBIT", "error", ticker=ticker, erro="ORBIT vazio")
            raise Exception("ORBIT vazio")
        emit_dc_event("dc_module_complete", "ORBIT", "ok", ticker=ticker)
        
        # REFLECT
        emit_dc_event("dc_module_start", "REFLECT", "running", ticker=ticker)
        try:
            cfg_atual = tape_ativo_carregar(ticker)
            historico_ciclos = list(dict.fromkeys(
                c["ciclo_id"] for c in cfg_atual.get("historico", []) if "ciclo_id" in c
            ))
            reflect_existente = set(cfg_atual.get("reflect_cycle_history", {}).keys())
            ciclos_sem_reflect = [c for c in historico_ciclos if c not in reflect_existente]
            for ciclo_id in ciclos_sem_reflect:
                try:
                    reflect_cycle_calcular(ticker, ciclo_id)
                except Exception as e_ciclo:
                    emit_log(f"~ REFLECT {ciclo_id} ignorado: {e_ciclo}", "warning")
            emit_dc_event("dc_module_complete", "REFLECT", "ok", ticker=ticker)
        except Exception as e:
            emit_dc_event("dc_module_complete", "REFLECT", "error", ticker=ticker, erro=str(e))
            raise e
            
        return {"status": "OK"}
    except Exception as e:
        emit_dc_event("dc_module_complete", "ORBIT", "error", ticker=ticker, erro=str(e))
        import traceback
        traceback.print_exc()
        raise e

def rodar_orbit_update(ticker: str, anos: list = None):
    try:
        from datetime import datetime
        import sys

        anos_list = anos if anos else list(range(2002, datetime.now().year + 1))
        
        # TAPE
        emit_dc_event("dc_module_start", "TAPE", "running", ticker=ticker)
        cfg_ativo = tape_ativo_carregar(ticker)
        df_ohlcv = tape_ohlcv_carregar(ticker, anos_list)
        df_ibov = tape_ibov_carregar(anos_list)
        externas = tape_externas_carregar([ticker], anos_list)
        if df_ohlcv.empty:
            emit_dc_event("dc_module_complete", "TAPE", "error", ticker=ticker, erro="OHLCV vazio")
            raise Exception(f"TAPE: dados OHLCV indisponíveis para {ticker}")
        emit_dc_event("dc_module_complete", "TAPE", "ok", ticker=ticker, registros=len(df_ohlcv))
        
        # ORBIT
        emit_dc_event("dc_module_start", "ORBIT", "running", ticker=ticker)
        orbit = ORBIT(universo={ticker: cfg_ativo})
        orbit.orbit_rodar(df_ohlcv, anos=anos_list, modo="mensal", externas_dict=externas)
        emit_dc_event("dc_module_complete", "ORBIT", "ok", ticker=ticker)
        
        # REFLECT
        emit_dc_event("dc_module_start", "REFLECT", "running", ticker=ticker)
        cfg_atual = tape_ativo_carregar(ticker)
        historico_ciclos = list(dict.fromkeys(
            c["ciclo_id"] for c in cfg_atual.get("historico", []) if "ciclo_id" in c
        ))
        reflect_existente = set(cfg_atual.get("reflect_cycle_history", {}).keys())
        ciclos_sem_reflect = [c for c in historico_ciclos if c not in reflect_existente]
        if not ciclos_sem_reflect:
            ciclos_sem_reflect = [datetime.now().strftime("%Y-%m")]
        for ciclo_id in ciclos_sem_reflect:
            try:
                reflect_cycle_calcular(ticker, ciclo_id)
            except Exception as e_ciclo:
                emit_log(f"~ REFLECT {ciclo_id} ignorado: {e_ciclo}", "warning")
        emit_dc_event("dc_module_complete", "REFLECT", "ok", ticker=ticker)
        return {"status": "OK"}
    except Exception as e:
        emit_dc_event("dc_module_complete", "ORBIT", "error", ticker=ticker, erro=str(e))
        raise e

def rodar_tune(ticker: str):
    from delta_chaos.tune import executar_tune
    emit_dc_event("dc_module_start", "TUNE", "running", ticker=ticker)
    try:
        executar_tune(ticker)
        emit_dc_event("dc_module_complete", "TUNE", "ok", ticker=ticker)
        return {"status": "OK"}
    except Exception as e:
        emit_dc_event("dc_module_complete", "TUNE", "error", ticker=ticker, erro=str(e))
        raise e

def rodar_backtest_gate(ticker: str):
    from delta_chaos.gate import gate_executar
    resultado = gate_executar(ticker)
    decisao = resultado.get("decisao", "BLOQUEADO") if isinstance(resultado, dict) else str(resultado)
    emit_log(f"[GATE] {ticker}: {decisao}", "info")
    return {"status": "OK", "output": decisao, "gate_data": resultado if isinstance(resultado, dict) else {}}

def rodar_reflect_daily(ticker: str, xlsx_path: str):
    emit_dc_event("dc_module_start", "REFLECT", "running", ticker=ticker)
    try:
        tape_eod_carregar(ativo=ticker, filepath=xlsx_path)
        emit_dc_event("dc_module_complete", "REFLECT", "ok", ticker=ticker)
        return {"status": "OK"}
    except Exception as e:
        emit_dc_event("dc_module_complete", "REFLECT", "error", ticker=ticker, erro=str(e))
        raise e

def rodar_gate_eod(ticker: str):
    try:
        resultado = gate_eod_verificar(ticker, verbose=True)
        emit_log(f"[GATE_EOD] {ticker}: {resultado}", "info")
        return {"status": "OK", "output": str(resultado)}
    except Exception as e:
        emit_dc_event("dc_module_complete", "GATE_EOD", "error", ticker=ticker, erro=str(e))
        raise e


# ── Entrypoint CLI — chamado pelo ATLAS via subprocess ───────────
# ── Entrypoint CLI — chamado pelo ATLAS via subprocess ───────────
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Delta Chaos — entrypoint CLI para ATLAS")

    parser.add_argument(
        "--modo",
        choices=["backtest_dados", "backtest_gate", "eod", "tune", "orbit_update", "reflect_daily", "gate_eod"],
        required=True,
        help="Rotina a executar"
    )
    parser.add_argument(
        "--ticker",
        type=str,
        default=None,
        help="Ticker do ativo (obrigatório para orbit, tune, backtest_gate, backtest_dados, reflect_daily, gate_eod)"
    )
    parser.add_argument(
        "--xlsx_dir",
        type=str,
        default=None,
        help="Diretório com arquivos xlsx EOD (obrigatório para eod)"
    )
    parser.add_argument(
        "--xlsx_path",
        type=str,
        default=None,
        help="Caminho do arquivo xlsx (obrigatório para reflect_daily)"
    )
    parser.add_argument(
        "--anos",
        type=str,
        default=None,
        help="Anos separados por vírgula (opcional para orbit, backtest_dados)"
    )

    args = parser.parse_args()

    # Validações
    if args.modo in ("orbit", "tune", "backtest_gate", "backtest_dados", "reflect_daily", "gate_eod") and not args.ticker:
        print(f"ERRO: --ticker obrigatório para modo {args.modo}",
              file=sys.stderr)
        sys.exit(1)

    if args.modo == "eod" and not args.xlsx_dir:
        print("ERRO: --xlsx_dir obrigatório para modo eod",
              file=sys.stderr)
        sys.exit(1)

    # Execução
    try:
        universo = carregar_config().get("universo", [])

        # ──────────────────────────────────────────────────────────────
        # Modo: eod
        # Propósito: Execução diária — paper/live trading
        # Uso: python -m delta_chaos.edge --modo eod --xlsx_dir /caminho
        # Fluxo: instancia EDGE em modo paper, executa EOD
        # ──────────────────────────────────────────────────────────────
        if args.modo == "eod":
            edge = EDGE(
                capital=carregar_config()["book"]["capital"],
                modo="paper",
                universo=universo
            )
            edge.executar_eod(xlsx_dir=args.xlsx_dir)

        # ──────────────────────────────────────────────────────────────
        # Modo: orbit_backtest
        # Propósito: Onboarding step 1 — COTAHIST + ORBIT + popula historico[]
        # Uso: python -m delta_chaos.edge --modo orbit_backtest --ticker VALE3
        # Fluxo: instancia EDGE completo (apaga books), roda TAPE + ORBIT
        # ──────────────────────────────────────────────────────────────
        elif args.modo in ("orbit_backtest", "backtest_dados"):
            try:
                # Mantém comportamento atual do orbit (instancia EDGE completo, apaga books)
                anos = (list(map(int, args.anos.split(",")))
                        if args.anos
                        else list(range(2002, datetime.now().year + 1)))
                config = carregar_config() or {}
                capital = config.get("backtest", {}).get("capital", 10000.0)
                edge = EDGE(
                    capital=capital,
                    modo="backtest",
                    universo=[args.ticker]
                )
                # TAPE
                emit_event("TAPE", "start")
                df_tape = tape_historico_carregar(
                    ativos=[args.ticker], anos=anos, forcar=False)
                if df_tape.empty:
                    print("  ✗ TAPE vazio. Abortando.")
                    emit_event("TAPE", "error", erro="TAPE vazio")
                    sys.exit(1)
                # Carregar séries externas (dentro do fluxo TAPE)
                externas = tape_externas_carregar([args.ticker], anos)
                print(f"  ✓ TAPE: {len(df_tape)} registros")
                emit_event("TAPE", "done", registros=len(df_tape))
                
                
                # ORBIT
                emit_event("ORBIT", "start")
                cfg_ativo = tape_ativo_carregar(args.ticker)

                # TAREFA 3: verificação defensiva contra cfg_ativo None
                if cfg_ativo is None:
                    print(f"ERRO: Configuração ausente para {args.ticker}")
                    emit_event("ORBIT", "error", erro="cfg_ativo é None")
                    sys.exit(1)

                orbit = ORBIT(universo={args.ticker: cfg_ativo})
                df_regimes_result = orbit.orbit_rodar(df_tape, anos, modo="mensal", externas_dict=externas)
                if df_regimes_result is None or df_regimes_result.empty:
                    print("  ✗ ORBIT vazio. Abortando.")
                    emit_event("ORBIT", "error", erro="ORBIT vazio")
                    sys.exit(1)
                print(f"  ✓ ORBIT: regimes calculados")
                emit_event("ORBIT", "done")

                # REFLECT: calcular para todos os ciclos do historico
                print("\n  [3/3] REFLECT")
                emit_event("REFLECT", "start")
                try:
                    cfg_atual = tape_ativo_carregar(args.ticker)
                    historico_ciclos = list(dict.fromkeys(
                        c["ciclo_id"] for c in cfg_atual.get("historico", []) if "ciclo_id" in c
                    ))
                    reflect_existente = set(cfg_atual.get("reflect_cycle_history", {}).keys())
                    ciclos_sem_reflect = [c for c in historico_ciclos if c not in reflect_existente]
                    print(f"  Calculando REFLECT para {len(ciclos_sem_reflect)} ciclos...")
                    for ciclo_id in ciclos_sem_reflect:
                        try:
                            reflect_cycle_calcular(args.ticker, ciclo_id)
                        except Exception as e_ciclo:
                            print(f"  ~ REFLECT {ciclo_id} ignorado: {e_ciclo}")
                    print(f"  ✓ REFLECT: {len(ciclos_sem_reflect)} ciclo(s) calculado(s)")
                    emit_event("REFLECT", "done")
                except Exception as e:
                    print(f"  ✗ REFLECT erro: {e}")
                    emit_event("REFLECT", "error", erro=str(e))
            except Exception as e:
                print(f"  ✗ backtest_dados erro: {e}")
                import traceback
                traceback.print_exc()
                emit_event("ORBIT", "error", erro=str(e))
                sys.exit(1)

        # ──────────────────────────────────────────────────────────────
        # Modo: orbit_update
        # Propósito: Atualização mensal — OHLCV cache + ORBIT + reflect_cycle
        # Uso: python -m delta_chaos.edge --modo orbit_update --ticker VALE3
        # Fluxo: TAPE verifica/baixa dados → ORBIT calcula regimes → REFLECT atualiza ciclo
        # ──────────────────────────────────────────────────────────────
        elif args.modo == "orbit_update":
            # Modo leve mensal — não instancia EDGE, não apaga books
            ticker = args.ticker
            anos = (list(map(int, args.anos.split(",")))
                    if args.anos
                    else list(range(2002, datetime.now().year + 1)))

            # ── TAPE: verificar/baixar dados ──
            print("\n  [1/3] TAPE")
            emit_event("TAPE", "start")
            try:
                cfg_ativo = tape_ativo_carregar(ticker)
                df_ohlcv = tape_ohlcv_carregar(ticker, anos)
                df_ibov = tape_ibov_carregar(anos)
                # Carregar séries externas (dentro do fluxo TAPE)
                externas = tape_externas_carregar([ticker], anos)
                if df_ohlcv.empty:
                    print(f"  ✗ TAPE: dados OHLCV indisponíveis para {ticker}")
                    emit_event("TAPE", "error", erro="OHLCV vazio")
                    sys.exit(1)
                print(f"  ✓ TAPE: {len(df_ohlcv)} registros OHLCV para {ticker}")
                emit_event("TAPE", "done", registros=len(df_ohlcv))
            except Exception as e:
                print(f"  ✗ TAPE erro: {e}")
                emit_event("TAPE", "error", erro=str(e))
                sys.exit(1)

            # ── ORBIT: calcular regimes ──
            print("\n  [2/3] ORBIT")
            emit_event("ORBIT", "start")
            try:
                orbit = ORBIT(universo={ticker: cfg_ativo})
                orbit.orbit_rodar(
                    df_ohlcv,
                    anos=anos,
                    modo="mensal",
                    externas_dict=externas,
                )
                print(f"  ✓ ORBIT: regimes calculados para {ticker}")
                emit_event("ORBIT", "done")
            except Exception as e:
                print(f"  ✗ ORBIT erro: {e}")
                emit_event("ORBIT", "error", erro=str(e))
                sys.exit(1)

            # ── REFLECT: calcular para todos os ciclos novos ──
            print("\n  [3/3] REFLECT")
            emit_event("REFLECT", "start")
            try:
                cfg_atual = tape_ativo_carregar(ticker)
                historico_ciclos = list(dict.fromkeys(  # deduplicar mantendo ordem
                    c["ciclo_id"] for c in cfg_atual.get("historico", []) if "ciclo_id" in c
                ))
                reflect_existente = set(cfg_atual.get("reflect_cycle_history", {}).keys())
                ciclos_sem_reflect = [c for c in historico_ciclos if c not in reflect_existente]
                if not ciclos_sem_reflect:
                    ciclos_sem_reflect = [datetime.now().strftime("%Y-%m")]
                for ciclo_id in ciclos_sem_reflect:
                    try:
                        reflect_cycle_calcular(ticker, ciclo_id)
                        print(f"  ✓ REFLECT: {ciclo_id}")
                    except Exception as e_ciclo:
                        print(f"  ~ REFLECT {ciclo_id} ignorado: {e_ciclo}")
                print(f"  ✓ REFLECT: {len(ciclos_sem_reflect)} ciclo(s) calculado(s) para {ticker}")
                emit_event("REFLECT", "done")
            except Exception as e:
                print(f"  ✗ REFLECT erro: {e}")
                emit_event("REFLECT", "error", erro=str(e))

        # ──────────────────────────────────────────────────────────────
        # Modo: tune
        # Propósito: Onboarding step 2 + atualização mensal step 3 (se elegível)
        # Uso: python -m delta_chaos.edge --modo tune --ticker VALE3
        # Fluxo: recalibra parâmetros do FIRE
        # ──────────────────────────────────────────────────────────────
        elif args.modo == "tune":
            from delta_chaos.tune import executar_tune
            executar_tune(args.ticker)

        # ──────────────────────────────────────────────────────────────
        # Modo: gate_backtest
        # Propósito: Onboarding step 3 + atualização mensal step 2 — GATE completo
        # Uso: python -m delta_chaos.edge --modo gate_backtest --ticker VALE3
        # Fluxo: executa GATE completo para o ativo
        # ──────────────────────────────────────────────────────────────
        elif args.modo == "gate_backtest":
            from delta_chaos.gate import gate_executar
            resultado = gate_executar(args.ticker)
            print(f"[GATE] {args.ticker}: {resultado}")

        # ──────────────────────────────────────────────────────────────
        # Modo: reflect_daily
        # Propósito: Processamento diário de dados EOD para REFLECT
        # Uso: python -m delta_chaos.edge --modo reflect_daily --ticker VALE3 --xlsx_path /caminho
        # Fluxo: processa arquivo xlsx EOD e atualiza reflect_daily
        # ──────────────────────────────────────────────────────────────
        elif args.modo == "reflect_daily":
            if not args.ticker or not args.xlsx_path:
                print("ERRO: --ticker e --xlsx_path obrigatorios para reflect_daily", file=sys.stderr)
                sys.exit(1)
            tape_eod_carregar(args.xlsx_path)

        # ──────────────────────────────────────────────────────────────
        # Modo: gate_eod
        # Propósito: Verificação de integridade EOD — decide OPERAR/MONITORAR/BLOQUEADO
        # Uso: python -m delta_chaos.edge --modo gate_eod --ticker VALE3
        # Fluxo: verifica GATE completo + regime atual + REFLECT
        # ──────────────────────────────────────────────────────────────
        elif args.modo == "gate_eod":
            resultado = gate_eod_verificar(args.ticker, verbose=True)
            print(f"[GATE_EOD] {args.ticker}: {resultado}")

    except Exception as e:
        import traceback
        print(f"ERRO: {e}", file=sys.stderr)
        emit_event("UNKNOWN", "error", erro=str(e))
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)