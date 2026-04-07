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
# Status válidos: SEM_EDGE | OPERAR | MONITORAR | SUSPENSO
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
#   1. Sem histórico OU lock ativo → SUSPENSO
#   2. Quedas REFLECT consecutivas >= 2 (D ou E) → SUSPENSO
#   3. GATE 8/8 + IR > 0 + REFLECT em A/B → OPERAR
#   4. GATE com resultado válido (não 8/8) → MONITORAR
#   5. Sem IR capturável em nenhum regime → SEM_EDGE
# ---------------------------------------------------------------------
# [ATLAS-STATUS-LOGIC-END] — DO NOT DELETE
# =====================================================================

#
# --modo backtest_dados   onboarding step 1: COTAHIST + ORBIT + popula historico[]
# --modo tune             onboarding step 2 + atualização mensal step 3 (se elegível)
# --modo backtest_gate    onboarding step 3 + atualização mensal step 2: GATE completo
# --modo orbit            atualização mensal: OHLCV cache + ORBIT + reflect_cycle
# --modo eod              diário: paper/live



from delta_chaos.init import (
    carregar_config, ATIVOS_DIR, BOOK_DIR,
    OPCOES_HOJE_DIR, DRIVE_BASE,
)
from pathlib import Path

# Diretório temporário para flags de módulos
TMP_DIR = Path(DRIVE_BASE) / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)
from delta_chaos.tape import (
    tape_carregar_ativo, tape_salvar_ativo,
    tape_paper, tape_backtest, tape_reflect_cycle,
    tape_sizing_reflect, tape_process_eod_file,
    tape_ohlcv, tape_ibov,
    _obter_selic,
)
from .orbit import ORBIT
from .book import BOOK
from .fire import FIRE
from .gate_eod import gate_eod

# ── Logging ATLAS (graceful fallback) ─────────────────────────────────
try:
    from atlas_backend.core.terminal_stream import emit_log, emit_error
    _atlas_disponivel = True
except ImportError:
    def emit_log(msg, level="info"): print(f"[{level.upper()}] {msg}")
    def emit_error(e): print(f"[ERROR] {e}")
    _atlas_disponivel = False

# Eventos estruturados do Delta Chaos (DESATIVADO — quem emite é o dc_runner)
# try:
#     from atlas_backend.core.event_bus import emit_dc_event
# except ImportError:
#     def emit_dc_event(event_type, modulo, status=None, **kwargs): pass

# ════════════════════════════════════════════════════════════════════
# DELTA CHAOS — EDGE v1.3
# Alterações em relação à v1.2:
# ADICIONADO: integração com REFLECT via tape_sizing_reflect()
# ADICIONADO: verificação reflect_permanent_block_flag antes de abrir
# ADICIONADO: tape_reflect_cycle no fechamento de cada ciclo mensal
# CORRIGIDO (SCAN-11): configs_ativos indefinido no modo paper — NameError
# CORRIGIDO (SCAN-9): cfg passado ao FIRE no paper — evita dupla leitura JSON
# ════════════════════════════════════════════════════════════════════

