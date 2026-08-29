import { useMemo } from "react";
import { type AllowlistLocale, type AllowlistMessageKey, allowlistMessages } from "./messages";

const STORAGE_KEY = "archon_allowlist_locale";

function resolveLocale(): AllowlistLocale {
  if (typeof window === "undefined") {
    return "en";
  }

  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "de" || stored === "en") {
    return stored;
  }

  const browserLang = navigator.language.toLowerCase();
  return browserLang.startsWith("de") ? "de" : "en";
}

export function useAllowlistMessages() {
  const locale = resolveLocale();

  return useMemo(() => {
    const t = (key: AllowlistMessageKey): string => allowlistMessages[locale][key];
    return { locale, t };
  }, [locale]);
}

export function setAllowlistLocale(locale: AllowlistLocale): void {
  localStorage.setItem(STORAGE_KEY, locale);
}
