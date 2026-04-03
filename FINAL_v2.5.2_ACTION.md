# MISSÃO FINAL v2.5.2 — Limpeza do AtivoView

Este é o plano de ação final para consolidar o layout Delta Chaos v2.5.2.

## 1. OBJETIVO
Remover redundâncias e botões manuais do componente de detalhe do ativo.

## 2. ARQUIVO ALVO
`atlas_ui/src/components/AtivoView.jsx`

## 3. MUDANÇAS EXIGIDAS
- **Remover sub-abas:** Excluir "ORQUESTRADOR" e "MANUTENÇÃO" da lista de sub-abas internas do Ativo.
- **Manter apenas:** [ ORBIT ] [ REFLECT ] [ CICLOS ] [ ANALYTICS ].
- **Limpeza de UI:** Remover todos os botões de execução individual de tarefas (`RUN GATE`, `RUN TUNE`, `RUN ORBIT`, `RUN EOD`). Operações isoladas agora pertencerão ao Terminal v2.6.
- **Preservar Lógica:** Garantir que o `activeTicker` continue fluindo corretamente para as abas restantes.

---
*Assinado: Inspetor Antigravity via Board Delta Chaos*
*Comando para IA Executora (MiniMax):* Execute estas mudanças de forma cirúrgica.
