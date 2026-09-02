import { useEffect } from 'react';
import { Sparkles, Bot, Scale, ShoppingCart, ArrowRight, Layers, ShieldCheck, Zap } from 'lucide-react';
import { useTranslation } from '../i18n/LocaleContext';

export default function AiShopping() {
  const { t } = useTranslation();

  // Automatically open the floating AI studio upon entering /ai
  useEffect(() => {
    const timer = setTimeout(() => {
      window.dispatchEvent(new CustomEvent('open-ai-studio'));
    }, 150);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-[85vh] bg-gradient-to-b from-background via-surface/40 to-background flex flex-col items-center justify-center p-6 text-center relative overflow-hidden">
      {/* Background Decorative Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-500/10 dark:bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 max-w-2xl mx-auto space-y-6">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-600 dark:text-indigo-400 text-xs font-bold shadow-xs">
          <Sparkles className="h-3.5 w-3.5 text-indigo-500 animate-pulse" />
          Autonomous Multi-Agent Shopping Engine
        </div>

        <h1 className="text-4xl sm:text-5xl font-extrabold text-primary tracking-tight">
          Experience <span className="bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">RazorHub AI</span>
        </h1>

        <p className="text-base text-secondary max-w-xl mx-auto leading-relaxed">
          Your personal AI shopping agent with real-time catalog search, side-by-side spec comparison, and autonomous checkout assistance.
        </p>

        <div className="pt-2 flex flex-wrap items-center justify-center gap-4">
          <button
            type="button"
            onClick={() => window.dispatchEvent(new CustomEvent('open-ai-studio'))}
            className="inline-flex items-center gap-2 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:opacity-95 text-white font-bold px-6 py-3.5 rounded-2xl shadow-xl shadow-indigo-500/25 transition-all hover:scale-105 active:scale-95 cursor-pointer"
          >
            <Bot className="h-5 w-5" />
            <span>Launch AI Shopping Studio</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>

        {/* Feature Highlights Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-10 text-left">
          <div className="p-4 rounded-2xl border border-border/80 bg-surface/70 backdrop-blur-md">
            <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 w-fit mb-3">
              <Layers className="h-4.5 w-4.5" />
            </div>
            <h3 className="font-bold text-sm text-primary mb-1">Dual-Window Studio</h3>
            <p className="text-xs text-secondary leading-relaxed">
              Real-time synchronization between conversational chat and live visual results canvas.
            </p>
          </div>

          <div className="p-4 rounded-2xl border border-border/80 bg-surface/70 backdrop-blur-md">
            <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-600 dark:text-purple-400 w-fit mb-3">
              <Scale className="h-4.5 w-4.5" />
            </div>
            <h3 className="font-bold text-sm text-primary mb-1">Spec Comparison</h3>
            <p className="text-xs text-secondary leading-relaxed">
              Instant side-by-side spec, rating, and pricing comparison for electronics and fashion.
            </p>
          </div>

          <div className="p-4 rounded-2xl border border-border/80 bg-surface/70 backdrop-blur-md">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 w-fit mb-3">
              <Zap className="h-4.5 w-4.5" />
            </div>
            <h3 className="font-bold text-sm text-primary mb-1">Instant Cart Sync</h3>
            <p className="text-xs text-secondary leading-relaxed">
              Add items and proceed directly to checkout from within the interactive AI canvas.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
