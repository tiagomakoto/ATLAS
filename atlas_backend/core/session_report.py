from datetime import datetime
from core.audit_logger import load_audit_log


def generate_report(state: dict, analytics: dict, staleness_seconds: int = 0):
    now = datetime.utcnow().isoformat()
    audit = load_audit_log(n=50)
    lines = []

    # CABEÇALHO
    lines.append("# Relatório de Sessão ATLAS")
    lines.append(f"Data/hora: {now}")
    lines.append("")

    # SEÇÃO 1 — RESUMO OPERACIONAL
    lines.append("## 1. Resumo Operacional")
    regime = state.get("regime") or {}
    lines.append(f"- Ativo monitorado: {state.get('cycle', {}).get('ativo', 'N/D')}")
    lines.append(f"- Regime classificado (ORBIT): "
                 f"{regime.get('regime', 'N/D')} — "
                 f"{regime.get('confidence', 'N/D')}")
    lines.append(f"- Saúde do sistema: {state.get('health', 'N/D')}")
    lines.append(f"- Posição aberta: "
                 f"{'Sim' if state.get('cycle', {}).get('posicao') else 'Não'}")
    lines.append(f"- P&L do ciclo: {state.get('cycle', {}).get('pnl', 'N/D')}")
    lines.append("")

    # SEÇÃO 2 — AÇÕES EXECUTADAS
    lines.append("## 2. Ações Executadas pelo Operador")
    acoes = [e for e in audit if e.get("action") in
             ("config_update", "mode_change", "terminal_log")]
    if acoes:
        for e in acoes:
            ts = e.get("timestamp", "")[:19]
            action = e.get("action", "")
            payload = e.get("payload", {})
            lines.append(f"- {ts} | {action} | {payload}")
    else:
        lines.append("- Nenhuma ação registrada nesta sessão.")
    lines.append("")

    # SEÇÃO 3 — REJEIÇÕES DO GATE
    lines.append("## 3. Rejeições do GATE")
    rejeicoes = [e for e in audit if e.get("action") == "terminal_log"
                 and "GATE REJECTED" in str(e.get("payload", {}))]
    if rejeicoes:
        for e in rejeicoes:
            ts = e.get("timestamp", "")[:19]
            msg = e.get("payload", {}).get("message", "")
            lines.append(f"- {ts} | {msg}")
    else:
        lines.append("- Nenhuma rejeição registrada nesta sessão.")
    lines.append("")

    # SEÇÃO 4 — ERROS E EXCEÇÕES
    lines.append("## 4. Erros e Exceções")
    erros = [e for e in audit if e.get("action") == "terminal_error"]
    if erros:
        for e in erros:
            ts = e.get("timestamp", "")[:19]
            error = e.get("payload", {}).get("error", "")
            tb_lines = e.get("payload", {}).get("traceback", "").split("\n")
            tb_resumido = " | ".join(l for l in tb_lines if l.strip())[:200]
            lines.append(f"- {ts} | {error}")
            if tb_resumido:
                lines.append(f"  traceback: {tb_resumido}")
    else:
        lines.append("- Nenhum erro registrado nesta sessão.")
    lines.append("")

    # SEÇÃO 5 — PARÂMETROS ALTERADOS
    lines.append("## 5. Parâmetros Alterados")
    alteracoes = [e for e in audit if e.get("action") == "config_update"]
    if alteracoes:
        for e in alteracoes:
            ts = e.get("timestamp", "")[:19]
            diff = e.get("payload", {})
            lines.append(f"- {ts} | config_update | {diff}")
    else:
        lines.append("- Nenhuma alteração de parâmetro registrada.")
    lines.append("")

    # SEÇÃO 6 — CONTEXTO ESTATÍSTICO
    lines.append("## 6. Contexto Estatístico")

    wf = analytics.get("walkForward")
    if wf and wf.get("series"):
        last = wf["series"][-1]
        ir = last.get("ir_mean", 0.0)
        ci_l = last.get("ci_lower", 0.0)
        ci_u = last.get("ci_upper", 0.0)
        n = last.get("n", "N/D")
        lines.append(f"- IR vigente: {ir:.4f} ± IC95% [{ci_l:.4f}, {ci_u:.4f}] (N={n})")
    else:
        lines.append("- IR vigente: dados não disponíveis")

    staleness_min = int(staleness_seconds / 60)
    if staleness_min < 30:
        staleness_label = "🟢 atualizado"
    elif staleness_min < 90:
        staleness_label = "🟡 atenção"
    else:
        staleness_label = "🔴 desatualizado"

    lines.append(f"- Staleness da calibração: {staleness_min}min — {staleness_label}")

    dist = analytics.get("distribution")
    if dist:
        lines.append(f"- Amostra de retornos: N={dist.get('n', 'N/D')}")

    tails = analytics.get("fatTails")
    if tails:
        lines.append(f"- Kurtosis: {tails.get('kurtosis', 0.0):.2f}")
        lines.append(f"- P1%: {tails.get('p1', 0.0):.4f} | P99%: {tails.get('p99', 0.0):.4f}")

    lines.append("")
    lines.append("---")
    lines.append("*Relatório gerado pelo ATLAS — sistema quantitativo Delta Chaos*")
    lines.append("*Destinatário: análise externa — não requer acesso ao sistema para leitura*")

    return "\n".join(lines)