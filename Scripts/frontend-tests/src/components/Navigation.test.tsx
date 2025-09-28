import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SideNavigation } from '../../../archon-ui-main/src/components/layouts/SideNavigation';

// Mock the settings context
vi.mock('../../../archon-ui-main/src/contexts/SettingsContext', () => ({
  useSettings: () => ({ projectsEnabled: true }),
}));

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('SideNavigation Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders navigation items correctly', () => {
    renderWithRouter(<SideNavigation />);
    expect(screen.getByLabelText('Knowledge Base')).toBeInTheDocument();
    expect(screen.getByLabelText('MCP Server')).toBeInTheDocument();
    expect(screen.getByLabelText('Settings')).toBeInTheDocument();
  });

  it('highlights active navigation item', () => {
    // Mock useLocation to return / path
    vi.mock('react-router-dom', async () => {
      const actual = await vi.importActual('react-router-dom');
      return {
        ...actual,
        useLocation: () => ({ pathname: '/' }),
      };
    });

    renderWithRouter(<SideNavigation />);
    const activeLink = screen.getByRole('link', { name: /knowledge base/i });
    expect(activeLink).toHaveClass('bg-gradient-to-b');
  });

  it('shows projects navigation when enabled', () => {
    renderWithRouter(<SideNavigation />);
    const logoLink = screen.getByRole('link', { name: /project management/i });
    expect(logoLink).toBeInTheDocument();
    expect(logoLink).toHaveAttribute('href', '/projects');
  });

  it('disables projects navigation when disabled', () => {
    // Mock settings to disable projects
    vi.mocked(vi.importMock('../../../archon-ui-main/src/contexts/SettingsContext')).useSettings.mockReturnValue({
      projectsEnabled: false,
    });

    renderWithRouter(<SideNavigation />);
    const logoDiv = screen.getByAltText('Knowledge Base Logo').closest('div');
    expect(logoDiv).toHaveClass('opacity-50');
    expect(logoDiv).toHaveClass('cursor-not-allowed');
  });

  it('shows tooltips on hover', async () => {
    renderWithRouter(<SideNavigation />);
    const knowledgeBaseLink = screen.getByLabelText('Knowledge Base');

    fireEvent.mouseEnter(knowledgeBaseLink);

    await waitFor(() => {
      expect(screen.getByText('Knowledge Base')).toBeInTheDocument();
    });

    fireEvent.mouseLeave(knowledgeBaseLink);

    await waitFor(() => {
      expect(screen.queryByText('Knowledge Base')).not.toBeInTheDocument();
    });
  });

  it('navigates to correct routes', () => {
    renderWithRouter(<SideNavigation />);
    const settingsLink = screen.getByLabelText('Settings');
    expect(settingsLink).toHaveAttribute('href', '/settings');
  });

  it('applies correct styling for active state', () => {
    // Mock location for settings page
    vi.mock('react-router-dom', async () => {
      const actual = await vi.importActual('react-router-dom');
      return {
        ...actual,
        useLocation: () => ({ pathname: '/settings' }),
      };
    });

    renderWithRouter(<SideNavigation />);
    const activeLink = screen.getByRole('link', { name: /settings/i });
    expect(activeLink).toHaveClass('bg-gradient-to-b');
    expect(activeLink).toHaveClass('text-blue-600');
  });

  it('renders MCP server icon correctly', () => {
    renderWithRouter(<SideNavigation />);
    const mcpLink = screen.getByLabelText('MCP Server');
    const svgIcon = mcpLink.querySelector('svg');
    expect(svgIcon).toBeInTheDocument();
    expect(svgIcon).toHaveAttribute('fill-rule', 'evenodd');
  });

  it('handles keyboard navigation', () => {
    renderWithRouter(<SideNavigation />);
    const navLinks = screen.getAllByRole('link');

    // Test that all navigation items are focusable
    navLinks.forEach(link => {
      link.focus();
      expect(document.activeElement).toBe(link);
    });
  });

  it('maintains accessibility standards', () => {
    renderWithRouter(<SideNavigation />);
    const navLinks = screen.getAllByRole('link');

    navLinks.forEach(link => {
      expect(link).toHaveAttribute('aria-label');
    });
  });
});
