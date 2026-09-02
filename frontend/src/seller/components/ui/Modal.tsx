import { type ReactNode,useEffect } from "react";

import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";

interface Props {
  isOpen?: boolean;
  closeModal: () => void;
  title?: string;
  children?: ReactNode;
}

const Modal = ({ isOpen = false, closeModal, title, children }: Props) => {
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        closeModal();
      }
    };

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = originalOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, closeModal]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="relative z-50 focus:outline-none">
          {/* Dimmed & Blurred Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={closeModal}
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs"
          />

          <div className="fixed inset-0 z-10 w-screen overflow-y-auto">
            <div className="flex min-h-full items-center justify-center p-4">
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 10 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 10 }}
                transition={{ type: "spring", damping: 25, stiffness: 350 }}
                className="w-full max-w-lg overflow-hidden rounded-2xl border border-gray-100 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900"
              >
                {/* Modal Header */}
                <div className="mb-4 flex items-center justify-between border-b border-gray-100 pb-4 dark:border-slate-800">
                  <div className="flex items-center gap-x-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-indigo-100 bg-indigo-50 text-indigo-600 dark:border-indigo-900 dark:bg-indigo-950/60 dark:text-indigo-400">
                      <svg
                        className="h-5 w-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 4v16m8-8H4"
                        />
                      </svg>
                    </div>
                    {title && (
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                        {title}
                      </h3>
                    )}
                  </div>

                  {/* Close Button */}
                  <button
                    type="button"
                    onClick={closeModal}
                    className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-full text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
                    aria-label="Close modal"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>

                <div>{children}</div>
              </motion.div>
            </div>
          </div>
        </div>
      )}
    </AnimatePresence>
  );
};

export default Modal;
