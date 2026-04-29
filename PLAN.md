BLOCO 1 — PARA APROVAÇÃO (LINGUAGEM DE NEGÓCIO)

O que muda para o usuário:
- O sistema agora irá registrar no log quando houver ciclos duplicados sendo processados pelo ORBIT, ajudando a identificar por que alguns meses parecem ser processados duas vezes.
- Não haverá mudança no comportamento de processamento: os ciclos continuarão sendo processados da mesma forma, incluindo o comportamento atual de ignorar meses antes do primeiro ciclo existente no cache (bootstrap).

O que muda no comportamento do sistema:
- Será adicionado um aviso no log sempre que a lista de ciclos a serem processados contiver duplicatas.
- Isso não afeta o resultado final, apenas fornece visibilidade para depuração.

Efeitos visíveis ou perceptíveis:
- Nos logs do terminal, aparecerá uma mensagem como "ORBIT: ciclos duplicados detectados e removidos: ['2023-05', '2023-05']" sempre que houver duplicatas na lista de ciclos a serem processados.
- Não haverá impacto na performance ou na geração de regimes.

Se houver impacto em contrato/interface:
- Não há alteração em interfaces ou contratos. A mudança é apenas interna de logging.

BLOCO 2 — PARA O BUILD (TÉCNICO)

TAREFA 1
Arquivo : C:\Users\tiago\OneDrive\Documentos\ATLAS\delta_chaos\orbit.py
Ação : modificar
Escopo : método orbit_rodar, logo após a linha que define `ciclos = ciclos_faltantes` (linha 474)
Detalhe : Adicionar código para verificar duplicatas na lista `ciclos` e logar um aviso se houver alguma, mantendo a lista original (sem remover duplicatas, pois o usuário optou por não adicionar deduplication).
Constraints: 
- Não alterar o comportamento de processamento dos ciclos.
- Não remover ou modificar a lista `ciclos` (apenas ler para detectar duplicatas).
- Usar a função `emit_log` existente para registrar o aviso no nível "warning".
Depende de : nenhuma
