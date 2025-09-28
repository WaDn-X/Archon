import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type SupportedLanguage = 'en' | 'es' | 'fr' | 'de' | 'ja' | 'zh' | 'pt' | 'it' | 'ru' | 'ko';

interface LanguageInfo {
  code: SupportedLanguage;
  name: string;
  nativeName: string;
  flag: string;
}

export const SUPPORTED_LANGUAGES: LanguageInfo[] = [
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
  { code: 'ja', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵' },
  { code: 'zh', name: 'Chinese', nativeName: '中文', flag: '🇨🇳' },
  { code: 'pt', name: 'Portuguese', nativeName: 'Português', flag: '🇵🇹' },
  { code: 'it', name: 'Italian', nativeName: 'Italiano', flag: '🇮🇹' },
  { code: 'ru', name: 'Russian', nativeName: 'Русский', flag: '🇷🇺' },
  { code: 'ko', name: 'Korean', nativeName: '한국어', flag: '🇰🇷' },
];

// Translation dictionaries
const translations = {
  en: {
    // Navigation
    nav: {
      dashboard: 'Dashboard',
      knowledgeBase: 'Knowledge Base',
      projects: 'Projects',
      settings: 'Settings',
      mcp: 'MCP Server',
      profile: 'Profile',
      logout: 'Logout',
    },

    // Common
    common: {
      save: 'Save',
      cancel: 'Cancel',
      delete: 'Delete',
      edit: 'Edit',
      create: 'Create',
      loading: 'Loading...',
      error: 'Error',
      success: 'Success',
      warning: 'Warning',
      info: 'Information',
      confirm: 'Confirm',
      search: 'Search',
      filter: 'Filter',
      sort: 'Sort',
      export: 'Export',
      import: 'Import',
      download: 'Download',
      upload: 'Upload',
      refresh: 'Refresh',
      close: 'Close',
      back: 'Back',
      next: 'Next',
      previous: 'Previous',
      finish: 'Finish',
      submit: 'Submit',
      reset: 'Reset',
      clear: 'Clear',
      selectAll: 'Select All',
      deselectAll: 'Deselect All',
    },

    // Dashboard
    dashboard: {
      title: 'Dashboard',
      welcome: 'Welcome back',
      overview: 'Overview',
      statistics: 'Statistics',
      recentActivity: 'Recent Activity',
      quickActions: 'Quick Actions',
      notifications: 'Notifications',
    },

    // Knowledge Base
    knowledge: {
      title: 'Knowledge Base',
      search: 'Search knowledge...',
      addDocument: 'Add Document',
      uploadFile: 'Upload File',
      crawlWebsite: 'Crawl Website',
      recentDocuments: 'Recent Documents',
      categories: 'Categories',
      tags: 'Tags',
      sources: 'Sources',
      lastModified: 'Last Modified',
      fileSize: 'File Size',
      wordCount: 'Word Count',
      readingTime: 'Reading Time',
    },

    // Projects
    projects: {
      title: 'Projects',
      createProject: 'Create Project',
      projectName: 'Project Name',
      description: 'Description',
      status: 'Status',
      priority: 'Priority',
      assignee: 'Assignee',
      dueDate: 'Due Date',
      progress: 'Progress',
      tasks: 'Tasks',
      completed: 'Completed',
      inProgress: 'In Progress',
      todo: 'To Do',
      blocked: 'Blocked',
    },

    // Settings
    settings: {
      title: 'Settings',
      appearance: 'Appearance',
      theme: 'Theme',
      language: 'Language',
      notifications: 'Notifications',
      privacy: 'Privacy',
      security: 'Security',
      integrations: 'Integrations',
      apiKeys: 'API Keys',
      preferences: 'Preferences',
      advanced: 'Advanced',
    },

    // Errors
    errors: {
      notFound: 'Page not found',
      unauthorized: 'Unauthorized access',
      forbidden: 'Access forbidden',
      serverError: 'Server error',
      networkError: 'Network error',
      validationError: 'Validation error',
      fileTooLarge: 'File too large',
      invalidFormat: 'Invalid format',
      required: 'This field is required',
      email: 'Please enter a valid email',
      password: 'Password must be at least 8 characters',
    },

    // Messages
    messages: {
      changesSaved: 'Changes saved successfully',
      itemDeleted: 'Item deleted successfully',
      itemCreated: 'Item created successfully',
      itemUpdated: 'Item updated successfully',
      operationFailed: 'Operation failed',
      loading: 'Loading...',
      noData: 'No data available',
      noResults: 'No results found',
      tryAgain: 'Please try again',
      confirmDelete: 'Are you sure you want to delete this item?',
    },
  },

  es: {
    nav: {
      dashboard: 'Panel',
      knowledgeBase: 'Base de Conocimiento',
      projects: 'Proyectos',
      settings: 'Configuración',
      mcp: 'Servidor MCP',
      profile: 'Perfil',
      logout: 'Cerrar Sesión',
    },
    common: {
      save: 'Guardar',
      cancel: 'Cancelar',
      delete: 'Eliminar',
      edit: 'Editar',
      create: 'Crear',
      loading: 'Cargando...',
      error: 'Error',
      success: 'Éxito',
      warning: 'Advertencia',
      info: 'Información',
      confirm: 'Confirmar',
      search: 'Buscar',
      filter: 'Filtrar',
      sort: 'Ordenar',
      export: 'Exportar',
      import: 'Importar',
      download: 'Descargar',
      upload: 'Subir',
      refresh: 'Actualizar',
      close: 'Cerrar',
      back: 'Atrás',
      next: 'Siguiente',
      previous: 'Anterior',
      finish: 'Finalizar',
      submit: 'Enviar',
      reset: 'Restablecer',
      clear: 'Limpiar',
    },
    dashboard: {
      title: 'Panel',
      welcome: 'Bienvenido de vuelta',
      overview: 'Resumen',
      statistics: 'Estadísticas',
      recentActivity: 'Actividad Reciente',
      quickActions: 'Acciones Rápidas',
      notifications: 'Notificaciones',
    },
    errors: {
      notFound: 'Página no encontrada',
      unauthorized: 'Acceso no autorizado',
      forbidden: 'Acceso prohibido',
      serverError: 'Error del servidor',
      networkError: 'Error de red',
      validationError: 'Error de validación',
    },
  },

  fr: {
    nav: {
      dashboard: 'Tableau de Bord',
      knowledgeBase: 'Base de Connaissances',
      projects: 'Projets',
      settings: 'Paramètres',
      mcp: 'Serveur MCP',
      profile: 'Profil',
      logout: 'Déconnexion',
    },
    common: {
      save: 'Enregistrer',
      cancel: 'Annuler',
      delete: 'Supprimer',
      edit: 'Modifier',
      create: 'Créer',
      loading: 'Chargement...',
      error: 'Erreur',
      success: 'Succès',
      warning: 'Avertissement',
      info: 'Information',
      confirm: 'Confirmer',
    },
    errors: {
      notFound: 'Page non trouvée',
      unauthorized: 'Accès non autorisé',
      forbidden: 'Accès interdit',
      serverError: 'Erreur serveur',
      networkError: 'Erreur réseau',
    },
  },

  de: {
    nav: {
      dashboard: 'Dashboard',
      knowledgeBase: 'Wissensbasis',
      projects: 'Projekte',
      settings: 'Einstellungen',
      mcp: 'MCP Server',
      profile: 'Profil',
      logout: 'Abmelden',
    },
    common: {
      save: 'Speichern',
      cancel: 'Abbrechen',
      delete: 'Löschen',
      edit: 'Bearbeiten',
      create: 'Erstellen',
      loading: 'Laden...',
      error: 'Fehler',
      success: 'Erfolg',
      warning: 'Warnung',
      info: 'Information',
      confirm: 'Bestätigen',
    },
    errors: {
      notFound: 'Seite nicht gefunden',
      unauthorized: 'Nicht autorisiert',
      forbidden: 'Verboten',
      serverError: 'Serverfehler',
      networkError: 'Netzwerkfehler',
    },
  },

  ja: {
    nav: {
      dashboard: 'ダッシュボード',
      knowledgeBase: '知識ベース',
      projects: 'プロジェクト',
      settings: '設定',
      mcp: 'MCPサーバー',
      profile: 'プロフィール',
      logout: 'ログアウト',
    },
    common: {
      save: '保存',
      cancel: 'キャンセル',
      delete: '削除',
      edit: '編集',
      create: '作成',
      loading: '読み込み中...',
      error: 'エラー',
      success: '成功',
      warning: '警告',
      info: '情報',
      confirm: '確認',
    },
    errors: {
      notFound: 'ページが見つかりません',
      unauthorized: '権限がありません',
      forbidden: 'アクセスが拒否されました',
      serverError: 'サーバーエラー',
      networkError: 'ネットワークエラー',
    },
  },

  zh: {
    nav: {
      dashboard: '仪表板',
      knowledgeBase: '知识库',
      projects: '项目',
      settings: '设置',
      mcp: 'MCP服务器',
      profile: '个人资料',
      logout: '登出',
    },
    common: {
      save: '保存',
      cancel: '取消',
      delete: '删除',
      edit: '编辑',
      create: '创建',
      loading: '加载中...',
      error: '错误',
      success: '成功',
      warning: '警告',
      info: '信息',
      confirm: '确认',
    },
    errors: {
      notFound: '页面未找到',
      unauthorized: '未授权访问',
      forbidden: '访问被禁止',
      serverError: '服务器错误',
      networkError: '网络错误',
    },
  },
};

interface I18nContextValue {
  language: SupportedLanguage;
  setLanguage: (lang: SupportedLanguage) => void;
  t: (key: string, params?: Record<string, any>) => string;
  availableLanguages: LanguageInfo[];
  isRtl: boolean;
}

const I18nContext = createContext<I18nContextValue | undefined>(undefined);

interface I18nProviderProps {
  children: ReactNode;
  defaultLanguage?: SupportedLanguage;
}

export const I18nProvider: React.FC<I18nProviderProps> = ({
  children,
  defaultLanguage = 'en'
}) => {
  const [language, setLanguageState] = useState<SupportedLanguage>(defaultLanguage);

  // Load language from localStorage on mount
  useEffect(() => {
    const storedLang = localStorage.getItem('zippy-language') as SupportedLanguage;
    if (storedLang && SUPPORTED_LANGUAGES.find(lang => lang.code === storedLang)) {
      setLanguageState(storedLang);
    } else {
      // Detect browser language
      const browserLang = navigator.language.split('-')[0] as SupportedLanguage;
      if (SUPPORTED_LANGUAGES.find(lang => lang.code === browserLang)) {
        setLanguageState(browserLang);
      }
    }
  }, []);

  // Save language to localStorage when changed
  useEffect(() => {
    localStorage.setItem('zippy-language', language);
    // Update document language attribute
    document.documentElement.lang = language;
  }, [language]);

  const setLanguage = (lang: SupportedLanguage) => {
    setLanguageState(lang);
  };

  const t = (key: string, params?: Record<string, any>): string => {
    const keys = key.split('.');
    let translation: any = translations[language];

    // Try current language
    for (const k of keys) {
      translation = translation?.[k];
    }

    // Fallback to English if translation not found
    if (!translation && language !== 'en') {
      let fallbackTranslation: any = translations.en;
      for (const k of keys) {
        fallbackTranslation = fallbackTranslation?.[k];
      }
      if (fallbackTranslation) {
        translation = fallbackTranslation;
      }
    }

    if (!translation) {
      console.warn(`Translation missing for key: ${key}`);
      return key;
    }

    // Parameter replacement
    if (params) {
      return Object.entries(params).reduce(
        (str, [param, value]) => str.replace(`{{${param}}}`, String(value)),
        translation
      );
    }

    return translation;
  };

  const isRtl = ['ar', 'he', 'fa'].includes(language);

  // Update document direction for RTL languages
  useEffect(() => {
    document.documentElement.dir = isRtl ? 'rtl' : 'ltr';
  }, [isRtl]);

  const value: I18nContextValue = {
    language,
    setLanguage,
    t,
    availableLanguages: SUPPORTED_LANGUAGES,
    isRtl,
  };

  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  );
};

export const useI18n = (): I18nContextValue => {
  const context = useContext(I18nContext);
  if (context === undefined) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
};

// Translation hook with type safety
export const useTranslation = (namespace?: string) => {
  const { t, ...rest } = useI18n();

  const tScoped = (key: string, params?: Record<string, any>): string => {
    const fullKey = namespace ? `${namespace}.${key}` : key;
    return t(fullKey, params);
  };

  return {
    ...rest,
    t: tScoped,
  };
};

// Export types for external use
export type { I18nContextValue, LanguageInfo };
