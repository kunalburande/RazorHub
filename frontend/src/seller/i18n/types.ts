export type SupportedLanguage = "en";

export interface LanguageOption {
  code: SupportedLanguage;
  name: string;
  nativeName: string;
  dir: "ltr";
}

export const SUPPORTED_LANGUAGES: LanguageOption[] = [
  {
    code: "en",
    name: "English",
    nativeName: "English",
    dir: "ltr",
  },
];

export const DEFAULT_LANGUAGE: SupportedLanguage = "en";
