import { API_BASE } from './api';

export const API = `${API_BASE}/products`;

export interface ProductImageType {
  id: number;
  image_url: string;
  alt_text: string;
  is_primary: boolean;
  order: number;
}

export interface CategoryType {
  id: number;
  name: string;
  slug: string;
  description?: string;
}

export interface BrandType {
  id: number;
  name: string;
  slug: string;
}

export interface SpecType {
  key: string;
  value: string;
}

export interface ProductType {
  id: number;
  name: string;
  slug: string;
  store?: {
    id: number;
    name: string;
    slug: string;
    support_email?: string;
    support_phone?: string;
  } | null;
  category: CategoryType;
  brand: BrandType | null;
  description: string;
  specifications: string;
  specs: SpecType[];
  price: string;
  discount_price: string | null;
  stock: number;
  rating: string;
  tag: string | null;
  is_featured: boolean;
  is_active: boolean;
  images: ProductImageType[];
  image_url?: string;
  reviews?: ReviewType[];
  review_count?: number;
  average_rating?: number;
}

export interface ReviewType {
  id: number;
  product: number;
  name: string;
  rating: number;
  title: string;
  comment: string;
  image_url?: string;
  video_url?: string;
  is_verified_purchase: boolean;
  created_at: string;
  updated_at: string;
}

export interface StoreType {
  id: number;
  name: string;
  slug: string;
  description: string;
  logo_url: string;
  banner_url: string;
  address: string;
  area: string;
  map_url: string;
  support_email: string;
  support_phone: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export const PRODUCT_FALLBACK_IMAGE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 400' width='400' height='400'%3E%3Crect width='400' height='400' fill='%23f8fafc'/%3E%3Cpath d='M140 150 C140 115 165 95 200 95 C235 95 260 115 260 150 M110 150 L290 150 L305 310 L95 310 Z' fill='none' stroke='%2394a3b8' stroke-width='14' stroke-linecap='round' stroke-linejoin='round'/%3E%3Ccircle cx='200' cy='225' r='18' fill='%23cbd5e1'/%3E%3C/svg%3E";

export const CATEGORY_FALLBACK_IMAGES: Record<string, string> = {
  headphones: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80',
  audio: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=80',
  laptop: 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&auto=format&fit=crop&q=80',
  tech: 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&auto=format&fit=crop&q=80',
  computer: 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&auto=format&fit=crop&q=80',
  phone: 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600&auto=format&fit=crop&q=80',
  smartphone: 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600&auto=format&fit=crop&q=80',
  mobile: 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600&auto=format&fit=crop&q=80',
  storage: 'https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=600&auto=format&fit=crop&q=80',
  drive: 'https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=600&auto=format&fit=crop&q=80',
  apparel: 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=600&auto=format&fit=crop&q=80',
  clothing: 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=600&auto=format&fit=crop&q=80',
  fashion: 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=600&auto=format&fit=crop&q=80',
  shoes: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&auto=format&fit=crop&q=80',
  sneakers: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&auto=format&fit=crop&q=80',
  footwear: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&auto=format&fit=crop&q=80',
  backpack: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80',
  bag: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80',
  foldsack: 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&auto=format&fit=crop&q=80',
  watch: 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&auto=format&fit=crop&q=80',
  camera: 'https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=600&auto=format&fit=crop&q=80',
  electronics: 'https://images.unsplash.com/photo-1498049794561-7780e7231661?w=600&auto=format&fit=crop&q=80',
};

export function getCategoryFallbackImage(categoryOrName?: string): string {
  if (!categoryOrName) return CATEGORY_FALLBACK_IMAGES.electronics;
  const lower = categoryOrName.toLowerCase();
  for (const [key, url] of Object.entries(CATEGORY_FALLBACK_IMAGES)) {
    if (lower.includes(key)) return url;
  }
  return CATEGORY_FALLBACK_IMAGES.electronics;
}

export function normalizeImageUrl(url?: string | null): string {
  if (!url) return '';
  if (url.includes('razorhub.vercel.app/product-media/')) {
    return url.replace(/^https?:\/\/razorhub\.vercel\.app/, '');
  }
  return url;
}

export function productImage(product: any): string {
  if (!product) return getCategoryFallbackImage();
  let rawUrl = '';
  if (product.image_url) {
    rawUrl = product.image_url;
  } else if (Array.isArray(product.images) && product.images.length > 0) {
    rawUrl = product.images.find((image: any) => image.is_primary)?.image_url || product.images[0]?.image_url || '';
  }
  if (rawUrl && typeof rawUrl === 'string' && rawUrl.trim().length > 0) {
    return normalizeImageUrl(rawUrl);
  }
  const catName = (typeof product.category === 'string' ? product.category : product.category?.name) || product.name || '';
  return getCategoryFallbackImage(catName);
}

export function price(product: ProductType) {
  return Number(product.discount_price || product.price);
}

export function formatPrice(value: number | string) {
  return `₹${Number(value).toLocaleString('en-IN')}`;
}

export function formatNumber(value: number | string) {
  return Number(value).toLocaleString('en-IN');
}

export function formatDate(value: string, options: Intl.DateTimeFormatOptions = {}) {
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: options.timeStyle,
    ...options,
  }).format(new Date(value));
}
