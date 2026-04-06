# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# DELTA CHAOS â€” FIRE v2.0
# AlteraÃ§Ãµes em relaÃ§Ã£o Ã  v1.2:
# MIGRADO (P2): imports explÃ­citos de init, tape, book â€” sem escopo global
# MIGRADO (P5): prints de inicializaÃ§Ã£o sob if __name__ == "__main__"
# MANTIDO: filtros, seletores, gatilhos TP/STOP, contrato com REFLECT
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

from delta_chaos.init import carregar_config, ATIVOS_DIR
from .tape import tape_carregar_ativo
from .book import (
    BOOK, Operacao, Core, Context,
    OrbitData, Leg, SCHEMA_VERSION,
)
import pandas as pd

# â”€â”€ Logging ATLAS (graceful fallback) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    from atlas_backend.core.terminal_stream import emit_log, emit_error
    _atlas_disponivel = True
except ImportError:
    def emit_log(msg, level="info"): print(f"[{level.upper()}] {msg}")
    def emit_error(e): print(f"[ERROR] {e}")
    _atlas_disponivel = False

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# DELTA CHAOS â€” FIRE v1.2
# AlteraÃ§Ãµes em relaÃ§Ã£o Ã  v1.1:
# ADICIONADO: verificaÃ§Ã£o reflect_permanent_block_flag em abrir()
# MANTIDO: sizing chega ao FIRE jÃ¡ modulado pelo REFLECT via EDGE
#          O FIRE nÃ£o conhece o REFLECT â€” apenas recebe sizing final
# MANTIDO: todos os filtros, seletores, gatilhos e verificar()
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

# â”€â”€ ParÃ¢metros via config global â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_cfg_fire = carregar_config()["fire"]

REGIMES_SIZING_PADRAO = _cfg_fire["regimes_sizing_padrao"]
TAKE_PROFIT      = _cfg_fire["take_profit"]
STOP_LOSS        = _cfg_fire["stop_loss"]
ROLL_DIAS        = _cfg_fire["roll_dias"]
IV_MINIMO        = _cfg_fire["iv_minimo"]
IV_RANK_MIN      = _cfg_fire["iv_rank_min"]
SELIC_MAX        = _cfg_fire["selic_max"]
SELIC_RED        = _cfg_fire["selic_red"]
PREMIO_MINIMO    = _cfg_fire["premio_minimo"]
VOL_FIN_MIN      = _cfg_fire.get("volume_financeiro_minimo", 10000)
COOLING_OFF_DIAS = _cfg_fire["cooling_off_dias"]
DIAS_MIN         = _cfg_fire["dias_min"]
DIAS_MAX         = _cfg_fire["dias_max"]

DELTA_ALVO = carregar_config()["fire"]["delta_alvo"]

REGIME_ESTRATEGIA = {
    "ALTA":              "CSP",
    "NEUTRO":            "BULL_PUT_SPREAD",
    "NEUTRO_BULL":       "BULL_PUT_SPREAD",
    "NEUTRO_BEAR":       "BEAR_CALL_SPREAD",
    "NEUTRO_LATERAL":    None,
    "NEUTRO_MORTO":      None,
    "NEUTRO_TRANSICAO":  None,
    "BAIXA":             None,
    "RECUPERACAO":       None,
    "PANICO":            None,
}

DIAS_MIN = 15
DIAS_MAX = 30

