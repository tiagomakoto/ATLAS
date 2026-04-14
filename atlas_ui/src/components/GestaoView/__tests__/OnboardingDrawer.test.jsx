import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import OnboardingDrawer from '../OnboardingDrawer';

// Mock do hook useWebSocket
jest.mock('../../hooks/useWebSocket', () => jest.fn());

describe('OnboardingDrawer', () => {
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

  it('deve iniciar com todos os steps em status idle', () => {
    mockUseWebSocket.mockImplementation((url, callback) => {
      // Simula conexão WebSocket
      return null;
    });

    render(<OnboardingDrawer ticker="PETR4" onClose={mockOnClose} />);
    
    // Verificar que o estado inicial é "idle" para todos os steps
    const step1 = screen.getByText(/PENDENTE/i);
    const step2 = screen.getByText(/PENDENTE/i);
    const step3 = screen.getByText(/PENDENTE/i);
    
    expect(step1).toBeInTheDocument();
    expect(step2).toBeInTheDocument();
    expect(step3).toBeInTheDocument();
  });

  it('não deve atualizar estado manualmente ao iniciar onboarding com sucesso', async () => {
    mockUseWebSocket.mockImplementation((url, callback) => {
      // Simula conexão WebSocket
      return null;
    });

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'started', step: 1 })
    });

    render(<OnboardingDrawer ticker="PETR4" onClose={mockOnClose} />);
    
    // Encontrar e clicar no botão "Iniciar Onboarding"
    const iniciarButton = screen.getByText(/Iniciar Onboarding/i);
    fireEvent.click(iniciarButton);

    // Aguardar a chamada fetch
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/delta-chaos/onboarding/iniciar',
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

    render(<OnboardingDrawer ticker="PETR4" onClose={mockOnClose} />);
    
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

    render(<OnboardingDrawer ticker="PETR4" onClose={mockOnClose} />);
    
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

    render(<OnboardingDrawer ticker="PETR4" onClose={mockOnClose} />);
    
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

    render(<OnboardingDrawer ticker="PETR4" onClose={mockOnClose} />);
    
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

    render(<OnboardingDrawer ticker="PETR4" onClose={mockOnClose} />);
    
    const iniciarButton = screen.getByText(/Iniciar Onboarding/i);
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

    render(<OnboardingDrawer ticker="PETR4" onClose={mockOnClose} />);
    
    const evento = {
      type: 'dc_module_start',
      data: {
        modulo: 'ORBIT',
        timestamp: '2024-01-01T12:00:00Z'
      }
    };
    
    wsCallback(evento);

    expect(consoleSpy).toHaveBeenCalledWith(
      '[ONBOARDING] Evento recebido:',
      'dc_module_start',
      evento.data
    );

    consoleSpy.mockRestore();
  });
});