import os
from datetime import datetime
from datetime import datetime, date
import pandas as pd
from tqdm.auto import tqdm as _tqdm

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
            cfg = tape_carregar_ativo(ticker)
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
          cfg = tape_carregar_ativo(ticker)
          cfg["reflect_all_cycles_history"] = []
          cfg["reflect_history"]            = []
          cfg["reflect_daily_history"]      = {}
          cfg["reflect_state"]              = "B"
          cfg["reflect_score"]              = 0.0
          tape_salvar_ativo(ticker, cfg)
          print(f"  ✓ REFLECT limpo — {ticker}")

      # [1/3] TAPE
      print(f"\n  [1/3] TAPE")
      df_tape = tape_backtest(
          ativos=self.ativos, anos=anos, forcar=False)
      if df_tape.empty:
          print("  ✗ TAPE vazio. Abortando.")
          return pd.DataFrame()
      print(f"  ✓ TAPE: {len(df_tape)} registros")
      df_selic = _obter_selic(min(anos), max(anos))

      # [2/3] ORBIT
      print(f"\n  [2/3] ORBIT v3.4")
      df_regimes = self.orbit.rodar(
          df_tape, anos, modo=modo_orbit)
      if df_regimes.empty:
          print("  ✗ ORBIT vazio. Abortando.")
          return pd.DataFrame()

      print(f"  ✓ ORBIT: regimes calculados")

      df_regimes["ciclo_id"] = \
          df_regimes["ciclo_id"].astype(str)
      regime_idx = df_regimes.set_index(
          ["ciclo_id","ativo"]).to_dict("index")

      # Config dos ativos carregada uma vez
      configs_ativos = {
          ativo: tape_carregar_ativo(ativo)
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
                  reflect_mult = tape_sizing_reflect(ativo)
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
                      tape_reflect_cycle(ativo, ciclo_id)
                      # Recarrega config após atualização do REFLECT
                      configs_ativos[ativo] = tape_carregar_ativo(ativo)
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
          parecer = gate_eod(ativo, verbose=True)
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
            ativo: tape_carregar_ativo(ativo)
            for ativo in self.ativos
        }

        for ativo in self.ativos:

            # GATE EOD — verificação leve antes de qualquer operação
            parecer = gate_eod(ativo, verbose=True)
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
            tape_process_eod_file(xlsx)

            try:
                preco = float(input(
                    f"  Preço atual {ativo}: R$ "))
            except Exception:
                print(f"  ⚠ Preço inválido para {ativo}")
                continue
            df_p = tape_paper(
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

            orbit_data   = self.orbit.regime_para_data(ativo, data_hoje)
            sizing_orbit = float(orbit_data.get("sizing", 0.0))

            # Modula sizing pelo REFLECT
            reflect_mult = tape_sizing_reflect(ativo)
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

# ── Entrypoint CLI — chamado pelo ATLAS via subprocess ───────────
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Delta Chaos — entrypoint CLI para ATLAS")

    parser.add_argument(
        "--modo",
        choices=["backtest_dados", "backtest_gate", "eod", "tune", "orbit", "reflect_daily", "gate_eod"],
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
        # Modo: backtest_dados
        # Propósito: Onboarding step 1 — COTAHIST + ORBIT + popula historico[]
        # Uso: python -m delta_chaos.edge --modo backtest_dados --ticker VALE3
        # Fluxo: instancia EDGE completo (apaga books), roda TAPE + ORBIT
        # ──────────────────────────────────────────────────────────────
        elif args.modo == "backtest_dados":
            # Mantém comportamento atual do orbit (instancia EDGE completo, apaga books)
            anos = (list(map(int, args.anos.split(",")))
                    if args.anos
                    else list(range(2002, datetime.now().year + 1)))
            edge = EDGE(
                capital=carregar_config().get("backtest", {}).get("capital", 10000.0),
                modo="backtest",
                universo=[args.ticker]
            )
            df_tape = tape_backtest(
                ativos=[args.ticker], anos=anos, forcar=False)
            orbit = ORBIT(universo={args.ticker: tape_carregar_ativo(args.ticker)})
            orbit.rodar(df_tape, anos, modo="mensal")

        # ──────────────────────────────────────────────────────────────
        # Modo: orbit
        # Propósito: Atualização mensal — OHLCV cache + ORBIT + reflect_cycle
        # Uso: python -m delta_chaos.edge --modo orbit --ticker VALE3
        # Fluxo: TAPE verifica/baixa dados → ORBIT calcula regimes → REFLECT atualiza ciclo
        # ──────────────────────────────────────────────────────────────
        elif args.modo == "orbit":
            # Modo leve mensal — não instancia EDGE, não apaga books
            ticker = args.ticker
            anos = (list(map(int, args.anos.split(",")))
                    if args.anos
                    else list(range(2002, datetime.now().year + 1)))

            # ── TAPE: verificar/baixar dados ──
            print(f"\n  [1/3] TAPE")
            try:
                cfg_ativo = tape_carregar_ativo(ticker)
                df_ohlcv = tape_ohlcv(ticker, anos)
                df_ibov = tape_ibov(anos)
                if df_ohlcv.empty:
                    print(f"  ✗ TAPE: dados OHLCV indisponíveis para {ticker}")
                    sys.exit(1)
                print(f"  ✓ TAPE: {len(df_ohlcv)} registros OHLCV para {ticker}")
                # Flag de sucesso para o dc_runner
                (TMP_DIR / f"TAPE_{ticker}.done").touch()
            except Exception as e:
                print(f"  ✗ TAPE erro: {e}")
                sys.exit(1)

            # ── ORBIT: calcular regimes ──
            print(f"\n  [2/3] ORBIT")
            try:
                orbit = ORBIT(universo={ticker: cfg_ativo})
                orbit.rodar(df_ohlcv, anos, modo="mensal")
                print(f"  ✓ ORBIT: regimes calculados para {ticker}")
                # Flag de sucesso para o dc_runner
                (TMP_DIR / f"ORBIT_{ticker}.done").touch()
            except Exception as e:
                print(f"  ✗ ORBIT erro: {e}")
                sys.exit(1)

            # ── REFLECT: atualizar ciclo ──
            print(f"\n  [3/3] REFLECT")
            try:
                tape_reflect_cycle(ticker, datetime.now().strftime("%Y-%m"))
                print(f"  ✓ REFLECT: ciclo atualizado para {ticker}")
                # Flag de sucesso para o dc_runner
                (TMP_DIR / f"REFLECT_{ticker}.done").touch()
            except Exception as e:
                print(f"  ✗ REFLECT erro: {e}")

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
        # Modo: backtest_gate
        # Propósito: Onboarding step 3 + atualização mensal step 2 — GATE completo
        # Uso: python -m delta_chaos.edge --modo backtest_gate --ticker VALE3
        # Fluxo: executa GATE completo para o ativo
        # ──────────────────────────────────────────────────────────────
        elif args.modo == "backtest_gate":
            from delta_chaos.gate import executar_gate
            resultado = executar_gate(args.ticker)
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
            tape_process_eod_file(args.xlsx_path)

        # ──────────────────────────────────────────────────────────────
        # Modo: gate_eod
        # Propósito: Verificação de integridade EOD — decide OPERAR/MONITORAR/BLOQUEADO
        # Uso: python -m delta_chaos.edge --modo gate_eod --ticker VALE3
        # Fluxo: verifica GATE completo + regime atual + REFLECT
        # ──────────────────────────────────────────────────────────────
        elif args.modo == "gate_eod":
            resultado = gate_eod(args.ticker, verbose=True)
            print(f"[GATE_EOD] {args.ticker}: {resultado}")

    except Exception as e:
        import traceback
        print(f"ERRO: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
