# ATLAS — Prompt de Integração: Delta Chaos via Subprocess

**Versão:** 2.4
**Natureza:** Integração — Delta Chaos como subprocess do ATLAS backend
**Base:** ATLAS v2.3 + prompt de migração Colab → .py v1.0
**Autorizado por:** CEO Tiago
**Redação:** Lilian Weng — Engenheira de Requisitos, Delta Chaos Board

---

## 1. CONTEXTO

O Delta Chaos foi migrado de células Colab para módulos `.py` locais.
O ATLAS agora precisa disparar essas rotinas quando o operador acionar
os endpoints correspondentes.

**Arquitetura:** o ATLAS backend chama o Delta Chaos como subprocess
assíncrono. O output do subprocess é capturado linha a linha e transmitido
via WebSocket para o terminal ATLAS em tempo real. O operador vê a execução
acontecer no terminal sem precisar de um terceiro terminal VS Code.

**Resultado esperado:**
```
Terminal 1: uvicorn atlas_backend   (porta 8000)
Terminal 2: npm run dev atlas_ui    (porta 5173)
            ↑ Delta Chaos roda como subprocess interno ao Terminal 1
```

---

## 2. PRÉ-REQUISITOS — VERIFICAR ANTES DE IMPLEMENTAR

### 2.1 `paths.json`

O arquivo `atlas_backend/config/paths.json` deve conter os seis campos:

```json
{
  "config_dir":       "G:\\Meu Drive\\Delta Chaos\\ativos",
  "ohlcv_dir":        "G:\\Meu Drive\\Delta Chaos\\TAPE\\ohlcv",
  "history_dir":      "G:\\Meu Drive\\Delta Chaos\\history",
  "book_dir":         "G:\\Meu Drive\\Delta Chaos\\BOOK",
  "delta_chaos_base": "G:\\Meu Drive\\Delta Chaos",
  "delta_chaos_dir":  "G:\\Meu Drive\\Delta Chaos\\delta_chaos"
}
```

Se `delta_chaos_base` ou `delta_chaos_dir` estiverem ausentes, o endpoint
retorna HTTP 503 com mensagem explícita — não tenta adivinhar o caminho.

### 2.2 `requirements.txt`

O `atlas_backend/requirements.txt` deve incluir todas as dependências
do Delta Chaos. Verificar se estão instaladas no ambiente do uvicorn:

```
yfinance>=0.2.36
scipy>=1.12.0
tqdm>=4.66.0
openpyxl>=3.1.0
pyarrow>=14.0.0
```

### 2.3 `edge.py` com argparse

O `edge.py` do Delta Chaos deve ter um bloco `if __name__ == "__main__"`
com `argparse`. Ver Seção 3 — este prompt especifica exatamente o que
adicionar.

---

## 3. MODIFICAÇÃO NO `edge.py` DO DELTA CHAOS

Adicionar ao **final** de `edge.py` — não alterar nenhuma lógica existente:

```python
# ── Entrypoint CLI — chamado pelo ATLAS via subprocess ───────────
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Delta Chaos — entrypoint CLI para ATLAS")

    parser.add_argument(
        "--modo",
        choices=["eod", "eod_preview", "orbit", "tune", "gate"],
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
                    else list(range(2002, 2026)))
            edge = EDGE(
                capital=carregar_config()["book"]["capital"],
                modo="backtest",
                universo=[args.ticker]
            )
            df_tape = tape_backtest(
                ativos=[args.ticker], anos=anos, forcar=False)
            orbit = ORBIT(universo={args.ticker: tape_carregar_ativo(args.ticker)})
            orbit.rodar(df_tape, anos, modo="mensal")

        elif args.modo == "tune":
            executar_tune(args.ticker)

        elif args.modo == "gate":
            resultado = executar_gate(args.ticker)
            print(f"[GATE] {args.ticker}: {resultado}")

    except Exception as e:
        import traceback
        print(f"ERRO: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
```

**Constraint:** o bloco acima é uma adição ao final do arquivo. Nenhuma
função existente é alterada.

---

## 4. NOVO ARQUIVO — `atlas_backend/core/dc_runner.py`

Criar este arquivo. É o único ponto do ATLAS que conhece como chamar
o Delta Chaos. Todos os endpoints usam este módulo — nunca chamam
subprocess diretamente.

