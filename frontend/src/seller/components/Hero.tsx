import { useCallback, useEffect, useState } from "react";

import { AnimatePresence, motion } from "framer-motion";
import { Bot, ChevronLeft, ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";

import { useTranslation } from "../i18n";
import Button from "./ui/Button";

interface Props {
  onAddProduct: () => void;
}

const Hero = ({ onAddProduct }: Props) => {
  const { t } = useTranslation();
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  const heroSlides = [
    {
      id: 1,
      badge: t("hero.slide1.badge", "🚀 Product Dashboard 2.0"),
      headingTitle: t("hero.slide1.headingTitle", "Build & Manage Your"),
      headingHighlight: t("hero.slide1.headingHighlight", "Premium Collection"),
      subtitle: t(
        "hero.slide1.subtitle",
        "Seamlessly add, edit, and organize your catalog of luxury accessories, electronics, sneakers, and modern lifestyle items in one place.",
      ),
      ctaPrimaryText: t("hero.slide1.ctaPrimary", "+ Add New Product"),
      ctaPrimaryAction: "add",
      ctaSecondaryText: t("hero.slide1.ctaSecondary", "Explore Catalog ↓"),
      ctaSecondaryHref: "#products-grid",
      gradient: "from-indigo-900 via-indigo-800 to-slate-900",
      glowColor1: "bg-indigo-500/20",
      glowColor2: "bg-purple-500/20",
    },
    {
      id: 2,
      badge: t("hero.slide2.badge", "📊 Visual Insights"),
      headingTitle: t("hero.slide2.headingTitle", "Track Catalog Worth &"),
      headingHighlight: t(
        "hero.slide2.headingHighlight",
        "Market Share Trends",
      ),
      subtitle: t(
        "hero.slide2.subtitle",
        "Real-time SVG market share charts, 12-month revenue curve graphs, and category intelligence metrics at your fingertips.",
      ),
      ctaPrimaryText: t("hero.slide2.ctaPrimary", "+ Add Product"),
      ctaPrimaryAction: "add",
      ctaSecondaryText: t("hero.slide2.ctaSecondary", "View Analytics ↓"),
      ctaSecondaryHref: "#analytics-section",
      gradient: "from-purple-900 via-slate-900 to-indigo-950",
      glowColor1: "bg-purple-500/25",
      glowColor2: "bg-pink-500/20",
    },
    {
      id: 3,
      badge: t("hero.slide3.badge", "⚡ High-Speed Catalog"),
      headingTitle: t("hero.slide3.headingTitle", "Instant Product Search &"),
      headingHighlight: t(
        "hero.slide3.headingHighlight",
        "Smart Category Filters",
      ),
      subtitle: t(
        "hero.slide3.subtitle",
        "Filter luxury goods by category, price range, or custom colors with instant real-time sorting and zero reload latency.",
      ),
      ctaPrimaryText: t("hero.slide3.ctaPrimary", "+ Add Product"),
      ctaPrimaryAction: "add",
      ctaSecondaryText: t("hero.slide3.ctaSecondary", "Categories ↓"),
      ctaSecondaryHref: "#categories-section",
      gradient: "from-slate-900 via-cyan-950 to-indigo-900",
      glowColor1: "bg-cyan-500/20",
      glowColor2: "bg-indigo-500/25",
    },
  ];

  const scrollPrev = useCallback(() => {
    setSelectedIndex((prev) => (prev === 0 ? heroSlides.length - 1 : prev - 1));
  }, [heroSlides.length]);

  const scrollNext = useCallback(() => {
    setSelectedIndex((prev) => (prev === heroSlides.length - 1 ? 0 : prev + 1));
  }, [heroSlides.length]);

  const scrollTo = useCallback((index: number) => {
    setSelectedIndex(index);
  }, []);

  // Auto-play effect with pause on hover
  useEffect(() => {
    if (isPaused) return;
    const interval = setInterval(() => {
      scrollNext();
    }, 5000);
    return () => clearInterval(interval);
  }, [isPaused, scrollNext]);

  const activeSlide = heroSlides[selectedIndex] || heroSlides[0];

  return (
    <div
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      className={`relative mb-10 overflow-hidden rounded-3xl bg-linear-to-r ${activeSlide.gradient} text-white shadow-2xl transition-all duration-700 select-none`}
    >
      {/* Decorative Blur Orbs */}
      <div
        className={`pointer-events-none absolute -top-24 -right-24 h-96 w-96 rounded-full ${activeSlide.glowColor1} blur-3xl transition-all duration-700`}
      />
      <div
        className={`pointer-events-none absolute -bottom-24 -left-24 h-96 w-96 rounded-full ${activeSlide.glowColor2} blur-3xl transition-all duration-700`}
      />

      {/* Slide Container */}
      <div className="relative min-h-70 w-full overflow-hidden p-5 pb-16 min-[360px]:p-8 min-[360px]:pb-16 md:p-12 md:pb-20">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeSlide.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.35, ease: "easeInOut" }}
            className="relative z-10 max-w-2xl min-w-0 sm:pl-2"
          >
            {/* Badge */}
            <div className="mb-4 inline-flex max-w-full items-center gap-x-2 rounded-full border border-indigo-400/30 bg-indigo-500/10 px-3.5 py-1 text-xs font-semibold [overflow-wrap:anywhere] break-words text-indigo-200 backdrop-blur-md">
              <span className="h-2 w-2 shrink-0 animate-pulse rounded-full bg-indigo-400" />
              <span className="[overflow-wrap:anywhere] break-words">
                {activeSlide.badge}
              </span>
            </div>

            {/* Heading */}
            <h1 className="mb-4 text-2xl leading-tight font-extrabold tracking-tight [overflow-wrap:anywhere] break-words min-[360px]:text-3xl md:text-5xl">
              {activeSlide.headingTitle} <br />
              <span className="bg-linear-to-r from-indigo-200 via-purple-200 to-pink-200 bg-clip-text [overflow-wrap:anywhere] break-words text-transparent">
                {activeSlide.headingHighlight}
              </span>
            </h1>

            {/* Subtitle */}
            <p className="mb-6 text-xs leading-relaxed [overflow-wrap:anywhere] break-words text-indigo-100/80 min-[360px]:text-sm md:text-base">
              {activeSlide.subtitle}
            </p>

            {/* CTAs */}
            <div className="flex flex-col flex-wrap items-stretch gap-3 min-[360px]:flex-row min-[360px]:items-center">
              <Button
                onClick={onAddProduct}
                className="bg-accent hover:bg-accent-hover w-full cursor-pointer px-5 py-2.5 text-center text-xs font-medium text-white shadow-lg transition-all min-[360px]:w-fit min-[360px]:px-6 min-[360px]:py-3 min-[360px]:text-sm"
              >
                {activeSlide.ctaPrimaryText}
              </Button>

              <Link
                to="/agents"
                className="inline-flex w-full cursor-pointer items-center justify-center gap-x-2 rounded-xl border border-indigo-400/40 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 px-4 py-2.5 text-center text-xs font-bold text-white shadow-lg shadow-indigo-600/30 transition-all hover:scale-105 active:scale-95 min-[360px]:w-auto min-[360px]:px-5 min-[360px]:py-3 min-[360px]:text-sm"
              >
                <Bot className="h-4 w-4 text-cyan-300 animate-pulse" />
                <span>Agent Studio →</span>
              </Link>

              <a
                href={activeSlide.ctaSecondaryHref}
                onClick={(e) => {
                  e.preventDefault();
                  const targetId = activeSlide.ctaSecondaryHref.replace(
                    "#",
                    "",
                  );
                  document
                    .getElementById(targetId)
                    ?.scrollIntoView({ behavior: "smooth" });
                }}
                className="inline-flex w-full cursor-pointer items-center justify-center gap-x-2 rounded-xl border border-white/20 bg-white/10 px-4 py-2.5 text-center text-xs font-medium text-white backdrop-blur-md transition-all hover:bg-white/20 min-[360px]:w-auto min-[360px]:px-5 min-[360px]:py-3 min-[360px]:text-sm"
              >
                {activeSlide.ctaSecondaryText}
              </a>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Baseline Navigation Row */}
      <div className="pointer-events-none">
        {/* Left Navigation Arrow */}
        <button
          type="button"
          onClick={scrollPrev}
          className="pointer-events-auto absolute inset-s-5 bottom-5 z-20 flex h-8 w-8 cursor-pointer items-center justify-center rounded-full border border-white/10 bg-white/5 text-white/60 backdrop-blur-md transition-all duration-200 hover:scale-105 hover:bg-white/15 hover:text-white active:scale-95 md:inset-s-10"
          aria-label={t("hero.prevSlide", "Previous Slide")}
          title={t("hero.prevSlide", "Previous Slide")}
        >
          <ChevronLeft className="h-4 w-4" />
        </button>

        {/* Minimal Centered Pagination Dots */}
        <div className="pointer-events-auto absolute bottom-6 left-1/2 z-20 flex -translate-x-1/2 items-center gap-x-2">
          {heroSlides.map((s, idx) => (
            <button
              key={s.id}
              type="button"
              onClick={() => scrollTo(idx)}
              className={`cursor-pointer rounded-full transition-all duration-300 ${
                selectedIndex === idx
                  ? "h-1.5 w-5 bg-white/90 shadow-xs shadow-white/30"
                  : "h-1.5 w-1.5 bg-white/30 hover:bg-white/60"
              }`}
              aria-label={t("hero.goToSlide", {
                index: idx + 1,
                defaultValue: `Go to slide ${idx + 1}`,
              })}
              title={`Slide ${idx + 1}`}
            />
          ))}
        </div>

        {/* Right Navigation Arrow */}
        <button
          type="button"
          onClick={scrollNext}
          className="pointer-events-auto absolute inset-e-5 bottom-5 z-20 flex h-8 w-8 cursor-pointer items-center justify-center rounded-full border border-white/10 bg-white/5 text-white/60 backdrop-blur-md transition-all duration-200 hover:scale-105 hover:bg-white/15 hover:text-white active:scale-95 md:inset-e-10"
          aria-label={t("hero.nextSlide", "Next Slide")}
          title={t("hero.nextSlide", "Next Slide")}
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};

export default Hero;
