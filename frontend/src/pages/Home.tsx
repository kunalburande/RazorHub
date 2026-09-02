import { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  Truck,
  ShieldCheck,
  RefreshCw,
  Flame,
  Star,
  Tag,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  Store,
  Clock,
  Zap,
  CreditCard,
  Percent,
} from 'lucide-react';

import ProductCard from '../components/ProductCard';
import AiInsightPanel from '../components/AiInsightPanel';
import { API, formatPrice, price, productImage } from '../lib/products';
import { marketAiOverview } from '../lib/ai';
import { getCategoryIcon } from '../lib/categoryIcons';
import type { CategoryType, ProductType } from '../lib/products';
import { useTranslation } from '../i18n/LocaleContext';
import Seo from '../components/Seo';

// ── Hero Banner Slides (Inspired by Vijay Sales, JioMart, Etsy) ──
const HERO_SLIDES = [
  {
    id: 1,
    badge: 'NEW LAUNCH • GALAXY AI',
    title: 'Samsung Galaxy S26 Ultra',
    subtitle: 'Next-generation AI photography, titanium build, and Snapdragon 8 Gen 4 power.',
    discount: 'UP TO ₹15,000 EXCHANGE BONUS',
    cta: 'Explore Flagship',
    link: '/products?category=mobiles',
    bgGradient: 'from-slate-900 via-indigo-950 to-slate-900',
    tagColor: 'bg-blue-500/20 text-blue-300 border-blue-400/30',
    image: 'https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?w=1200&auto=format&fit=crop&q=80',
  },
  {
    id: 2,
    badge: 'HELLO MONSOON MEGA SALE',
    title: 'Home & Kitchen Appliances',
    subtitle: 'Smart Inverter Air Conditioners, 4K OLED TVs, and Front-Load Washing Machines.',
    discount: 'FLAT 50% OFF + NO COST EMI',
    cta: 'Shop Appliances',
    link: '/products?category=appliances',
    bgGradient: 'from-amber-950 via-zinc-900 to-stone-900',
    tagColor: 'bg-amber-500/20 text-amber-300 border-amber-400/30',
    image: 'https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=1200&auto=format&fit=crop&q=80',
  },
  {
    id: 3,
    badge: 'THE GOURMET & SNACK BASH',
    title: 'Fresh Groceries & Bakery',
    subtitle: 'Imported cookies, artisan sourdough, organic pantry staples, and beverages.',
    discount: 'STARTS AT ₹19 • 33% OFF',
    cta: 'Shop Groceries',
    link: '/products?category=groceries',
    bgGradient: 'from-emerald-950 via-teal-950 to-stone-900',
    tagColor: 'bg-emerald-500/20 text-emerald-300 border-emerald-400/30',
    image: 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=1200&auto=format&fit=crop&q=80',
  },
  {
    id: 4,
    badge: 'CREATIVE SELLER SPOTLIGHT',
    title: 'Handcrafted Fashion & Jewelry',
    subtitle: 'Unique handmade apparel, bohemian accessories, and custom home décor.',
    discount: 'OVER 1,000+ ARTISAN CREATORS',
    cta: 'Discover Creators',
    link: '/products?category=fashion',
    bgGradient: 'from-rose-950 via-purple-950 to-zinc-900',
    tagColor: 'bg-rose-500/20 text-rose-300 border-rose-400/30',
    image: 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=1200&auto=format&fit=crop&q=80',
  },
];

