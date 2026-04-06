# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
import json
import os
# DELTA CHAOS â€” BOOK v2.0
# AlteraÃ§Ãµes em relaÃ§Ã£o Ã  v1.2:
# MIGRADO (P2): imports explÃ­citos de init e tape â€” sem escopo global
# MIGRADO (P5): prints de inicializaÃ§Ã£o sob if __name__ == "__main__"
# MANTIDO: dataclasses, mÃ©tricas, persistÃªncia atÃ´mica, dashboard REFLECT
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

from .init import carregar_config, BOOK_DIR
from delta_chaos.tape import tape_carregar_ativo

# â”€â”€ Logging ATLAS (graceful fallback) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    from atlas_backend.core.terminal_stream import emit_log, emit_error
    _atlas_disponivel = True
except ImportError:
    def emit_log(msg, level="info"): print(f"[{level.upper()}] {msg}")
    def emit_error(e): print(f"[ERROR] {e}")
    _atlas_disponivel = False

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# DELTA CHAOS â€” BOOK v1.2
# AlteraÃ§Ãµes em relaÃ§Ã£o Ã  v1.1:
# ADICIONADO: seÃ§Ã£o REFLECT no dashboard() â€” estado e histÃ³rico por ativo
# ADICIONADO: import tape_carregar_ativo para leitura do estado REFLECT
# MANTIDO: toda a lÃ³gica de Operacao, persistÃªncia e mÃ©tricas
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

from dataclasses import dataclass, field
from typing import Optional, List
import math, json, os
import numpy as np
import pandas as pd
from datetime import datetime


# â”€â”€ Constantes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
SCHEMA_VERSION   = "1.0"

_cfg_book    = carregar_config()["book"]
RISCO_TRADE  = _cfg_book["risco_trade"]
RISCO_TOTAL  = _cfg_book["risco_total"]

TAKE_PROFIT      = 0.50
STOP_LOSS        = 2.0
ROLL_DIAS        = 7
PREMIO_MINIMO    = 0.30
COOLING_OFF_DIAS = 21

# â”€â”€ Dataclasses â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@dataclass
class Core:
    ativo:               str
    estrategia:          str
    data_entrada:        str
    fonte:               str
    data_saida:          Optional[str]   = None
    motivo_saida:        Optional[str]   = None
    motivo_nao_entrada:  Optional[str]   = None
    pnl:                 Optional[float] = None
    pnl_pct:             Optional[float] = None
    n_contratos:         float           = 0

@dataclass
class Context:
    preco_acao_entrada:  float
    selic_entrada:       float
    sizing_filtro3:      float
    slippage_aplicado:   float = 0.10

@dataclass
class OrbitData:
    ciclo:               str
    regime_entrada:      str
    ir_orbit:            float
    sizing_orbit:        float
    regime_saida:        Optional[str]   = None
    ir_realizado:        Optional[float] = None

@dataclass
class Leg:
    tipo:                str
    posicao:             str
    ticker:              str
    strike:              float
    vencimento:          str
    premio_entrada:      float
    premio_saida:        Optional[float] = None
    delta:               Optional[float] = None
    gamma:               Optional[float] = None
    theta:               Optional[float] = None
    vega:                Optional[float] = None
    iv:                  Optional[float] = None
    iv_rank:             Optional[float] = None

@dataclass
class Operacao:
    op_id:               str
    schema_version:      str
    core:                Core
    context:             Context
    orbit:               OrbitData
    legs:                List[Leg] = field(default_factory=list)


