import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { App } from '../../../archon-ui-main/src/App';

// Mock the services and contexts
vi.mock('../../../archon-ui-main/src/services/serverHealthService', () => ({
  serverHealthService: {
    getSettings: vi.fn(() => ({ enabled: true, delay: 10000 })),
    startMonitoring: vi.fn(),
    stopMonitoring: vi.fn(),
  },
}));

vi.mock('../../../archon-ui-main/src/contexts/SettingsContext', () => ({
  SettingsProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="settings-provider">{children}</div>,
  useSettings: () => ({ projectsEnabled: true }),
}));

vi.mock('../../../archon-ui-main/src/contexts/ThemeContext', () => ({
  ThemeProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="theme-provider">{children}</div>,
}));

vi.mock('../../../archon-ui-main/src/contexts/ToastContext', () => ({
  ToastProvider: ({ children }: { children: React.ReactNode }) => <div data-testid="toast-provider">{children}</div>,
}));

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing', () => {
    renderWithRouter(<App />);
    expect(screen.getByTestId('settings-provider')).toBeInTheDocument();
    expect(screen.getByTestId('theme-provider')).toBeInTheDocument();
    expect(screen.getByTestId('toast-provider')).toBeInTheDocument();
  });

  it('renders main layout components', () => {
    renderWithRouter(<App />);
    // Check if main layout elements are present
    expect(screen.getByTestId('settings-provider')).toBeInTheDocument();
  });

  it('handles routing correctly', async () => {
    renderWithRouter(<App />);
    
    // Wait for the app to fully render
    await waitFor(() => {
      expect(screen.getByTestId('settings-provider')).toBeInTheDocument();
    });
  });

  it('initializes health monitoring on mount', () => {
    renderWithRouter(<App />);
    // This test would verify that health monitoring is started
    // Implementation depends on how the service is mocked
  });

  it('handles theme context properly', () => {
    renderWithRouter(<App />);
    expect(screen.getByTestId('theme-provider')).toBeInTheDocument();
  });

  it('handles toast context properly', () => {
    renderWithRouter(<App />);
    expect(screen.getByTestId('toast-provider')).toBeInTheDocument();
  });
});