// ── Bank Offers (Vijay Sales Style) ──
const BANK_OFFERS = [
  {
    bank: 'ICICI Bank',
    offer: 'Get 5% Upto ₹7,500 Instant Discount',
    card: 'ICICI Bank Credit Cards EMI',
    badge: 'ICICI',
    color: 'border-orange-500/30 bg-orange-500/5 text-orange-600 dark:text-orange-400',
  },
  {
    bank: 'HSBC',
    offer: 'Get Upto ₹12,000 Instant Discount',
    card: 'HSBC Bank Cards for EMI & Non-EMI',
    badge: 'HSBC',
    color: 'border-red-500/30 bg-red-500/5 text-red-600 dark:text-red-400',
  },
  {
    bank: 'HDFC Bank',
    offer: 'Flat ₹2,500 Instant Cashback',
    card: 'HDFC Credit & Debit Cards EMI',
    badge: 'HDFC',
    color: 'border-blue-500/30 bg-blue-500/5 text-blue-600 dark:text-blue-400',
  },
  {
    bank: 'YES Bank',
    offer: 'Get 5% Instant Discount Upto ₹2,500',
    card: 'YES Bank Credit Card EMI',
    badge: 'YES BANK',
    color: 'border-cyan-500/30 bg-cyan-500/5 text-cyan-600 dark:text-cyan-400',
  },
  {
    bank: 'Razorpay UPI',
    offer: 'Extra ₹500 Instant Discount',
    card: 'UPI / Cards with Razorpay Test Mode',
    badge: 'RAZORPAY',
    color: 'border-indigo-500/30 bg-indigo-500/5 text-indigo-600 dark:text-indigo-400',
  },
];

// ── Visual Category Bubbles (Vijay Sales / JioMart Style) ──
const VISUAL_CATEGORIES = [
  { name: 'Mobiles', slug: 'mobiles', emoji: '📱', bg: 'from-blue-500/20 to-indigo-500/20' },
  { name: 'Laptops', slug: 'laptops', emoji: '💻', bg: 'from-purple-500/20 to-pink-500/20' },
  { name: 'Air Conditioners', slug: 'appliances', emoji: '❄️', bg: 'from-cyan-500/20 to-blue-500/20' },
  { name: 'Television', slug: 'electronics', emoji: '📺', bg: 'from-rose-500/20 to-red-500/20' },
  { name: 'Washing Machines', slug: 'appliances', emoji: '🫧', bg: 'from-teal-500/20 to-emerald-500/20' },
  { name: 'Audio & Sound', slug: 'audio', emoji: '🎧', bg: 'from-amber-500/20 to-orange-500/20' },
  { name: 'Fashion & Style', slug: 'fashion', emoji: '👗', bg: 'from-fuchsia-500/20 to-purple-500/20' },
  { name: 'Fresh Groceries', slug: 'groceries', emoji: '🥑', bg: 'from-emerald-500/20 to-lime-500/20' },
];

function SectionHeader({
  icon: Icon,
  title,
  subtitle,
  linkTo,
  linkLabel,
  badge,
}: {
  icon?: React.ElementType;
  title: string;
  subtitle?: string;
  linkTo?: string;
  linkLabel?: string;
  badge?: string;
}) {
  return (
    <div className="mb-5 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        {Icon && (
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent/10 text-accent">
            <Icon className="h-5 w-5" />
          </span>
        )}
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold tracking-tight text-primary sm:text-2xl">{title}</h2>
            {badge && (
              <span className="rounded-full bg-accent/10 border border-accent/20 px-2 py-0.5 text-[10px] font-extrabold uppercase tracking-wider text-accent">
                {badge}
              </span>
            )}
          </div>
          {subtitle && <p className="text-xs text-secondary mt-0.5">{subtitle}</p>}
        </div>
      </div>
      {linkTo && (
        <Link
          to={linkTo}
          className="flex items-center gap-1 text-xs sm:text-sm font-semibold text-accent hover:underline shrink-0"
        >
          {linkLabel || 'View all'} <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      )}
    </div>
  );
}

