import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MainLayout } from '../../../archon-ui-main/src/components/layouts/MainLayout';

// Mock the services and hooks
vi.mock('../../../archon-ui-main/src/contexts/ToastContext', () => ({
  useToast: () => ({
    showToast: vi.fn(),
  }),
}));

vi.mock('../../../archon-ui-main/src/services/credentialsService', () => ({
  credentialsService: {
    baseUrl: 'http://localhost:8181',
  },
}));

vi.mock('../../../archon-ui-main/src/utils/onboarding', () => ({
  isLmConfigured: () => true,
}));

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('MainLayout Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock fetch for health check
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ ready: true }),
      })
    ) as any;
  });

  it('renders without crashing', () => {
    renderWithRouter(
      <MainLayout>
        <div data-testid="test-content">Test Content</div>
      </MainLayout>
    );
    expect(screen.getByTestId('test-content')).toBeInTheDocument();
  });

  it('renders side navigation', () => {
    renderWithRouter(
      <MainLayout>
        <div>Test Content</div>
      </MainLayout>
    );
    // Check if side navigation is present
    expect(screen.getByRole('navigation')).toBeInTheDocument();
  });

  it('handles chat panel toggle', async () => {
    renderWithRouter(
      <MainLayout>
        <div>Test Content</div>
      </MainLayout>
    );
    
    // Find and click chat toggle button
    const chatToggle = screen.getByRole('button', { name: /chat/i });
    fireEvent.click(chatToggle);
    
    await waitFor(() => {
      // Verify chat panel state change
      expect(screen.getByTestId('chat-panel')).toBeInTheDocument();
    });
  });

  it('performs backend health check on mount', async () => {
    renderWithRouter(
      <MainLayout>
        <div>Test Content</div>
      </MainLayout>
    );
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8181/api/health',
        expect.any(Object)
      );
    });
  });

  it('handles backend startup failure gracefully', async () => {
    // Mock fetch to simulate backend failure
    global.fetch = vi.fn(() =>
      Promise.reject(new Error('Connection failed'))
    ) as any;
    
    renderWithRouter(
      <MainLayout>
        <div>Test Content</div>
      </MainLayout>
    );
    
    await waitFor(() => {
      // Should show error state or fallback
      expect(screen.getByText(/backend/i)).toBeInTheDocument();
    });
  });

  it('displays disconnect screen when backend is unavailable', async () => {
    // Mock fetch to simulate backend unavailability
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 503,
      })
    ) as any;
    
    renderWithRouter(
      <MainLayout>
        <div>Test Content</div>
      </MainLayout>
    );
    
    await waitFor(() => {
      // Should show disconnect overlay
      expect(screen.getByTestId('disconnect-overlay')).toBeInTheDocument();
    });
  });

  it('handles navigation correctly', () => {
    renderWithRouter(
      <MainLayout>
        <div>Test Content</div>
      </MainLayout>
    );
    
    // Test navigation functionality
    const navItems = screen.getAllByRole('link');
    expect(navItems.length).toBeGreaterThan(0);
  });

  it('maintains responsive design', () => {
    renderWithRouter(
      <MainLayout>
        <div>Test Content</div>
      </MainLayout>
    );
    
    // Test responsive behavior
    const layout = screen.getByTestId('main-layout');
    expect(layout).toHaveClass('responsive');
  });
});
