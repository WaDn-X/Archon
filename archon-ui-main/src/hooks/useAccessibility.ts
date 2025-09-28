import { useEffect, useState, useCallback } from 'react';

interface AccessibilityPreferences {
  reducedMotion: boolean;
  highContrast: boolean;
  screenReader: boolean;
  colorBlindMode: 'none' | 'protanopia' | 'deuteranopia' | 'tritanopia';
  fontSize: 'small' | 'medium' | 'large' | 'extra-large';
}

interface FocusTrapOptions {
  initialFocusRef?: React.RefObject<HTMLElement>;
  restoreFocus?: boolean;
}

export const useAccessibility = () => {
  const [preferences, setPreferences] = useState<AccessibilityPreferences>({
    reducedMotion: false,
    highContrast: false,
    screenReader: false,
    colorBlindMode: 'none',
    fontSize: 'medium',
  });

  // Detect system preferences on mount
  useEffect(() => {
    const mediaQueryMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const mediaQueryContrast = window.matchMedia('(prefers-contrast: high)');

    const updatePreferences = () => {
      setPreferences(prev => ({
        ...prev,
        reducedMotion: mediaQueryMotion.matches,
        highContrast: mediaQueryContrast.matches,
      }));
    };

    // Initial detection
    updatePreferences();

    // Listen for changes
    mediaQueryMotion.addEventListener('change', updatePreferences);
    mediaQueryContrast.addEventListener('change', updatePreferences);

    return () => {
      mediaQueryMotion.removeEventListener('change', updatePreferences);
      mediaQueryContrast.removeEventListener('change', updatePreferences);
    };
  }, []);

  // Announce content to screen readers
  const announceToScreenReader = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.style.position = 'absolute';
    announcement.style.left = '-10000px';
    announcement.style.width = '1px';
    announcement.style.height = '1px';
    announcement.style.overflow = 'hidden';

    document.body.appendChild(announcement);
    announcement.textContent = message;

    // Remove after announcement
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  }, []);

  // Skip link functionality
  const useSkipLink = (targetId: string) => {
    const handleSkip = useCallback((event: React.KeyboardEvent) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        const target = document.getElementById(targetId);
        if (target) {
          target.focus();
          target.scrollIntoView({ behavior: preferences.reducedMotion ? 'auto' : 'smooth' });
        }
      }
    }, [targetId, preferences.reducedMotion]);

    return handleSkip;
  };

  // Focus trap for modals and dialogs
  const useFocusTrap = useCallback((containerRef: React.RefObject<HTMLElement>, options: FocusTrapOptions = {}) => {
    const { initialFocusRef, restoreFocus = true } = options;

    useEffect(() => {
      if (!containerRef.current) return;

      const container = containerRef.current;
      const focusableElements = container.querySelectorAll(
        'a[href], button, textarea, input[type="text"], input[type="radio"], input[type="checkbox"], select, [tabindex]:not([tabindex="-1"])'
      );

      const firstElement = focusableElements[0] as HTMLElement;
      const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

      let previouslyFocusedElement: Element | null = null;

      if (restoreFocus) {
        previouslyFocusedElement = document.activeElement;
      }

      // Focus initial element
      const initialFocus = initialFocusRef?.current || firstElement;
      if (initialFocus) {
        initialFocus.focus();
      }

      const handleKeyDown = (event: KeyboardEvent) => {
        if (event.key !== 'Tab') return;

        if (event.shiftKey) {
          // Shift + Tab
          if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement?.focus();
          }
        } else {
          // Tab
          if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement?.focus();
          }
        }
      };

      container.addEventListener('keydown', handleKeyDown);

      return () => {
        container.removeEventListener('keydown', handleKeyDown);
        if (restoreFocus && previouslyFocusedElement instanceof HTMLElement) {
          previouslyFocusedElement.focus();
        }
      };
    }, [containerRef, initialFocusRef, restoreFocus]);
  }, []);

  // Generate unique IDs for form associations
  const useUniqueId = (prefix: string = 'id') => {
    const [id] = useState(() => `${prefix}-${Math.random().toString(36).substr(2, 9)}`);
    return id;
  };

  // Handle keyboard navigation
  const useKeyboardNavigation = (
    items: any[],
    onSelect: (item: any, index: number) => void,
    loop: boolean = true
  ) => {
    const [focusedIndex, setFocusedIndex] = useState(-1);

    const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          setFocusedIndex(prev => {
            const next = prev + 1;
            return loop ? next % items.length : Math.min(next, items.length - 1);
          });
          break;
        case 'ArrowUp':
          event.preventDefault();
          setFocusedIndex(prev => {
            const next = prev - 1;
            return loop ? (next + items.length) % items.length : Math.max(next, 0);
          });
          break;
        case 'Enter':
        case ' ':
          event.preventDefault();
          if (focusedIndex >= 0 && focusedIndex < items.length) {
            onSelect(items[focusedIndex], focusedIndex);
          }
          break;
        case 'Home':
          event.preventDefault();
          setFocusedIndex(0);
          break;
        case 'End':
          event.preventDefault();
          setFocusedIndex(items.length - 1);
          break;
      }
    }, [items, focusedIndex, onSelect, loop]);

    return { focusedIndex, handleKeyDown };
  };

  // Color contrast utilities
  const getContrastRatio = useCallback((color1: string, color2: string): number => {
    // Simple contrast calculation (in production, use a proper color library)
    const getLuminance = (color: string) => {
      // Convert hex to RGB and calculate relative luminance
      // This is a simplified version - use a proper color library for production
      return 0.5; // Placeholder
    };

    const lum1 = getLuminance(color1);
    const lum2 = getLuminance(color2);

    const brightest = Math.max(lum1, lum2);
    const darkest = Math.min(lum1, lum2);

    return (brightest + 0.05) / (darkest + 0.05);
  }, []);

  const hasGoodContrast = useCallback((foreground: string, background: string): boolean => {
    const ratio = getContrastRatio(foreground, background);
    return preferences.highContrast ? ratio >= 7 : ratio >= 4.5;
  }, [getContrastRatio, preferences.highContrast]);

  return {
    preferences,
    announceToScreenReader,
    useSkipLink,
    useFocusTrap,
    useUniqueId,
    useKeyboardNavigation,
    getContrastRatio,
    hasGoodContrast,
  };
};
