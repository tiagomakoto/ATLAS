import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

const ModeToggle = () => {
  const [mode, setMode] = useState('observe');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/mode`)
      .then(res => res.json())
      .then(data => setMode(data.mode))
      .catch(err => setError('Falha ao carregar modo'));
  }, []);

  const toggleMode = async () => {
    const newMode = mode === 'observe' ? 'live' : 'observe';
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: newMode })
      });

      if (!res.ok) throw new Error(await res.text());
      setMode(newMode);
    } catch (err) {
      setError(`❌ ${err.message}`);
      setTimeout(() => setError(null), 5000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <button 
        onClick={toggleMode} 
        disabled={loading}
        className={`mode-toggle ${mode}`}
        style={{
          opacity: loading ? 0.7 : 1,
          cursor: loading ? 'not-allowed' : 'pointer'
        }}
      >
        {loading ? '⏳ ' : ''}
        {mode === 'live' ? '🔴 LIVE' : '👁 OBSERVE'}
      </button>

      {error && (
        <div style={{
          position: 'absolute',
          top: '100%',
          left: 0,
          marginTop: '4px',
          padding: '4px 8px',
          background: 'rgba(239, 68, 68, 0.9)',
          color: '#fff',
          fontSize: '10px',
          fontFamily: 'monospace',
          borderRadius: '2px',
          whiteSpace: 'nowrap',
          zIndex: 10
        }}>
          {error}
        </div>
      )}
    </div>
  );
};

export default ModeToggle;