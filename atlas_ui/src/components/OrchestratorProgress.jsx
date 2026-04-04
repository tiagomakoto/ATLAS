// atlas_ui/src/components/OrchestratorProgress.jsx
import React from 'react';

export default function OrchestratorProgress({ progresso, cicloNovo, ativoAtual }) {
  // Segmentos dinâmicos conforme SPEC v2.6
  const segmentosDiarios = [
    { id: "v0", label: "V0" },
    { id: "reflect_daily", label: "reflect_daily" },
    { id: "posicao_gate", label: "posição/gate_eod" },
    { id: "fim", label: "fim" }
  ];

  const segmentosMensais = [
    { id: "v0", label: "V0" },
    { id: "reflect_daily", label: "reflect_daily" },
    { id: "orbit", label: "ORBIT" },
    { id: "reflect_cycle", label: "reflect_cycle" },
    { id: "backtest_gate", label: "backtest_gate" },
    { id: "tune", label: "TUNE?" },
    { id: "posicao_gate", label: "posição/gate_eod" },
    { id: "fim", label: "fim" }
  ];

  const segmentos = cicloNovo ? segmentosMensais : segmentosDiarios;

  // Se tem progresso legacy (v2.5.2), usa o formato antigo
  if (progresso && !cicloNovo && ativoAtual === "") {
    const { tarefa_atual, total_tarefas, modulo, porcentagem } = progresso;
    const segLegacy = [1, 2, 3, 4];

    return (
      <div style={{
        padding: '12px 14px',
        background: 'var(--atlas-surface)',
        border: '1px solid var(--atlas-border)',
        borderRadius: 2,
        fontFamily: 'monospace',
        fontSize: 10
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: 8,
          color: 'var(--atlas-text-primary)'
        }}>
          <span>Tarefa {tarefa_atual}/{total_tarefas}: Verificando {modulo}</span>
          <span style={{ color: 'var(--atlas-blue)' }}>{porcentagem}%</span>
        </div>

        <div style={{
          height: 6,
          background: 'var(--atlas-bg)',
          borderRadius: 1,
          overflow: 'hidden',
          marginBottom: 10,
          display: 'flex'
        }}>
          <div style={{
            width: `${porcentagem}%`,
            background: 'var(--atlas-blue)',
            transition: 'width 0.3s ease'
          }} />
        </div>

        <div style={{ display: 'flex', gap: 6 }}>
          {segLegacy.map(s => (
            <div
              key={s}
              style={{
                height: 2,
                flex: 1,
                background: s <= tarefa_atual ? 'var(--atlas-blue)' : 'var(--atlas-border)',
                opacity: s === tarefa_atual ? 1 : 0.4
              }}
            />
          ))}
        </div>
      </div>
    );
  }

  // Novo formato v2.6 — segmentos nomeados
  return (
    <div style={{
      padding: '12px 14px',
      background: 'var(--atlas-surface)',
      border: '1px solid var(--atlas-border)',
      borderRadius: 2,
      fontFamily: 'monospace',
      fontSize: 10
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        marginBottom: 8,
        color: 'var(--atlas-text-primary)'
      }}>
        <span>
          {cicloNovo ? "Ciclo mensal" : "Fluxo diário"}
          {ativoAtual ? ` — ${ativoAtual}` : ""}
        </span>
        {progresso?.porcentagem && (
          <span style={{ color: 'var(--atlas-blue)' }}>{progresso.porcentagem}%</span>
        )}
      </div>

      {/* Barra de Progresso Principal */}
      {progresso?.porcentagem && (
        <div style={{
          height: 6,
          background: 'var(--atlas-bg)',
          borderRadius: 1,
          overflow: 'hidden',
          marginBottom: 10,
          display: 'flex'
        }}>
          <div style={{
            width: `${progresso.porcentagem}%`,
            background: 'var(--atlas-blue)',
            transition: 'width 0.3s ease'
          }} />
        </div>
      )}

      {/* Segmentos nomeados */}
      <div style={{ display: 'flex', gap: 6 }}>
        {segmentos.map((seg, i) => {
          // Determina estado do segmento baseado no ativoAtual
          const tickers = Object.keys(progresso?.digestPorAtivo || {});
          const idxAtual = tickers.indexOf(ativoAtual);
          const concluido = idxAtual > i;
          const ativo = tickers[idxAtual] === ativoAtual;

          return (
            <div
              key={seg.id}
              title={seg.label}
              style={{
                height: 2,
                flex: 1,
                background: concluido
                  ? 'var(--atlas-green)'
                  : ativo
                    ? 'var(--atlas-blue)'
                    : 'var(--atlas-border)',
                opacity: ativo ? 1 : 0.4,
                transition: 'background 0.3s ease'
              }}
            />
          );
        })}
      </div>

      {/* Labels dos segmentos */}
      <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
        {segmentos.map((seg, i) => {
          const tickers = Object.keys(progresso?.digestPorAtivo || {});
          const idxAtual = tickers.indexOf(ativoAtual);
          const concluido = idxAtual > i;
          const ativo = tickers[idxAtual] === ativoAtual;

          return (
            <div
              key={seg.id}
              style={{
                flex: 1,
                fontSize: 7,
                color: concluido
                  ? 'var(--atlas-green)'
                  : ativo
                    ? 'var(--atlas-blue)'
                    : 'var(--atlas-text-secondary)',
                textAlign: 'center',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}
            >
              {concluido ? "✓" : ""}{seg.label}
            </div>
          );
        })}
      </div>
    </div>
  );
}
