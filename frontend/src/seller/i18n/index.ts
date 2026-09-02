import { resolveNestedKey, type TranslationOptions } from "./LocaleContext";
import enMessages from "./locales/en.json";

export * from "./LocaleContext";
export { default as en } from "./locales/en.json";
export * from "./types";

export const i18n = {
  t: (key: string, optionsOrDefault?: string | TranslationOptions, maybeDefault?: string) => {
    const val = resolveNestedKey(enMessages, key);
    if (typeof val === "string") return val;
    if (typeof optionsOrDefault === "string") return optionsOrDefault;
    if (optionsOrDefault && typeof optionsOrDefault === "object" && optionsOrDefault.defaultValue) {
      return optionsOrDefault.defaultValue as string;
    }
    if (typeof maybeDefault === "string") return maybeDefault;
    return key;
  },
  language: "en" as const,
  dir: () => "ltr" as const,
};

export default i18n;