# â”€â”€ Classe BOOK â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class BOOK:

    def __init__(self, fonte: str, capital: float = 10_000):
        self._ops         = []
        self._counter     = 0
        self.capital      = capital
        self.fonte        = fonte
        self._abertas_idx: dict = {}
        self._carregar()
        print(f"  BOOK ({fonte}) â€” {len(self._ops)} operaÃ§Ãµes")

    # â”€â”€ Ãndice â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @property
    def posicoes_abertas(self) -> list:
        return list(self._abertas_idx.values())

    def posicoes_por_ativo(self, ativo: str) -> list:
        return [op for op in self._abertas_idx.values()
                if op.core.ativo == ativo]

    def pode_abrir(self) -> bool:
        if not self._abertas_idx:
            return True
        risco = 0.0
        for op in self._abertas_idx.values():
            if not op.legs: continue
            premio_max = max(
                (leg.premio_entrada for leg in op.legs
                 if leg.posicao == "vendida"), default=0.0)
            risco += (op.core.n_contratos *
                      premio_max * 1.10 / self.capital)
        return risco < RISCO_TOTAL

    def _registrar_abertura(self, op: Operacao) -> None:
        self._abertas_idx[op.op_id] = op

    def _registrar_fechamento(self, op_id: str) -> None:
        self._abertas_idx.pop(op_id, None)

    def _reconstruir_idx(self) -> None:
        self._abertas_idx = {
            op.op_id: op for op in self._ops
            if (op.core.motivo_saida is None and
                op.core.motivo_nao_entrada is None)
        }

    # â”€â”€ Abertura â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def registrar(self, op: Operacao) -> Operacao:
        self._counter += 1
        op.op_id = f"B{self._counter:04d}"
        self._ops.append(op)
        if (op.core.motivo_saida is None and
                op.core.motivo_nao_entrada is None):
            self._registrar_abertura(op)
        self._salvar()
        return op

    def registrar_nao_entrada(self, ativo, data,
                               motivo, regime, ciclo) -> None:
        self._counter += 1
        op = Operacao(
            op_id          = f"B{self._counter:04d}",
            schema_version = SCHEMA_VERSION,
            core = Core(
                ativo              = ativo,
                estrategia         = "â€”",
                data_entrada       = data,
                fonte              = self.fonte,
                motivo_nao_entrada = motivo,
                n_contratos        = 0),
            context = Context(
                preco_acao_entrada = 0.0,
                selic_entrada      = 0.0,
                sizing_filtro3     = 0.0),
            orbit = OrbitData(
                ciclo          = ciclo,
                regime_entrada = regime,
                ir_orbit       = 0.0,
                sizing_orbit   = 0.0),
            legs = [],
        )
        self._ops.append(op)

    # â”€â”€ Fechamento â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def fechar(self, op_id: str, data: str,
               precos_saida: list, motivo: str,
               preco_acao: float = 0.0) -> None:
        op = self._abertas_idx.get(op_id)
        if op is None:
            for o in self._ops:
                if o.op_id == op_id:
                    op = o; break
        if op is None: return

        pnl = 0.0
        for i, leg in enumerate(op.legs):
            p_saida = (precos_saida[i]
                       if i < len(precos_saida)
                       else leg.premio_entrada)
            leg.premio_saida = p_saida
            slip = op.context.slippage_aplicado
            if leg.posicao == "vendida":
                # entrada: recebeu menos; saÃ­da: pagou mais
                entrada_liq = leg.premio_entrada * (1 - slip)
                saida_liq   = p_saida * (1 + slip)
                pnl += ((entrada_liq - saida_liq) *
                         op.core.n_contratos)
            else:
                # entrada: pagou mais; saÃ­da: recebeu menos
                entrada_liq = leg.premio_entrada * (1 + slip)
                saida_liq   = p_saida * (1 - slip)
                pnl += ((saida_liq - entrada_liq) *
                         op.core.n_contratos)

        op.core.data_saida    = data
        op.core.motivo_saida  = motivo
        op.core.pnl           = round(pnl, 4)
        op.orbit.regime_saida = None

        premio_ref = max(sum(
            leg.premio_entrada for leg in op.legs
            if leg.posicao == "vendida"), 0.01)
        op.core.pnl_pct = round(
            pnl / (op.core.n_contratos * premio_ref + 1e-10), 4)

        self._registrar_fechamento(op_id)
        self._salvar()
        print(f"  âœ“ Fechado {op_id}: P&L={pnl:+.4f} ({motivo})")

    # â”€â”€ MÃ©tricas â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @property
    def risco_atual(self) -> float:
        if not self._abertas_idx: return 0.0
        risco = 0.0
        for op in self._abertas_idx.values():
            if not op.legs: continue
            premio_max = max(
                (leg.premio_entrada for leg in op.legs
                 if leg.posicao == "vendida"), default=0.0)
            risco += (op.core.n_contratos *
                      premio_max * 1.10 / self.capital)
        return round(risco * 100, 2)

    def calcular_contratos(self, premio_liq: float,
                            sizing_orbit: float,
                            sizing_filtro3: float) -> int:
        _fator = carregar_config()["book"]["fator_margem"]
        _n_min = carregar_config()["book"]["n_contratos_minimo"]
        n = math.floor(
            self.capital * RISCO_TRADE *
            sizing_orbit * sizing_filtro3 /
            (premio_liq * _fator + 1e-10))
        return max(n, _n_min)

    # â”€â”€ Dashboard â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def dashboard(self) -> None:
        fechadas = [op for op in self._ops if op.core.motivo_saida]
        abertas  = list(self._abertas_idx.values())

        pnls  = [op.core.pnl for op in fechadas
                 if op.core.pnl is not None]
        venc  = [p for p in pnls if p > 0]
        perd  = [p for p in pnls if p <= 0]

        pnl_total = sum(pnls)
        acerto    = len(venc) / max(len(pnls), 1) * 100

        ir = (float(np.mean(pnls)) /
              (float(np.std(pnls)) + 1e-10) *
              math.sqrt(252/21)
              if len(pnls) > 5 else 0.0)

        ganho_medio = float(np.mean(venc)) if venc else 0.0
        perda_media = float(np.mean(perd)) if perd else 0.0
        valor_esperado = (
            (acerto/100) * ganho_medio +
            (1 - acerto/100) * perda_media)

        fechadas_ord = sorted(
            fechadas, key=lambda x: x.core.data_saida or "")
        curva = []
        acum  = 0.0
        for op in fechadas_ord:
            acum += op.core.pnl or 0.0
            curva.append(acum)

        max_dd = pico = 0.0
        for v in curva:
            if v > pico: pico = v
            dd = pico - v
            if dd > max_dd: max_dd = dd

        max_stops_seq = seq_atual = 0
        for op in fechadas_ord:
            if op.core.pnl is not None and op.core.pnl < 0:
                seq_atual += 1
                max_stops_seq = max(max_stops_seq, seq_atual)
            else:
                seq_atual = 0

        ir_treinos = [op.orbit.ir_orbit for op in fechadas
                      if hasattr(op, "orbit") and op.orbit.ir_orbit > 0]
        ir_treino_medio = float(np.mean(ir_treinos)) if ir_treinos else 0.0
        gap_ir = ir_treino_medio - ir

        anos = {}
        for op in fechadas:
            if op.core.data_entrada:
                ano = str(op.core.data_entrada)[:4]
                if ano not in anos:
                    anos[ano] = {"pnl":0.0,"n":0,"venc":0,"stops":0}
                anos[ano]["pnl"] += op.core.pnl or 0.0
                anos[ano]["n"]   += 1
                if (op.core.pnl or 0) > 0: anos[ano]["venc"]  += 1
                else:                       anos[ano]["stops"] += 1

        motivos = {}
        for op in fechadas:
            m = op.core.motivo_saida or "?"
            if m not in motivos:
                motivos[m] = {"n":0, "pnl":0.0}
            motivos[m]["n"]   += 1
            motivos[m]["pnl"] += op.core.pnl or 0.0

        selic_media = 10.0
        rf_diario   = selic_media / 100 / 252
        sharpe = 0.0
        if len(pnls) > 5:
            retornos = np.array(pnls) / self.capital
            excesso  = retornos - rf_diario
            sharpe   = float(
                np.mean(excesso) /
                (np.std(excesso) + 1e-10) *
                math.sqrt(252/21))

        total_ops = len([op for op in self._ops
                         if op.core.motivo_nao_entrada is None])
        pct_ativo = total_ops / max(len(self._ops), 1) * 100

        # â”€â”€ REFLECT por ativo â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        reflect_history_len = carregar_config()["reflect"]["reflect_history_length"]
        todos_ativos = sorted(set(op.core.ativo for op in self._ops))
        reflect_info = {}
        for ativo in todos_ativos:
            try:
                cfg   = tape_carregar_ativo(ativo)
                state = cfg.get("reflect_state", "?")
                hist  = cfg.get("reflect_history", [])
                score = cfg.get("reflect_score", 0.0)
                # Ãšltimos N estados para o dashboard
                hist_str = " ".join(
                    h.get("state","?")
                    for h in hist[-reflect_history_len:])
                reflect_info[ativo] = {
                    "state":   state,
                    "score":   score,
                    "history": hist_str,
                }
            except Exception:
                reflect_info[ativo] = {
                    "state": "?", "score": 0.0,
                    "history": ""}

        # â”€â”€ ImpressÃ£o â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        sep = "â•" * 55
        print(f"\n  {sep}")
        print(f"  BOOK ({self.fonte}) â€” capital R${self.capital:,.0f}")
        print(f"  {sep}")
        print(f"  Total: {len(self._ops)} | "
              f"abertas: {len(abertas)} | "
              f"fechadas: {len(fechadas)}")

        if abertas:
            print(f"\n  PosiÃ§Ãµes abertas:")
            for op in abertas:
                print(f"    {op.op_id:8} {op.core.ativo:8} "
                      f"{op.core.estrategia:15} "
                      f"regime={op.orbit.regime_entrada}")

        print(f"\n  â”€â”€ Retorno â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")
        print(f"  P&L realizado:     R${pnl_total:+,.2f}")
        print(f"  Acerto:            {acerto:.1f}%")
        print(f"  IR realizado:      {ir:+.4f}")
        print(f"  Sharpe realizado:  {sharpe:+.4f}")
        print(f"  Risco atual:       "
              f"{self.risco_atual:.1f}% "
              f"(mÃ¡x {RISCO_TOTAL*100:.0f}%)")

        print(f"\n  â”€â”€ REFLECT (metamodelo) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")
        for ativo, info in reflect_info.items():
            bloq  = "â›” BLOQUEADO" if info["blocked"] else ""
            score = f"{info['score']:+.3f}" if info["score"] != 0.0 else "  n/a"
            print(f"  {ativo:8} Edge {info['state']}  "
              f"Score={score:>8}  "
              f"Hist=[Edge {' | Edge '.join(info['history'].split())}]  {bloq}")

        print(f"\n  â”€â”€ Valor esperado (P1) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")
        print(f"  Ganho mÃ©dio:       R${ganho_medio:+,.2f}  "
              f"({len(venc)} trades)")
        print(f"  Perda mÃ©dia:       R${perda_media:+,.2f}  "
              f"({len(perd)} trades)")
        print(f"  Valor esperado:    R${valor_esperado:+,.2f} por trade")

        print(f"\n  â”€â”€ Risco (P2) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")
        print(f"  Drawdown mÃ¡ximo:   R${max_dd:,.2f}")
        print(f"  Max stops seguidos:{max_stops_seq}")

        print(f"\n  â”€â”€ Modelo (P3) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")
        print(f"  IR treino mÃ©dio:   {ir_treino_medio:+.4f}")
        print(f"  IR realizado:      {ir:+.4f}")
        print(f"  Gap IR:            {gap_ir:+.4f}")

        print(f"\n  â”€â”€ Por ano (P3) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")
        for ano in sorted(anos.keys()):
            d  = anos[ano]
            ac = d["venc"] / max(d["n"],1) * 100
            print(f"  {ano}  n={d['n']:3}  "
                  f"P&L=R${d['pnl']:+,.2f}  "
                  f"acerto={ac:.0f}%  stops={d['stops']}")

        print(f"\n  â”€â”€ Por motivo (P4) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")
        for m, d in sorted(motivos.items()):
            medio = d["pnl"] / max(d["n"],1)
            print(f"  {m:12} n={d['n']:3}  "
                  f"P&L=R${d['pnl']:+,.2f}  "
                  f"mÃ©dio=R${medio:+,.2f}")

        print(f"\n  â”€â”€ Operacional (P5) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")
        print(f"  Tempo com posiÃ§Ã£o: {pct_ativo:.1f}%")
        print(f"\n  {sep}")

    # â”€â”€ DataFrame â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def df(self) -> pd.DataFrame:
        rows = []
        for op in self._ops:
            rows.append({
                "op_id":             op.op_id,
                "ativo":             op.core.ativo,
                "estrategia":        op.core.estrategia,
                "data_entrada":      op.core.data_entrada,
                "data_saida":        op.core.data_saida,
                "motivo_saida":      op.core.motivo_saida,
                "motivo_nao_entrada":op.core.motivo_nao_entrada,
                "pnl":               op.core.pnl,
                "pnl_pct":           op.core.pnl_pct,
                "n_contratos":       op.core.n_contratos,
                "regime_entrada":    op.orbit.regime_entrada,
                "regime_saida":      op.orbit.regime_saida,
                "ir_orbit":          op.orbit.ir_orbit,
                "sizing_orbit":      op.orbit.sizing_orbit,
                "ciclo":             op.orbit.ciclo,
                "premio_entrada": (op.legs[0].premio_entrada
                                   if op.legs else None),
                "delta_entrada":  (op.legs[0].delta
                                   if op.legs else None),
            })
        return pd.DataFrame(rows)

    # â”€â”€ PersistÃªncia â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _salvar(self) -> None:
        try:
            os.makedirs(BOOK_DIR, exist_ok=True)
            nome  = f"book_{self.fonte}"
            path  = os.path.join(BOOK_DIR, f"{nome}.json")
            dados = {
                "fonte":   self.fonte,
                "capital": self.capital,
                "counter": self._counter,
                "ops":     [self._op_to_dict(op)
                            for op in self._ops],
            }
    
            if self.fonte == "backtest":
                # S1 â€” backtest: save direto, sem overhead de tempfile
                # O backtest Ã© descartÃ¡vel â€” nÃ£o hÃ¡ risco de
                # perder posiÃ§Ãµes abertas entre sessÃµes.
                with open(path, "w") as f:
                    json.dump(dados, f, indent=2, default=str)
            else:
                # S1 â€” paper/real: escrita atÃ´mica via tempfile + os.replace
                # Cada trade fechado precisa ser persistido imediatamente
                # e com garantia de integridade.
                import tempfile
                dir_ = os.path.dirname(path)
                with tempfile.NamedTemporaryFile(
                        "w", dir=dir_, suffix=".tmp",
                        delete=False, encoding="utf-8") as tf:
                    json.dump(dados, tf, indent=2, default=str)
                    tmp_path = tf.name
                os.replace(tmp_path, path)
    
            # Parquet â€” sempre direto (formato binÃ¡rio,
            # pandas lida com escrita segura internamente)
            self.df().to_parquet(
                os.path.join(BOOK_DIR, f"{nome}.parquet"),
                index=False)
 
        except Exception as e:
            try:
                if 'tmp_path' in locals() and \
                  os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            print(f"  âš  BOOK salvar: {e}")
 

    def _carregar(self) -> None:
        try:
            nome = f"book_{self.fonte}"
            path = os.path.join(BOOK_DIR, f"{nome}.json")
            if not os.path.exists(path):
                return
            with open(path) as f:
                dados = json.load(f)
            self._counter = dados.get("counter", 0)
            for d in dados.get("ops", []):
                op = self._dict_to_op(d)
                if op:
                    self._ops.append(op)
            self._reconstruir_idx()
    
        except Exception as e:
            # S3 â€” backup + audit_log antes de reiniciar vazio
            ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome = f"book_{self.fonte}"
            path = os.path.join(BOOK_DIR, f"{nome}.json")
    
            # 1. Backup do arquivo corrompido
            bak = os.path.join(
                BOOK_DIR,
                f"book_{self.fonte}_corrupto_{ts}.json")
            try:
                import shutil
                if os.path.exists(path):
                    shutil.copy2(path, bak)
                    bak_nome = os.path.basename(bak)
                else:
                    bak_nome = "arquivo nÃ£o encontrado"
            except Exception as e2:
                bak_nome = f"backup falhou: {e2}"
    
            # 2. Entrada no audit_log
            audit_path = os.path.join(
                BOOK_DIR, "book_audit_log.json")
            entrada = {
                "timestamp": str(datetime.now())[:19],
                "evento":    "carregar_falhou",
                "fonte":     self.fonte,
                "motivo":    str(e),
                "backup":    bak_nome,
            }
            try:
                audit = []
                if os.path.exists(audit_path):
                    with open(audit_path) as f:
                        audit = json.load(f)
                audit.append(entrada)
                with open(audit_path, "w") as f:
                    json.dump(audit, f,
                              indent=2, default=str)
            except Exception:
                pass
    
            # 3. Aviso crÃ­tico â€” visÃ­vel, nÃ£o silencioso
            print(f"\n  {'â–ˆ'*55}")
            print(f"  CRÃTICO â€” S3: BOOK nÃ£o carregado")
            print(f"  Fonte:  {self.fonte}")
            print(f"  Motivo: {e}")
            print(f"  Backup: {bak_nome}")
            print(f"  Audit:  book_audit_log.json atualizado")
            print(f"  AÃ‡ÃƒO NECESSÃRIA: verifique o backup antes")
            print(f"  de operar. PosiÃ§Ãµes abertas podem estar")
            print(f"  invisÃ­veis ao sistema.")
            print(f"  {'â–ˆ'*55}\n")
            # Estado vazio â€” mas agora com aviso explÃ­cito

    def _op_to_dict(self, op) -> dict:
        return {
            "op_id":  op.op_id,
            "schema": op.schema_version,
            "core": {
                "ativo":             op.core.ativo,
                "estrategia":        op.core.estrategia,
                "data_entrada":      op.core.data_entrada,
                "data_saida":        op.core.data_saida,
                "fonte":             op.core.fonte,
                "motivo_saida":      op.core.motivo_saida,
                "motivo_nao_entrada":op.core.motivo_nao_entrada,
                "pnl":               op.core.pnl,
                "pnl_pct":           op.core.pnl_pct,
                "n_contratos":       op.core.n_contratos,
            },
            "context": {
                "preco_acao_entrada": op.context.preco_acao_entrada,
                "selic_entrada":      op.context.selic_entrada,
                "sizing_filtro3":     op.context.sizing_filtro3,
            },
            "orbit": {
                "ciclo":          op.orbit.ciclo,
                "regime_entrada": op.orbit.regime_entrada,
                "regime_saida":   op.orbit.regime_saida,
                "ir_orbit":       op.orbit.ir_orbit,
                "sizing_orbit":   op.orbit.sizing_orbit,
            },
            "legs": [
                {
                    "tipo":           leg.tipo,
                    "posicao":        leg.posicao,
                    "ticker":         leg.ticker,
                    "strike":         leg.strike,
                    "vencimento":     leg.vencimento,
                    "premio_entrada": leg.premio_entrada,
                    "premio_saida":   leg.premio_saida,
                    "delta":          leg.delta,
                    "gamma":          leg.gamma,
                    "theta":          leg.theta,
                    "vega":           leg.vega,
                    "iv":             leg.iv,
                    "iv_rank":        leg.iv_rank,
                }
                for leg in op.legs
            ],
        }

    def _dict_to_op(self, d: dict):
        try:
            legs = [
                Leg(
                    tipo            = l["tipo"],
                    posicao         = l["posicao"],
                    ticker          = l["ticker"],
                    strike          = l["strike"],
                    vencimento      = l["vencimento"],
                    premio_entrada  = l["premio_entrada"],
                    premio_saida    = l.get("premio_saida"),
                    delta           = l.get("delta"),
                    gamma           = l.get("gamma"),
                    theta           = l.get("theta"),
                    vega            = l.get("vega"),
                    iv              = l.get("iv"),
                    iv_rank         = l.get("iv_rank"),
                )
                for l in d.get("legs", [])
            ]
            return Operacao(
                op_id          = d["op_id"],
                schema_version = d.get("schema", SCHEMA_VERSION),
                core = Core(
                    ativo              = d["core"]["ativo"],
                    estrategia         = d["core"]["estrategia"],
                    data_entrada       = d["core"]["data_entrada"],
                    data_saida         = d["core"].get("data_saida"),
                    fonte              = d["core"]["fonte"],
                    motivo_saida       = d["core"].get("motivo_saida"),
                    motivo_nao_entrada = d["core"].get("motivo_nao_entrada"),
                    pnl                = d["core"].get("pnl"),
                    pnl_pct            = d["core"].get("pnl_pct"),
                    n_contratos        = d["core"].get("n_contratos", 0),
                ),
                context = Context(
                    preco_acao_entrada = d["context"].get(
                        "preco_acao_entrada", 0.0),
                    selic_entrada      = d["context"].get(
                        "selic_entrada", 0.0),
                    sizing_filtro3     = d["context"].get(
                        "sizing_filtro3", 1.0),
                ),
                orbit = OrbitData(
                    ciclo          = d["orbit"].get("ciclo",""),
                    regime_entrada = d["orbit"].get("regime_entrada",""),
                    regime_saida   = d["orbit"].get("regime_saida"),
                    ir_orbit       = d["orbit"].get("ir_orbit", 0.0),
                    sizing_orbit   = d["orbit"].get("sizing_orbit", 1.0),
                ),
                legs = legs,
            )
        except Exception as e:
            print(f"  âš  _dict_to_op: {e}")
            return None

if __name__ == "__main__":
    print("âœ“ BOOK v1.2 carregado")
    print("  Dataclasses: Operacao Core Context OrbitData Leg")
    print("  Ãndice em memÃ³ria â€” posicoes_abertas O(1)")
    print("  Dashboard: seÃ§Ã£o REFLECT com estado e histÃ³rico por ativo")
