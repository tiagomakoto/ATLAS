// Novos testes para CalibracaoDrawer.test.jsx
// Adicionar estes testes ao final do arquivo, antes do último `});`

// ─── NOVOS TESTES: GATE + FIRE + Estados Finais ───

describe('CalibracaoDrawer - Step 3 GATE + FIRE', () => {
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

  it('deve exibir 3 steps ao inicializar', () => {
    mockUseWebSocket.mockImplementation((url, callback) => null);

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    const pendentes = screen.getAllByText(/PENDENTE/i);
    expect(pendentes.length).toBeGreaterThanOrEqual(3);
  });

  it('deve exibir sub-fases GATE e FIRE quando step 3 está running', async () => {
    let wsCallback = null;
    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        steps: {
          "1_backtest_dados": { status: "done" },
          "2_tune": { status: "done" },
          "3_gate_fire": { status: "running" }
        },
        gate_resultado: null,
        fire_diagnostico: null
      })
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText(/EXECUTANDO/i)).toBeInTheDocument();
    });
  });

  it('deve exibir resultado BLOQUEADO quando GATE falha via WebSocket', async () => {
    let wsCallback = null;
    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        steps: {
          "1_backtest_dados": { status: "done" },
          "2_tune": { status: "done" },
          "3_gate_fire": { status: "running" }
        },
        gate_resultado: null,
        fire_diagnostico: null
      })
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    const gateCompleteEvent = {
      type: 'dc_module_complete',
      data: {
        modulo: 'GATE',
        status: 'ok',
        gate_resultado: {
          ticker: 'PETR4',
          ciclo: '2026-04',
          criterios: [
            { id: 'E1', nome: 'Taxa de acerto', passou: true, valor: '94.2%' },
            { id: 'E2', nome: 'IR mínimo', passou: true, valor: '+3.34' },
            { id: 'E3', nome: 'N mínimo de trades', passou: true, valor: '69' },
            { id: 'E4', nome: 'Consistência anual', passou: true, valor: '4/4 anos' },
            { id: 'E5', nome: 'IR por regime', passou: false, valor: '-0.2' },
            { id: 'E6', nome: 'Drawdown máximo', passou: true, valor: '-12%' },
            { id: 'E7', nome: 'Consecutivos negativos', passou: true, valor: '2' },
            { id: 'E8', nome: 'Cobertura de regimes', passou: true, valor: '5/6' }
          ],
          resultado: 'BLOQUEADO',
          falhas: ['E5']
        }
      }
    };

    wsCallback(gateCompleteEvent);

    await waitFor(() => {
      expect(screen.getByText(/BLOQUEADO/i)).toBeInTheDocument();
    });
  });

  it('deve exibir painel de sucesso quando GATE aprova e FIRE completa', async () => {
    mockUseWebSocket.mockImplementation((url, callback) => null);

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        steps: {
          "1_backtest_dados": { status: "done" },
          "2_tune": { status: "done" },
          "3_gate_fire": { status: "done" }
        },
        gate_resultado: {
          ticker: 'PETR4',
          ciclo: '2026-04',
          criterios: [
            { id: 'E1', nome: 'Taxa de acerto', passou: true, valor: '94.2%' },
            { id: 'E2', nome: 'IR mínimo', passou: true, valor: '+3.34' },
            { id: 'E3', nome: 'N mínimo de trades', passou: true, valor: '69' },
            { id: 'E4', nome: 'Consistência anual', passou: true, valor: '4/4 anos' },
            { id: 'E5', nome: 'IR por regime', passou: true, valor: '+1.8' },
            { id: 'E6', nome: 'Drawdown máximo', passou: true, valor: '-12%' },
            { id: 'E7', nome: 'Consecutivos negativos', passou: true, valor: '2' },
            { id: 'E8', nome: 'Cobertura de regimes', passou: true, valor: '6/6' }
          ],
          resultado: 'OPERAR',
          falhas: []
        },
        fire_diagnostico: {
          ticker: 'PETR4',
          regimes: [
            { regime: 'ALTA', trades: 24, acerto_pct: 95.8, ir: 4.1, worst_trade: '-R$320', estrategia_dominante: 'Bear Call Spread' },
            { regime: 'BAIXA', trades: 18, acerto_pct: 88.9, ir: 2.7, worst_trade: '-R$480', estrategia_dominante: 'Bull Put Spread' }
          ],
          cobertura: { ciclos_com_operacao: 69, total_ciclos: 84, total_trades: 42, acerto_geral_pct: 92.9, pnl_total: 12500.0 },
          stops_por_regime: { BAIXA: 4, ALTA: 2 }
        }
      })
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText(/CALIBRAÇÃO CONCLUÍDA/i)).toBeInTheDocument();
      expect(screen.getByText(/Confirmar OPERAR/i)).toBeInTheDocument();
      expect(screen.getByText(/Manter MONITORAR/i)).toBeInTheDocument();
    });
  });

  it('deve exibir painel de bloqueio quando GATE falha', async () => {
    mockUseWebSocket.mockImplementation((url, callback) => null);

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        steps: {
          "1_backtest_dados": { status: "done" },
          "2_tune": { status: "done" },
          "3_gate_fire": { status: "done" }
        },
        gate_resultado: {
          ticker: 'PETR4',
          ciclo: '2026-04',
          criterios: [
            { id: 'E1', nome: 'Taxa de acerto', passou: true, valor: '85%' },
            { id: 'E2', nome: 'IR mínimo', passou: false, valor: '0.3' },
            { id: 'E3', nome: 'N mínimo de trades', passou: true, valor: '50' },
            { id: 'E4', nome: 'Consistência anual', passou: true, valor: '4/4 anos' },
            { id: 'E5', nome: 'IR por regime', passou: false, valor: '-0.2' },
            { id: 'E6', nome: 'Drawdown máximo', passou: true, valor: '-10%' },
            { id: 'E7', nome: 'Consecutivos negativos', passou: true, valor: '2' },
            { id: 'E8', nome: 'Cobertura de regimes', passou: true, valor: '5/6' }
          ],
          resultado: 'BLOQUEADO',
          falhas: ['E2', 'E5']
        },
        fire_diagnostico: null
      })
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText(/GATE BLOQUEADO/i)).toBeInTheDocument();
      expect(screen.getByText(/Exportar relatório GATE/i)).toBeInTheDocument();
      expect(screen.getByText(/Fechar/i)).toBeInTheDocument();
    });
  });

  it('deve exibir diagnóstico FIRE quando disponível', async () => {
    mockUseWebSocket.mockImplementation((url, callback) => null);

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        steps: {
          "1_backtest_dados": { status: "done" },
          "2_tune": { status: "done" },
          "3_gate_fire": { status: "done" }
        },
        gate_resultado: {
          criterios: [
            { id: 'E1', nome: 'Taxa de acerto', passou: true, valor: '94%' },
            { id: 'E2', nome: 'IR mínimo', passou: true, valor: '+3.0' },
            { id: 'E3', nome: 'N mínimo de trades', passou: true, valor: '60' },
            { id: 'E4', nome: 'Consistência anual', passou: true, valor: '4/4 anos' },
            { id: 'E5', nome: 'IR por regime', passou: true, valor: '+2.0' },
            { id: 'E6', nome: 'Drawdown máximo', passou: true, valor: '-10%' },
            { id: 'E7', nome: 'Consecutivos negativos', passou: true, valor: '2' },
            { id: 'E8', nome: 'Cobertura de regimes', passou: true, valor: '6/6' }
          ],
          resultado: 'OPERAR',
          falhas: []
        },
        fire_diagnostico: {
          regimes: [
            { regime: 'ALTA', trades: 24, acerto_pct: 95.8, ir: 4.1, worst_trade: '-R$320', estrategia_dominante: 'Bear Call Spread' }
          ],
          cobertura: { ciclos_com_operacao: 69, total_ciclos: 84, total_trades: 42, acerto_geral_pct: 92.9, pnl_total: 12500.0 },
          stops_por_regime: { BAIXA: 4 }
        }
      })
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText(/FIRE/i)).toBeInTheDocument();
      expect(screen.getByText(/ALTA/i)).toBeInTheDocument();
    });
  });

  it('deve ter botão de exportar relatório quando há gateResult', async () => {
    mockUseWebSocket.mockImplementation((url, callback) => null);

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        steps: {
          "1_backtest_dados": { status: "done" },
          "2_tune": { status: "done" },
          "3_gate_fire": { status: "done" }
        },
        gate_resultado: {
          criterios: [
            { id: 'E1', nome: 'Taxa de acerto', passou: true, valor: '90%' }
          ],
          resultado: 'OPERAR',
          falhas: []
        },
        fire_diagnostico: null
      })
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText(/Exportar relatório/i)).toBeInTheDocument();
    });
  });

  it('deve buscar gate_resultado via endpoint quando step 3 done mas sem dados', async () => {
    mockUseWebSocket.mockImplementation((url, callback) => null);

    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          steps: {
            "1_backtest_dados": { status: "done" },
            "2_tune": { status: "done" },
            "3_gate_fire": { status: "done" }
          },
          gate_resultado: null,
          fire_diagnostico: null
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ticker: 'PETR4',
          ciclo: '2026-04',
          criterios: [
            { id: 'E1', nome: 'Taxa de acerto', passou: true, valor: '90%' }
          ],
          resultado: 'OPERAR',
          falhas: []
        })
      });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/ativos/PETR4/gate-resultado'),
        expect.any(Object)
      );
    });
  });

  it('deve buscar fire_diagnostico via endpoint quando GATE aprova mas sem fireDiag', async () => {
    mockUseWebSocket.mockImplementation((url, callback) => null);

    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          steps: {
            "1_backtest_dados": { status: "done" },
            "2_tune": { status: "done" },
            "3_gate_fire": { status: "done" }
          },
          gate_resultado: {
            resultado: 'OPERAR',
            criterios: [
              { id: 'E1', nome: 'Taxa de acerto', passou: true, valor: '90%' }
            ],
            falhas: []
          },
          fire_diagnostico: null
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          ticker: 'PETR4',
          regimes: [
            { regime: 'ALTA', trades: 20, acerto_pct: 90.0, ir: 3.5, estrategia_dominante: 'Bear Call Spread' }
          ],
          cobertura: { ciclos_com_operacao: 60, total_ciclos: 72, total_trades: 120, acerto_geral_pct: 87.5, pnl_total: 15000.0 },
          stops_por_regime: {}
        })
      });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/ativos/PETR4/fire-diagnostico'),
        expect.any(Object)
      );
    });
  });
});

