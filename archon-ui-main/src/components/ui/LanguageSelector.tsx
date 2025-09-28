import React, { useState } from 'react';
import { useI18n, SupportedLanguage } from '../../contexts/I18nContext';
import { ChevronDown, Check, Globe } from 'lucide-react';

interface LanguageSelectorProps {
  className?: string;
  variant?: 'default' | 'minimal';
  showFlags?: boolean;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  className = '',
  variant = 'default',
  showFlags = true
}) => {
  const { language, setLanguage, availableLanguages } = useI18n();
  const [isOpen, setIsOpen] = useState(false);

  const currentLang = availableLanguages.find(lang => lang.code === language);

  const handleLanguageChange = (langCode: SupportedLanguage) => {
    setLanguage(langCode);
    setIsOpen(false);
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      setIsOpen(false);
    } else if (event.key === 'Enter' || event.key === ' ') {
      setIsOpen(!isOpen);
    }
  };

  if (variant === 'minimal') {
    return (
      <div className={`relative ${className}`}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          onKeyDown={handleKeyDown}
          className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-foreground hover:text-brand-blue transition-colors rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          aria-label="Select language"
        >
          <Globe className="w-4 h-4" />
          {currentLang?.flag} {currentLang?.nativeName}
          <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {isOpen && (
          <>
            <div
              className="fixed inset-0 z-10"
              onClick={() => setIsOpen(false)}
            />
            <div className="absolute top-full mt-2 right-0 w-56 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-20">
              {availableLanguages.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => handleLanguageChange(lang.code)}
                  className={`w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                    language === lang.code ? 'bg-brand-blue/10 text-brand-blue' : ''
                  }`}
                  role="option"
                  aria-selected={language === lang.code}
                >
                  {showFlags && <span className="text-lg">{lang.flag}</span>}
                  <div className="flex-1">
                    <div className="font-medium">{lang.nativeName}</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">{lang.name}</div>
                  </div>
                  {language === lang.code && <Check className="w-4 h-4 text-brand-blue" />}
                </button>
              ))}
            </div>
          </>
        )}
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        className="flex items-center gap-3 w-full px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-brand-blue transition-colors"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-label="Select language"
      >
        <div className="flex items-center gap-3 flex-1">
          {showFlags && <span className="text-2xl">{currentLang?.flag}</span>}
          <div className="text-left">
            <div className="font-medium text-foreground">{currentLang?.nativeName}</div>
            <div className="text-sm text-gray-500 dark:text-gray-400">{currentLang?.name}</div>
          </div>
        </div>
        <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full mt-2 left-0 right-0 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-20 max-h-64 overflow-y-auto">
            {availableLanguages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => handleLanguageChange(lang.code)}
                className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                  language === lang.code ? 'bg-brand-blue/10 text-brand-blue' : ''
                }`}
                role="option"
                aria-selected={language === lang.code}
              >
                {showFlags && <span className="text-lg">{lang.flag}</span>}
                <div className="flex-1 text-left">
                  <div className="font-medium">{lang.nativeName}</div>
                  <div className="text-sm text-gray-500 dark:text-gray-400">{lang.name}</div>
                </div>
                {language === lang.code && <Check className="w-5 h-5 text-brand-blue" />}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};
