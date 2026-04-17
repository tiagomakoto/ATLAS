// atlas_ui/src/components/GestaoView/__tests__/CalibracaoDrawer.test.jsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import CalibracaoDrawer from '../CalibracaoDrawer';

// Mock do hook useWebSocket
jest.mock('../../hooks/useWebSocket', () => jest.fn());

describe('CalibracaoDrawer', () => {
  const mockOnClose = jest.fn();
  const mockUseWebSocket = require('../../hooks/useWebSocket');

  beforeEach(() => {
    mockUseWebSocket.mockClear();
    mockOnClose.mockClear();
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('deve inicializar sem progresso de indexação', () => {
    mockUseWebSocket.mockImplementation((url, callback) => {
      // Simula conexão WebSocket
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);
    
    // Verifica que os estados iniciais estão corretos
    expect(screen.queryByText(/Indexando dias:/)).not.toBeInTheDocument();
    expect(screen.queryByText(/dias indexados/)).not.toBeInTheDocument();
    expect(screen.getByText(/Integridade de dados/)).toBeInTheDocument();
  });

  it('deve capturar e exibir progresso da indexação de dias com vírgulas', async () => {
    let wsCallback = null;
    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);
    
    // Simula evento de terminal_log com progresso de indexação (com vírgulas)
    const indexEvent = {
      type: "terminal_log",
      data: {
        message: "TUNE [PETR4] indexando dias: 1,500/6,004 (25%)",
        level: "info"
      }
    };
    
    // Chama o handler de mensagem WebSocket
    wsCallback(indexEvent);
    
    // Verifica que o progresso foi atualizado
    await waitFor(() => {
      expect(screen.getByText(/Indexando dias: 1,500 / 6,004/)).toBeInTheDocument();
      expect(screen.getByText(/25%/)).toBeInTheDocument();
    });
    
    // Verifica que o sub-título mudou para "Indexação"
    expect(screen.getByText(/Indexação/)).toBeInTheDocument();
  });

  it('deve exibir texto de conclusão da indexação após pré-cômputo concluído', async () => {
    let wsCallback = null;
    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);
    
    // Primeiro, simula o progresso de indexação
    const indexEvent = {
      type: "terminal_log",
      data: {
        message: "TUNE [PETR4] indexando dias: 6,004/6,004 (100%)",
        level: "info"
      }
    };
    wsCallback(indexEvent);
    
    // Depois, simula a conclusão da indexação
    const completeEvent = {
      type: "terminal_log",
      data: {
        message: "pré-cômputo concluído",
        level: "info"
      }
    };
    wsCallback(completeEvent);
    
    // Verifica que o texto de conclusão foi exibido
    await waitFor(() => {
      expect(screen.getByText(/6,004 dias indexados/)).toBeInTheDocument();
      expect(screen.queryByText(/Indexando dias:/)).not.toBeInTheDocument();
    });
    
    // Verifica que o sub-título mudou para "Otimização"
    expect(screen.getByText(/Otimização/)).toBeInTheDocument();
  });

  it('deve resetar progresso de indexação quando step 2 inicia', async () => {
    let wsCallback = null;
    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);
    
    // Simula progresso de indexação
    const indexEvent = {
      type: "terminal_log",
      data: {
        message: "TUNE [PETR4] indexando dias: 1,500/6,004 (25%)",
        level: "info"
      }
    };
    wsCallback(indexEvent);
    
    // Verifica que o progresso foi exibido
    await waitFor(() => {
      expect(screen.getByText(/Indexando dias: 1,500 / 6,004/)).toBeInTheDocument();
    });
    
    // Simula início do step 2 (TUNE)
    const tuneStartEvent = {
      type: "dc_module_start",
      data: {
        modulo: "TUNE",
        timestamp: new Date().toISOString()
      }
    };
    wsCallback(tuneStartEvent);
    
    // Verifica que o progresso foi resetado
    await waitFor(() => {
      expect(screen.queryByText(/Indexando dias:/)).not.toBeInTheDocument();
      expect(screen.queryByText(/dias indexados/)).not.toBeInTheDocument();
    });
    
    // Verifica que o sub-título mudou para "Integridade de dados" (resetado)
    expect(screen.getByText(/Integridade de dados/)).toBeInTheDocument();
  });

  it('deve exibir barra de trials após conclusão da indexação', async () => {
    let wsCallback = null;
    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);
    
    // Simula progresso de indexação
    const indexEvent = {
      type: "terminal_log",
      data: {
        message: "TUNE [PETR4] indexando dias: 6,004/6,004 (100%)",
        level: "info"
      }
    };
    wsCallback(indexEvent);
    
    // Simula conclusão da indexação
    const completeEvent = {
      type: "terminal_log",
      data: {
        message: "pré-cômputo concluído",
        level: "info"
      }
    };
    wsCallback(completeEvent);
    
    // Simula progresso de trials
    const tuneProgressEvent = {
      type: "dc_tune_progress",
      data: {
        trial: 50,
        total: 200,
        ir: 1.2345
      }
    };
    wsCallback(tuneProgressEvent);
    
    // Verifica que a barra de trials foi exibida
    await waitFor(() => {
      expect(screen.getByText(/50 / 200 trials/)).toBeInTheDocument();
      expect(screen.getByText(/IR: 1.2345/)).toBeInTheDocument();
    });
    
    // Verifica que o sub-título é "Otimização"
    expect(screen.getByText(/Otimização/)).toBeInTheDocument();
  });

  it('deve iniciar com todos os steps em status idle', () => {
    mockUseWebSocket.mockImplementation((url, callback) => {
      // Simula conexão WebSocket
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);
    
    // Verificar que o estado inicial é "idle" para todos os steps
    const step1 = screen.getByText(/PENDENTE/i);
    const step2 = screen.getByText(/PENDENTE/i);
    const step3 = screen.getByText(/PENDENTE/i);

    expect(step1).toBeInTheDocument();
    expect(step2).toBeInTheDocument();
    expect(step3).toBeInTheDocument();
    
    // Verifica que o sub-título inicial é "Integridade de dados"
    expect(screen.getByText(/Integridade de dados/)).toBeInTheDocument();
  });

  it('não deve atualizar estado manualmente ao iniciar calibração com sucesso', async () => {
    mockUseWebSocket.mockImplementation((url, callback) => {
      // Simula conexão WebSocket
      return null;
    });

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'started', step: 1 })
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

// Encontrar e clicar no botão "Iniciar Calibração"
  const iniciarButton = screen.getByText(/Iniciar Calibração/i);
    fireEvent.click(iniciarButton);

    // Aguardar a chamada fetch
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/delta-chaos/calibracao/iniciar',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
      );
    });

    // Verificar que o estado NÃO foi atualizado manualmente para "running"
    // (O estado deve permanecer "idle" até que o evento WebSocket chegue)
    const step1 = screen.getByText(/PENDENTE/i);
    expect(step1).toBeInTheDocument();
    
    // Verifica que o sub-título é "Integridade de dados"
    expect(screen.getByText(/Integridade de dados/)).toBeInTheDocument();
  });

  it('deve atualizar estado ao receber evento dc_module_start', () => {
    let wsCallback = null;
    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    // Simular evento dc_module_start para ORBIT
    const evento = {
      type: 'dc_module_start',
      data: {
        modulo: 'ORBIT',
        timestamp: '2024-01-01T12:00:00Z'
      }
    };

    wsCallback(evento);

    // Verificar que o step 1 agora está como "EXECUTANDO"
    const step1 = screen.getByText(/EXECUTANDO/i);
    expect(step1).toBeInTheDocument();
    
    // Verifica que o sub-título mudou para "Integridade de dados"
    expect(screen.getByText(/Integridade de dados/)).toBeInTheDocument();
  });

  it('deve atualizar estado ao receber evento dc_module_complete', () => {
    let wsCallback = null;
    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    // Primeiro, iniciar o step
    const startEvento = {
      type: 'dc_module_start',
      data: {
        modulo: 'ORBIT',
        timestamp: '2024-01-01T12:00:00Z'
      }
    };
    wsCallback(startEvento);

    // Depois, completar com sucesso
    const completeEvento = {
      type: 'dc_module_complete',
      data: {
        modulo: 'ORBIT',
        status: 'ok',
        timestamp: '2024-01-01T12:05:00Z'
      }
    };
    wsCallback(completeEvento);

    // Verificar que o step 1 agora está como "CONCLUÍDO"
    const step1 = screen.getByText(/CONCLUÍDO/i);
    expect(step1).toBeInTheDocument();
    
    // Verifica que o sub-título é "Integridade de dados"
    expect(screen.getByText(/Integridade de dados/)).toBeInTheDocument();
  });

  it('deve usar URL dinâmica para WebSocket', () => {
    // Mock window.location
    const originalLocation = window.location;
    delete window.location;
    window.location = {
      hostname: 'localhost',
      port: '3000'
    };

    mockUseWebSocket.mockImplementation((url, callback) => {
      expect(url).toBe('ws://localhost:3000/ws/events');
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    // Restaurar window.location
    window.location = originalLocation;
  });

  it('deve usar porta padrão 8000 quando não houver porta definida', () => {
    // Mock window.location sem porta
    const originalLocation = window.location;
    delete window.location;
    window.location = {
      hostname: 'localhost',
      port: ''
    };

    mockUseWebSocket.mockImplementation((url, callback) => {
      expect(url).toBe('ws://localhost:8000/ws/events');
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

// Restaurar window.location
  window.location = originalLocation;
});

it('deve atualizar estado para error quando fetch falhar', async () => {
  mockUseWebSocket.mockImplementation((url, callback) => {
    return null;
  });

  global.fetch.mockResolvedValueOnce({
    ok: false,
    statusText: 'Internal Server Error'
  });

  render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

  const iniciarButton = screen.getByText(/Iniciar Calibração/i);
  fireEvent.click(iniciarButton);

  await waitFor(() => {
    // Verificar que o estado foi atualizado para "error"
    const step1 = screen.getByText(/ERRO/i);
    expect(step1).toBeInTheDocument();
  });
    
    // Verifica que o sub-título é "Integridade de dados"
    expect(screen.getByText(/Integridade de dados/)).toBeInTheDocument();
  });

  it('deve logar eventos recebidos no console', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    let wsCallback = null;

    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    const evento = {
      type: 'dc_module_start',
      data: {
        modulo: 'ORBIT',
        timestamp: '2024-01-01T12:00:00Z'
      }
    };

    wsCallback(evento);

    expect(consoleSpy).toHaveBeenCalledWith(
      '[CALIBRACAO] Evento recebido:',
      'dc_module_start',
      evento.data
    );

    consoleSpy.mockRestore();
  });
});

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('deve inicializar sem progresso de indexação', () => {
    mockUseWebSocket.mockImplementation((url, callback) => {
      // Simula conexão WebSocket
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);
    
    // Verifica que os estados iniciais estão corretos
    expect(screen.queryByText(/Indexando dias:/)).not.toBeInTheDocument();
    expect(screen.queryByText(/dias indexados/)).not.toBeInTheDocument();
  });

  it('deve capturar e exibir progresso da indexação de dias', async () => {
    let wsCallback = null;
    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);
    
    // Simula evento de terminal_log com progresso de indexação
    const indexEvent = {
      type: "terminal_log",
      data: {
        message: "TUNE [PETR4] indexando dias: 1500/6000 (25%)",
        level: "info"
      }
    };
    
    // Chama o handler de mensagem WebSocket
    wsCallback(indexEvent);
    
    // Verifica que o progresso foi atualizado
    await waitFor(() => {
      expect(screen.getByText(/Indexando dias: 1500 / 6000/)).toBeInTheDocument();
      expect(screen.getByText(/25%/)).toBeInTheDocument();
    });
  });

  it('deve exibir texto de conclusão da indexação após pré-cômputo concluído', async () => {
    let wsCallback = null;
    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);
    
    // Primeiro, simula o progresso de indexação
    const indexEvent = {
      type: "terminal_log",
      data: {
        message: "TUNE [PETR4] indexando dias: 6000/6000 (100%)",
        level: "info"
      }
    };
    wsCallback(indexEvent);
    
    // Depois, simula a conclusão da indexação
    const completeEvent = {
      type: "terminal_log",
      data: {
        message: "pré-cômputo concluído",
        level: "info"
      }
    };
    wsCallback(completeEvent);
    
    // Verifica que o texto de conclusão foi exibido
    await waitFor(() => {
      expect(screen.getByText(/6000 dias indexados/)).toBeInTheDocument();
      expect(screen.queryByText(/Indexando dias:/)).not.toBeInTheDocument();
    });
  });

  it('deve resetar progresso de indexação quando step 2 inicia', async () => {
    let wsCallback = null;
    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);
    
    // Simula progresso de indexação
    const indexEvent = {
      type: "terminal_log",
      data: {
        message: "TUNE [PETR4] indexando dias: 1500/6000 (25%)",
        level: "info"
      }
    };
    wsCallback(indexEvent);
    
    // Verifica que o progresso foi exibido
    await waitFor(() => {
      expect(screen.getByText(/Indexando dias: 1500 / 6000/)).toBeInTheDocument();
    });
    
    // Simula início do step 2 (TUNE)
    const tuneStartEvent = {
      type: "dc_module_start",
      data: {
        modulo: "TUNE",
        timestamp: new Date().toISOString()
      }
    };
    wsCallback(tuneStartEvent);
    
    // Verifica que o progresso foi resetado
    await waitFor(() => {
      expect(screen.queryByText(/Indexando dias:/)).not.toBeInTheDocument();
      expect(screen.queryByText(/dias indexados/)).not.toBeInTheDocument();
    });
  });

  it('deve exibir barra de trials após conclusão da indexação', async () => {
    let wsCallback = null;
    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);
    
    // Simula progresso de indexação
    const indexEvent = {
      type: "terminal_log",
      data: {
        message: "TUNE [PETR4] indexando dias: 6000/6000 (100%)",
        level: "info"
      }
    };
    wsCallback(indexEvent);
    
    // Simula conclusão da indexação
    const completeEvent = {
      type: "terminal_log",
      data: {
        message: "pré-cômputo concluído",
        level: "info"
      }
    };
    wsCallback(completeEvent);
    
    // Simula progresso de trials
    const tuneProgressEvent = {
      type: "dc_tune_progress",
      data: {
        trial: 50,
        total: 200,
        ir: 1.2345
      }
    };
    wsCallback(tuneProgressEvent);
    
    // Verifica que a barra de trials foi exibida
    await waitFor(() => {
      expect(screen.getByText(/50 / 200 trials/)).toBeInTheDocument();
      expect(screen.getByText(/IR: 1.2345/)).toBeInTheDocument();
    });
  });

  it('deve iniciar com todos os steps em status idle', () => {
    mockUseWebSocket.mockImplementation((url, callback) => {
      // Simula conexão WebSocket
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);
    
    // Verificar que o estado inicial é "idle" para todos os steps
    const step1 = screen.getByText(/PENDENTE/i);
    const step2 = screen.getByText(/PENDENTE/i);
    const step3 = screen.getByText(/PENDENTE/i);

    expect(step1).toBeInTheDocument();
    expect(step2).toBeInTheDocument();
    expect(step3).toBeInTheDocument();
  });

  it('não deve atualizar estado manualmente ao iniciar calibração com sucesso', async () => {
    mockUseWebSocket.mockImplementation((url, callback) => {
      // Simula conexão WebSocket
      return null;
    });

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'started', step: 1 })
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

// Encontrar e clicar no botão "Iniciar Calibração"
  const iniciarButton = screen.getByText(/Iniciar Calibração/i);
    fireEvent.click(iniciarButton);

    // Aguardar a chamada fetch
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/delta-chaos/calibracao/iniciar',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
      );
    });

    // Verificar que o estado NÃO foi atualizado manualmente para "running"
    // (O estado deve permanecer "idle" até que o evento WebSocket chegue)
    const step1 = screen.getByText(/PENDENTE/i);
    expect(step1).toBeInTheDocument();
  });

  it('deve atualizar estado ao receber evento dc_module_start', () => {
    let wsCallback = null;
    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    // Simular evento dc_module_start para ORBIT
    const evento = {
      type: 'dc_module_start',
      data: {
        modulo: 'ORBIT',
        timestamp: '2024-01-01T12:00:00Z'
      }
    };

    wsCallback(evento);

    // Verificar que o step 1 agora está como "EXECUTANDO"
    const step1 = screen.getByText(/EXECUTANDO/i);
    expect(step1).toBeInTheDocument();
  });

  it('deve atualizar estado ao receber evento dc_module_complete', () => {
    let wsCallback = null;
    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    // Primeiro, iniciar o step
    const startEvento = {
      type: 'dc_module_start',
      data: {
        modulo: 'ORBIT',
        timestamp: '2024-01-01T12:00:00Z'
      }
    };
    wsCallback(startEvento);

    // Depois, completar com sucesso
    const completeEvento = {
      type: 'dc_module_complete',
      data: {
        modulo: 'ORBIT',
        status: 'ok',
        timestamp: '2024-01-01T12:05:00Z'
      }
    };
    wsCallback(completeEvento);

    // Verificar que o step 1 agora está como "CONCLUÍDO"
    const step1 = screen.getByText(/CONCLUÍDO/i);
    expect(step1).toBeInTheDocument();
  });

  it('deve usar URL dinâmica para WebSocket', () => {
    // Mock window.location
    const originalLocation = window.location;
    delete window.location;
    window.location = {
      hostname: 'localhost',
      port: '3000'
    };

    mockUseWebSocket.mockImplementation((url, callback) => {
      expect(url).toBe('ws://localhost:3000/ws/events');
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    // Restaurar window.location
    window.location = originalLocation;
  });

  it('deve usar porta padrão 8000 quando não houver porta definida', () => {
    // Mock window.location sem porta
    const originalLocation = window.location;
    delete window.location;
    window.location = {
      hostname: 'localhost',
      port: ''
    };

    mockUseWebSocket.mockImplementation((url, callback) => {
      expect(url).toBe('ws://localhost:8000/ws/events');
      return null;
    });

render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

  // Restaurar window.location
  window.location = originalLocation;
});

it('deve atualizar estado para error quando fetch falhar', async () => {
  mockUseWebSocket.mockImplementation((url, callback) => {
    return null;
  });

  global.fetch.mockResolvedValueOnce({
    ok: false,
    statusText: 'Internal Server Error'
  });

  render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

  const iniciarButton = screen.getByText(/Iniciar Calibração/i);
  fireEvent.click(iniciarButton);

  await waitFor(() => {
    // Verificar que o estado foi atualizado para "error"
    const step1 = screen.getByText(/ERRO/i);
    expect(step1).toBeInTheDocument();
  });
});

  it('deve logar eventos recebidos no console', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    let wsCallback = null;

    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    const evento = {
      type: 'dc_module_start',
      data: {
        modulo: 'ORBIT',
        timestamp: '2024-01-01T12:00:00Z'
      }
    };

    wsCallback(evento);

    expect(consoleSpy).toHaveBeenCalledWith(
      '[CALIBRACAO] Evento recebido:',
      'dc_module_start',
      evento.data
    );

    consoleSpy.mockRestore();
  });
});