describe('CalibracaoDrawer - TuneRegimeProgressPanel TP/STOP/IR exibição', () => {
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

  it('exibe TP/STOP/IR calibrados para regime competitiva após Etapa 3B', async () => {
    let wsCallback = null;
    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    const tuneStartEvent = {
      type: "dc_module_start",
      data: { modulo: "TUNE", timestamp: new Date().toISOString() }
    };
    wsCallback(tuneStartEvent);

    await waitFor(() => {
      expect(screen.getByText(/EXECUTANDO/i)).toBeInTheDocument();
    });

    const regimeCompleteEvent = {
      type: "dc_tune_eleicao_regime_complete",
      data: {
        ticker: "PETR4",
        regime: "ALTA",
        eleicao_status: "competitiva",
        estrategia_eleita: "CSP",
        tp_calibrado: 0.54,
        stop_calibrado: 0.32,
        ir_calibrado: 1.234,
        ranking_eleicao: [
          { estrategia: "CSP", ir_mediana: 1.2, n_trades_reais: 30 },
          { estrategia: "Put", ir_mediana: 0.8, n_trades_reais: 30 }
        ],
        n_trades_reais: 30
      }
    };
    wsCallback(regimeCompleteEvent);

    await waitFor(() => {
      expect(screen.getByText(/CSP \| TP: 0\.54 \| Stop: 0\.32 \| IR: 1\.234/)).toBeInTheDocument();
    });
  });

  it('exibe IR mediana para regime competitiva antes da Etapa 3B', async () => {
    let wsCallback = null;
    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    const tuneStartEvent = {
      type: "dc_module_start",
      data: { modulo: "TUNE", timestamp: new Date().toISOString() }
    };
    wsCallback(tuneStartEvent);

    await waitFor(() => {
      expect(screen.getByText(/EXECUTANDO/i)).toBeInTheDocument();
    });

    const regimeCompleteEvent = {
      type: "dc_tune_eleicao_regime_complete",
      data: {
        ticker: "PETR4",
        regime: "ALTA",
        eleicao_status: "competitiva",
        estrategia_eleita: "CSP",
        tp_calibrado: null,
        stop_calibrado: null,
        ir_calibrado: null,
        ranking_eleicao: [
          { estrategia: "CSP", ir_mediana: 2.1, n_trades_reais: 30 },
          { estrategia: "Put", ir_mediana: 0.8, n_trades_reais: 30 }
        ],
        n_trades_reais: 30
      }
    };
    wsCallback(regimeCompleteEvent);

    await waitFor(() => {
      expect(screen.getByText(/CSP \| IR mediana: 2\.100/)).toBeInTheDocument();
      expect(screen.queryByText(/TP:/)).not.toBeInTheDocument();
      expect(screen.queryByText(/Stop:/)).not.toBeInTheDocument();
    });
  });

  it('exibe TP/STOP para regime estrutural_fixo com fallback (sem IR calibrado)', async () => {
    let wsCallback = null;
    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    const tuneStartEvent = {
      type: "dc_module_start",
      data: { modulo: "TUNE", timestamp: new Date().toISOString() }
    };
    wsCallback(tuneStartEvent);

    await waitFor(() => {
      expect(screen.getByText(/EXECUTANDO/i)).toBeInTheDocument();
    });

    const regimeCompleteEvent = {
      type: "dc_tune_eleicao_regime_complete",
      data: {
        ticker: "PETR4",
        regime: "BAIXA",
        eleicao_status: "estrutural_fixo",
        estrategia_eleita: "Put",
        tp_calibrado: 0.50,
        stop_calibrado: 0.30,
        ir_calibrado: null,
        ranking_eleicao: [{ estrategia: "Put", ir_mediana: 1.5, n_trades_reais: 25 }],
        n_trades_reais: 25
      }
    };
    wsCallback(regimeCompleteEvent);

    await waitFor(() => {
      expect(screen.getByText(/Put \| TP: 0\.50 \| Stop: 0\.30/)).toBeInTheDocument();
      expect(screen.queryByText(/IR:/)).not.toBeInTheDocument();
    });
  });

  it('exibe apenas estratégia quando não há dados de calibração nem IR mediana', async () => {
    let wsCallback = null;
    mockUseWebSocket.mockImplementation((url, callback) => {
      wsCallback = callback;
      return null;
    });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    const tuneStartEvent = {
      type: "dc_module_start",
      data: { modulo: "TUNE", timestamp: new Date().toISOString() }
    };
    wsCallback(tuneStartEvent);

    await waitFor(() => {
      expect(screen.getByText(/EXECUTANDO/i)).toBeInTheDocument();
    });

    const regimeCompleteEvent = {
      type: "dc_tune_eleicao_regime_complete",
      data: {
        ticker: "PETR4",
        regime: "ALTA",
        eleicao_status: "estrutural_fixo",
        estrategia_eleita: "CSP",
        tp_calibrado: null,
        stop_calibrado: null,
        ir_calibrado: null,
        ranking_eleicao: [],
        n_trades_reais: 0
      }
    };
    wsCallback(regimeCompleteEvent);

    await waitFor(() => {
      expect(screen.getByText(/CSP/)).toBeInTheDocument();
      expect(screen.queryByText(/TP:/)).not.toBeInTheDocument();
      expect(screen.queryByText(/Stop:/)).not.toBeInTheDocument();
      expect(screen.queryByText(/IR mediana:/)).not.toBeInTheDocument();
    });
  });
});

