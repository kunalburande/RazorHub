import React, { createContext, useContext, useState, useEffect, useCallback, useMemo, useRef } from 'react';
import type { Locale } from './localeStore';
import { getStoredLocale, setCurrentLocale, getLocaleDirection } from './localeStore';

type TranslationDict = Record<string, unknown>;

const lazyFiles = import.meta.glob<{ default: TranslationDict }>('./messages/en/*.json');

interface LocaleContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, options?: Record<string, string | number> & { defaultValue?: string }) => string;
}

const LocaleContext = createContext<LocaleContextType | undefined>(undefined);

function pathToKey(path: string): string | null {
  const match = path.match(/\.\/messages\/en\/([^/]+)\.json$/);
  return match ? `en/${match[1]}` : null;
}

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const [locale] = useState<Locale>(getStoredLocale());
  const [ready, setReady] = useState(false);
  const cache = useRef<Record<string, TranslationDict>>({});

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const paths = Object.keys(lazyFiles);
      await Promise.all(
        paths.map((p) =>
          lazyFiles[p]().then((m) => {
            if (!cancelled) {
              const key = pathToKey(p);
              if (key) cache.current[key] = m.default;
            }
          })
        )
      );
      if (!cancelled) setReady(true);
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const setLocale = useCallback((_newLocale: Locale) => {
    // Single language (English)
  }, []);

  useEffect(() => {
    document.documentElement.lang = 'en';
    document.documentElement.dir = getLocaleDirection('en');
    setCurrentLocale('en');
  }, []);

  const t = useCallback(
    (key: string, options?: Record<string, string | number> & { defaultValue?: string }): string => {
      const parts = key.split('.');
      const namespace = parts[0];
      const translationKey = parts.slice(1).join('.');

      const module = cache.current[`en/${namespace}`];
      let text: unknown;
      if (module) {
        text = translationKey.split('.').reduce<unknown>((current, segment) => {
          if (!current || typeof current !== 'object') return undefined;
          return (current as Record<string, unknown>)[segment];
        }, module);
      }

      const defaultValue = options?.defaultValue;
      const variables = options
        ? Object.fromEntries(Object.entries(options).filter(([name]) => name !== 'defaultValue'))
        : undefined;

      if (typeof text !== 'string') {
        if (typeof defaultValue === 'string') return defaultValue;
        if (import.meta.env.DEV && ready) {
          console.warn(`[i18n] Missing translation for key: ${key}`);
        }
        return key;
      }

      let resolved = text;
      if (variables) {
        Object.entries(variables).forEach(([k, v]) => {
          resolved = resolved.replace(`{${k}}`, String(v));
        });
      }

      return resolved;
    },
    [ready]
  );

  const value = useMemo(() => ({ locale, setLocale, t }), [locale, setLocale, t]);

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useTranslation() {
  const context = useContext(LocaleContext);
  if (context === undefined) {
    throw new Error('useTranslation must be used within a LocaleProvider');
  }
  return context;
}