```python
# atlas_backend/core/dc_runner.py
"""
Executor de subprocessos do Delta Chaos.
Único ponto de integração entre ATLAS e Delta Chaos.
"""

import asyncio
import sys
from pathlib import Path
from typing import AsyncIterator, Optional

from core.paths import get_paths
from core.terminal_stream import emit_log, emit_error
from core.audit_logger import log_action


def _get_dc_script() -> Path:
    """
    Retorna o caminho para edge.py do Delta Chaos.
    Lança FileNotFoundError se paths.json não tiver delta_chaos_dir
    ou se edge.py não existir.
    """
    paths = get_paths()

    dc_dir = paths.get("delta_chaos_dir")
    if not dc_dir:
        raise FileNotFoundError(
            "Campo 'delta_chaos_dir' ausente no paths.json. "
            "Adicionar o caminho para o diretório dos módulos .py "
            "do Delta Chaos."
        )

    script = Path(dc_dir) / "edge.py"
    if not script.exists():
        raise FileNotFoundError(
            f"edge.py não encontrado em: {dc_dir}. "
            f"Verificar se a migração Colab → .py foi concluída."
        )

    return script


async def _stream_subprocess(
    args: list[str],
    cwd: Path,
    action_name: str,
    action_payload: dict
) -> dict:
    """
    Executa subprocess assíncrono e transmite output via WebSocket.
    Retorna {"status": "OK"|"ERRO", "returncode": int, "output": str}
    """
    full_output = []

    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,          # mesmo Python do uvicorn
            *args,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=None                  # herda env do processo pai
        )

        # Transmite linha a linha para o terminal ATLAS
        async for raw_line in proc.stdout:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            full_output.append(line)

            # Nível baseado no prefixo
            if line.startswith("ERRO") or line.startswith("✗"):
                emit_log(line, level="error")
            elif line.startswith("⚠") or line.startswith("~"):
                emit_log(line, level="warning")
            else:
                emit_log(line, level="info")

        await proc.wait()
        output_str = "\n".join(full_output)

        status = "OK" if proc.returncode == 0 else "ERRO"

        log_action(
            action=action_name,
            payload=action_payload,
            response={
                "status": status,
                "returncode": proc.returncode,
                "linhas": len(full_output)
            }
        )

        return {
            "status": status,
            "returncode": proc.returncode,
            "output": output_str
        }

    except Exception as e:
        emit_error(e)
        log_action(
            action=action_name,
            payload=action_payload,
            response={"status": "ERRO", "error": str(e)}
        )
        raise


async def run_eod_preview(xlsx_dir: str) -> dict:
    script = _get_dc_script()
    return await _stream_subprocess(
        args=[str(script), "--modo", "eod_preview",
              "--xlsx_dir", xlsx_dir],
        cwd=script.parent,
        action_name="dc_eod_preview",
        action_payload={"xlsx_dir": xlsx_dir}
    )


async def run_eod(xlsx_dir: str) -> dict:
    script = _get_dc_script()
    return await _stream_subprocess(
        args=[str(script), "--modo", "eod",
              "--xlsx_dir", xlsx_dir],
        cwd=script.parent,
        action_name="dc_eod_executar",
        action_payload={"xlsx_dir": xlsx_dir}
    )


async def run_orbit(ticker: str, anos: Optional[list] = None) -> dict:
    script = _get_dc_script()
    args = [str(script), "--modo", "orbit", "--ticker", ticker]
    if anos:
        args += ["--anos", ",".join(str(a) for a in anos)]
    return await _stream_subprocess(
        args=args,
        cwd=script.parent,
        action_name="dc_orbit",
        action_payload={"ticker": ticker, "anos": anos}
    )


async def run_tune(ticker: str) -> dict:
    script = _get_dc_script()
    return await _stream_subprocess(
        args=[str(script), "--modo", "tune", "--ticker", ticker],
        cwd=script.parent,
        action_name="dc_tune",
        action_payload={"ticker": ticker}
    )


async def run_gate(ticker: str) -> dict:
    script = _get_dc_script()
    return await _stream_subprocess(
        args=[str(script), "--modo", "gate", "--ticker", ticker],
        cwd=script.parent,
        action_name="dc_gate",
        action_payload={"ticker": ticker}
    )
```

---

## 5. NOVO ARQUIVO — `atlas_backend/api/routes/delta_chaos.py`

