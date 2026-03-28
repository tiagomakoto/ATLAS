import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

const ReadingPanel = ({ data }) => {
  const [reading, setReading] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/reading`)
      .then(res => res.json())
      .then(json => {
        setReading(json);
        setLoading(false);
      })
      .catch(err => {
        console.error('Erro ao carregar reading:', err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="reading-panel loading">Carregando...</div>;

  // Usa props data se passado, senão usa state reading
  const displayData = data || reading;
  const health = displayData?.health ?? 'N/A';
  const regime = displayData?.regime ?? 'N/A';
  const signal = displayData?.signal ?? 'N/A';

  return (
    <div className="reading-panel">
      {/* BUG-03: CycleBar REMOVIDO daqui - agora fica no header global */}
      
      <h2>Leitura de Mercado</h2>
      
      <div className="metric">
        <span>Health:</span>
        <strong className={health === 'ok' ? 'ok' : 'warn'}>{health}</strong>
      </div>
      
      <div className="metric">
        <span>Regime:</span>
        <strong>{regime}</strong>
      </div>
      
      <div className="metric">
        <span>Signal:</span>
        <strong>{signal}</strong>
      </div>
    </div>
  );
};

export default ReadingPanel;