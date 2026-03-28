import React from 'react';

const CycleBar = ({ cycleData }) => {
  // Defensive: se não houver dados, mostra placeholder
  if (!cycleData) {
    return (
      <div className="cycle-bar loading">
        <span>Carregando ciclo...</span>
      </div>
    );
  }

  return (
    <div className="cycle-bar">
      <span className="status">{cycleData.ativo || '---'}</span>
      <span className="regime">{cycleData.regime || '---'}</span>
      <span className="confidence">
        {cycleData.confianca !== undefined ? `${Math.round(cycleData.confianca * 100)}%` : '---'}
      </span>
      <span className="position">{cycleData.posicao || '---'}</span>
      <span className="pnl">{cycleData.pnl?.toFixed(2) || '0.00'}</span>
    </div>
  );
};

export default CycleBar;