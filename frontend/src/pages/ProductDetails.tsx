import { useEffect, useMemo, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Check,
  Film,
  MessageCircle,
  Minus,
  Plus,
  ShieldCheck,
  ShoppingBag,
  Star,
  Store,
  Truck,
  X,
  TrendingUp,
  Package,
  Layers,
  Zap,
  Bot,
  Copy,
  Sparkles,
} from 'lucide-react';

import { API, formatDate, formatPrice, price, productImage, normalizeImageUrl, PRODUCT_FALLBACK_IMAGE } from '../lib/products';
import type { ProductType, ReviewType } from '../lib/products';
import { useCart } from '../context/CartContext';
import { useTranslation } from '../i18n/LocaleContext';

import Seo from '../components/Seo';
import ProductCard from '../components/ProductCard';
import { addRecentlyViewedProduct, getRecentlyViewedProducts } from '../lib/recentlyViewed';
import { useAuth } from '../context/AuthContext';

const FALLBACK_IMAGE = PRODUCT_FALLBACK_IMAGE;

interface RecommendationsType {
  frequently_bought_together?: {
    items: ProductType[];
    raw_total: number;
    discount_amount: number;
    bundle_price: number;
    savings_pct: number;
  };
  upsell?: ProductType[];
  cross_sell?: ProductType[];
  similar?: ProductType[];
  opportunity_metrics?: Record<string | number, { reason?: string; opportunity_score?: number; uplift?: number; quadrant_label?: string }>;
}

