# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
import os
from datetime import datetime
# DELTA CHAOS â€” EDGE v2.0
# AlteraÃ§Ãµes em relaÃ§Ã£o Ã  v1.3:
# MIGRADO (P2): imports explÃ­citos de todos os mÃ³dulos â€” sem escopo global
# MIGRADO (P5): prints de inicializaÃ§Ã£o sob if __name__ == "__main__"
# MANTIDO: orquestraÃ§Ã£o backtest/paper/EOD, REFLECT, GATE EOD, BOOK
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

from delta_chaos.init import (
    carregar_config, ATIVOS_DIR, BOOK_DIR,
    OPCOES_HOJE_DIR, DRIVE_BASE,
)
from delta_chaos.tape import (
    tape_carregar_ativo, tape_salvar_ativo,
    tape_paper, tape_backtest, tape_reflect_cycle,
    tape_sizing_reflect, tape_process_eod_file,
    _obter_selic,
)
from .orbit import ORBIT
from .book import BOOK
from .fire import FIRE
from .gate_eod import gate_eod

# â”€â”€ Logging ATLAS (graceful fallback) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    from atlas_backend.core.terminal_stream import emit_log, emit_error
    _atlas_disponivel = True
except ImportError:
    def emit_log(msg, level="info"): print(f"[{level.upper()}] {msg}")
    def emit_error(e): print(f"[ERROR] {e}")
    _atlas_disponivel = False

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# DELTA CHAOS â€” EDGE v1.3
# AlteraÃ§Ãµes em relaÃ§Ã£o Ã  v1.2:
# ADICIONADO: integraÃ§Ã£o com REFLECT via tape_sizing_reflect()
# ADICIONADO: verificaÃ§Ã£o reflect_permanent_block_flag antes de abrir
# ADICIONADO: tape_reflect_cycle no fechamento de cada ciclo mensal
# CORRIGIDO (SCAN-11): configs_ativos indefinido no modo paper â€” NameError
# CORRIGIDO (SCAN-9): cfg passado ao FIRE no paper â€” evita dupla leitura JSON
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

import os
from datetime import datetime
from datetime import datetime, date
import pandas as pd
from tqdm.auto import tqdm as _tqdm

