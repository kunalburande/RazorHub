import React, { useState, useEffect } from 'react';
import { Sparkles, X } from 'lucide-react';
import CommerceStudio from './CommerceStudio';

export default function AiAssistantWidget() {
  const [open, setOpen] = useState(false);

  // Close on ESC key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <>
      {/* ── Floating Launcher Pill Button (when Studio is closed) ── */}
      {!open && (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 rounded-full bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-600 px-4 py-3 text-sm font-bold text-white shadow-2xl shadow-indigo-500/40 hover:scale-105 hover:shadow-indigo-500/60 active:scale-95 transition-all duration-300 group cursor-pointer border border-white/20"
          aria-label="Open AI Shopping Studio"
        >
          <div className="relative">
            <Sparkles className="h-5 w-5 text-amber-300 animate-pulse" />
            <span className="absolute -top-1 -right-1 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
          </div>
          <span className="tracking-wide font-extrabold">AI Shop</span>
        </button>
      )}

      {/* ── Dual-Window Floating AI Shopping Studio (when open) ── */}
      {open && (
        <div className="fixed inset-0 z-[85] pointer-events-none transition-all duration-300">
          {/* Subtle Ambient Backdrop */}
          <div
            onClick={() => setOpen(false)}
            className="absolute inset-0 bg-black/60 backdrop-blur-md pointer-events-auto transition-opacity animate-in fade-in duration-300"
          />

          {/* Floating Dual-Window Container */}
          <div className="absolute top-4 sm:top-6 bottom-4 sm:bottom-6 left-2 sm:left-6 right-2 sm:right-6 max-w-[1720px] mx-auto pointer-events-auto overflow-hidden shadow-2xl rounded-3xl">
            <CommerceStudio isFloating={true} onClose={() => setOpen(false)} />
          </div>
        </div>
      )}
    </>
  );
}