describe('CalibracaoDrawer - Guard e Skip Step 1', () => {
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

  it('deve exibir guard quando dados são recentes (menos de 7 dias)', async () => {
    mockUseWebSocket.mockImplementation((url, callback) => null);

    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          steps: {
            "1_backtest_dados": { status: "idle" },
            "2_tune": { status: "idle" },
            "3_gate_fire": { status: "idle" }
          }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          dados_recentes: true,
          dias_desde_atualizacao: 3,
          data_ultimo_cotahist: '2026-04-14'
        })
      });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.getByText(/Dados atualizados/i)).toBeInTheDocument();
      expect(screen.getByText(/Pular step 1/i)).toBeInTheDocument();
      expect(screen.getByText(/Rodar mesmo assim/i)).toBeInTheDocument();
    });
  });

  it('deve pular step 1 quando usuário clica em Pular step 1', async () => {
    mockUseWebSocket.mockImplementation((url, callback) => null);

    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          steps: {
            "1_backtest_dados": { status: "idle" },
            "2_tune": { status: "idle" },
            "3_gate_fire": { status: "idle" }
          }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          dados_recentes: true,
          dias_desde_atualizacao: 3,
          data_ultimo_cotahist: '2026-04-14'
        })
      });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    await waitFor(() => {
      fireEvent.click(screen.getByText(/Pular step 1/i));
    });

    await waitFor(() => {
      expect(screen.queryByText(/Pular step 1/i)).not.toBeInTheDocument();
    });
  });

  it('não deve exibir guard quando dados são antigos (mais de 7 dias)', async () => {
    mockUseWebSocket.mockImplementation((url, callback) => null);

    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          steps: {
            "1_backtest_dados": { status: "idle" },
            "2_tune": { status: "idle" },
            "3_gate_fire": { status: "idle" }
          }
        })
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          dados_recentes: false,
          dias_desde_atualizacao: 15,
          data_ultimo_cotahist: '2026-03-30'
        })
      });

    render(<CalibracaoDrawer ticker="PETR4" onClose={mockOnClose} />);

    await waitFor(() => {
      expect(screen.queryByText(/Pular step 1/i)).not.toBeInTheDocument();
      expect(screen.getByText(/Iniciar calibração/i)).toBeInTheDocument();
    });
  });
});