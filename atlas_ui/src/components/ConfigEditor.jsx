import React, { useState, useEffect } from 'react';
import DiffViewer from './DiffViewer';

const API_BASE = 'http://localhost:8000';

const ConfigEditor = ({ initialConfig }) => {
  const [draft, setDraft] = useState(initialConfig || {});
  const [diff, setDiff] = useState(null);
  const [showDiff, setShowDiff] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setDraft((prev) => ({ ...prev, [name]: value }));
    if (showDiff) setShowDiff(false);
  };

  const computeDiff = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/config/diff`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: draft }),
      });
      const result = await res.json();
      setDiff(result);
      setShowDiff(true);
    } catch (err) {
      console.error('Erro ao calcular diff:', err);
      alert('Falha ao calcular diff. Verifique o backend.');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!diff || !diff.has_changes) return;
    try {
      await fetch(`${API_BASE}/config/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: draft }),
      });
      alert('Configuração salva com sucesso!');
      setShowDiff(false);
      setDiff(null);
    } catch (err) {
      console.error('Erro ao salvar:', err);
    }
  };

  return (
    <div className="config-editor">
      <h2>Editor de Configuração</h2>
      
      <div className="form-group">
        <label>Take Profit:</label>
        <input
          name="take_profit"
          value={draft.take_profit || ''}
          onChange={handleChange}
          type="number"
          step="0.01"
        />
      </div>

      <div className="form-group">
        <label>Stop Loss:</label>
        <input
          name="stop_loss"
          value={draft.stop_loss || ''}
          onChange={handleChange}
          type="number"
          step="0.01"
        />
      </div>

      <div className="actions">
        <button onClick={computeDiff} disabled={loading}>
          {loading ? 'Calculando...' : 'Ver Diff'}
        </button>
        
        <button 
          onClick={handleSave} 
          disabled={!showDiff || !diff?.has_changes}
          className={(!showDiff || !diff?.has_changes) ? 'disabled' : 'primary'}
        >
          Salvar Configuração
        </button>
      </div>

      {showDiff && diff && (
        <div className="diff-container">
          <h3>Mudanças Detectadas</h3>
          <DiffViewer diff={diff} />
        </div>
      )}
    </div>
  );
};

export default ConfigEditor;