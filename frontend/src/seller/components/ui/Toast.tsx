import { useEffect } from "react";

import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";

export interface ToastMessage {
  id: string;
  type: "success" | "error" | "info";
  title: string;
  message: string;
  count?: number;
  resetCounter?: number;
}

interface ToastProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

const Toast = ({ toasts, onDismiss }: ToastProps) => {
  return (
    <div className="pointer-events-none fixed right-5 bottom-5 z-50 flex w-full max-w-sm flex-col gap-y-2.5 px-4 sm:px-0">
      <AnimatePresence mode="popLayout">
        {toasts.slice(0, 3).map((toast) => (
          <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
        ))}
      </AnimatePresence>
    </div>
  );
};

const ToastItem = ({
  toast,
  onDismiss,
}: {
  toast: ToastMessage;
  onDismiss: (id: string) => void;
}) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss(toast.id);
    }, 4000);

    return () => clearTimeout(timer);
  }, [toast.id, toast.resetCounter, onDismiss]);

  const bgStyles =
    toast.type === "success"
      ? "bg-slate-900 dark:bg-slate-800 text-white border border-emerald-500/30 shadow-emerald-950/20"
      : toast.type === "error"
        ? "bg-rose-950 text-white border border-rose-500/40 shadow-rose-950/20"
        : "bg-indigo-950 text-white border border-indigo-500/40 shadow-indigo-950/20";

  const icon =
    toast.type === "success" ? "🎉" : toast.type === "error" ? "⚠️" : "ℹ️";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
      transition={{ type: "spring", stiffness: 380, damping: 26 }}
      className={`pointer-events-auto flex items-start gap-x-3 rounded-2xl p-4 shadow-xl backdrop-blur-md ${bgStyles}`}
    >
      <span className="text-base leading-none">{icon}</span>
      <div className="min-w-0 flex-1">
        <h5 className="flex items-center gap-1.5 text-xs leading-tight font-bold">
          {toast.title}
          {toast.count && toast.count > 1 && (
            <span className="inline-flex items-center justify-center rounded-full bg-white/20 px-1.5 py-0.5 text-[9px] font-bold dark:bg-white/10">
              x{toast.count}
            </span>
          )}
        </h5>
        <p className="mt-0.5 text-[11px] leading-relaxed opacity-90">
          {toast.message}
        </p>
      </div>
      <button
        type="button"
        onClick={() => onDismiss(toast.id)}
        className="cursor-pointer text-xs text-gray-400 transition-colors hover:text-white"
        aria-label="Close Toast"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </motion.div>
  );
};

export default Toast;
