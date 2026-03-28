import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

const ModeToggle = () => {
  const [mode, setMode] = useState('observation'); // observation | execution

  useEffect(() => {
    // Busca modo atual ao carregar
    fetch(`${API_BASE}/mode`)
      .then(res => res.json())
      .then(data => setMode(data.mode))
      .catch(err => console.error('Erro ao fetch mode:', err));
  }, []);

  const toggleMode = async () => {
    const newMode = mode === 'observation' ? 'execution' : 'observation';
    try {
      await fetch(`${API_BASE}/mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: newMode }),
      });
      setMode(newMode);
    } catch (err) {
      console.error('Erro ao alterar modo:', err);
    }
  };

  return (
    <button onClick={toggleMode} className={`mode-toggle ${mode}`}>
      {mode === 'execution' ? '🔴 EXECUÇÃO' : '🟢 OBSERVAÇÃO'}
    </button>
  );
};

export default ModeToggle;