// atlas_ui/src/components/OrchestratorProgress.jsx
import React from 'react';

export default function OrchestratorProgress({ progresso }) {
  if (!progresso) return null;

  const { tarefa_atual, total_tarefas, modulo, porcentagem } = progresso;

  // Calcula os segmentos da barra (um visual mais "Delta Chaos")
  const segmentos = [1, 2, 3, 4];

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

      {/* Barra de Progresso Principal */}
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

      {/* Segmentos por Tarefa */}
      <div style={{ display: 'flex', gap: 6 }}>
        {segmentos.map(s => (
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
