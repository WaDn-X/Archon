import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MCPClients } from '../../../archon-ui-main/src/components/mcp/MCPClients';
import { ToolTestingPanel } from '../../../archon-ui-main/src/components/mcp/ToolTestingPanel';

// Mock services
vi.mock('../../../archon-ui-main/src/services/mcpClientService', () => ({
  mcpClientService: {
    getClients: vi.fn(() => Promise.resolve({
      clients: [
        {
          id: '1',
          name: 'Test Client',
          status: 'connected',
          tools: ['read_file', 'write_file'],
          last_seen: '2024-01-01T00:00:00Z',
        },
      ],
    })),
    connectClient: vi.fn(() => Promise.resolve({ success: true })),
    disconnectClient: vi.fn(() => Promise.resolve({ success: true })),
    testTool: vi.fn(() => Promise.resolve({ success: true, result: 'Test output' })),
  },
}));

vi.mock('../../../archon-ui-main/src/services/mcpServerService', () => ({
  mcpServerService: {
    getServerStatus: vi.fn(() => Promise.resolve({ status: 'running', port: 8051 })),
    startServer: vi.fn(() => Promise.resolve({ success: true })),
    stopServer: vi.fn(() => Promise.resolve({ success: true })),
  },
}));

vi.mock('../../../archon-ui-main/src/contexts/ToastContext', () => ({
  useToast: () => ({
    showToast: vi.fn(),
  }),
}));