```python
# atlas_backend/api/routes/delta_chaos.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from core.dc_runner import (
    run_eod_preview, run_eod,
    run_orbit, run_tune, run_gate
)
from core.delta_chaos_reader import list_ativos
from core.paths import get_paths
from pathlib import Path

router = APIRouter(prefix="/delta-chaos", tags=["delta-chaos"])


# ── Schemas ───────────────────────────────────────────────────────

class EodPayload(BaseModel):
    xlsx_dir: Optional[str] = None
    confirm: bool = False
    description: str = ""

class TickerPayload(BaseModel):
    ticker: str
    confirm: bool = False
    description: str = ""
    anos: Optional[List[int]] = None


# ── Validações comuns ─────────────────────────────────────────────

def _validar_confirm(confirm: bool, description: str):
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="CONFIRMATION_REQUIRED — envie confirm=true"
        )
    if not description.strip():
        raise HTTPException(
            status_code=400,
            detail="DESCRIPTION_REQUIRED — descrição obrigatória"
        )

def _validar_ticker(ticker: str):
    ativos = list_ativos()
    if ticker not in ativos:
        raise HTTPException(
            status_code=404,
            detail=f"Ativo '{ticker}' não encontrado nos ativos parametrizados"
        )

def _resolver_xlsx_dir(xlsx_dir: Optional[str]) -> str:
    if xlsx_dir:
        return xlsx_dir
    paths = get_paths()
    base = paths.get("delta_chaos_base")
    if not base:
        raise HTTPException(
            status_code=503,
            detail="delta_chaos_base ausente no paths.json"
        )
    default = str(Path(base) / "opcoes_hoje")
    return default


# ── Endpoints ─────────────────────────────────────────────────────

@router.post("/eod/preview")
async def eod_preview(payload: EodPayload):
    """
    Estágio 1 — verifica quais ativos serão processados no EOD.
    Não executa nada. O operador vê o resultado e decide se avança.
    """
    xlsx_dir = _resolver_xlsx_dir(payload.xlsx_dir)
    try:
        result = await run_eod_preview(xlsx_dir=xlsx_dir)
        return {"status": result["status"], "output": result["output"]}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/eod/executar")
async def eod_executar(payload: EodPayload):
    """
    Estágio 2 — executa EOD completo para os ativos aprovados.
    Requer confirm=true e description.
    Deve ser chamado somente após /eod/preview ter sido exibido.
    """
    _validar_confirm(payload.confirm, payload.description)
    xlsx_dir = _resolver_xlsx_dir(payload.xlsx_dir)
    try:
        result = await run_eod(xlsx_dir=xlsx_dir)
        return {"status": result["status"], "output": result["output"]}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orbit")
async def orbit(payload: TickerPayload):
    """
    Roda ORBIT para o ticker informado.
    Usar quando ciclo_id do último historico[] < mês corrente.
    """
    _validar_confirm(payload.confirm, payload.description)
    _validar_ticker(payload.ticker)
    try:
        result = await run_orbit(
            ticker=payload.ticker,
            anos=payload.anos
        )
        return {"status": result["status"], "output": result["output"]}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tune")
async def tune(payload: TickerPayload):
    """
    Roda TUNE para o ticker informado.
    Usar quando staleness_days >= 126.
    Calcula e registra — não aplica automaticamente.
    """
    _validar_confirm(payload.confirm, payload.description)
    _validar_ticker(payload.ticker)
    try:
        result = await run_tune(ticker=payload.ticker)
        return {"status": result["status"], "output": result["output"]}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gate")
async def gate(payload: TickerPayload):
    """
    Roda GATE completo para o ticker informado.
    Usar quando gate_eod() retorna GATE VENCIDO.
    """
    _validar_confirm(payload.confirm, payload.description)
    _validar_ticker(payload.ticker)
    try:
        result = await run_gate(ticker=payload.ticker)
        return {
            "status": result["status"],
            "output": result["output"],
            "returncode": result["returncode"]
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 6. REGISTRAR O ROUTER EM `main.py`

Adicionar em `atlas_backend/main.py`:

```python
from api.routes import delta_chaos

app.include_router(delta_chaos.router)
```

---

## 7. MODIFICAÇÕES NO FRONTEND

### 7.1 — Seção Manutenção: botões de disparo

Em `atlas_ui/src/layouts/MainScreen.jsx`, componente `ManutencaoView`,
adicionar os botões de disparo das rotinas:

```jsx
const API_BASE = "http://localhost:8000";

