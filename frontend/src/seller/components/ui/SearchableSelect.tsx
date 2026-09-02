import { useEffect, useMemo, useRef, useState } from "react";

import { AnimatePresence, motion } from "framer-motion";
import { Check, ChevronDown, Globe, Search } from "lucide-react";

import { useTranslation } from "../../i18n";
import { cn } from "../../utils/cn";

interface CountryOption {
  code: string;
  name: string;
  flag: string;
}

const COUNTRIES: CountryOption[] = [
  { code: "IN", name: "India", flag: "🇮🇳" }
];

interface SearchableSelectProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export default function SearchableSelect({
  value,
  onChange,
  placeholder,
}: SearchableSelectProps) {
  const { t } = useTranslation();
  const defaultPlaceholder =
    placeholder || t("users.modal.selectCountry", "Select a country");
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const selectedCountry = useMemo(() => {
    return COUNTRIES.find((c) => c.name.toLowerCase() === value.toLowerCase());
  }, [value]);

  const filteredCountries = useMemo(() => {
    if (!search.trim()) return COUNTRIES;
    const q = search.toLowerCase();
    return COUNTRIES.filter(
      (c) =>
        c.name.toLowerCase().includes(q) || c.code.toLowerCase().includes(q),
    );
  }, [search]);

  useEffect(() => {
    if (!open) return;

    inputRef.current?.focus();

    const handleClickOutside = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
        setSearch("");
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        setSearch("");
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  const handleToggle = () => {
    if (open) {
      setOpen(false);
      setSearch("");
    } else {
      setOpen(true);
    }
  };

  return (
    <div ref={containerRef} className="relative w-full">
      <button
        type="button"
        onClick={handleToggle}
        aria-haspopup="listbox"
        aria-expanded={open}
        className="relative flex h-10 w-full cursor-pointer items-center justify-between rounded-lg border border-zinc-200 bg-zinc-50 ps-9 pe-3.5 text-left text-sm text-zinc-900 outline-hidden transition-all select-none hover:bg-zinc-100/50 focus:ring-2 focus:ring-zinc-400 dark:border-zinc-700 dark:bg-zinc-800/50 dark:text-zinc-100 dark:hover:bg-zinc-800 dark:focus:ring-zinc-600"
      >
        <span className="pointer-events-none absolute inset-y-0 inset-s-0 flex items-center ps-3 text-zinc-400">
          <Globe className="h-4 w-4" />
        </span>
        <span className="block truncate">
          {selectedCountry ? (
            <span className="flex items-center gap-2">
              <span>{selectedCountry.flag}</span>
              <span>{selectedCountry.name}</span>
            </span>
          ) : (
            <span className="text-zinc-400 dark:text-zinc-500">
              {defaultPlaceholder}
            </span>
          )}
        </span>
        <ChevronDown
          className={cn(
            "h-4 w-4 shrink-0 text-zinc-400 transition-transform duration-200 dark:text-zinc-500",
            open && "rotate-180",
          )}
        />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 4, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.98 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className="absolute start-0 z-50 mt-1 max-h-64 w-full overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-xl dark:border-zinc-800 dark:bg-zinc-900"
          >
            <div className="flex items-center border-b border-zinc-100 px-3 py-2 dark:border-zinc-800">
              <Search className="me-2 h-4 w-4 shrink-0 text-zinc-400" />
              <input
                ref={inputRef}
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={t(
                  "users.modal.searchCountries",
                  "Search countries...",
                )}
                className="w-full bg-transparent text-xs text-zinc-900 placeholder:text-zinc-400 focus:outline-hidden dark:text-zinc-100 dark:placeholder:text-zinc-500"
              />
            </div>

            <div className="max-h-48 overflow-y-auto p-1 text-xs">
              {filteredCountries.length === 0 ? (
                <div className="py-6 text-center text-xs text-zinc-500">
                  {t("users.modal.noCountries", "No countries found.")}
                </div>
              ) : (
                filteredCountries.map((country) => {
                  const isSelected = selectedCountry?.name === country.name;
                  return (
                    <button
                      key={country.code}
                      type="button"
                      onClick={() => {
                        onChange(country.name);
                        setOpen(false);
                        setSearch("");
                      }}
                      className={cn(
                        "flex w-full cursor-pointer items-center justify-between rounded-lg px-2.5 py-1.5 text-left text-zinc-700 transition-colors select-none hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800/70",
                        isSelected &&
                        "bg-blue-50/80 font-semibold text-blue-600 dark:bg-blue-500/15 dark:text-blue-400",
                      )}
                    >
                      <span className="flex items-center gap-2.5">
                        <span className="text-sm leading-none">
                          {country.flag}
                        </span>
                        <span>{country.name}</span>
                      </span>
                      {isSelected && (
                        <Check className="h-3.5 w-3.5 shrink-0 text-blue-600 dark:text-blue-400" />
                      )}
                    </button>
                  );
                })
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
