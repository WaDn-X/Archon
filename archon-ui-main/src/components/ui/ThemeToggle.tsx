import React, { useEffect, useState } from 'react';
import { useEnhancedTheme } from '../../contexts/EnhancedThemeContext';
import { Sun, Moon, Monitor, Palette } from 'lucide-react';
import { cn } from '../../utils/cn';

interface ThemeToggleProps {
  variant?: 'default' | 'minimal' | 'button';
  showLabel?: boolean;
  className?: string;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({
  variant = 'default',
  showLabel = true,
  className = ''
}) => {
  const { theme, updateTheme, isDark } = useEnhancedTheme();
  const [systemTheme, setSystemTheme] = useState<'light' | 'dark'>('light');

  // Track system theme preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    setSystemTheme(mediaQuery.matches ? 'dark' : 'light');

    const handleChange = (event: MediaQueryListEvent) => {
      setSystemTheme(event.matches ? 'dark' : 'light');
      // Auto-update if system preference changes and we're using system theme
      if (theme.mode === 'system') {
        updateTheme({ mode: 'system' }); // Trigger re-evaluation
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme.mode, updateTheme]);

  const handleThemeChange = (newMode: 'light' | 'dark' | 'system') => {
    updateTheme({ mode: newMode });
  };

  const getCurrentIcon = () => {
    if (theme.mode === 'system') {
      return systemTheme === 'dark' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />;
    }
    return theme.mode === 'dark' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />;
  };

  const getCurrentLabel = () => {
    if (theme.mode === 'system') {
      return `System (${systemTheme})`;
    }
    return theme.mode === 'dark' ? 'Dark' : 'Light';
  };

  if (variant === 'minimal') {
    return (
      <button
        onClick={() => handleThemeChange(theme.mode === 'light' ? 'dark' : 'light')}
        className={cn(
          'flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg transition-colors',
          'hover:bg-gray-100 dark:hover:bg-gray-800',
          'text-gray-700 dark:text-gray-300',
          className
        )}
        title={`Switch to ${theme.mode === 'light' ? 'dark' : 'light'} mode`}
      >
        {getCurrentIcon()}
        {showLabel && <span>{getCurrentLabel()}</span>}
      </button>
    );
  }

  if (variant === 'button') {
    return (
      <div className={cn('relative', className)}>
        <button
          onClick={() => handleThemeChange(theme.mode === 'light' ? 'dark' : 'light')}
          className={cn(
            'relative inline-flex h-10 w-18 items-center rounded-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 transition-colors',
            'hover:bg-gray-50 dark:hover:bg-gray-700',
            'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
          )}
          aria-label={`Switch to ${theme.mode === 'light' ? 'dark' : 'light'} mode`}
        >
          <span
            className={cn(
              'inline-block h-6 w-6 transform rounded-full bg-blue-500 transition-transform',
              theme.mode === 'dark' ? 'translate-x-9' : 'translate-x-1'
            )}
          >
            {theme.mode === 'dark' ? (
              <Moon className="h-4 w-4 text-white absolute top-1 left-1" />
            ) : (
              <Sun className="h-4 w-4 text-white absolute top-1 left-1" />
            )}
          </span>
        </button>
        {showLabel && (
          <span className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 text-xs text-gray-500 dark:text-gray-400">
            {getCurrentLabel()}
          </span>
        )}
      </div>
    );
  }

  // Default variant - full theme selector
  return (
    <div className={cn('space-y-3', className)}>
      {showLabel && (
        <label className="text-sm font-medium text-foreground flex items-center gap-2">
          <Palette className="w-4 h-4" />
          Theme
        </label>
      )}

      <div className="grid grid-cols-3 gap-3">
        {/* Light Mode */}
        <button
          onClick={() => handleThemeChange('light')}
          className={cn(
            'flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all',
            theme.mode === 'light'
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300'
              : 'border-gray-200 dark:border-gray-700 hover:border-blue-300'
          )}
        >
          <Sun className="w-6 h-6" />
          <span className="text-sm font-medium">Light</span>
        </button>

        {/* Dark Mode */}
        <button
          onClick={() => handleThemeChange('dark')}
          className={cn(
            'flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all',
            theme.mode === 'dark'
              ? 'border-purple-500 bg-purple-50 dark:bg-purple-950 text-purple-700 dark:text-purple-300'
              : 'border-gray-200 dark:border-gray-700 hover:border-purple-300'
          )}
        >
          <Moon className="w-6 h-6" />
          <span className="text-sm font-medium">Dark</span>
        </button>

        {/* System Mode */}
        <button
          onClick={() => handleThemeChange('system')}
          className={cn(
            'flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all',
            theme.mode === 'system'
              ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300'
              : 'border-gray-200 dark:border-gray-700 hover:border-emerald-300'
          )}
        >
          <Monitor className="w-6 h-6" />
          <span className="text-sm font-medium">System</span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            ({systemTheme})
          </span>
        </button>
      </div>

      {/* Status indicator */}
      <div className="flex items-center justify-center gap-2 text-xs text-gray-500 dark:text-gray-400">
        <div className={cn(
          'w-2 h-2 rounded-full',
          isDark ? 'bg-purple-500' : 'bg-blue-500'
        )} />
        <span>
          Currently using {theme.mode === 'system' ? `system (${systemTheme})` : theme.mode} theme
        </span>
      </div>
    </div>
  );
};

// Compact theme toggle for navigation bars
export const ThemeToggleCompact: React.FC<{ className?: string }> = ({ className }) => {
  const { theme, updateTheme } = useEnhancedTheme();

  return (
    <button
      onClick={() => updateTheme({ mode: theme.mode === 'light' ? 'dark' : 'light' })}
      className={cn(
        'flex items-center justify-center w-10 h-10 rounded-lg transition-colors',
        'hover:bg-gray-100 dark:hover:bg-gray-800',
        'text-gray-700 dark:text-gray-300',
        'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
        className
      )}
      title={`Switch to ${theme.mode === 'light' ? 'dark' : 'light'} mode`}
      aria-label={`Switch to ${theme.mode === 'light' ? 'dark' : 'light'} mode`}
    >
      {theme.mode === 'dark' ? (
        <Sun className="w-5 h-5" />
      ) : (
        <Moon className="w-5 h-5" />
      )}
    </button>
  );
};

// Hook for theme-related utilities
export const useThemeDetector = () => {
  const [systemTheme, setSystemTheme] = useState<'light' | 'dark'>('light');
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  const [prefersHighContrast, setPrefersHighContrast] = useState(false);

  useEffect(() => {
    // System color scheme
    const colorQuery = window.matchMedia('(prefers-color-scheme: dark)');
    setSystemTheme(colorQuery.matches ? 'dark' : 'light');

    // Reduced motion
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(motionQuery.matches);

    // High contrast
    const contrastQuery = window.matchMedia('(prefers-contrast: high)');
    setPrefersHighContrast(contrastQuery.matches);

    const handleChange = () => {
      setSystemTheme(colorQuery.matches ? 'dark' : 'light');
      setPrefersReducedMotion(motionQuery.matches);
      setPrefersHighContrast(contrastQuery.matches);
    };

    colorQuery.addEventListener('change', handleChange);
    motionQuery.addEventListener('change', handleChange);
    contrastQuery.addEventListener('change', handleChange);

    return () => {
      colorQuery.removeEventListener('change', handleChange);
      motionQuery.removeEventListener('change', handleChange);
      contrastQuery.removeEventListener('change', handleChange);
    };
  }, []);

  return {
    systemTheme,
    prefersReducedMotion,
    prefersHighContrast,
  };
};