const ManutencaoView = ({ activeTicker }) => {
  const [running, setRunning] = useState(null);
  const [lastOutput, setLastOutput] = useState("");

  async function disparar(endpoint, payload, label) {
    if (!window.confirm(`Confirmar: ${label}?`)) return;
    setRunning(label);
    setLastOutput("");
    try {
      const res = await fetch(`${API_BASE}/delta-chaos/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...payload,
          confirm: true,
          description: label
        })
      });
      const data = await res.json();
      setLastOutput(data.output || data.detail || "Concluído");
    } catch (err) {
      setLastOutput(`Erro: ${err.message}`);
    } finally {
      setRunning(null);
    }
  }

  // EOD com dois estágios
  async function dispararEod() {
    setRunning("EOD Preview");
    setLastOutput("");
    try {
      // Estágio 1: preview
      const prev = await fetch(`${API_BASE}/delta-chaos/eod/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      });
      const prevData = await prev.json();
      setLastOutput(prevData.output || "");
      setRunning(null);

      // Operador confirma via diálogo nativo
      if (!window.confirm(
        "Preview concluído. Ver resultado no terminal.\n\nExecutar EOD agora?"
      )) return;

      // Estágio 2: executar
      setRunning("EOD Executar");
      const exec = await fetch(`${API_BASE}/delta-chaos/eod/executar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          confirm: true,
          description: `EOD ${new Date().toISOString().slice(0, 10)}`
        })
      });
      const execData = await exec.json();
      setLastOutput(execData.output || "Concluído");
    } catch (err) {
      setLastOutput(`Erro: ${err.message}`);
    } finally {
      setRunning(null);
    }
  }

  const btnStyle = (cor) => ({
    padding: "8px 16px",
    background: running ? "var(--atlas-border)" : cor,
    border: "none",
    color: running ? "var(--atlas-text-secondary)" : "#fff",
    fontFamily: "monospace",
    fontSize: 10,
    borderRadius: 2,
    cursor: running ? "not-allowed" : "pointer",
    textTransform: "uppercase",
    letterSpacing: 1
  });

  return (
    <div style={{ fontFamily: "monospace", fontSize: 11,
                  display: "flex", flexDirection: "column", gap: 20 }}>

      {/* Rotinas Delta Chaos */}
      <section>
        <div style={{ fontSize: 9, color: "var(--atlas-text-secondary)",
                      textTransform: "uppercase", letterSpacing: 1,
                      marginBottom: 12 }}>
          Rotinas Delta Chaos
        </div>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>

          <button
            style={btnStyle("var(--atlas-blue)")}
            disabled={!!running}
            onClick={dispararEod}
          >
            {running === "EOD Preview" ? "● Preview..." :
             running === "EOD Executar" ? "● Executando..." :
             "EOD Diário"}
          </button>

          <button
            style={btnStyle("var(--atlas-green)")}
            disabled={!!running || !activeTicker}
            onClick={() => disparar(
              "orbit",
              { ticker: activeTicker },
              `ORBIT ${activeTicker}`
            )}
          >
            {running?.startsWith("ORBIT") ? "● Rodando..." : "ORBIT"}
          </button>

          <button
            style={btnStyle("var(--atlas-amber)")}
            disabled={!!running || !activeTicker}
            onClick={() => disparar(
              "tune",
              { ticker: activeTicker },
              `TUNE ${activeTicker}`
            )}
          >
            {running?.startsWith("TUNE") ? "● Calibrando..." : "TUNE"}
          </button>

          <button
            style={btnStyle("var(--atlas-text-secondary)")}
            disabled={!!running || !activeTicker}
            onClick={() => disparar(
              "gate",
              { ticker: activeTicker },
              `GATE ${activeTicker}`
            )}
          >
            {running?.startsWith("GATE") ? "● Validando..." : "GATE"}
          </button>

        </div>

        {/* Status de execução */}
        {running && (
          <div style={{ marginTop: 8, color: "var(--atlas-amber)",
                        fontSize: 10 }}>
            ● {running} em execução — acompanhe no Terminal abaixo
          </div>
        )}
      </section>

      {/* Upload EOD */}
      <section>
        <div style={{ fontSize: 9, color: "var(--atlas-text-secondary)",
                      textTransform: "uppercase", letterSpacing: 1,
                      marginBottom: 8 }}>
          Upload EOD
        </div>
        <div style={{ color: "var(--atlas-text-secondary)", fontSize: 10 }}>
          Coloque os arquivos xlsx em:<br />
          <code style={{ color: "var(--atlas-text-primary)" }}>
            G:\Meu Drive\Delta Chaos\opcoes_hoje\
          </code>
          <br />antes de disparar o EOD Diário.
        </div>
      </section>

      {/* Upload Calendário */}
      <section>
        <div style={{ fontSize: 9, color: "var(--atlas-text-secondary)",
                      textTransform: "uppercase", letterSpacing: 1,
                      marginBottom: 8 }}>
          Upload Calendário de Eventos
        </div>
        <div style={{ color: "var(--atlas-text-secondary)", fontSize: 10 }}>
          Schema: data | ticker | tipo_evento | descricao | impacto_esperado_iv
        </div>
      </section>

    </div>
  );
};
```

### 7.2 — Passar `activeTicker` para `ManutencaoView`

Em `MainScreen.jsx`, atualizar a chamada:

```jsx
{internalTab === "manutencao" && (
  <ManutencaoView activeTicker={activeTicker} />
)}
```

---

## 8. SEGURANÇA — CONSTRAINTS OBRIGATÓRIOS

### 8.1 — Validação de caminho

`dc_runner.py` nunca aceita caminho arbitrário do frontend. O `xlsx_dir`
deve estar dentro do `delta_chaos_base`:

```python
def _validar_caminho(caminho: str) -> None:
    paths = get_paths()
    base = Path(paths.get("delta_chaos_base", ""))
    try:
        Path(caminho).resolve().relative_to(base.resolve())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Caminho fora do diretório permitido: {base}"
        )
```

Adicionar esta chamada em `run_eod()` e `run_eod_preview()` antes
de passar o caminho ao subprocess.

### 8.2 — Timeout

Processos longos (ORBIT, backtest) podem durar minutos. Definir timeout
máximo de 30 minutos:

```python
try:
    await asyncio.wait_for(proc.wait(), timeout=1800)
except asyncio.TimeoutError:
    proc.kill()
    emit_log("TIMEOUT: processo encerrado após 30 minutos", level="error")
    raise HTTPException(status_code=504, detail="TIMEOUT")
```

### 8.3 — Um processo por vez

O ATLAS não permite dois processos Delta Chaos simultâneos:

```python
# Em dc_runner.py — estado global simples
_dc_running: bool = False

async def _stream_subprocess(...):
    global _dc_running
    if _dc_running:
        raise HTTPException(
            status_code=409,
            detail="CONFLICT — outra rotina Delta Chaos já está em execução"
        )
    _dc_running = True
    try:
        # ... execução ...
    finally:
        _dc_running = False
```

---

## 9. DEFINIÇÃO DE PRONTO

- [ ] `edge.py` com bloco `if __name__ == "__main__"` e argparse
      para `--modo`, `--ticker`, `--xlsx_dir`, `--anos`
- [ ] `atlas_backend/core/dc_runner.py` criado com as cinco funções
- [ ] `atlas_backend/api/routes/delta_chaos.py` criado com os quatro endpoints
- [ ] Router registrado em `main.py`
- [ ] Validação de caminho implementada em `dc_runner.py`
- [ ] Timeout de 30 minutos implementado
- [ ] Lock de processo único implementado
- [ ] Botões de disparo na seção Manutenção do frontend
- [ ] Output do subprocess transmitido via WebSocket e visível no Terminal ATLAS
- [ ] EOD com dois estágios (preview → confirmar → executar) verificável
- [ ] Teste manual: disparar GATE para VALE3 via ATLAS e ver output no terminal

**Critério de rejeição imediato:** qualquer endpoint que execute operações
no Delta Chaos sem `confirm: true`, ou qualquer subprocess que aceite
caminhos de arquivo fora do `delta_chaos_base`.

---

*Prompt redigido por Lilian Weng — Engenheira de Requisitos, Delta Chaos Board*
*Sessão: off-ata | Autorização: CEO Tiago*
*Base: ATLAS v2.3 + Delta Chaos migrado para .py*
*Pré-requisitos: paths.json atualizado + requirements.txt unificado instalado*