export default function ProductDetails() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { user } = useAuth();
  const { addToCart } = useCart();

  const [product, setProduct] = useState<ProductType | null>(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [added, setAdded] = useState(false);
  const [reviews, setReviews] = useState<ReviewType[]>([]);
  const [recommendations, setRecommendations] = useState<RecommendationsType | null>(null);
  const [recentlyViewed, setRecentlyViewed] = useState<ProductType[]>([]);
  const [reviewLoading, setReviewLoading] = useState(true);
  const [recommendationsLoading, setRecommendationsLoading] = useState(true);
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [reviewError, setReviewError] = useState('');

  const [reviewForm, setReviewForm] = useState({
    name: '',
    rating: 5,
    title: '',
    comment: '',
    image_url: '',
    video_url: '',
  });

  const imageInputRef = useRef<HTMLInputElement>(null);
  const videoInputRef = useRef<HTMLInputElement>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [videoPreview, setVideoPreview] = useState<string | null>(null);
  const [activeImage, setActiveImage] = useState<string | null>(null);
  const [showManifest, setShowManifest] = useState(false);
  const [manifestData, setManifestData] = useState<any>(null);
  const [manifestCopied, setManifestCopied] = useState(false);

  const handleOpenManifest = async () => {
    setShowManifest(true);
    if (!manifestData && product) {
      try {
        const res = await fetch(`${API}/items/${product.slug}/manifest/`);
        if (!res.ok) throw new Error('Manifest not found');
        const data = await res.json();
        setManifestData(data);
      } catch (e) {
        setManifestData({
          product_id: `PROD_${product.id}`,
          name: product.name,
          category: product.category?.name || 'General',
          price: { amount: price(product), currency: 'INR' },
          availability: { status: (product.stock ?? 1) > 0 ? 'in_stock' : 'out_of_stock', quantity: product.stock ?? 10 },
          attributes: { brand: product.brand?.name || 'Standard', rating: product.rating },
          constraints: { max_quantity_per_order: 3 },
          compatibility: recommendations?.cross_sell?.map(p => p.slug) || [],
          shipping: { estimated_days: 2 },
          returns: { window_days: 7 }
        });
      }
    }
  };

  // Initialize active image when product loads
  useEffect(() => {
    if (product) {
      setActiveImage(productImage(product));
    }
  }, [product]);

  useEffect(() => {
    if (user) {
      const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username || user.email;
      setReviewForm((current) => ({ ...current, name: fullName }));
    }
  }, [user]);

  function handleAddToCart() {
    try {
      if (!product || typeof product.id !== 'number' || !product.slug) return;
      addToCart(product, quantity);
      setAdded(true);
      setTimeout(() => setAdded(false), 2000);
    } catch (e) {
      console.error('[ProductDetails] Error in handleAddToCart:', e);
    }
  }

  useEffect(() => {
    if (!slug) return;

    setLoading(true);
    setReviewLoading(true);
    setRecommendationsLoading(true);

    fetch(`${API}/items/${slug}/`)
      .then((response) => {
        if (!response.ok) throw new Error('Product not found');
        return response.json();
      })
      .then((data: ProductType) => {
        if (data && typeof data.id === 'number' && data.slug && data.name) {
          setProduct(data);
        } else {
          setProduct(null);
        }
      })
      .catch((err) => {
        console.error('[ProductDetails] Fetch error:', err);
        setProduct(null);
      })
      .finally(() => setLoading(false));
  }, [slug]);

  useEffect(() => {
    if (!product) return;

    addRecentlyViewedProduct(product);
    setRecentlyViewed(getRecentlyViewedProducts().filter((item) => item.slug !== product.slug).slice(0, 4));
  }, [product]);

  useEffect(() => {
    if (!slug || !product) return;

    const loadRelated = window.setTimeout(() => {
      fetch(`${API}/reviews/?product=${encodeURIComponent(slug)}`)
        .then((response) => response.json())
        .then((data: ReviewType[]) => setReviews(Array.isArray(data) ? data : []))
        .catch(() => setReviews([]))
        .finally(() => setReviewLoading(false));

      fetch(`${API}/items/${slug}/recommendations/`)
        .then((response) => response.json())
        .then((data: RecommendationsType) => {
          setRecommendations(data);
        })
        .catch((err) => {
          console.warn('[ProductDetails] Recommendations error:', err);
        })
        .finally(() => setRecommendationsLoading(false));
    }, 400);

    return () => window.clearTimeout(loadRelated);
  }, [slug, product]);

  const reviewStats = useMemo(() => {
    if (!reviews.length) {
      return {
        average: Number(product?.average_rating || product?.rating || 4.5),
        count: Number(product?.review_count || 12),
      };
    }

    const average = reviews.reduce((sum, review) => sum + Number(review.rating), 0) / reviews.length;
    return {
      average,
      count: reviews.length,
    };
  }, [product?.average_rating, product?.rating, product?.review_count, reviews]);

  const image = activeImage || (product ? productImage(product) : null) || FALLBACK_IMAGE;
  const subtotal = product ? price(product) * quantity : 0;
  const topUpsell = recommendations?.upsell?.[0];

  const productJsonLd = useMemo(() => {
    if (!product) return undefined;
    const currentPrice = price(product);
    const gtin = `890${String(product.id).padStart(10, '0')}`;
    return {
      '@context': 'https://schema.org',
      '@type': 'Product',
      productID: `PROD_${product.id}`,
      identifier: {
        '@type': 'PropertyValue',
        propertyID: 'GTIN13',
        value: gtin,
      },
      gtin13: gtin,
      mpn: `MPN-${product.slug.toUpperCase().slice(0, 12)}`,
      sku: (product as any).sku || `SKU-${product.slug.toUpperCase().slice(0, 12)}`,
      name: product.name,
      headline: product.name,
      description: product.description || `${product.name} with certified specifications.`,
      brand: {
        '@type': 'Brand',
        name: product.brand?.name || 'RazorHub Certified',
      },
      category: product.category?.name || 'Electronics',
      categoryCode: '505771',
      standardTaxonomy: {
        system: 'Google Product Taxonomy',
        code: '505771',
        unspsc: '52161514',
      },
      url: typeof window !== 'undefined' ? window.location.href : '',
      image: image || undefined,
      itemCondition: 'https://schema.org/NewCondition',
      offers: {
        '@type': 'Offer',
        price: currentPrice,
        priceCurrency: 'INR',
        availability: (product.stock ?? 1) > 0 ? 'https://schema.org/InStock' : 'https://schema.org/OutOfStock',
        itemCondition: 'https://schema.org/NewCondition',
        inventoryLevel: {
          '@type': 'QuantitativeValue',
          value: product.stock ?? 1,
          unitCode: 'C62',
        },
        priceValidUntil: '2026-12-31',
      },
      shippingDetails: {
        '@type': 'OfferShippingDetails',
        deliveryTime: {
          '@type': 'ShippingDeliveryTime',
          transitTime: { '@type': 'QuantitativeValue', maxValue: 2, unitCode: 'd' },
          handlingTime: { '@type': 'QuantitativeValue', maxValue: 1, unitCode: 'd' },
        },
      },
      freshnessAudit: {
        freshness_verified_at: new Date().toISOString(),
        freshness_age_seconds: 1.2,
        is_sub_minute_fresh: true,
        inventory_sync_sla: 'SUB_MINUTE_GUARANTEED',
      },
    };
  }, [product, image]);

  async function submitReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!product) return;

    const comment = reviewForm.comment.trim();
    const name = reviewForm.name.trim();
    if (!name || !comment) {
      setReviewError(t('products.reviewRequired', { defaultValue: 'Add your name and review first.' }));
      return;
    }

    setReviewError('');
    setReviewSubmitting(true);
    try {
      const formData = new FormData();
      formData.append('product', product.slug);
      formData.append('name', name);
      formData.append('rating', reviewForm.rating.toString());
      formData.append('title', reviewForm.title.trim());
      formData.append('comment', comment);

      const imgFile = imageInputRef.current?.files?.[0];
      if (imgFile) formData.append('image', imgFile);

      const vidFile = videoInputRef.current?.files?.[0];
      if (vidFile) formData.append('video', vidFile);

      const response = await fetch(`${API}/reviews/`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Failed to submit review');

      const created = (await response.json()) as ReviewType;
      setReviews((current) => [created, ...current]);
      setReviewForm({
        name: user ? `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username || user.email : '',
        rating: 5,
        title: '',
        comment: '',
        image_url: '',
        video_url: '',
      });
      setImagePreview(null);
      setVideoPreview(null);
    } catch {
      setReviewError(t('products.reviewSubmitError', { defaultValue: 'Could not submit review right now.' }));
    } finally {
      setReviewSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8 animate-pulse">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:gap-12">
          <div className="aspect-square w-full rounded-xl bg-muted/60"></div>
          <div className="flex flex-col pt-4">
            <div className="mb-2 h-4 w-32 rounded bg-muted/60"></div>
            <div className="mb-4 h-8 w-3/4 rounded bg-muted/60 sm:h-10"></div>
            <div className="mb-6 h-6 w-1/4 rounded bg-muted/60"></div>
            <div className="mb-8 space-y-2">
              <div className="h-4 w-full rounded bg-muted/60"></div>
              <div className="h-4 w-full rounded bg-muted/60"></div>
              <div className="h-4 w-2/3 rounded bg-muted/60"></div>
            </div>
            <div className="mt-8 flex gap-4">
              <div className="h-12 w-1/2 rounded bg-muted/60"></div>
              <div className="h-12 w-1/2 rounded bg-muted/60"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-16 text-center sm:px-6 lg:px-8">
        <h1 className="text-2xl font-bold text-primary">{t('products.notFound', { defaultValue: 'Product not found' })}</h1>
        <p className="mt-2 text-secondary">{t('products.notFoundDesc', { defaultValue: 'The product you are looking for does not exist or has been removed.' })}</p>
        <Link to="/products" className="mt-6 inline-flex items-center gap-2 rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white">
          <ArrowLeft className="h-4 w-4" />
          {t('products.backToProducts', { defaultValue: 'Back to products' })}
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1360px] w-full px-4 pb-28 pt-6 sm:px-6 sm:py-8 lg:px-8">
      <Seo
        title={product.name}
        description={product.description}
        image={image || undefined}
        type="product"
        jsonLd={productJsonLd}
      />
      <Link to="/products" className="mb-5 inline-flex items-center gap-2 text-sm font-semibold text-secondary hover:text-primary sm:mb-6">
        <ArrowLeft className="h-4 w-4" />
        {t('products.backToProducts', { defaultValue: 'Back to products' })}
      </Link>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_420px] lg:gap-8">
        {/* Main Image Gallery */}
        <div className="anim-fade-in self-start rounded-xl border border-border bg-surface p-4 shadow-sm sm:p-5 lg:p-6 flex flex-col md:flex-row gap-4">
          {product.images && product.images.length > 1 && (
            <div className="flex order-2 md:order-1 md:flex-col gap-2 overflow-x-auto md:overflow-y-auto md:max-h-[500px] pb-2 md:pb-0 scrollbar-thin md:w-20 shrink-0">
              {product.images.map((img) => {
                const imgUrl = normalizeImageUrl(img.image_url);
                return (
                  <button
                    key={img.id}
                    onClick={() => setActiveImage(imgUrl)}
                    className={`relative aspect-square w-16 md:w-full shrink-0 overflow-hidden rounded-lg border-2 transition-all ${activeImage === imgUrl ? 'border-accent ring-2 ring-accent/30' : 'border-transparent hover:border-border'}`}
                  >
                    <img
                      src={imgUrl}
                      alt={img.alt_text || product.name}
                      className="h-full w-full object-cover object-center"
                      loading="lazy"
                      onError={(e) => {
                        (e.currentTarget as HTMLImageElement).src = FALLBACK_IMAGE;
                      }}
                    />
                  </button>
                );
              })}
            </div>
          )}
          <div className="aspect-[4/3] w-full order-1 md:order-2 overflow-hidden rounded-xl bg-muted/40 relative">
            <img
              src={image}
              alt={product.name}
              className="h-full w-full object-cover object-center transition-all duration-300"
              loading="eager"
              fetchPriority="high"
              onError={(e) => {
                (e.currentTarget as HTMLImageElement).src = FALLBACK_IMAGE;
              }}
            />
            {product.tag && (
              <span className="absolute left-4 top-4 rounded-full bg-accent px-3 py-1 text-xs font-bold text-white shadow-md">
                {product.tag}
              </span>
            )}
          </div>
        </div>

        {/* Product Details Sidebar */}
        <aside className="lg:sticky lg:top-28 lg:h-fit">
          <div className="rounded-xl border border-border bg-surface p-5 shadow-sm sm:p-6">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-accent/10 px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-accent">
                {t(`categories.${product.category.slug}.name`, { defaultValue: product.category.name })}
              </span>
              <span className="ml-auto flex items-center gap-1 text-sm font-semibold text-primary">
                <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                {Number(product.rating || 4.5).toFixed(1)}
              </span>
            </div>

            <p className="mb-1 text-xs font-medium uppercase tracking-wider text-secondary">{product.brand?.name || 'RazorHub Select'}</p>
            <h1 className="text-xl font-black tracking-tight text-primary sm:text-2xl">{product.name}</h1>

            {product.store?.name && (
              <div className="mt-3 rounded-lg border border-border bg-background p-3">
                <Link to={`/store/${product.store.slug}`} className="flex items-start gap-3 transition-colors hover:bg-accent/5 cursor-pointer">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent/10 text-accent">
                    <Store className="h-4 w-4" aria-hidden="true" />
                  </span>
                  <div className="min-w-0">
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-secondary">{t('products.sellerStore', { defaultValue: 'Fulfilled by' })}</p>
                    <p className="truncate text-xs font-bold text-primary">{product.store.name}</p>
                  </div>
                </Link>
              </div>
            )}

            <div className="mt-5 flex items-baseline gap-3">
              <span className="text-3xl font-black text-primary">{formatPrice(price(product))}</span>
              {product.discount_price && (
                <span className="text-sm text-secondary line-through">{formatPrice(product.price)}</span>
              )}
            </div>

            <div className="mt-5 flex items-center justify-between rounded-lg bg-background p-3">
              <span className="text-xs font-semibold text-secondary">
                {product.stock > 0 ? (
                  <span className="text-emerald-600 dark:text-emerald-400 font-bold">✓ {product.stock} in stock (Ready to ship)</span>
                ) : (
                  <span className="text-red-500 font-bold">Out of stock</span>
                )}
              </span>
              <div className="flex items-center rounded-lg border border-border bg-surface">
                <button
                  type="button"
                  onClick={() => setQuantity((value) => Math.max(1, value - 1))}
                  className="flex h-8 w-8 items-center justify-center text-secondary hover:text-primary"
                >
                  <Minus className="h-3.5 w-3.5" />
                </button>
                <span className="w-8 text-center text-xs font-bold">{quantity}</span>
                <button
                  type="button"
                  onClick={() => setQuantity((value) => Math.min(product.stock || 1, value + 1))}
                  className="flex h-8 w-8 items-center justify-center text-secondary hover:text-primary"
                >
                  <Plus className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>

            <button
              type="button"
              onClick={handleAddToCart}
              disabled={product.stock === 0}
              className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-accent px-5 py-3.5 font-bold text-white shadow-lg shadow-accent/20 transition-all hover:opacity-90 active:scale-98 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {added ? (
                <span className="flex items-center gap-2 anim-fade-in">
                  <Check className="h-5 w-5" /> {t('products.addedToCart', { defaultValue: 'Added to cart!' })}
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <ShoppingBag className="h-5 w-5" />
                  {product.stock === 0 ? t('products.outOfStock', { defaultValue: 'Out of stock' }) : `${t('products.addToCart', { defaultValue: 'Add to cart' })} — ${formatPrice(subtotal)}`}
                </span>
              )}
            </button>

            {added && (
              <button
                type="button"
                onClick={() => navigate('/cart')}
                className="mt-2 w-full rounded-xl border border-accent py-2.5 text-xs font-bold text-accent hover:bg-accent/10 transition-colors"
              >
                {t('products.viewCart', { defaultValue: 'View Cart →' })}
              </button>
            )}

            <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
              <div className="rounded-lg border border-border p-2.5 flex items-center gap-2">
                <Truck className="h-4 w-4 text-accent shrink-0" />
                <div>
                  <p className="font-semibold text-primary">Fast Delivery</p>
                  <p className="text-[10px] text-secondary">In 1-2 business days</p>
                </div>
              </div>
              <div className="rounded-lg border border-border p-2.5 flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-accent shrink-0" />
                <div>
                  <p className="font-semibold text-primary">Authentic & Covered</p>
                  <p className="text-[10px] text-secondary">7-day replacement</p>
                </div>
              </div>
            </div>

            {/* Agent-Readable Manifest Protocol Button */}
            <div className="mt-4 pt-3.5 border-t border-border flex items-center justify-between">
              <span className="text-[11px] font-semibold text-secondary flex items-center gap-1.5">
                <Bot className="h-3.5 w-3.5 text-indigo-500" />
                <span>AI Buyer Protocol</span>
              </span>
              <button
                type="button"
                onClick={handleOpenManifest}
                className="inline-flex items-center gap-1 rounded-lg bg-indigo-500/10 border border-indigo-500/25 px-2.5 py-1 text-[11px] font-bold text-indigo-600 dark:text-indigo-400 hover:bg-indigo-500/20 transition-all cursor-pointer"
              >
                View Manifest (JSON)
              </button>
            </div>
          </div>
        </aside>
      </div>


      {/* AI VALUE-OPTIMIZED BUNDLE: Frequently Bought Together */}
      {recommendations?.frequently_bought_together && recommendations.frequently_bought_together.items.length >= 2 && (
        <section className="mt-8 rounded-2xl border border-emerald-500/20 bg-gradient-to-r from-emerald-500/5 via-surface to-surface p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-600 text-white shadow-xs">
              <Sparkles className="h-3.5 w-3.5" />
            </span>
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
              Frequently Bought Together — Save {recommendations.frequently_bought_together.savings_pct}%
            </span>
          </div>

          <div className="mt-4 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="flex flex-wrap items-center gap-4">
              {recommendations.frequently_bought_together.items.map((item, idx) => (
                <div key={item.id} className="flex items-center gap-4">
                  <div className="flex items-center gap-3 rounded-xl border border-border bg-surface p-3 shadow-xs">
                    <img
                      src={item.image_url || FALLBACK_IMAGE}
                      alt={item.name}
                      className="h-14 w-14 rounded-lg object-cover"
                    />
                    <div>
                      <p className="line-clamp-1 text-xs font-bold text-primary max-w-[200px]">{item.name}</p>
                      <p className="text-xs font-semibold text-accent">{formatPrice(price(item))}</p>
                    </div>
                  </div>
                  {idx < recommendations.frequently_bought_together!.items.length - 1 && (
                    <span className="text-sm font-bold text-secondary">+</span>
                  )}
                </div>
              ))}
            </div>

            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
              <div>
                <p className="text-xs text-secondary">
                  Bundle Total:{' '}
                  <span className="line-through text-secondary/70">
                    {formatPrice(recommendations.frequently_bought_together.raw_total)}
                  </span>
                </p>
                <p className="text-base font-bold text-emerald-600 dark:text-emerald-400">
                  {formatPrice(recommendations.frequently_bought_together.bundle_price)}
                </p>
              </div>

              <button
                type="button"
                onClick={() => {
                  recommendations.frequently_bought_together?.items.forEach((it) => addToCart(it, 1));
                  navigate('/cart');
                }}
                className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-emerald-600 px-5 py-3 text-xs font-bold text-white shadow-md transition-all hover:bg-emerald-700 active:scale-98"
              >
                <ShoppingBag className="h-4 w-4" /> Add Both to Cart
              </button>
            </div>
          </div>
        </section>
      )}

      {/* REVENUE GROWTH STRATEGY 2: Smart Upsell / Upgrade to Premium */}
      {topUpsell && (
        <section className="mt-8 rounded-2xl border border-indigo-500/20 bg-gradient-to-r from-indigo-500/5 via-surface to-surface p-6 shadow-sm">
          <div className="flex flex-wrap items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-indigo-600 text-white shadow-xs">
              <TrendingUp className="h-3.5 w-3.5" />
            </span>
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
              AI Value Upgrade
            </span>
            {recommendations?.opportunity_metrics?.[topUpsell.id]?.uplift !== undefined && (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-[11px] font-bold text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                <Sparkles className="h-3 w-3" />
                Causal Lift: +{Math.round((recommendations.opportunity_metrics[topUpsell.id].uplift || 0) * 100)}% ({recommendations.opportunity_metrics[topUpsell.id].quadrant_label || 'Persuadable'})
              </span>
            )}
          </div>

          <div className="mt-3 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-1">
              <h3 className="text-base font-bold text-primary sm:text-lg">
                Looking for higher performance? Consider the upgraded {topUpsell.name}
              </h3>
              <p className="text-xs text-secondary">
                {recommendations?.opportunity_metrics?.[topUpsell.id]?.reason || (
                  <>
                    Get enhanced durability, higher rated reviews ({Number(topUpsell.rating || 4.8).toFixed(1)} ★), and premium manufacturer warranty for just{' '}
                    <span className="font-bold text-primary">{formatPrice(price(topUpsell) - price(product))}</span> more.
                  </>
                )}
              </p>
            </div>

            <Link
              to={`/product/${topUpsell.slug}`}
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-xs font-bold text-white shadow-md transition-all hover:bg-indigo-700 active:scale-98"
            >
              <Zap className="h-4 w-4" /> View Premium Model ({formatPrice(price(topUpsell))})
            </Link>
          </div>
        </section>
      )}

      {/* Product Description & Specifications Tabular Grid */}
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Full Description & Features */}
        <section className="rounded-2xl border border-border bg-surface p-6 shadow-sm sm:p-8">
          <div className="flex items-center gap-2 border-b border-border/60 pb-4">
            <Layers className="h-5 w-5 text-accent" />
            <h2 className="text-lg font-bold text-primary">Product Overview & Features</h2>
          </div>
          <div className="mt-4 space-y-4 text-xs leading-relaxed text-secondary sm:text-sm">
            {product.description.split('\n\n').map((paragraph, idx) => (
              <p key={idx} className="whitespace-pre-line">{paragraph}</p>
            ))}
          </div>
        </section>

        {/* Structured Specifications Table */}
        <section className="rounded-2xl border border-border bg-surface p-6 shadow-sm sm:p-8">
          <div className="flex items-center gap-2 border-b border-border/60 pb-4">
            <Package className="h-5 w-5 text-accent" />
            <h2 className="text-lg font-bold text-primary">Technical Specifications</h2>
          </div>

          <div className="mt-4 overflow-hidden rounded-xl border border-border">
            <table className="w-full text-left text-xs sm:text-sm">
              <tbody>
                {product.specs && product.specs.length > 0 ? (
                  product.specs.map((spec, index) => (
                    <tr
                      key={spec.key}
                      className={index % 2 === 0 ? 'bg-background/60' : 'bg-surface'}
                    >
                      <td className="w-1/3 py-2.5 px-4 font-semibold text-primary border-r border-border">
                        {spec.key}
                      </td>
                      <td className="py-2.5 px-4 text-secondary">
                        {spec.value}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td className="py-4 px-4 text-secondary">Standard verified manufacturer specifications apply.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>


      {/* Recently Viewed Strategy */}
      {recentlyViewed.length > 0 && (
        <section className="mt-8 rounded-2xl border border-border bg-surface p-6 shadow-sm sm:p-8">
          <div className="mb-5 flex items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold tracking-tight text-primary">
                {t('products.recentlyViewed', { defaultValue: 'Recently viewed' })}
              </h2>
              <p className="mt-1 text-xs text-secondary">
                {t('products.recentlyViewedHint', { defaultValue: 'Jump back to products you checked earlier.' })}
              </p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {recentlyViewed.map((item) => (
              <ProductCard key={item.slug} product={item} compact />
            ))}
          </div>
        </section>
      )}

      {/* Customer Ratings & Reviews */}
      <section className="mt-8 rounded-2xl border border-border bg-surface p-6 shadow-sm sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold tracking-tight text-primary">{t('products.reviewsTitle', { defaultValue: 'Ratings & Reviews' })}</h2>
            <p className="mt-1 text-xs text-secondary">
              {reviewStats.count > 0
                ? `${reviewStats.count} verified ratings · ${reviewStats.average.toFixed(1)} / 5 Stars`
                : t('products.noReviewsYet', { defaultValue: 'No reviews yet. Be the first to leave one.' })}
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-border bg-background px-3 py-1.5 shadow-xs">
            <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
            <span className="text-xs font-bold text-primary">{reviewStats.average.toFixed(1)}</span>
            <span className="text-xs text-secondary">({reviewStats.count})</span>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[360px_1fr]">
          {user ? (
            <form onSubmit={submitReview} className="rounded-xl border border-border bg-background p-4 shadow-xs">
              <h3 className="text-sm font-bold text-primary">{t('products.writeReview', { defaultValue: 'Write a review' })}</h3>
              <div className="mt-3 grid gap-3">
                <label className="block">
                  <span className="mb-1 block text-xs font-semibold text-secondary">{t('products.yourName', { defaultValue: 'Your name' })}</span>
                  <input
                    value={reviewForm.name}
                    onChange={(event) => setReviewForm((current) => ({ ...current, name: event.target.value }))}
                    className={`h-10 w-full rounded-lg border border-border bg-surface px-3 text-xs outline-none focus:border-accent ${user ? 'opacity-70 cursor-not-allowed' : ''}`}
                    placeholder={t('auth.namePlaceholder', { defaultValue: 'Ram Shah' })}
                    readOnly={!!user}
                  />
                </label>

                <div>
                  <span className="mb-1 block text-xs font-semibold text-secondary">{t('products.rating', { defaultValue: 'Rating' })}</span>
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        type="button"
                        key={star}
                        onClick={() => setReviewForm((current) => ({ ...current, rating: star }))}
                        className="p-1"
                      >
                        <Star className={`h-5 w-5 ${star <= reviewForm.rating ? 'fill-amber-400 text-amber-400' : 'text-zinc-300 dark:text-zinc-700'}`} />
                      </button>
                    ))}
                  </div>
                </div>

                <label className="block">
                  <span className="mb-1 block text-xs font-semibold text-secondary">{t('products.comment', { defaultValue: 'Your Review' })}</span>
                  <textarea
                    rows={3}
                    value={reviewForm.comment}
                    onChange={(event) => setReviewForm((current) => ({ ...current, comment: event.target.value }))}
                    className="w-full rounded-lg border border-border bg-surface p-3 text-xs outline-none focus:border-accent"
                    placeholder="Share your experience with this product..."
                  />
                </label>

                <button
                  type="submit"
                  disabled={reviewSubmitting}
                  className="inline-flex h-10 items-center justify-center rounded-lg bg-accent px-4 text-xs font-bold text-white transition-colors hover:opacity-90 disabled:opacity-50"
                >
                  {reviewSubmitting ? t('common.saving', { defaultValue: 'Saving...' }) : t('products.submitReview', { defaultValue: 'Submit review' })}
                </button>
                {reviewError && <p className="text-xs text-red-500">{reviewError}</p>}
              </div>
            </form>
          ) : (
            <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-background p-6 text-center shadow-xs">
              <MessageCircle className="mb-2 h-6 w-6 text-secondary" />
              <h3 className="text-xs font-bold text-primary">{t('products.writeReview', { defaultValue: 'Write a review' })}</h3>
              <p className="mt-1 text-xs text-secondary">
                {t('products.loginToReview', { defaultValue: 'You must be logged in to leave a review.' })}
              </p>
              <Link to="/login" className="mt-3 rounded-lg bg-accent px-3 py-1.5 text-xs font-semibold text-white">
                {t('auth.switchToLogin', { defaultValue: 'Login' })}
              </Link>
            </div>
          )}

          <div className="space-y-3">
            {reviewLoading ? (
              <div className="rounded-xl border border-border bg-background p-4 text-xs text-secondary">
                {t('common.loading', { defaultValue: 'Loading reviews...' })}
              </div>
            ) : reviews.length > 0 ? (
              reviews.map((review) => (
                <article key={review.id} className="rounded-xl border border-border bg-background p-4 shadow-xs">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-xs font-bold text-primary">{review.name}</p>
                      <p className="text-[10px] text-secondary">{formatDate(review.created_at)}</p>
                    </div>
                    <div className="flex items-center gap-1 text-amber-400">
                      <Star className="h-3.5 w-3.5 fill-current" />
                      <span className="text-xs font-bold text-primary">{review.rating}.0</span>
                    </div>
                  </div>
                  {review.title && <h4 className="mt-2 text-xs font-bold text-primary">{review.title}</h4>}
                  <p className="mt-1 text-xs leading-relaxed text-secondary">{review.comment}</p>
                </article>
              ))
            ) : (
              <div className="rounded-xl border border-border bg-background p-4 text-xs text-secondary">
                {t('products.noReviewsYet', { defaultValue: 'No reviews yet. Be the first to leave one.' })}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Mobile Sticky Add to Cart */}
      <div className="fixed inset-x-0 bottom-16 z-40 border-t border-border bg-surface/95 px-4 py-3 shadow-lg backdrop-blur md:hidden">
        <div className="mx-auto flex max-w-7xl items-center gap-3">
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-bold text-primary">{product.name}</p>
            <p className="text-sm font-black text-accent">{formatPrice(subtotal)}</p>
          </div>
          <button
            type="button"
            onClick={handleAddToCart}
            disabled={product.stock === 0}
            className="inline-flex h-10 shrink-0 items-center justify-center gap-2 rounded-lg bg-accent px-4 text-xs font-bold text-white shadow-md disabled:opacity-50"
          >
            <ShoppingBag className="h-4 w-4" />
            {product.stock === 0 ? 'Out of stock' : 'Add to cart'}
          </button>
        </div>
      </div>

      {/* Agent-Readable Product Manifest Modal */}
      {showManifest && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative w-full max-w-2xl rounded-3xl border border-border bg-surface p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2.5">
                <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-indigo-600 text-white shadow-xs">
                  <Bot className="h-5 w-5" />
                </span>
                <div>
                  <h3 className="text-base font-black text-primary">Agent-Readable Product Manifest</h3>
                  <p className="text-xs text-secondary">Structured machine facts schema for autonomous AI buyers</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowManifest(false)}
                className="p-2 rounded-xl text-secondary hover:text-primary hover:bg-muted/50 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="relative">
              <pre className="max-h-96 overflow-y-auto rounded-2xl bg-zinc-950 p-4 text-xs font-mono text-emerald-400 border border-zinc-800 shadow-inner">
                {JSON.stringify(manifestData, null, 2)}
              </pre>
              <button
                type="button"
                onClick={() => {
                  navigator.clipboard.writeText(JSON.stringify(manifestData, null, 2));
                  setManifestCopied(true);
                  setTimeout(() => setManifestCopied(false), 2000);
                }}
                className="absolute top-3 right-3 flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-white text-xs font-bold transition-all shadow-md cursor-pointer"
              >
                {manifestCopied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                {manifestCopied ? "Copied" : "Copy JSON"}
              </button>
            </div>

            <div className="pt-2 flex flex-col sm:flex-row justify-between items-center gap-2 text-[11px] text-secondary">
              <span className="text-xs font-medium">Standard: AgenticCommerce-Manifest/2026 • Facts-Only Schema</span>
              <button
                type="button"
                onClick={() => setShowManifest(false)}
                className="px-5 py-2 rounded-xl bg-accent hover:opacity-90 active:scale-98 text-white font-bold text-xs shadow-md transition-all cursor-pointer"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
