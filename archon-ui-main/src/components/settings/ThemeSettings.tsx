import React from 'react';
import { useThemeUtils } from '../../contexts/EnhancedThemeContext';
import { useI18n } from '../../contexts/I18nContext';
import { LanguageSelector } from '../ui/LanguageSelector';
import { ThemeToggle } from '../ui/ThemeToggle';
import { Palette, Type, CornerDownLeft, Contrast, RotateCcw, Languages } from 'lucide-react';

interface ThemeSettingsProps {
  className?: string;
}

export const ThemeSettings: React.FC<ThemeSettingsProps> = ({ className = '' }) => {
  const {
    mode,
    accentColor,
    fontSize,
    borderRadius,
    reducedMotion,
    highContrast,
    toggleTheme,
    setAccentColor,
    setFontSize,
    setBorderRadius,
    toggleReducedMotion,
    toggleHighContrast,
    resetTheme,
  } = useThemeUtils();

  const accentColors = [
    { value: 'purple' as const, label: 'Purple', color: '#9333ea' },
    { value: 'blue' as const, label: 'Blue', color: '#3b82f6' },
    { value: 'emerald' as const, label: 'Emerald', color: '#10b981' },
    { value: 'pink' as const, label: 'Pink', color: '#ec4899' },
  ];

  const fontSizes = [
    { value: 'sm' as const, label: 'Small' },
    { value: 'md' as const, label: 'Medium' },
    { value: 'lg' as const, label: 'Large' },
    { value: 'xl' as const, label: 'Extra Large' },
  ];

  const borderRadii = [
    { value: 'sm' as const, label: 'Small' },
    { value: 'md' as const, label: 'Medium' },
    { value: 'lg' as const, label: 'Large' },
    { value: 'xl' as const, label: 'Extra Large' },
  ];

  return (
    <div className={`space-y-8 ${className}`}>
      <div>
        <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
          <Palette className="w-5 h-5" />
          Appearance
        </h3>

        {/* Theme Mode */}
        <div className="space-y-3">
          <label className="text-sm font-medium text-foreground">Theme</label>
          <ThemeToggle variant="default" showLabel={false} />
        </div>

        {/* Accent Color */}
        <div className="space-y-3 mt-6">
          <label className="text-sm font-medium text-foreground">Accent Color</label>
          <div className="grid grid-cols-4 gap-3">
            {accentColors.map((color) => (
              <button
                key={color.value}
                onClick={() => setAccentColor(color.value)}
                className={`flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all ${
                  accentColor === color.value
                    ? 'border-gray-400 bg-gray-50 dark:bg-gray-800'
                    : 'border-border hover:border-gray-300'
                }`}
              >
                <div
                  className="w-6 h-6 rounded-full border-2 border-white shadow-sm"
                  style={{ backgroundColor: color.color }}
                />
                <span className="text-sm font-medium">{color.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Font Size */}
        <div className="space-y-3 mt-6">
          <label className="text-sm font-medium text-foreground flex items-center gap-2">
            <Type className="w-4 h-4" />
            Font Size
          </label>
          <div className="grid grid-cols-2 gap-3">
            {fontSizes.map((size) => (
              <button
                key={size.value}
                onClick={() => setFontSize(size.value)}
                className={`p-3 rounded-lg border-2 text-center transition-all ${
                  fontSize === size.value
                    ? 'border-brand-blue bg-brand-blue/10 text-brand-blue'
                    : 'border-border hover:border-brand-blue/50'
                }`}
              >
                <span className="text-sm font-medium">{size.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Border Radius */}
        <div className="space-y-3 mt-6">
          <label className="text-sm font-medium text-foreground flex items-center gap-2">
            <CornerDownLeft className="w-4 h-4" />
            Border Radius
          </label>
          <div className="grid grid-cols-2 gap-3">
            {borderRadii.map((radius) => (
              <button
                key={radius.value}
                onClick={() => setBorderRadius(radius.value)}
                className={`p-3 rounded-lg border-2 text-center transition-all ${
                  borderRadius === radius.value
                    ? 'border-brand-blue bg-brand-blue/10 text-brand-blue'
                    : 'border-border hover:border-brand-blue/50'
                }`}
                style={{
                  borderRadius: radius.value === 'sm' ? '0.25rem' :
                               radius.value === 'md' ? '0.375rem' :
                               radius.value === 'lg' ? '0.5rem' : '0.75rem'
                }}
              >
                <span className="text-sm font-medium">{radius.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
          <Contrast className="w-5 h-5" />
          Accessibility
        </h3>

        <div className="space-y-4">
          {/* Reduced Motion */}
          <div className="flex items-center justify-between p-4 rounded-lg border border-border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <RotateCcw className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h4 className="font-medium text-foreground">Reduced Motion</h4>
                <p className="text-sm text-muted-foreground">
                  Minimize animations and transitions
                </p>
              </div>
            </div>
            <button
              onClick={toggleReducedMotion}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                reducedMotion ? 'bg-brand-blue' : 'bg-gray-200 dark:bg-gray-700'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  reducedMotion ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* High Contrast */}
          <div className="flex items-center justify-between p-4 rounded-lg border border-border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Contrast className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h4 className="font-medium text-foreground">High Contrast</h4>
                <p className="text-sm text-muted-foreground">
                  Increase contrast for better visibility
                </p>
              </div>
            </div>
            <button
              onClick={toggleHighContrast}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                highContrast ? 'bg-brand-blue' : 'bg-gray-200 dark:bg-gray-700'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  highContrast ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Language Settings */}
      <div>
        <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
          <Languages className="w-5 h-5" />
          Language & Region
        </h3>

        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-foreground mb-3 block">
              Display Language
            </label>
            <LanguageSelector className="max-w-md" />
            <p className="text-xs text-muted-foreground mt-2">
              Choose your preferred language for the interface. Some content may still appear in English.
            </p>
          </div>
        </div>
      </div>

      {/* Reset Button */}
      <div className="pt-6 border-t border-border">
        <button
          onClick={resetTheme}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-destructive hover:bg-destructive/10 rounded-lg transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          Reset to Defaults
        </button>
        <p className="text-xs text-muted-foreground mt-2">
          This will reset all theme settings to their default values.
        </p>
      </div>
    </div>
  );
};