class FIRE:
    def __init__(self, book, modo="paper"):
        assert modo in ("backtest", "paper", "real")
        self.book = book
        self.modo = modo
        # S4 â€” cache do config global â€” uma leitura por sessÃ£o
        self._cfg_global = carregar_config()
        print(f"  FIRE v1.2 ({modo})")

    # â”€â”€ Filtros â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _filtrar(self, candidatas, df_selic, data):
        sizing = 1.0
        motivo = None
        if "iv" in candidatas.columns:
            candidatas = candidatas[
                candidatas["iv"].notna() &
                (candidatas["iv"] >= IV_MINIMO)]
            if candidatas.empty:
                return candidatas, sizing, "filtro_iv_minimo"
        if "iv_rank" in candidatas.columns:
            validas = candidatas[candidatas["iv_rank"].notna()]
            if len(validas) >= 10:
                if validas["iv_rank"].mean() < IV_RANK_MIN:
                    return pd.DataFrame(), sizing, "filtro_iv_rank"
        if df_selic is not None and len(df_selic) > 0:
            ts     = pd.Timestamp(data)
            ts_63d = ts - pd.Timedelta(days=90)
            sh = df_selic[pd.to_datetime(df_selic["data"]) <= ts]
            s6 = df_selic[pd.to_datetime(df_selic["data"]) <= ts_63d]
            if len(sh) > 0 and len(s6) > 0:
                if (float(sh["selic_aa"].iloc[-1]) -
                        float(s6["selic_aa"].iloc[-1])) > SELIC_MAX:
                    sizing = SELIC_RED
                    motivo = "selic_regime_adverso"
        return candidatas, sizing, motivo

    # â”€â”€ Seletores â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    # S6 â€” espelho intencional de TUNE._melhor_opcao()
    # Mantidas separadas por diferenÃ§a de contexto:
    # FIRE usa iv_rank, TUNE nÃ£o usa.
    # Se TUNE._melhor_opcao() for alterada, atualizar aqui tambÃ©m.
    def _melhor(self, df, tipo, delta_alvo):
        cands = df[
            (df["tipo"] == tipo) &
            (df["delta"].notna()) &
            (df["T"] * 252 >= DIAS_MIN) &
            (df["T"] * 252 <= DIAS_MAX) &
            (df["volume"] > 0)
        ].copy()
        if cands.empty: return None
        cands["dist"] = (
            cands["delta"] - delta_alvo).abs()
        return cands.nsmallest(1, "dist").iloc[0]

    def _leg(self, row, posicao):
        return Leg(
            tipo           = row["tipo"],
            posicao        = posicao,
            ticker         = str(row.get("ticker","")),
            strike         = float(row["strike"]),
            vencimento     = str(row["vencimento"])[:10],
            premio_entrada = float(row["fechamento"]),
            delta   = float(row["delta"])
                      if pd.notna(row.get("delta")) else None,
            gamma   = float(row["gamma"])
                      if pd.notna(row.get("gamma")) else None,
            theta   = float(row["theta"])
                      if pd.notna(row.get("theta")) else None,
            vega    = float(row["vega"])
                      if pd.notna(row.get("vega")) else None,
            iv      = float(row["iv"])
                      if pd.notna(row.get("iv")) else None,
            iv_rank = float(row["iv_rank"])
                      if pd.notna(row.get("iv_rank")) else None,
        )

    def _montar_csp(self, df):
        r = self._melhor(df, "PUT",
                         DELTA_ALVO["CSP"]["put_vendida"])
        return [self._leg(r, "vendida")] if r is not None else []

    def _montar_bull_put(self, df):
        v = self._melhor(df, "PUT",
                         DELTA_ALVO["BULL_PUT_SPREAD"]["put_vendida"])
        if v is None: return []
        df_rem = df[df["ticker"] != v["ticker"]]
        c = self._melhor(df_rem, "PUT",
                         DELTA_ALVO["BULL_PUT_SPREAD"]["put_comprada"])
        if c is None: return []
        if float(v["strike"]) <= float(c["strike"]): return []
        premio_liq = float(v["fechamento"]) - float(c["fechamento"])
        if premio_liq <= 0.05: return []
        return [self._leg(v, "vendida"), self._leg(c, "comprada")]

    def _montar_bear_call(self, df):
        v = self._melhor(df, "CALL",
                         DELTA_ALVO["BEAR_CALL_SPREAD"]["call_vendida"])
        if v is None: return []
        df_rem = df[df["ticker"] != v["ticker"]]
        c = self._melhor(df_rem, "CALL",
                         DELTA_ALVO["BEAR_CALL_SPREAD"]["call_comprada"])
        if c is None: return []

        # ValidaÃ§Ã£o correta: strike vendida deve ser MENOR que comprada
        if float(v["strike"]) > float(c["strike"]):
            return []
        premio_liq = float(v["fechamento"]) - float(c["fechamento"])
        if premio_liq <= 0.05: return []
        return [self._leg(v, "vendida"), self._leg(c, "comprada")]

    # â”€â”€ Abrir posiÃ§Ã£o â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def abrir(self, ativo, data, df_dia,
              orbit_data, df_selic=None, cfg=None):
        regime       = orbit_data.get("regime", "DESCONHECIDO")
        ciclo        = orbit_data.get("ciclo", "")
        # sizing jÃ¡ chega modulado pelo REFLECT via EDGE
        sizing_orbit = orbit_data.get("sizing", 0.0)

        if cfg is None:
            cfg = tape_carregar_ativo(ativo)

        regimes_sizing = cfg.get(
            "regimes_sizing", REGIMES_SIZING_PADRAO)
        
        sizing_config = float(
            regimes_sizing.get(regime, 0.0))

        # â”€â”€ TP e STOP â€” S4: recebe cfg_global cacheado â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        _cfg_f = self._cfg_global["fire"]
        _tp    = float(cfg.get("take_profit")
                       or _cfg_f["take_profit"])
        _stop  = float(cfg.get("stop_loss")
                       or _cfg_f["stop_loss"])

        # sizing_orbit jÃ¡ carrega o fator REFLECT aplicado pelo EDGE
        sizing_final = sizing_orbit

        _regime_estrategia_global = carregar_config()["fire"]["regime_estrategia"]
        estrategia = (
            (cfg.get("estrategias") or {}).get(regime)
            or _regime_estrategia_global.get(regime)
        )

        if estrategia is None:
            self.book.registrar_nao_entrada(
                ativo, data,
                "estrategia_nao_configurada",
                regime, ciclo)
            return None

        if sizing_final <= 0.0:
            self.book.registrar_nao_entrada(
                ativo, data,
                "regime_bloqueado"
                if sizing_config == 0.0
                else "sizing_orbit_reflect_zero",
                regime, ciclo)
            return None

        if not self.book.pode_abrir():
            self.book.registrar_nao_entrada(
                ativo, data,
                "risco_total_excedido",
                regime, ciclo)
            return None

        if self.book.posicoes_por_ativo(ativo):
            return None

        # Cooling off

        # Q8 â€” timezone consistente
        data_ts = pd.Timestamp(data).tz_localize(None)
        for op in reversed(self.book._ops):
            if (op.core.ativo == ativo and
                    op.core.motivo_saida == "STOP" and
                    op.core.data_saida):
                data_stop = pd.Timestamp(op.core.data_saida)
                if (data_ts - data_stop).days < COOLING_OFF_DIAS:
                    self.book.registrar_nao_entrada(
                        ativo, data, "cooling_off",
                        regime, ciclo)
                    return None
                else:
                    break

        df_ativo          = df_dia[
            df_dia["ativo_base"] == ativo].copy()
        df_f, sf3, motivo = self._filtrar(
            df_ativo, df_selic, data)

        if df_f.empty and motivo in (
                "filtro_iv_minimo","filtro_iv_rank"):
            self.book.registrar_nao_entrada(
                ativo, data, motivo, regime, ciclo)
            return None

        df_op = df_f if not df_f.empty else df_ativo
        legs  = {
            "CSP":             self._montar_csp,
            "BULL_PUT_SPREAD": self._montar_bull_put,
            "BEAR_CALL_SPREAD": self._montar_bear_call,
        }.get(estrategia, lambda df: [])(df_op)

        if not legs:
            self.book.registrar_nao_entrada(
                ativo, data,
                "sem_opcao_adequada", regime, ciclo)
            return None

        premio_liq = sum(
            leg.premio_entrada if leg.posicao == "vendida"
            else -leg.premio_entrada
            for leg in legs)

        if premio_liq < PREMIO_MINIMO:
            self.book.registrar_nao_entrada(
                ativo, data,
                "premio_insuficiente", regime, ciclo)
            return None

        acao = df_dia[
            (df_dia["ativo_base"] == ativo) &
            (df_dia["tipo"] == "ACAO")]["fechamento"]
        preco_acao = float(acao.iloc[0]) if not acao.empty else 0.0

        selic_hoje = 13.5
        if df_selic is not None and len(df_selic) > 0:
            s = df_selic[
                pd.to_datetime(df_selic["data"]) <=
                pd.Timestamp(data)]
            if len(s) > 0:
                selic_hoje = float(s["selic_aa"].iloc[-1])

        n = self.book.calcular_contratos(
            premio_liq, sizing_final, sf3)

        op = Operacao(
            op_id="", schema_version=SCHEMA_VERSION,
            core    = Core(
                ativo        = ativo,
                estrategia   = estrategia,
                data_entrada = data,
                fonte        = self.modo,
                n_contratos  = n),
            context = Context(
                preco_acao_entrada = preco_acao,
                selic_entrada      = selic_hoje,
                sizing_filtro3     = sf3),
            orbit   = OrbitData(
                ciclo          = ciclo,
                regime_entrada = regime,
                ir_orbit       = orbit_data.get("ir", 0.0),
                sizing_orbit   = sizing_final),
            legs=legs,
        )
        return self._executar(op)

    # â”€â”€ Executar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _executar(self, op):
        if self.modo == "backtest":
            return self.book.registrar(op)
        elif self.modo == "paper":
            print(f"  [PAPER] {op.core.ativo} "
                  f"{op.core.estrategia} "
                  f"n={op.core.n_contratos}")
            for leg in op.legs:
                print(f"    {leg.posicao:8} {leg.tipo:4} "
                      f"K={leg.strike:.2f} "
                      f"Î´={leg.delta} "
                      f"prÃªmio={leg.premio_entrada:.4f}")
            return self.book.registrar(op)
        else:
            raise NotImplementedError("FIRE.real: Fase 3.")

    # â”€â”€ Verificar gatilhos â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def verificar(self, df_dia, data, df_selic=None,
                  cfg_global=None, configs_ativos=None):
        acoes   = []
        # Q8 â€” timezone consistente
        data_ts = pd.Timestamp(data).tz_localize(None)

        # S4 â€” cache em memÃ³ria, nÃ£o relÃª disco a cada pregÃ£o
        if cfg_global is None:
            cfg_global = carregar_config()
        _cfg_fire    = cfg_global["fire"]
        _tp_global   = _cfg_fire["take_profit"]
        _stop_global = _cfg_fire["stop_loss"]

        for op in self.book.posicoes_abertas:
            ativo = op.core.ativo
            if not op.legs: continue

            # Q8 â€” timezone consistente
            venc      = pd.Timestamp(
                op.legs[0].vencimento).tz_localize(None)
            dias_rest = (venc - data_ts).days

            if dias_rest <= 0:
                preco_acao = self._preco_acao(df_dia, ativo)
                strike     = op.legs[0].strike
                if preco_acao <= 0: preco_acao = strike

                precos_exerc = []
                for leg in op.legs:
                    if leg.tipo=="PUT" and leg.posicao=="vendida":
                        precos_exerc.append(
                            max(0, leg.strike - preco_acao))
                    elif leg.tipo=="PUT" and leg.posicao=="comprada":
                        precos_exerc.append(
                            max(0, leg.strike - preco_acao))
                    elif leg.tipo=="CALL" and leg.posicao=="vendida":
                        precos_exerc.append(
                            max(0, preco_acao - leg.strike))
                    elif leg.tipo=="CALL" and leg.posicao=="comprada":
                        precos_exerc.append(
                            max(0, preco_acao - leg.strike))
                    else:
                        precos_exerc.append(0.0)

                self.book.fechar(
                    op.op_id, data,
                    precos_exerc, "VENCIMENTO", preco_acao)
                acoes.append({"op_id": op.op_id, "ativo": ativo,
                               "acao": "VENCIMENTO"})
                continue

            precos_hoje     = []
            algum_encontrado = False
            for leg in op.legs:
                ph = df_dia[
                    (df_dia["ativo_base"] == ativo) &
                    (df_dia["ticker"] == leg.ticker)
                ]["fechamento"]
                if not ph.empty:
                    precos_hoje.append(float(ph.iloc[0]))
                    algum_encontrado = True
                else:
                    precos_hoje.append(leg.premio_entrada)

            if not algum_encontrado: continue

            pnl_atual = sum(
                (leg.premio_entrada - p) if leg.posicao == "vendida"
                else (p - leg.premio_entrada)
                for leg, p in zip(op.legs, precos_hoje))

            premio_liq = sum(
                leg.premio_entrada if leg.posicao == "vendida"
                else -leg.premio_entrada
                for leg in op.legs)
            premio_ref = max(premio_liq, 0.01)
            pnl_pct    = pnl_atual / premio_ref

            # S5 â€” usa configs_ativos cacheado se disponÃ­vel
            cfg_ativo = (configs_ativos or {}).get(ativo) \
                        or tape_carregar_ativo(ativo)
            _tp   = float(cfg_ativo.get("take_profit")
                          or _tp_global)
            _stop = float(cfg_ativo.get("stop_loss")
                          or _stop_global)

            if pnl_pct >= _tp:
                self.book.fechar(
                    op.op_id, data,
                    precos_hoje, "TP",
                    self._preco_acao(df_dia, ativo))
                acoes.append({"op_id": op.op_id, "ativo": ativo,
                               "acao": "TP", "pnl_pct": pnl_pct})
                continue

            if pnl_pct <= -_stop:
                self.book.fechar(
                    op.op_id, data,
                    precos_hoje, "STOP",
                    self._preco_acao(df_dia, ativo))
                acoes.append({"op_id": op.op_id, "ativo": ativo,
                               "acao": "STOP", "pnl_pct": pnl_pct})
                continue

            if dias_rest <= ROLL_DIAS:
                acoes.append({"op_id": op.op_id, "ativo": ativo,
                               "acao": "ROLAR", "dias_rest": dias_rest})

        return acoes

    def _preco_acao(self, df_dia, ativo):
        s = df_dia[
            (df_dia["ativo_base"] == ativo) &
            (df_dia["tipo"] == "ACAO")]["fechamento"]
        return float(s.iloc[0]) if not s.empty else 0.0

if __name__ == "__main__":
    print("FIRE v1.2 - .abrir() | .verificar()")
    print("  Sizing recebido ja modulado pelo REFLECT via EDGE")