export default function Home() {
  const { t } = useTranslation();
  const [currentSlide, setCurrentSlide] = useState(0);
  const [products, setProducts] = useState<ProductType[]>([]);
  const [categories, setCategories] = useState<CategoryType[]>([]);
  const [loading, setLoading] = useState(true);

  // Auto slide
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % HERO_SLIDES.length);
    }, 5500);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/homepage/`).then((r) => r.json()).catch(() => null),
      fetch(`${API}/categories/`).then((r) => r.json()).catch(() => []),
    ])
      .then(([homeData, catData]) => {
        if (homeData && homeData.featured) {
          const combined = [
            ...(homeData.featured || []),
            ...(homeData.newest || []),
            ...(homeData.flash_deals || []),
          ];
          const unique = Array.from(new Map(combined.map((item) => [item.id, item])).values());
          setProducts(unique);
        }
        setCategories(catData || []);
      })
      .finally(() => setLoading(false));
  }, []);

  const flashDeals = products.filter((p) => p.is_featured || p.discount_price).slice(0, 4);
  const bestOfTech = products.filter((p) => ['mobiles', 'laptops', 'electronics', 'appliances', 'audio'].includes(p.category?.slug || '')).slice(0, 4);
  const trendingApparel = products.filter((p) => ['fashion', 'beauty', 'accessories'].includes(p.category?.slug || '')).slice(0, 4);
  const allDeals = products.slice(0, 8);

  const prevSlide = () => setCurrentSlide((p) => (p - 1 + HERO_SLIDES.length) % HERO_SLIDES.length);
  const nextSlide = () => setCurrentSlide((p) => (p + 1) % HERO_SLIDES.length);

  return (
    <div className="space-y-8 pb-16">
      <Seo
        title="RazorHub — Electronics, Mobiles, Fashion & Daily Essentials"
        description="Shop the best deals in India on electronics, smartphones, laptops, appliances, fashion, and groceries with fast local delivery."
      />

      {/* ── 1. Hero Carousel Banner (Vijay Sales / JioMart / Etsy Style) ── */}
      <section className="mx-auto max-w-[1360px] w-full px-4 sm:px-6 lg:px-8 pt-4 sm:pt-6">
        <div className="relative overflow-hidden rounded-2xl md:rounded-3xl border border-border shadow-lg">
          <div
            className="flex transition-transform duration-700 ease-out"
            style={{ transform: `translateX(-${currentSlide * 100}%)` }}
          >
            {HERO_SLIDES.map((slide) => (
              <div
                key={slide.id}
                className={`relative w-full shrink-0 min-h-[300px] sm:min-h-[380px] md:min-h-[440px] flex items-center bg-gradient-to-r ${slide.bgGradient} text-white p-6 sm:p-10 lg:p-14`}
              >
                {/* Background Artwork */}
                <div className="absolute inset-0 opacity-25 mix-blend-overlay">
                  <img
                    src={slide.image}
                    alt={slide.title}
                    className="h-full w-full object-cover object-center"
                    loading="lazy"
                  />
                </div>
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />

                {/* Banner Content */}
                <div className="relative z-10 max-w-xl space-y-3 sm:space-y-4">
                  <div className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[11px] font-extrabold uppercase tracking-wider backdrop-blur-md">
                    <span className="h-2 w-2 rounded-full bg-accent animate-pulse" />
                    <span>{slide.badge}</span>
                  </div>

                  <h1 className="text-2xl font-black tracking-tight sm:text-4xl lg:text-5xl leading-tight">
                    {slide.title}
                  </h1>

                  <p className="text-xs sm:text-sm text-zinc-200 line-clamp-2 sm:line-clamp-3">
                    {slide.subtitle}
                  </p>

                  <div className="pt-2 flex flex-wrap items-center gap-3">
                    <span className="inline-block rounded-lg bg-white/10 px-3 py-1.5 text-xs font-black text-amber-300 backdrop-blur-xs border border-white/15">
                      {slide.discount}
                    </span>
                    <Link
                      to={slide.link}
                      className="inline-flex items-center gap-2 rounded-xl bg-accent px-5 py-2.5 text-xs sm:text-sm font-bold text-white shadow-md hover:opacity-90 transition-opacity"
                    >
                      {slide.cta} <ArrowRight className="h-4 w-4" />
                    </Link>
                  </div>
                </div>

                {/* Right Decorative Image on Desktop */}
                <div className="hidden lg:block absolute right-12 bottom-6 top-6 w-[420px] rounded-2xl overflow-hidden shadow-2xl border border-white/10">
                  <img
                    src={slide.image}
                    alt={slide.title}
                    className="h-full w-full object-cover object-center"
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Carousel Arrows */}
          <button
            type="button"
            onClick={prevSlide}
            aria-label="Previous Slide"
            className="absolute left-3 top-1/2 -translate-y-1/2 flex h-9 w-9 sm:h-11 sm:w-11 items-center justify-center rounded-full bg-black/40 hover:bg-black/70 text-white backdrop-blur-md transition-all shadow-md"
          >
            <ChevronLeft className="h-5 w-5 sm:h-6 sm:w-6" />
          </button>
          <button
            type="button"
            onClick={nextSlide}
            aria-label="Next Slide"
            className="absolute right-3 top-1/2 -translate-y-1/2 flex h-9 w-9 sm:h-11 sm:w-11 items-center justify-center rounded-full bg-black/40 hover:bg-black/70 text-white backdrop-blur-md transition-all shadow-md"
          >
            <ChevronRight className="h-5 w-5 sm:h-6 sm:w-6" />
          </button>

          {/* Dots Indicator */}
          <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-2">
            {HERO_SLIDES.map((_, i) => (
              <button
                key={i}
                onClick={() => setCurrentSlide(i)}
                aria-label={`Slide ${i + 1}`}
                className={`h-2 rounded-full transition-all ${
                  currentSlide === i ? 'w-6 bg-accent' : 'w-2 bg-white/50 hover:bg-white'
                }`}
              />
            ))}
          </div>
        </div>
      </section>

      {/* ── 2. Bank Offers & Partner Strip (Vijay Sales Style) ── */}
      <section className="mx-auto max-w-[1360px] w-full px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-hide">
          {BANK_OFFERS.map((bank, idx) => (
            <div
              key={idx}
              className={`shrink-0 w-[240px] sm:w-[260px] rounded-xl border p-3 bg-surface shadow-2xs transition-all hover:shadow-sm ${bank.color}`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-md bg-muted text-primary border border-border">
                  {bank.badge}
                </span>
                <span className="text-[9px] text-secondary font-medium">*T&C Apply</span>
              </div>
              <p className="text-xs font-bold text-primary line-clamp-1">{bank.offer}</p>
              <p className="text-[11px] text-secondary truncate mt-0.5">{bank.card}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── 3. Visual Category Strip (Vijay Sales / JioMart Style) ── */}
      <section className="mx-auto max-w-[1360px] w-full px-4 sm:px-6 lg:px-8">
        <div className="rounded-2xl border border-border bg-surface p-4 sm:p-5 shadow-2xs">
          <div className="grid grid-cols-4 sm:grid-cols-4 md:grid-cols-8 gap-3 sm:gap-4 text-center">
            {VISUAL_CATEGORIES.map((cat) => (
              <Link
                key={cat.name}
                to={`/products?category=${cat.slug}`}
                className="group flex flex-col items-center gap-2 p-2 rounded-xl hover:bg-muted/60 transition-colors"
              >
                <div
                  className={`flex h-14 w-14 sm:h-16 sm:w-16 items-center justify-center rounded-2xl bg-gradient-to-tr ${cat.bg} text-2xl sm:text-3xl shadow-xs transition-transform group-hover:scale-110`}
                >
                  <span>{cat.emoji}</span>
                </div>
                <span className="text-xs font-semibold text-primary group-hover:text-accent truncate max-w-full">
                  {cat.name}
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ── 4. Flash Deals (4 Balanced Cards) ── */}
      <section className="mx-auto max-w-[1360px] w-full px-4 sm:px-6 lg:px-8">
        <SectionHeader
          icon={Flame}
          title="Flash Deals & Hot Picks"
          subtitle="Exclusive discounts on top-rated products from verified sellers"
          linkTo="/products"
          linkLabel="See all deals"
          badge="HOT"
        />
        {loading ? (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-72 rounded-xl bg-muted/40 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {flashDeals.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </section>

      {/* ── 5. AI Shopping Insight ── */}
      {products.length > 0 && (
        <section className="mx-auto max-w-[1360px] w-full px-4 sm:px-6 lg:px-8">
          <AiInsightPanel title="AI Market & Price Overview" insights={marketAiOverview(products)} />
        </section>
      )}

      {/* ── 6. Best of Tech & Electronics (Vijay Sales Style) ── */}
      {bestOfTech.length > 0 && (
        <section className="mx-auto max-w-[1360px] w-full px-4 sm:px-6 lg:px-8">
          <SectionHeader
            icon={Zap}
            title="Best of Tech & Computing"
            subtitle="Smartphones, Gaming Laptops & Premium Audio"
            linkTo="/products?category=mobiles"
            linkLabel="View tech store"
          />
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {bestOfTech.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </section>
      )}

      {/* ── 7. Two Prominent Curated Banners (Etsy / JioMart Style) ── */}
      <section className="mx-auto max-w-[1360px] w-full px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-950 via-slate-900 to-indigo-900 p-6 sm:p-8 text-white shadow-md">
            <span className="text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full bg-accent/20 text-accent border border-accent/30">
              FEATURED ARTISANS
            </span>
            <h3 className="mt-3 text-xl sm:text-2xl font-black">
              Fresh Autumn Fashion from Creative Sellers
            </h3>
            <p className="mt-1 text-xs text-zinc-300">
              Directly support independent creators and designers with handmade fashion.
            </p>
            <Link
              to="/products?category=fashion"
              className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-accent px-4 py-2 text-xs font-bold text-white hover:opacity-90"
            >
              Shop These Looks <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-amber-950 via-zinc-900 to-stone-900 p-6 sm:p-8 text-white shadow-md">
            <span className="text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full bg-amber-500/20 text-amber-300 border border-amber-400/30">
              DAILY GOURMET
            </span>
            <h3 className="mt-3 text-xl sm:text-2xl font-black">
              The Biscuit & Snacks Bash — Starts ₹19
            </h3>
            <p className="mt-1 text-xs text-zinc-300">
              Delicious cookies, artisan spreads, and snacking favorites at up to 33% off.
            </p>
            <Link
              to="/products?category=groceries"
              className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-amber-600 px-4 py-2 text-xs font-bold text-white hover:opacity-90"
            >
              Shop Bakery & Snacks <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* ── 8. Recommended Catalog Products (4 Balanced Columns) ── */}
      <section className="mx-auto max-w-[1360px] w-full px-4 sm:px-6 lg:px-8">
        <SectionHeader
          icon={Star}
          title="Recommended For You"
          subtitle="Top rated by buyers across all categories"
          linkTo="/products"
          linkLabel="Explore all"
        />
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          {allDeals.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </section>

      {/* ── 9. Trust Badges & Customer Assurance ── */}
      <section className="border-y border-border bg-muted/30">
        <div className="mx-auto max-w-[1360px] w-full px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center sm:text-left">
            <div className="flex flex-col sm:flex-row items-center gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent/10 text-accent">
                <Truck className="h-5 w-5" />
              </span>
              <div>
                <p className="text-xs font-bold text-primary">Fast Delivery</p>
                <p className="text-[11px] text-secondary">Same-day / Express in India</p>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row items-center gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent/10 text-accent">
                <ShieldCheck className="h-5 w-5" />
              </span>
              <div>
                <p className="text-xs font-bold text-primary">100% Genuine</p>
                <p className="text-[11px] text-secondary">Directly from verified sellers</p>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row items-center gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent/10 text-accent">
                <CreditCard className="h-5 w-5" />
              </span>
              <div>
                <p className="text-xs font-bold text-primary">Instant Bank EMI</p>
                <p className="text-[11px] text-secondary">Razorpay, ICICI, HDFC, SBI</p>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row items-center gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent/10 text-accent">
                <RefreshCw className="h-5 w-5" />
              </span>
              <div>
                <p className="text-xs font-bold text-primary">7-Day Return</p>
                <p className="text-[11px] text-secondary">Easy hassle-free replacements</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
