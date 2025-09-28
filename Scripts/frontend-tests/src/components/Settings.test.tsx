import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { APIKeysSection } from '../../../archon-ui-main/src/components/settings/APIKeysSection';
import { RAGSettings } from '../../../archon-ui-main/src/components/settings/RAGSettings';

// Mock services
vi.mock('../../../archon-ui-main/src/services/credentialsService', () => ({
  credentialsService: {
    getCredentialsByCategory: vi.fn(() => Promise.resolve([])),
    setCredentials: vi.fn(() => Promise.resolve({ success: true })),
    deleteCredentials: vi.fn(() => Promise.resolve({ success: true })),
    testCredentials: vi.fn(() => Promise.resolve({ success: true })),
  },
}));

vi.mock('../../../archon-ui-main/src/contexts/ToastContext', () => ({
  useToast: () => ({
    showToast: vi.fn(),
  }),
}));

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('Settings Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('APIKeysSection', () => {
    it('renders API keys interface correctly', async () => {
      renderWithRouter(<APIKeysSection />);

      await waitFor(() => {
        expect(screen.getByText('API Keys')).toBeInTheDocument();
      });

      expect(screen.getByText('Add API Key')).toBeInTheDocument();
    });

    it('displays existing API keys', async () => {
      const mockCredentials = [
        {
          id: '1',
          category: 'api_keys',
          name: 'OpenAI API Key',
          value: 'sk-...1234',
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/credentialsService')
      ).credentialsService;

      mockService.getCredentialsByCategory.mockResolvedValue(mockCredentials);

      renderWithRouter(<APIKeysSection />);

      await waitFor(() => {
        expect(screen.getByText('OpenAI API Key')).toBeInTheDocument();
        expect(screen.getByText('sk-...1234')).toBeInTheDocument();
      });
    });

    it('handles adding new API key', async () => {
      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/credentialsService')
      ).credentialsService;

      renderWithRouter(<APIKeysSection />);

      await waitFor(() => {
        expect(screen.getByText('Add API Key')).toBeInTheDocument();
      });

      const addButton = screen.getByText('Add API Key');
      fireEvent.click(addButton);

      // Should show add form
      expect(screen.getByText('Add New API Key')).toBeInTheDocument();

      // Fill form
      const nameInput = screen.getByLabelText('Key Name');
      const valueInput = screen.getByLabelText('API Key');
      const categorySelect = screen.getByLabelText('Category');

      fireEvent.change(nameInput, { target: { value: 'Test Key' } });
      fireEvent.change(valueInput, { target: { value: 'test-key-value' } });
      fireEvent.change(categorySelect, { target: { value: 'api_keys' } });

      const saveButton = screen.getByText('Save');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(mockService.setCredentials).toHaveBeenCalledWith({
          name: 'Test Key',
          value: 'test-key-value',
          category: 'api_keys',
        });
      });
    });

    it('handles testing API key', async () => {
      const mockCredentials = [
        {
          id: '1',
          category: 'api_keys',
          name: 'OpenAI API Key',
          value: 'sk-...1234',
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/credentialsService')
      ).credentialsService;

      mockService.getCredentialsByCategory.mockResolvedValue(mockCredentials);

      renderWithRouter(<APIKeysSection />);

      await waitFor(() => {
        expect(screen.getByText('OpenAI API Key')).toBeInTheDocument();
      });

      const testButton = screen.getByText('Test');
      fireEvent.click(testButton);

      await waitFor(() => {
        expect(mockService.testCredentials).toHaveBeenCalledWith('1');
      });
    });

    it('handles deleting API key', async () => {
      const mockCredentials = [
        {
          id: '1',
          category: 'api_keys',
          name: 'OpenAI API Key',
          value: 'sk-...1234',
          created_at: '2024-01-01T00:00:00Z',
        },
      ];

      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/credentialsService')
      ).credentialsService;

      mockService.getCredentialsByCategory.mockResolvedValue(mockCredentials);

      renderWithRouter(<APIKeysSection />);

      await waitFor(() => {
        expect(screen.getByText('OpenAI API Key')).toBeInTheDocument();
      });

      const deleteButton = screen.getByText('Delete');
      fireEvent.click(deleteButton);

      // Should show confirmation
      expect(screen.getByText('Confirm Delete')).toBeInTheDocument();

      const confirmButton = screen.getByText('Confirm');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockService.deleteCredentials).toHaveBeenCalledWith('1');
      });
    });

    it('handles API key validation errors', async () => {
      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/credentialsService')
      ).credentialsService;

      mockService.setCredentials.mockRejectedValue(new Error('Invalid API key'));

      renderWithRouter(<APIKeysSection />);

      await waitFor(() => {
        expect(screen.getByText('Add API Key')).toBeInTheDocument();
      });

      const addButton = screen.getByText('Add API Key');
      fireEvent.click(addButton);

      const saveButton = screen.getByText('Save');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText('Invalid API key')).toBeInTheDocument();
      });
    });
  });

  describe('RAGSettings', () => {
    it('renders RAG settings interface correctly', async () => {
      renderWithRouter(<RAGSettings />);

      await waitFor(() => {
        expect(screen.getByText('RAG Settings')).toBeInTheDocument();
      });

      expect(screen.getByText('Embeddings')).toBeInTheDocument();
      expect(screen.getByText('Search Strategy')).toBeInTheDocument();
      expect(screen.getByText('Reranking')).toBeInTheDocument();
    });

    it('displays current RAG configuration', async () => {
      renderWithRouter(<RAGSettings />);

      await waitFor(() => {
        expect(screen.getByText('RAG Settings')).toBeInTheDocument();
      });

      // Check for configuration toggles
      const toggles = screen.getAllByRole('switch');
      expect(toggles.length).toBeGreaterThan(0);
    });

    it('handles configuration changes', async () => {
      renderWithRouter(<RAGSettings />);

      await waitFor(() => {
        expect(screen.getByText('RAG Settings')).toBeInTheDocument();
      });

      // Find and toggle a setting
      const contextualEmbeddingsToggle = screen.getByLabelText('Use Contextual Embeddings');
      fireEvent.click(contextualEmbeddingsToggle);

      // Should trigger configuration update
      expect(contextualEmbeddingsToggle).toBeChecked();
    });

    it('validates configuration changes', async () => {
      renderWithRouter(<RAGSettings />);

      await waitFor(() => {
        expect(screen.getByText('RAG Settings')).toBeInTheDocument();
      });

      // Test configuration validation
      const saveButton = screen.getByText('Save Settings');
      fireEvent.click(saveButton);

      // Should show success or validation message
      await waitFor(() => {
        expect(screen.getByText('Settings saved successfully')).toBeInTheDocument();
      });
    });

    it('handles configuration load errors', async () => {
      // Mock service to throw error
      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/credentialsService')
      ).credentialsService;

      mockService.getCredentialsByCategory.mockRejectedValue(new Error('Load failed'));

      renderWithRouter(<RAGSettings />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load RAG settings')).toBeInTheDocument();
      });
    });
  });

  describe('Settings Integration', () => {
    it('persists settings across sessions', async () => {
      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/credentialsService')
      ).credentialsService;

      renderWithRouter(<APIKeysSection />);

      await waitFor(() => {
        expect(screen.getByText('Add API Key')).toBeInTheDocument();
      });

      // Add a key
      const addButton = screen.getByText('Add API Key');
      fireEvent.click(addButton);

      const nameInput = screen.getByLabelText('Key Name');
      const valueInput = screen.getByLabelText('API Key');

      fireEvent.change(nameInput, { target: { value: 'Persistent Key' } });
      fireEvent.change(valueInput, { target: { value: 'persistent-value' } });

      const saveButton = screen.getByText('Save');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(mockService.setCredentials).toHaveBeenCalledWith({
          name: 'Persistent Key',
          value: 'persistent-value',
          category: 'api_keys',
        });
      });
    });

    it('handles concurrent setting updates', async () => {
      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/credentialsService')
      ).credentialsService;

      // Simulate slow response
      mockService.setCredentials.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
      );

      renderWithRouter(<APIKeysSection />);

      await waitFor(() => {
        expect(screen.getByText('Add API Key')).toBeInTheDocument();
      });

      // Trigger multiple updates quickly
      const addButton = screen.getByText('Add API Key');
      fireEvent.click(addButton);

      const saveButton = screen.getByText('Save');
      fireEvent.click(saveButton);
      fireEvent.click(saveButton); // Click again before first completes

      // Should handle concurrent requests properly
      await waitFor(() => {
        expect(mockService.setCredentials).toHaveBeenCalledTimes(2);
      });
    });
  });
});
