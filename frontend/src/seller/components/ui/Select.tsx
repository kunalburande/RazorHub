import { type ReactNode,useEffect, useRef, useState } from "react";

import { AnimatePresence, motion } from "framer-motion";
import { Check, ChevronDown } from "lucide-react";

import { cn } from "../../utils/cn";

export interface SelectOption<T = string> {
  value: T;
  label: string;
  imageURL?: string;
  icon?: ReactNode;
  badge?: string;
}

interface SelectProps<T = string> {
  options: SelectOption<T>[];
  value: T;
  onChange: (value: T) => void;
  label?: string;
  placeholder?: string;
  className?: string;
  size?: "sm" | "md";
  disabled?: boolean;
}

export default function Select<T extends string | number = string>({
  options,
  value,
  onChange,
  label,
  placeholder = "Select an option...",
  className,
  size = "md",
  disabled = false,
}: SelectProps<T>) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedOption =
    options.find((opt) => opt.value === value) || options[0];
  const isSm = size === "sm";

  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const handleSelect = (val: T) => {
    onChange(val);
    setIsOpen(false);
  };

  return (
    <div ref={containerRef} className={cn("w-full", className)}>
      {label && (
        <label className="mb-1.5 block text-xs font-semibold tracking-wider text-gray-700 uppercase dark:text-slate-300">
          {label}
        </label>
      )}
      <div className="relative">
        <button
          type="button"
          disabled={disabled}
          onClick={() => !disabled && setIsOpen((prev) => !prev)}
          className={cn(
            "relative flex w-full cursor-pointer items-center justify-between rounded-xl border border-gray-200/90 bg-white/90 text-left text-gray-900 shadow-2xs backdrop-blur-md transition-all duration-200 hover:border-gray-300 hover:bg-white focus:outline-hidden focus-visible:ring-2 focus-visible:ring-indigo-500/20 dark:border-slate-800 dark:bg-slate-900/90 dark:text-slate-100 dark:hover:border-slate-700 dark:hover:bg-slate-900",
            isSm ? "px-3 py-1.5 text-xs" : "px-3.5 py-2.5 text-xs sm:text-sm",
            disabled && "cursor-not-allowed opacity-50",
          )}
        >
          <div className="flex items-center gap-2.5 overflow-hidden">
            {selectedOption?.imageURL && (
              <img
                src={selectedOption.imageURL}
                alt={selectedOption.label}
                className="h-4 w-4 shrink-0 rounded-full object-cover ring-1 ring-gray-200 dark:ring-slate-700"
              />
            )}
            {selectedOption?.icon && (
              <span className="shrink-0 text-gray-500 dark:text-slate-400">
                {selectedOption.icon}
              </span>
            )}
            <span className="truncate font-medium">
              {selectedOption ? selectedOption.label : placeholder}
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            {selectedOption?.badge && (
              <span className="bg-accent-light text-accent rounded-full px-1.5 py-0.5 text-[10px] font-bold">
                {selectedOption.badge}
              </span>
            )}
            <ChevronDown
              className={cn(
                "h-4 w-4 shrink-0 text-gray-400 transition-transform duration-200 dark:text-slate-500",
                isOpen && "rotate-180",
                isSm && "h-3.5 w-3.5",
              )}
            />
          </div>
        </button>

        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, y: 4, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 4, scale: 0.98 }}
              transition={{ duration: 0.15, ease: "easeOut" }}
              className="absolute start-0 z-50 mt-1.5 max-h-60 w-full overflow-auto rounded-xl border border-gray-200/90 bg-white/95 p-1 text-xs shadow-xl outline-hidden backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/95 dark:text-slate-100"
            >
              {options.map((option) => {
                const isSelected = option.value === value;
                return (
                  <button
                    key={String(option.value)}
                    type="button"
                    onClick={() => handleSelect(option.value)}
                    className={cn(
                      "relative flex w-full cursor-pointer items-center justify-between rounded-lg px-3 py-2 text-left text-gray-700 transition-colors select-none hover:bg-indigo-50/80 hover:text-indigo-600 dark:text-slate-300 dark:hover:bg-indigo-950/40 dark:hover:text-indigo-400",
                      isSelected &&
                        "bg-indigo-50 font-semibold text-indigo-600 dark:bg-indigo-950/50 dark:text-indigo-400",
                    )}
                  >
                    <div className="flex items-center gap-2.5">
                      {option.imageURL && (
                        <img
                          src={option.imageURL}
                          alt={option.label}
                          className="h-4 w-4 shrink-0 rounded-full object-cover"
                        />
                      )}
                      {option.icon && (
                        <span className="shrink-0 text-gray-400 dark:text-slate-500">
                          {option.icon}
                        </span>
                      )}
                      <span className="block truncate font-medium">
                        {option.label}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {option.badge && (
                        <span className="bg-accent-light text-accent rounded-full px-1.5 py-0.5 text-[10px] font-bold">
                          {option.badge}
                        </span>
                      )}
                      {isSelected && (
                        <Check className="h-3.5 w-3.5 shrink-0 text-indigo-600 dark:text-indigo-400" />
                      )}
                    </div>
                  </button>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