const mockClient = {
  id: '1',
  name: 'Test MCP Client',
  status: 'connected',
  tools: ['read_file', 'write_file', 'run_terminal_cmd'],
  capabilities: ['file_system', 'terminal'],
  last_seen: '2024-01-01T00:00:00Z',
  version: '1.0.0',
};

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('MCP Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('MCPClients', () => {
    it('renders MCP clients list correctly', async () => {
      renderWithRouter(<MCPClients />);

      await waitFor(() => {
        expect(screen.getByText('MCP Clients')).toBeInTheDocument();
      });

      expect(screen.getByText('Test Client')).toBeInTheDocument();
      expect(screen.getByText('connected')).toBeInTheDocument();
    });

    it('displays client details correctly', async () => {
      renderWithRouter(<MCPClients />);

      await waitFor(() => {
        expect(screen.getByText('Test Client')).toBeInTheDocument();
      });

      // Check client information display
      expect(screen.getByText('read_file')).toBeInTheDocument();
      expect(screen.getByText('write_file')).toBeInTheDocument();
      expect(screen.getByText('2 tools')).toBeInTheDocument();
    });

    it('handles client connection status', async () => {
      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/mcpClientService')
      ).mcpClientService;

      // Mock disconnected client
      mockService.getClients.mockResolvedValueOnce({
        clients: [
          {
            ...mockClient,
            status: 'disconnected',
          },
        ],
      });

      renderWithRouter(<MCPClients />);

      await waitFor(() => {
        expect(screen.getByText('disconnected')).toBeInTheDocument();
      });

      // Should show reconnect button
      expect(screen.getByText('Reconnect')).toBeInTheDocument();
    });

    it('handles connecting new client', async () => {
      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/mcpClientService')
      ).mcpClientService;

      renderWithRouter(<MCPClients />);

      await waitFor(() => {
        expect(screen.getByText('Add Client')).toBeInTheDocument();
      });

      const addButton = screen.getByText('Add Client');
      fireEvent.click(addButton);

      // Should show connection form
      expect(screen.getByText('Connect New Client')).toBeInTheDocument();

      const nameInput = screen.getByLabelText('Client Name');
      const urlInput = screen.getByLabelText('Server URL');

      fireEvent.change(nameInput, { target: { value: 'New Client' } });
      fireEvent.change(urlInput, { target: { value: 'http://localhost:8051' } });

      const connectButton = screen.getByText('Connect');
      fireEvent.click(connectButton);

      await waitFor(() => {
        expect(mockService.connectClient).toHaveBeenCalledWith({
          name: 'New Client',
          url: 'http://localhost:8051',
        });
      });
    });

    it('handles disconnecting client', async () => {
      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/mcpClientService')
      ).mcpClientService;

      renderWithRouter(<MCPClients />);

      await waitFor(() => {
        expect(screen.getByText('Test Client')).toBeInTheDocument();
      });

      const disconnectButton = screen.getByText('Disconnect');
      fireEvent.click(disconnectButton);

      // Should show confirmation
      expect(screen.getByText('Confirm Disconnect')).toBeInTheDocument();

      const confirmButton = screen.getByText('Disconnect');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockService.disconnectClient).toHaveBeenCalledWith('1');
      });
    });

    it('handles client refresh', async () => {
      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/mcpClientService')
      ).mcpClientService;

      renderWithRouter(<MCPClients />);

      await waitFor(() => {
        expect(screen.getByText('Test Client')).toBeInTheDocument();
      });

      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(mockService.getClients).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('ToolTestingPanel', () => {
    it('renders tool testing interface correctly', async () => {
      renderWithRouter(<ToolTestingPanel clientId="1" />);

      await waitFor(() => {
        expect(screen.getByText('Tool Testing')).toBeInTheDocument();
      });

      expect(screen.getByText('Select Tool')).toBeInTheDocument();
      expect(screen.getByText('Test')).toBeInTheDocument();
    });

    it('displays available tools', async () => {
      renderWithRouter(<ToolTestingPanel clientId="1" />);

      await waitFor(() => {
        expect(screen.getByText('read_file')).toBeInTheDocument();
        expect(screen.getByText('write_file')).toBeInTheDocument();
        expect(screen.getByText('run_terminal_cmd')).toBeInTheDocument();
      });
    });

    it('handles tool selection', async () => {
      renderWithRouter(<ToolTestingPanel clientId="1" />);

      await waitFor(() => {
        expect(screen.getByText('read_file')).toBeInTheDocument();
      });

      const toolSelect = screen.getByLabelText('Select Tool');
      fireEvent.change(toolSelect, { target: { value: 'read_file' } });

      // Should show tool parameters form
      expect(screen.getByText('Parameters')).toBeInTheDocument();
    });

    it('handles tool execution', async () => {
      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/mcpClientService')
      ).mcpClientService;

      renderWithRouter(<ToolTestingPanel clientId="1" />);

      await waitFor(() => {
        expect(screen.getByText('read_file')).toBeInTheDocument();
      });

      const toolSelect = screen.getByLabelText('Select Tool');
      fireEvent.change(toolSelect, { target: { value: 'read_file' } });

      // Fill parameters
      const pathInput = screen.getByLabelText('path');
      fireEvent.change(pathInput, { target: { value: '/test/file.txt' } });

      const testButton = screen.getByText('Execute');
      fireEvent.click(testButton);

      await waitFor(() => {
        expect(mockService.testTool).toHaveBeenCalledWith('1', 'read_file', {
          path: '/test/file.txt',
        });
      });
    });

    it('displays test results', async () => {
      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/mcpClientService')
      ).mcpClientService;

      mockService.testTool.mockResolvedValue({
        success: true,
        result: 'File contents here',
        execution_time: 0.5,
      });

      renderWithRouter(<ToolTestingPanel clientId="1" />);

      await waitFor(() => {
        expect(screen.getByText('read_file')).toBeInTheDocument();
      });

      const toolSelect = screen.getByLabelText('Select Tool');
      fireEvent.change(toolSelect, { target: { value: 'read_file' } });

      const testButton = screen.getByText('Execute');
      fireEvent.click(testButton);

      await waitFor(() => {
        expect(screen.getByText('File contents here')).toBeInTheDocument();
        expect(screen.getByText('Execution time: 0.5s')).toBeInTheDocument();
      });
    });

    it('handles tool execution errors', async () => {
      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/mcpClientService')
      ).mcpClientService;

      mockService.testTool.mockRejectedValue(new Error('Tool execution failed'));

      renderWithRouter(<ToolTestingPanel clientId="1" />);

      await waitFor(() => {
        expect(screen.getByText('read_file')).toBeInTheDocument();
      });

      const toolSelect = screen.getByLabelText('Select Tool');
      fireEvent.change(toolSelect, { target: { value: 'read_file' } });

      const testButton = screen.getByText('Execute');
      fireEvent.click(testButton);

      await waitFor(() => {
        expect(screen.getByText('Tool execution failed')).toBeInTheDocument();
      });
    });

    it('validates tool parameters', async () => {
      renderWithRouter(<ToolTestingPanel clientId="1" />);

      await waitFor(() => {
        expect(screen.getByText('read_file')).toBeInTheDocument();
      });

      const toolSelect = screen.getByLabelText('Select Tool');
      fireEvent.change(toolSelect, { target: { value: 'read_file' } });

      // Try to execute without required parameters
      const testButton = screen.getByText('Execute');
      fireEvent.click(testButton);

      // Should show validation error
      expect(screen.getByText('Path parameter is required')).toBeInTheDocument();
    });
  });

  describe('MCP Integration', () => {
    it('handles real-time client status updates', async () => {
      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/mcpClientService')
      ).mcpClientService;

      renderWithRouter(<MCPClients />);

      await waitFor(() => {
        expect(screen.getByText('Test Client')).toBeInTheDocument();
      });

      // Simulate WebSocket update
      const mockWebSocket = {
        onmessage: null,
        send: vi.fn(),
      };

      // Mock WebSocket connection and simulate status change
      mockService.getClients.mockResolvedValueOnce({
        clients: [
          {
            ...mockClient,
            status: 'disconnected',
          },
        ],
      });

      // Trigger refresh to simulate real-time update
      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(screen.getByText('disconnected')).toBeInTheDocument();
      });
    });

    it('maintains connection state during navigation', async () => {
      const { rerender } = renderWithRouter(<MCPClients />);

      await waitFor(() => {
        expect(screen.getByText('Test Client')).toBeInTheDocument();
      });

      // Simulate navigation away and back
      rerender(
        <BrowserRouter>
          <div>Other Page</div>
        </BrowserRouter>
      );

      rerender(
        <BrowserRouter>
          <MCPClients />
        </BrowserRouter>
      );

      // Should maintain connection state
      await waitFor(() => {
        expect(screen.getByText('Test Client')).toBeInTheDocument();
      });
    });

    it('handles server status changes', async () => {
      const mockServerService = vi.mocked(
        await import('../../../archon-ui-main/src/services/mcpServerService')
      ).mcpServerService;

      renderWithRouter(<MCPClients />);

      await waitFor(() => {
        expect(screen.getByText('Test Client')).toBeInTheDocument();
      });

      // Mock server going down
      mockServerService.getServerStatus.mockResolvedValueOnce({
        status: 'stopped',
        port: 8051,
      });

      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(screen.getByText('Server Unavailable')).toBeInTheDocument();
      });
    });
  });
});
