import { useEffect } from "react";

import { AnimatePresence, motion } from "framer-motion";

import { useAI } from "../../context/AIContext";
import AIHeader from "./AIHeader";
import AIInput from "./AIInput";
import AIMessageList from "./AIMessageList";

export default function AIChatPanel() {
  const { isOpen, setIsOpen } = useAI();

  // Close on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, setIsOpen]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={() => setIsOpen(false)}
            className="fixed inset-0 bg-black/40 backdrop-blur-xs"
          />

          {/* Floating Panel */}
          <div className="fixed inset-x-3 top-16 bottom-4 z-50 flex flex-col justify-end sm:inset-auto sm:top-[72px] sm:bottom-6 sm:right-6 sm:left-auto">
            <motion.div
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 20, scale: 0.95 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="flex w-full flex-col overflow-hidden rounded-2xl border border-zinc-200/80 bg-white shadow-2xl dark:border-zinc-800 dark:bg-zinc-900 
                h-[calc(100svh-5.5rem)] min-h-[calc(100svh-5.5rem)] max-h-[calc(100svh-5.5rem)]
                sm:w-[480px] sm:min-w-[480px] sm:max-w-[480px] sm:h-[calc(100vh-6rem)] sm:min-h-[calc(100vh-6rem)] sm:max-h-[calc(100vh-6rem)]"
            >
              {/* Header */}
              <AIHeader onClose={() => setIsOpen(false)} />

              {/* Messages Area */}
              <AIMessageList />

              {/* Input Area */}
              <AIInput />
            </motion.div>
          </div>
        </div>
      )}
    </AnimatePresence>
  );
}
