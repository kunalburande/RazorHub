/* eslint-disable react-refresh/only-export-components */
import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
} from "react";

import enMessages from "./locales/en.json";

type TranslationDict = Record<string, unknown>;

export interface TranslationOptions {
  [key: string]: unknown;
  defaultValue?: string;
  count?: number;
}

export interface LocaleContextType {
  locale: "en";
  setLocale: (locale: "en") => void;
  t: (
    key: string,
    optionsOrDefault?: string | TranslationOptions,
    maybeDefault?: string,
  ) => string;
  i18n: {
    language: "en";
    dir: () => "ltr";
    t: (
      key: string,
      optionsOrDefault?: string | TranslationOptions,
      maybeDefault?: string,
    ) => string;
  };
}

const LocaleContext = createContext<LocaleContextType | undefined>(undefined);

const dictionary: TranslationDict = enMessages as unknown as TranslationDict;

export function resolveNestedKey(obj: unknown, path: string): unknown {
  if (!obj || typeof obj !== "object") return undefined;
  const parts = path.split(".");
  let current: unknown = obj;
  for (const part of parts) {
    if (
      current &&
      typeof current === "object" &&
      part in (current as Record<string, unknown>)
    ) {
      current = (current as Record<string, unknown>)[part];
    } else {
      return undefined;
    }
  }
  return current;
}

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.lang = "en";
      document.documentElement.dir = "ltr";
      document.documentElement.classList.remove("rtl");
      document.body.classList.remove("rtl");
    }
  }, []);

  const setLocale = useCallback(() => {
    // English only
  }, []);

  const t = useCallback(
    (
      key: string,
      optionsOrDefault?: string | TranslationOptions,
      maybeDefault?: string,
    ): string => {
      let defaultValue: string | undefined;
      let variables: Record<string, unknown> | undefined;

      if (typeof optionsOrDefault === "string") {
        defaultValue = optionsOrDefault;
      } else if (optionsOrDefault && typeof optionsOrDefault === "object") {
        defaultValue = optionsOrDefault.defaultValue || maybeDefault;
        const filtered: Record<string, unknown> = {};
        for (const [k, v] of Object.entries(optionsOrDefault)) {
          if (k !== "defaultValue" && v !== undefined) {
            filtered[k] = v;
          }
        }
        variables = filtered;
      } else if (typeof maybeDefault === "string") {
        defaultValue = maybeDefault;
      }

      // Check pluralization if count is provided
      let text = resolveNestedKey(dictionary, key);
      if (
        variables?.count !== undefined &&
        typeof variables.count === "number" &&
        variables.count > 1
      ) {
        const pluralText = resolveNestedKey(dictionary, `${key}_plural`);
        if (pluralText) {
          text = pluralText;
        }
      }

      if (typeof text !== "string") {
        if (defaultValue !== undefined) return defaultValue;
        return key;
      }

      let resolved = text;
      if (variables) {
        Object.entries(variables).forEach(([k, v]) => {
          const strVal =
            typeof v === "object" && v !== null && "en" in v
              ? String((v as { en: unknown }).en)
              : String(v);
          resolved = resolved
            .replace(new RegExp(`\\{\\{${k}\\}\\}`, "g"), strVal)
            .replace(new RegExp(`\\{${k}\\}`, "g"), strVal);
        });
      }

      return resolved;
    },
    [],
  );

  const i18n = useMemo(
    () => ({
      language: "en" as const,
      dir: () => "ltr" as const,
      t,
    }),
    [t],
  );

  const value = useMemo(
    () => ({
      locale: "en" as const,
      setLocale,
      t,
      i18n,
    }),
    [setLocale, t, i18n],
  );

  return (
    <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>
  );
}

export function useTranslation() {
  const context = useContext(LocaleContext);
  if (!context) {
    const fallbackT = (
      key: string,
      optionsOrDefault?: string | TranslationOptions,
      maybeDefault?: string,
    ) => {
      if (typeof optionsOrDefault === "string") return optionsOrDefault;
      if (
        optionsOrDefault &&
        typeof optionsOrDefault === "object" &&
        optionsOrDefault.defaultValue
      ) {
        return optionsOrDefault.defaultValue as string;
      }
      if (typeof maybeDefault === "string") return maybeDefault;
      return key;
    };
    return {
      locale: "en" as const,
      setLocale: () => {},
      t: fallbackT,
      i18n: {
        language: "en" as const,
        dir: () => "ltr" as const,
        t: fallbackT,
      },
    };
  }
  return context;
}
