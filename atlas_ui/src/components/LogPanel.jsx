import React, { useState, useEffect, useRef } from 'react';

const LogPanel = () => {
    const [logs, setLogs] = useState([]);
    const [status, setStatus] = useState('Conectando...');
    const logsEndRef = useRef(null);
    const wsRef = useRef(null);

    useEffect(() => {
        const ws = new WebSocket('ws://localhost:8000/ws/logs');
        wsRef.current = ws;

        ws.onopen = () => setStatus('Online');
        ws.onclose = () => setStatus('Offline');
        ws.onerror = () => setStatus('Offline');

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'terminal_log') {
                    setLogs((prev) => [...prev, data]);
                }
            } catch (e) {
                console.error('Failed to parse log message', e);
            }
        };

        return () => {
            ws.close();
        };
    }, []);

    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    const clearLogs = () => setLogs([]);

    const getLevelColor = (level) => {
        switch (level?.toUpperCase()) {
            case 'DEBUG': return 'var(--atlas-gray, #6b7280)';
            case 'INFO': return 'var(--atlas-green, #22c55e)';
            case 'WARN': return 'var(--atlas-amber, #f59e0b)';
            case 'ERROR': return 'var(--atlas-red, #ef4444)';
            default: return '#9ca3af';
        }
    };

    return (
        <div style={{ backgroundColor: '#020617', color: '#e2e8f0', fontFamily: 'monospace', padding: '1rem', borderRadius: '8px', marginTop: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', borderBottom: '1px solid #1e293b', paddingBottom: '0.5rem' }}>
                <span>Status: <strong style={{ color: status === 'Online' ? 'var(--atlas-green, #22c55e)' : status === 'Offline' ? 'var(--atlas-red, #ef4444)' : '#f59e0b' }}>{status}</strong></span>
                <button onClick={clearLogs} style={{ background: '#1e293b', color: '#e2e8f0', border: '1px solid #334155', padding: '4px 8px', cursor: 'pointer', borderRadius: '4px', fontSize: '0.8rem' }}>Clear</button>
            </div>
            <div style={{ height: '300px', overflowY: 'auto', fontSize: '0.85rem', lineHeight: '1.5' }}>
                {logs.map((log, idx) => (
                    <div key={idx} style={{ color: getLevelColor(log.level), whiteSpace: 'pre-wrap' }}>
                        [{log.level?.toUpperCase()}] {log.message}
                    </div>
                ))}
                <div ref={logsEndRef} />
            </div>
        </div>
    );
};

export default LogPanel;