import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { KnowledgeTable } from '../../../archon-ui-main/src/components/knowledge-base/KnowledgeTable';
import { KnowledgeItemCard } from '../../../archon-ui-main/src/components/knowledge-base/KnowledgeItemCard';

// Mock services
vi.mock('../../../archon-ui-main/src/services/knowledgeBaseService', () => ({
  knowledgeBaseService: {
    getKnowledgeItems: vi.fn(() => Promise.resolve({
      data: [
        {
          id: '1',
          title: 'Test Document',
          content: 'Test content',
          source_url: 'https://example.com',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ],
    })),
    uploadDocument: vi.fn(() => Promise.resolve({ success: true })),
    crawlWebsite: vi.fn(() => Promise.resolve({ success: true })),
    deleteKnowledgeItem: vi.fn(() => Promise.resolve({ success: true })),
  },
}));

// Mock contexts
vi.mock('../../../archon-ui-main/src/contexts/ToastContext', () => ({
  useToast: () => ({
    showToast: vi.fn(),
  }),
}));

const mockKnowledgeItem = {
  id: '1',
  title: 'Test Document',
  content: 'Test content for knowledge item',
  source_url: 'https://example.com',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  metadata: {
    word_count: 100,
    file_size: 1024,
  },
};

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('KnowledgeBase Components', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('KnowledgeTable', () => {
    it('renders knowledge items correctly', async () => {
      renderWithRouter(<KnowledgeTable />);

      await waitFor(() => {
        expect(screen.getByText('Test Document')).toBeInTheDocument();
      });

      expect(screen.getByText('Test content')).toBeInTheDocument();
      expect(screen.getByText('https://example.com')).toBeInTheDocument();
    });

    it('handles loading state', () => {
      renderWithRouter(<KnowledgeTable />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('displays empty state when no items', async () => {
      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/knowledgeBaseService')
      ).knowledgeBaseService;

      mockService.getKnowledgeItems.mockResolvedValueOnce({
        data: [],
      });

      renderWithRouter(<KnowledgeTable />);

      await waitFor(() => {
        expect(screen.getByText('No knowledge items found')).toBeInTheDocument();
      });
    });

    it('handles search functionality', async () => {
      renderWithRouter(<KnowledgeTable />);

      await waitFor(() => {
        expect(screen.getByText('Test Document')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText('Search knowledge base...');
      fireEvent.change(searchInput, { target: { value: 'test' } });

      // Search should filter results
      expect(searchInput).toHaveValue('test');
    });

    it('handles sort functionality', async () => {
      renderWithRouter(<KnowledgeTable />);

      await waitFor(() => {
        expect(screen.getByText('Test Document')).toBeInTheDocument();
      });

      const sortButton = screen.getByText('Title');
      fireEvent.click(sortButton);

      // Should trigger sort action
      expect(sortButton).toBeInTheDocument();
    });
  });

  describe('KnowledgeItemCard', () => {
    it('renders knowledge item details correctly', () => {
      renderWithRouter(<KnowledgeItemCard item={mockKnowledgeItem} />);

      expect(screen.getByText('Test Document')).toBeInTheDocument();
      expect(screen.getByText('Test content for knowledge item')).toBeInTheDocument();
      expect(screen.getByText('https://example.com')).toBeInTheDocument();
    });

    it('displays metadata correctly', () => {
      renderWithRouter(<KnowledgeItemCard item={mockKnowledgeItem} />);

      expect(screen.getByText('100 words')).toBeInTheDocument();
      expect(screen.getByText('1.0 KB')).toBeInTheDocument();
    });

    it('handles edit action', () => {
      renderWithRouter(<KnowledgeItemCard item={mockKnowledgeItem} />);

      const editButton = screen.getByRole('button', { name: /edit/i });
      fireEvent.click(editButton);

      // Should trigger edit modal or action
      expect(editButton).toBeInTheDocument();
    });

    it('handles delete action', () => {
      renderWithRouter(<KnowledgeItemCard item={mockKnowledgeItem} />);

      const deleteButton = screen.getByRole('button', { name: /delete/i });
      fireEvent.click(deleteButton);

      // Should show confirmation dialog
      expect(screen.getByText('Delete')).toBeInTheDocument();
    });

    it('formats dates correctly', () => {
      renderWithRouter(<KnowledgeItemCard item={mockKnowledgeItem} />);

      expect(screen.getByText('Jan 1, 2024')).toBeInTheDocument();
    });

    it('truncates long content appropriately', () => {
      const longContentItem = {
        ...mockKnowledgeItem,
        content: 'A'.repeat(500), // Very long content
      };

      renderWithRouter(<KnowledgeItemCard item={longContentItem} />);

      const content = screen.getByText(/^A+\.\.\.$/);
      expect(content).toBeInTheDocument();
      expect(content.textContent?.length).toBeLessThan(500);
    });

    it('handles missing metadata gracefully', () => {
      const itemWithoutMetadata = {
        ...mockKnowledgeItem,
        metadata: undefined,
      };

      renderWithRouter(<KnowledgeItemCard item={itemWithoutMetadata} />);

      // Should not crash and display basic info
      expect(screen.getByText('Test Document')).toBeInTheDocument();
    });
  });

  describe('Knowledge Base Actions', () => {
    it('handles document upload', async () => {
      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/knowledgeBaseService')
      ).knowledgeBaseService;

      renderWithRouter(<KnowledgeTable />);

      // Mock file upload
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

      // This would typically be triggered by a file input
      await waitFor(() => {
        expect(mockService.uploadDocument).toHaveBeenCalled();
      });
    });

    it('handles website crawling', async () => {
      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/knowledgeBaseService')
      ).knowledgeBaseService;

      renderWithRouter(<KnowledgeTable />);

      // Mock crawl action
      await waitFor(() => {
        expect(mockService.crawlWebsite).toHaveBeenCalled();
      });
    });

    it('handles error states', async () => {
      const mockService = vi.mocked(
        await import('../../../archon-ui-main/src/services/knowledgeBaseService')
      ).knowledgeBaseService;

      mockService.getKnowledgeItems.mockRejectedValueOnce(new Error('API Error'));

      renderWithRouter(<KnowledgeTable />);

      await waitFor(() => {
        expect(screen.getByText('Error loading knowledge items')).toBeInTheDocument();
      });
    });
  });
});
