import { useState, useEffect, Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { EnhancedThemeProvider } from './contexts/EnhancedThemeContext';
import { I18nProvider } from './contexts/I18nContext';
import { ToastProvider } from './contexts/ToastContext';
import { SettingsProvider } from './contexts/SettingsContext';
import { ErrorBoundaryWithBugReport } from './components/bug-report/ErrorBoundaryWithBugReport';
import { PageLoadingState } from './components/ui/LoadingStates';

// Lazy load heavy components for better performance
const KnowledgeBasePage = lazy(() => import('./pages/KnowledgeBasePage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const MCPPage = lazy(() => import('./pages/MCPPage'));
const OnboardingPage = lazy(() => import('./pages/OnboardingPage'));
const MainLayout = lazy(() => import('./components/layouts/MainLayout'));
const ProjectPage = lazy(() => import('./pages/ProjectPage'));
const DisconnectScreenOverlay = lazy(() => import('./components/DisconnectScreenOverlay'));

const AppRoutes = () => {
  const { projectsEnabled } = useSettings();

  return (
    <Suspense fallback={<PageLoadingState message="Loading page..." />}>
      <Routes>
        <Route path="/" element={<KnowledgeBasePage />} />
        <Route path="/onboarding" element={<OnboardingPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/mcp" element={<MCPPage />} />
        {projectsEnabled ? (
          <Route path="/projects" element={<ProjectPage />} />
        ) : (
          <Route path="/projects" element={<Navigate to="/" replace />} />
        )}
      </Routes>
    </Suspense>
  );
};

const AppContent = () => {
  const [disconnectScreenActive, setDisconnectScreenActive] = useState(false);
  const [disconnectScreenDismissed, setDisconnectScreenDismissed] = useState(false);
  const [disconnectScreenSettings, setDisconnectScreenSettings] = useState({
    enabled: true,
    delay: 10000
  });

  useEffect(() => {
    // Load initial settings
    const settings = serverHealthService.getSettings();
    setDisconnectScreenSettings(settings);

    // Stop any existing monitoring before starting new one to prevent multiple intervals
    serverHealthService.stopMonitoring();

    // Start health monitoring
    serverHealthService.startMonitoring({
      onDisconnected: () => {
        if (!disconnectScreenDismissed) {
          setDisconnectScreenActive(true);
        }
      },
      onReconnected: () => {
        setDisconnectScreenActive(false);
        setDisconnectScreenDismissed(false);
        // Refresh the page to ensure all data is fresh
        window.location.reload();
      }
    });

    return () => {
      serverHealthService.stopMonitoring();
    };
  }, [disconnectScreenDismissed]);

  const handleDismissDisconnectScreen = () => {
    setDisconnectScreenActive(false);
    setDisconnectScreenDismissed(true);
  };

  return (
    <Suspense fallback={<PageLoadingState message="Loading application..." />}>
      <Router>
        <ErrorBoundaryWithBugReport>
          <MainLayout>
            <AppRoutes />
          </MainLayout>
        </ErrorBoundaryWithBugReport>
      </Router>
      <DisconnectScreenOverlay
        isActive={disconnectScreenActive && disconnectScreenSettings.enabled}
        onDismiss={handleDismissDisconnectScreen}
      />
    </Suspense>
  );
};

export function App() {
  return (
    <I18nProvider>
      <EnhancedThemeProvider>
        <ToastProvider>
          <SettingsProvider>
            <AppContent />
          </SettingsProvider>
        </ToastProvider>
      </EnhancedThemeProvider>
    </I18nProvider>
  );
}