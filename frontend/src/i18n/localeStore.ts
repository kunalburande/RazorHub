export type Locale = 'en';

export const LOCALE_STORAGE_KEY = 'razorhub_locale';

export function isLocale(value: string | null | undefined): value is Locale {
  return value === 'en';
}

let currentLocale: Locale = 'en';
const listeners = new Set<(locale: Locale) => void>();

export function getLocaleLabel(_locale: Locale = 'en') {
  return 'English';
}

export function getLocaleDirection(_locale: Locale = 'en') {
  return 'ltr' as const;
}

export function getStoredLocale(): Locale {
  return 'en';
}

export function getCurrentLocale(): Locale {
  return currentLocale;
}

export function setCurrentLocale(locale: Locale) {
  currentLocale = locale;
  listeners.forEach((listener) => listener(locale));
}

export function subscribeLocale(listener: (locale: Locale) => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
