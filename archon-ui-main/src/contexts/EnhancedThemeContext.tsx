import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';

export type ThemeMode = 'light' | 'dark' | 'system';
export type AccentColor = 'purple' | 'blue' | 'emerald' | 'pink';
export type FontSize = 'sm' | 'md' | 'lg' | 'xl';
export type BorderRadius = 'sm' | 'md' | 'lg' | 'xl';

interface ThemeConfig {
  mode: ThemeMode;
  accentColor: AccentColor;
  fontSize: FontSize;
  borderRadius: BorderRadius;
  reducedMotion: boolean;
  highContrast: boolean;
}

interface ThemeContextValue {
  theme: ThemeConfig;
  updateTheme: (updates: Partial<ThemeConfig>) => void;
  resetTheme: () => void;
  isDark: boolean;
  resolvedAccentColor: string;
}

const defaultTheme: ThemeConfig = {
  mode: 'system',
  accentColor: 'purple',
  fontSize: 'md',
  borderRadius: 'md',
  reducedMotion: false,
  highContrast: false,
};

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

interface EnhancedThemeProviderProps {
  children: ReactNode;
  initialTheme?: Partial<ThemeConfig>;
}

export const EnhancedThemeProvider: React.FC<EnhancedThemeProviderProps> = ({
  children,
  initialTheme = {}
}) => {
  const [theme, setTheme] = useState<ThemeConfig>({
    ...defaultTheme,
    ...initialTheme,
  });

  // Load theme from localStorage on mount
  useEffect(() => {
    const storedTheme = localStorage.getItem('zippy-theme');
    if (storedTheme) {
      try {
        const parsed = JSON.parse(storedTheme);
        setTheme(prev => ({ ...prev, ...parsed }));
      } catch (error) {
        console.warn('Failed to parse stored theme:', error);
      }
    }

    // Check system preferences
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      if (theme.mode === 'system') {
        updateDocumentTheme(e.matches ? 'dark' : 'light');
      }
    };

    mediaQuery.addEventListener('change', handleChange);

    // Check for reduced motion preference
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (motionQuery.matches && theme.mode === 'system') {
      setTheme(prev => ({ ...prev, reducedMotion: true }));
    }

    // Check for high contrast preference
    const contrastQuery = window.matchMedia('(prefers-contrast: high)');
    if (contrastQuery.matches && theme.mode === 'system') {
      setTheme(prev => ({ ...prev, highContrast: true }));
    }

    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  // Update document theme when theme changes
  useEffect(() => {
    const resolvedMode = getResolvedThemeMode(theme.mode);
    updateDocumentTheme(resolvedMode);
    updateDocumentPreferences(theme);
  }, [theme]);

  // Save theme to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('zippy-theme', JSON.stringify(theme));
  }, [theme]);

  const updateTheme = (updates: Partial<ThemeConfig>) => {
    setTheme(prev => ({ ...prev, ...updates }));
  };

  const resetTheme = () => {
    setTheme(defaultTheme);
  };

  const getResolvedThemeMode = (mode: ThemeMode): 'light' | 'dark' => {
    if (mode === 'system') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return mode;
  };

  const updateDocumentTheme = (mode: 'light' | 'dark') => {
    const root = document.documentElement;

    if (mode === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  };

  const updateDocumentPreferences = (config: ThemeConfig) => {
    const root = document.documentElement;

    // Font size
    root.setAttribute('data-font-size', config.fontSize);

    // Border radius
    root.setAttribute('data-border-radius', config.borderRadius);

    // Accent color
    root.setAttribute('data-accent-color', config.accentColor);

    // Reduced motion
    if (config.reducedMotion) {
      root.setAttribute('data-reduced-motion', 'true');
    } else {
      root.removeAttribute('data-reduced-motion');
    }

    // High contrast
    if (config.highContrast) {
      root.setAttribute('data-high-contrast', 'true');
    } else {
      root.removeAttribute('data-high-contrast');
    }
  };

  const isDark = getResolvedThemeMode(theme.mode) === 'dark';

  const resolvedAccentColor = getAccentColorValue(theme.accentColor, isDark);

  const value: ThemeContextValue = {
    theme,
    updateTheme,
    resetTheme,
    isDark,
    resolvedAccentColor,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useEnhancedTheme = (): ThemeContextValue => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useEnhancedTheme must be used within an EnhancedThemeProvider');
  }
  return context;
};

// Helper functions
const getAccentColorValue = (accent: AccentColor, isDark: boolean): string => {
  const colors = {
    purple: {
      light: 'hsl(147, 51, 234)', // --color-brand-purple
      dark: 'hsl(147, 51, 234)',  // Same for dark mode
    },
    blue: {
      light: 'hsl(59, 130, 246)', // --color-brand-blue
      dark: 'hsl(59, 130, 246)',
    },
    emerald: {
      light: 'hsl(16, 185, 129)', // --color-brand-emerald
      dark: 'hsl(16, 185, 129)',
    },
    pink: {
      light: 'hsl(236, 72, 153)', // --color-brand-pink
      dark: 'hsl(236, 72, 153)',
    },
  };

  return colors[accent][isDark ? 'dark' : 'light'];
};

// Theme hook with utilities
export const useThemeUtils = () => {
  const { theme, updateTheme } = useEnhancedTheme();

  const toggleTheme = () => {
    const newMode: ThemeMode = theme.mode === 'light' ? 'dark' : 'light';
    updateTheme({ mode: newMode });
  };

  const setAccentColor = (color: AccentColor) => {
    updateTheme({ accentColor: color });
  };

  const setFontSize = (size: FontSize) => {
    updateTheme({ fontSize: size });
  };

  const setBorderRadius = (radius: BorderRadius) => {
    updateTheme({ borderRadius: radius });
  };

  const toggleReducedMotion = () => {
    updateTheme({ reducedMotion: !theme.reducedMotion });
  };

  const toggleHighContrast = () => {
    updateTheme({ highContrast: !theme.highContrast });
  };

  return {
    ...theme,
    toggleTheme,
    setAccentColor,
    setFontSize,
    setBorderRadius,
    toggleReducedMotion,
    toggleHighContrast,
  };
};

// Export types for external use
export type { ThemeConfig, ThemeContextValue };