class EDGE:
    """
    Orquestra TAPE â†’ ORBIT â†’ FIRE â†’ BOOK
    ConfiguraÃ§Ã£o de ativos via master JSON em ATIVOS_DIR
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
                    print(f"  âœ“ {os.path.basename(p)} removido")

        self.book  = BOOK(fonte=modo, capital=capital)
        self.fire  = FIRE(book=self.book, modo=modo)
        self.orbit = ORBIT(universo=self.universo)

        print(f"\n  {'â•'*55}")
        print(f"  EDGE v1.3 â€” modo={modo}")
        print(f"  Capital:  R${capital:,.0f}")
        print(f"  Ativos:   {self.ativos}")
        print(f"  {'â•'*55}")

    def executar(self, anos=None, xlsx_dir=None,
                 modo_orbit="pipeline",
                 reset=False):
        if reset:
            self.book._ops         = []
            self.book._counter     = 0
            self.book._abertas_idx = {}
            self.book._salvar()
            print("  âœ“ BOOK resetado â€” backtest limpo")

        if self.modo == "backtest":
            if anos is None:
                anos = [2020,2021,2022,2023,2024,2025,2026]
            return self._executar_backtest(anos, modo_orbit)
        elif self.modo == "paper":
            return self._executar_paper(xlsx_dir)
        elif self.modo == "real":
            raise NotImplementedError("EDGE.real â€” Fase 3.")

    def _executar_backtest(self, anos, modo_orbit):
      print(f"\n  {'â•'*55}")
      print(f"  EDGE.backtest â€” {anos[0]}â†’{anos[-1]}")
      print(f"  {'â•'*55}")

      self.book._ativo_atual = "_".join(self.ativos)

      # Limpa BOOK antes de backtest
      for ext in ["json", "parquet"]:
          p = os.path.join(BOOK_DIR, f"book_backtest.{ext}")
          if os.path.exists(p):
              os.remove(p)
              print(f"  âœ“ {os.path.basename(p)} removido")

      # Limpa histÃ³rico REFLECT dos ativos â€” evita z-score
      # contaminado por backtest anterior
      for ticker in self.ativos:
          cfg = tape_carregar_ativo(ticker)
          cfg["reflect_all_cycles_history"] = []
          cfg["reflect_history"]            = []
          cfg["reflect_daily_history"]      = {}
          cfg["reflect_state"]              = "B"
          cfg["reflect_score"]              = 0.0
          cfg["reflect_permanent_block_flag"] = False
          tape_salvar_ativo(ticker, cfg)
          print(f"  âœ“ REFLECT limpo â€” {ticker}")

      # [1/3] TAPE
      print(f"\n  [1/3] TAPE")
      df_tape = tape_backtest(
          ativos=self.ativos, anos=anos, forcar=False)
      if df_tape.empty:
          print("  âœ— TAPE vazio. Abortando.")
          return pd.DataFrame()
      df_selic = _obter_selic(min(anos), max(anos))

      # [2/3] ORBIT
      print(f"\n  [2/3] ORBIT v3.4")
      df_regimes = self.orbit.rodar(
          df_tape, anos, modo=modo_orbit)
      if df_regimes.empty:
          print("  âœ— ORBIT vazio. Abortando.")
          return pd.DataFrame()

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
                unit="pregÃ£o", ncols=None) as pbar:
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

                  # Bloqueio permanente REFLECT estado E
                  if cfg_ativo.get(
                          "reflect_permanent_block_flag", False):
                      self.book.registrar_nao_entrada(
                          ativo, data_str,
                          "permanently_blocked_reflect_E",
                          "N/A", ciclo_id)
                      continue

                  raw = regime_idx.get((ciclo_id, ativo), {})
                  sizing_orbit = float(raw.get("sizing", 0.0))

                  # Modula sizing do ORBIT pelo REFLECT
                  reflect_mult, _ = tape_sizing_reflect(ativo)
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

              # REFLECT de ciclo â€” uma vez por ciclo mensal
              if ciclo_id not in reflect_ciclos_processados:
                  for ativo in self.ativos:
                      tape_reflect_cycle(ativo, ciclo_id)
                      # Recarrega config apÃ³s atualizaÃ§Ã£o do REFLECT
                      configs_ativos[ativo] = tape_carregar_ativo(ativo)
                  reflect_ciclos_processados.add(ciclo_id)

              pbar.update(1)
              pbar.set_postfix(
                  abertas  = len(self.book.posicoes_abertas),
                  fechadas = sum(
                      1 for op in self.book._ops
                      if op.core.motivo_saida),
              )

      print(f"\n  {'â•'*55}")
      print(f"  EDGE.backtest concluÃ­do")
      print(f"  {'â•'*55}")
      self.book.dashboard()
      return self.book.df()

    def executar_eod(self,
                     xlsx_dir=None,
                     capital=None):
      """
      Fluxo completo de paper trading diÃ¡rio.
      Substitui chamada manual Ã  CÃ©lula EOD.

      Etapas:
        1. Arquiva xlsx do dia em opcoes_historico/
        2. GATE EOD por ativo â€” exclui bloqueados
        3. _executar_paper() nos aprovados
      """
      import shutil
      from datetime import date

      xlsx_dir  = xlsx_dir or OPCOES_HOJE_DIR
      data_hoje = str(date.today())
      hist_dir  = os.path.join(
          DRIVE_BASE, "opcoes_historico")
      os.makedirs(hist_dir, exist_ok=True)

      print(f"\n  {'â•'*55}")
      print(f"  EDGE.executar_eod â€” {data_hoje}")
      print(f"  {'â•'*55}")

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
              print(f"  âœ“ {data_hoje} "
                    f"{ativo}.xlsx â†’ opcoes_historico/")
          else:
              print(f"  âš  NÃ£o encontrado: "
                    f"{ativo}.xlsx")

      # 2. GATE EOD por ativo
      print(f"\n  [2/3] GATE EOD...")
      aprovados = []
      for ativo in self.ativos:
          parecer = gate_eod(ativo, verbose=True)
          if parecer in ("BLOQUEADO",
                          "GATE VENCIDO"):
              print(f"  â†’ {ativo} excluÃ­do "
                    f"({parecer})\n")
          else:
              aprovados.append(ativo)

      if not aprovados:
          print(f"\n  Nenhum ativo aprovado "
                f"pelo GATE EOD hoje.")
          print(f"  {'â•'*55}\n")
          return self.book.df()

      print(f"\n  Aprovados: {aprovados}")

      # 3. Paper trading â€” apenas aprovados
      print(f"\n  [3/3] EDGE paper...")
      self.ativos = aprovados
      return self._executar_paper(xlsx_dir)


    def _executar_paper(self, xlsx_dir=None):
        xlsx_dir  = xlsx_dir or OPCOES_HOJE_DIR
        data_hoje = str(date.today())
        print(f"\n  EDGE.paper â€” {data_hoje}")

        frames = []
        # SCAN-11 CORRIGIDO: configs_ativos definido antes do loop de ativos
        configs_ativos = {
            ativo: tape_carregar_ativo(ativo)
            for ativo in self.ativos
        }

        for ativo in self.ativos:

            # GATE EOD â€” verificaÃ§Ã£o leve antes de qualquer operaÃ§Ã£o
            parecer = gate_eod(ativo, verbose=True)
            if parecer in ("BLOQUEADO", "GATE VENCIDO"):
                print(f"  â†’ {ativo} excluÃ­do do EOD ({parecer})\n")
                continue

            # MONITORAR e OPERAR prosseguem normalmente
            hoje  = str(date.today())
            xlsx  = os.path.join(xlsx_dir, f"{ativo}.xlsx")
            xlsx2 = os.path.join(xlsx_dir, f"{hoje} {ativo}.xlsx")

            if not os.path.exists(xlsx) and os.path.exists(xlsx2):
                import shutil
                shutil.copy2(xlsx2, xlsx)
                print(f"  âœ“ {hoje} {ativo}.xlsx â†’ {ativo}.xlsx")

            if not os.path.exists(xlsx):
                print(f"  âš  {ativo}.xlsx nÃ£o encontrado")
                continue

            # Processa EOD para alimentar o REFLECT diÃ¡rio
            tape_process_eod_file(xlsx)

            try:
                preco = float(input(
                    f"  PreÃ§o atual {ativo}: R$ "))
            except Exception:
                print(f"  âš  PreÃ§o invÃ¡lido para {ativo}")
                continue
            df_p = tape_paper(
                ativo=ativo, filepath=xlsx,
                preco_acao=preco, data=data_hoje)
            if not df_p.empty:
                frames.append(df_p)

        if not frames:
            print("  âœ— Nenhum XLSX carregado.")
            return pd.DataFrame()

        df_hoje  = pd.concat(frames, ignore_index=True)
        df_selic = _obter_selic(
            datetime.now().year, datetime.now().year)

        self.fire.verificar(
            df_hoje, data_hoje, df_selic,
            configs_ativos=configs_ativos)

        for ativo in self.ativos:
            cfg_ativo = configs_ativos[ativo]

            # Bloqueio permanente REFLECT estado E
            if cfg_ativo.get("reflect_permanent_block_flag", False):
                self.book.registrar_nao_entrada(
                    ativo, data_hoje,
                    "permanently_blocked_reflect_E",
                    "N/A", data_hoje[:7])
                continue

            orbit_data   = self.orbit.regime_para_data(ativo, data_hoje)
            sizing_orbit = float(orbit_data.get("sizing", 0.0))

            # Modula sizing pelo REFLECT
            reflect_mult, _ = tape_sizing_reflect(ativo)
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
        choices=["eod", "eod_preview", "orbit", "tune", "gate", "reflect"],
        required=True,
        help="Rotina a executar"
    )
    parser.add_argument(
        "--ticker",
        type=str,
        default=None,
        help="Ticker do ativo (obrigatório para orbit, tune, gate)"
    )
    parser.add_argument(
        "--xlsx_dir",
        type=str,
        default=None,
        help="Diretório com arquivos xlsx EOD (obrigatório para eod)"
    )
    parser.add_argument(
        "--anos",
        type=str,
        default=None,
        help="Anos separados por vírgula (opcional para orbit)"
    )

    args = parser.parse_args()

    # Validações
    if args.modo in ("orbit", "tune", "gate") and not args.ticker:
        print(f"ERRO: --ticker obrigatório para modo {args.modo}",
              file=sys.stderr)
        sys.exit(1)

    if args.modo in ("eod", "eod_preview") and not args.xlsx_dir:
        print("ERRO: --xlsx_dir obrigatório para modo eod",
              file=sys.stderr)
        sys.exit(1)

    # Execução
    try:
        universo = carregar_config().get("universo", [])

        if args.modo == "eod_preview":
            # Apenas gate_eod por ativo — sem executar
            print(f"[PREVIEW] Verificando {len(universo)} ativos...")
            for ticker in universo:
                parecer = gate_eod(ticker, verbose=True)
                print(f"[PREVIEW] {ticker}: {parecer}")

        elif args.modo == "eod":
            edge = EDGE(
                capital=carregar_config()["book"]["capital"],
                modo="paper",
                universo=universo
            )
            edge.executar_eod(xlsx_dir=args.xlsx_dir)

        elif args.modo == "orbit":
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

        elif args.modo == "tune":
            from delta_chaos.tune import executar_tune
            executar_tune(args.ticker)

        elif args.modo == "gate":
            from delta_chaos.gate import executar_gate
            resultado = executar_gate(args.ticker)
            print(f"[GATE] {args.ticker}: {resultado}")

        elif args.modo == "reflect":
            # Reflect = executar_gate (atualiza historico e reflect_state)
            from delta_chaos.gate import executar_gate
            resultado = executar_gate(args.ticker)
            print(f"[REFLECT] {args.ticker}: {resultado}")

    except Exception as e:
        import traceback
        print(f"ERRO: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
