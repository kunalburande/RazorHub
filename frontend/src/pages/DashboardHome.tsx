import React, { useState, useEffect, useRef } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useCart } from '../context/CartContext';
import { useTranslation } from '../i18n/LocaleContext';
import { apiRequest, unwrapList } from '../lib/api';
import { formatPrice, price, productImage, PRODUCT_FALLBACK_IMAGE } from '../lib/products';
import type { ProductType } from '../lib/products';
import ProductCard from '../components/ProductCard';
import {
  AlertTriangle,
  ArrowRight,
  Bell,
  Box,
  Check,
  CheckCircle2,
  ChevronRight,
  Clock,
  CreditCard,
  Download,
  Eye,
  Heart,
  HelpCircle,
  KeyRound,
  LayoutDashboard,
  Loader2,
  Lock,
  LogOut,
  Mail,
  MapPin,
  Moon,
  Package,
  Palette,
  Phone,
  Plus,
  RefreshCw,
  RotateCcw,
  Save,
  Search,
  Shield,
  ShieldCheck,
  ShoppingBag,
  Sliders,
  Smartphone,
  Sparkles,
  Star,
  Sun,
  Trash2,
  Truck,
  Upload,
  User as UserIcon,
  X,
  Zap,
} from 'lucide-react';

const PRESET_AVATARS = [
  'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80',
  'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=300&q=80',
  'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=300&q=80',
  'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=300&q=80',
  'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=300&q=80',
  'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=300&q=80',
];

export default function DashboardHome() {
  const { user } = useAuth();

  if (user?.effective_role === 'seller') return <Navigate to="/seller" replace />;
  if (user?.effective_role === 'admin') return <Navigate to="/admin" replace />;
  return <CustomerDashboard />;
}

interface OrderItem {
  id: number;
  product: ProductType;
  quantity: number;
  price: string;
}

interface CustomerOrder {
  id: number;
  order_number?: string;
  total_price: string;
  status: 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled';
  created_at: string;
  items: OrderItem[];
  shipping_address?: any;
}

interface SavedAddress {
  id: number;
  full_name?: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  state: string;
  postal_code: string;
  country?: string;
  phone?: string;
  is_default?: boolean;
}

function CustomerDashboard() {
  const { user, token, logout, requestDeleteAccount, confirmDeleteAccount } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { addToCart, totalCount: cartTotalCount } = useCart();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Single active section
  const [activeSection, setActiveSection] = useState<
    'overview' | 'orders' | 'wishlist' | 'addresses' | 'profile' | 'preferences'
  >('overview');

  // Live Database States
  const [orders, setOrders] = useState<CustomerOrder[]>([]);
  const [wishlist, setWishlist] = useState<ProductType[]>([]);
  const [addresses, setAddresses] = useState<SavedAddress[]>([]);
  const [recommendations, setRecommendations] = useState<ProductType[]>([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<{ type: 'success' | 'error' | 'info'; title: string; message: string } | null>(null);

  // Profile Form State
  const [profileForm, setProfileForm] = useState({
    firstName: user?.first_name || '',
    lastName: user?.last_name || '',
    email: user?.email || '',
    phone: user?.phone || '',
  });

  const [avatarUrl, setAvatarUrl] = useState<string>(() => {
    return user?.avatar || localStorage.getItem('razorhub_user_avatar') || PRESET_AVATARS[0];
  });

  // Address Form Modal
  const [isAddressModalOpen, setIsAddressModalOpen] = useState(false);
  const [addressForm, setAddressForm] = useState({
    fullName: '',
    phone: '',
    addressLine1: '',
    addressLine2: '',
    city: 'Bengaluru',
    state: 'Karnataka',
    postalCode: '560001',
    isDefault: false,
  });

  // Password State
  const [passwords, setPasswords] = useState({
    current: '',
    newPass: '',
    confirmPass: '',
  });

  function showToast(type: 'success' | 'error' | 'info', title: string, message: string) {
    setToast({ type, title, message });
    setTimeout(() => setToast(null), 3500);
  }

  // Load all live customer data from NeonDB
  const loadCustomerData = async () => {
    setLoading(true);
    try {
      const [ordersRes, wishlistRes, addrRes, recRes] = await Promise.all([
        apiRequest<any>('/orders/', { token }).catch(() => []),
        apiRequest<any>('/wishlist/', { token }).catch(() => []),
        apiRequest<any>('/auth/addresses/', { token }).catch(() => []),
        apiRequest<any>('/products/personalized/').catch(() => []),
      ]);

      setOrders(unwrapList<CustomerOrder>(ordersRes));
      setWishlist(unwrapList<ProductType>(wishlistRes));
      setAddresses(unwrapList<SavedAddress>(addrRes));
      setRecommendations(unwrapList<ProductType>(recRes).slice(0, 4));
    } catch (err) {
      console.warn('Customer data load notice:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCustomerData();
  }, [token]);

  useEffect(() => {
    if (user) {
      setProfileForm({
        firstName: user.first_name || '',
        lastName: user.last_name || '',
        email: user.email || '',
        phone: user.phone || '',
      });
      if (user.avatar) setAvatarUrl(user.avatar);
    }
  }, [user]);

  // Handle Profile Save
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (user?.id) {
        await apiRequest(`/auth/users/${user.id}/`, {
          token,
          method: 'PATCH',
          body: JSON.stringify({
            first_name: profileForm.firstName,
            last_name: profileForm.lastName,
            email: profileForm.email,
            phone: profileForm.phone,
            avatar: avatarUrl,
          }),
        });
      }
      showToast('success', 'Profile Updated', 'Your profile details have been synced with the database.');
    } catch (err: any) {
      showToast('error', 'Update Failed', err?.message || 'Could not save profile details.');
    }
  };

  // Handle Add Address
  const handleSaveAddress = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest('/auth/addresses/', {
        token,
        method: 'POST',
        body: JSON.stringify({
          address_line1: addressForm.addressLine1,
          address_line2: addressForm.addressLine2,
          city: addressForm.city,
          state: addressForm.state,
          postal_code: addressForm.postalCode,
          country: 'India',
        }),
      });
      showToast('success', 'Address Saved', 'New delivery address added successfully.');
      setIsAddressModalOpen(false);
      setAddressForm({
        fullName: '',
        phone: '',
        addressLine1: '',
        addressLine2: '',
        city: 'Bengaluru',
        state: 'Karnataka',
        postalCode: '560001',
        isDefault: false,
      });
      loadCustomerData();
    } catch (err: any) {
      showToast('error', 'Failed', err?.message || 'Could not save address.');
    }
  };

  // Handle Delete Address
  const handleDeleteAddress = async (id: number) => {
    try {
      await apiRequest(`/auth/addresses/${id}/`, {
        token,
        method: 'DELETE',
      });
      showToast('info', 'Address Removed', 'Address removed from your address book.');
      loadCustomerData();
    } catch (err: any) {
      showToast('error', 'Failed', err?.message || 'Could not delete address.');
    }
  };

  // Handle Remove from Wishlist
  const handleRemoveWishlist = async (id: number) => {
    try {
      await apiRequest(`/wishlist/${id}/`, {
        token,
        method: 'DELETE',
      });
      setWishlist((prev) => prev.filter((p) => p.id !== id));
      showToast('info', 'Wishlist Updated', 'Item removed from your wishlist.');
    } catch (err: any) {
      showToast('error', 'Failed', 'Could not remove wishlist item.');
    }
  };

  // Navigation Items
  const navTabs = [
    { id: 'overview' as const, label: 'Overview', icon: LayoutDashboard, badge: null },
    { id: 'orders' as const, label: 'My Orders', icon: Package, badge: orders.length > 0 ? String(orders.length) : null },
    { id: 'wishlist' as const, label: 'Wishlist', icon: Heart, badge: wishlist.length > 0 ? String(wishlist.length) : null },
    { id: 'addresses' as const, label: 'Delivery Addresses', icon: MapPin, badge: addresses.length > 0 ? String(addresses.length) : null },
    { id: 'profile' as const, label: 'Profile & Security', icon: UserIcon, badge: null },
    { id: 'preferences' as const, label: 'Settings', icon: Sliders, badge: null },
  ];

  const displayName = [profileForm.firstName, profileForm.lastName].filter(Boolean).join(' ') || user?.email?.split('@')[0] || 'Customer';

  return (
    <div className="min-h-screen bg-zinc-50/50 dark:bg-zinc-950 pb-16 transition-colors duration-300">
      {/* Toast Notification */}
      {toast && (
        <div className="fixed right-6 top-6 z-50 flex items-center gap-2.5 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-4 py-3 text-xs font-semibold text-emerald-600 shadow-xl backdrop-blur-md dark:text-emerald-400 animate-in fade-in">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <div>
            <p className="font-bold">{toast.title}</p>
            <p className="text-[11px] opacity-90">{toast.message}</p>
          </div>
        </div>
      )}

      {/* ── Customer Top Profile Hero ── */}
      <div className="border-b border-border bg-surface px-4 py-8 sm:px-6 lg:px-8 shadow-xs">
        <div className="mx-auto max-w-7xl flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="relative group">
              <img
                src={avatarUrl}
                alt={displayName}
                className="h-18 w-18 rounded-2xl object-cover border-2 border-accent shadow-md"
              />
              <button
                type="button"
                onClick={() => {
                  setActiveSection('profile');
                  fileInputRef.current?.click();
                }}
                className="absolute -bottom-1 -right-1 h-6 w-6 rounded-full bg-accent text-white flex items-center justify-center shadow-md hover:scale-110 transition-transform"
                title="Change Photo"
              >
                <Upload className="h-3 w-3" />
              </button>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-black tracking-tight text-primary">
                  {displayName}
                </h1>
                <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-[10px] font-bold text-amber-600 dark:text-amber-400 border border-amber-500/20">
                  <Star className="h-3 w-3 fill-amber-500" />
                  Gold Member
                </span>
              </div>
              <p className="text-xs text-secondary mt-0.5">{user?.email || 'customer@razorhub.in'}</p>
            </div>
          </div>

          {/* Quick KPI Cards */}
          <div className="grid grid-cols-3 gap-3 sm:gap-4">
            <button
              onClick={() => setActiveSection('orders')}
              className="flex flex-col items-center justify-center rounded-xl border border-border bg-background/60 p-3 text-center transition-all hover:border-accent hover:bg-accent/5"
            >
              <Package className="h-4 w-4 text-accent mb-1" />
              <span className="text-base font-black text-primary">{orders.length}</span>
              <span className="text-[10px] font-semibold text-secondary uppercase">Orders</span>
            </button>

            <button
              onClick={() => setActiveSection('wishlist')}
              className="flex flex-col items-center justify-center rounded-xl border border-border bg-background/60 p-3 text-center transition-all hover:border-accent hover:bg-accent/5"
            >
              <Heart className="h-4 w-4 text-rose-500 mb-1" />
              <span className="text-base font-black text-primary">{wishlist.length}</span>
              <span className="text-[10px] font-semibold text-secondary uppercase">Wishlist</span>
            </button>

            <Link
              to="/cart"
              className="flex flex-col items-center justify-center rounded-xl border border-border bg-background/60 p-3 text-center transition-all hover:border-accent hover:bg-accent/5"
            >
              <ShoppingBag className="h-4 w-4 text-emerald-500 mb-1" />
              <span className="text-base font-black text-primary">{cartTotalCount}</span>
              <span className="text-[10px] font-semibold text-secondary uppercase">In Cart</span>
            </Link>
          </div>
        </div>
      </div>

      {/* ── Main Unified Dashboard Layout ── */}
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-8 items-start">
          
          {/* ── Single Unified Left Navigation ── */}
          <aside className="rounded-2xl border border-border bg-surface p-3 shadow-xs space-y-1 lg:sticky lg:top-24">
            {navTabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeSection === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveSection(tab.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-xs font-bold transition-all text-left ${
                    isActive
                      ? 'bg-accent text-white shadow-md shadow-accent/20'
                      : 'text-secondary hover:bg-muted/60 hover:text-primary'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`h-4 w-4 shrink-0 ${isActive ? 'text-white' : 'text-secondary'}`} />
                    <span>{tab.label}</span>
                  </div>
                  {tab.badge && (
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-black ${isActive ? 'bg-white/20 text-white' : 'bg-muted text-secondary'}`}>
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}

            <div className="pt-3 border-t border-border mt-3">
              <button
                type="button"
                onClick={logout}
                className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold text-red-600 dark:text-red-400 hover:bg-red-500/10 transition-colors"
              >
                <LogOut className="h-4 w-4" />
                <span>Sign Out</span>
              </button>
            </div>
          </aside>

          {/* ── Main Active Section Content Panel ── */}
          <main className="space-y-6">

            {/* SECTION 1: OVERVIEW */}
            {activeSection === 'overview' && (
              <div className="space-y-6 animate-in fade-in">
                {/* Welcome & Status Banner */}
                <div className="rounded-2xl border border-border bg-gradient-to-r from-accent/10 via-surface to-surface p-6 sm:p-8 shadow-xs">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-accent">Customer Dashboard Hub</span>
                      <h2 className="text-xl sm:text-2xl font-black text-primary mt-1">Welcome back, {displayName}!</h2>
                      <p className="text-xs text-secondary mt-1 max-w-xl">
                        Track live orders, manage saved delivery locations, browse your curated wishlist, and enjoy instant express checkout.
                      </p>
                    </div>
                    <Link
                      to="/products"
                      className="inline-flex items-center gap-2 rounded-xl bg-accent px-4 py-2.5 text-xs font-bold text-white shadow-md hover:opacity-90 transition-all self-start sm:self-auto"
                    >
                      <ShoppingBag className="h-4 w-4" />
                      Shop Catalog
                    </Link>
                  </div>
                </div>

                {/* Recent Orders Preview */}
                <div className="rounded-2xl border border-border bg-surface p-6 shadow-xs">
                  <div className="flex items-center justify-between border-b border-border pb-4 mb-4">
                    <div className="flex items-center gap-2">
                      <Package className="h-4 w-4 text-accent" />
                      <h3 className="text-sm font-bold text-primary">Recent Orders ({orders.length})</h3>
                    </div>
                    <button
                      type="button"
                      onClick={() => setActiveSection('orders')}
                      className="text-xs font-bold text-accent hover:underline flex items-center gap-1"
                    >
                      View All <ChevronRight className="h-3.5 w-3.5" />
                    </button>
                  </div>

                  {orders.length > 0 ? (
                    <div className="divide-y divide-border/60">
                      {orders.slice(0, 3).map((order) => (
                        <div key={order.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-xs text-primary">Order #{order.id}</span>
                              <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-600 dark:text-emerald-400 capitalize">
                                {order.status}
                              </span>
                            </div>
                            <p className="text-[11px] text-secondary mt-1">
                              Placed on {new Date(order.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                            </p>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-sm font-black text-primary">
                              ₹{Number(order.total_price).toLocaleString('en-IN')}
                            </span>
                            <button
                              type="button"
                              onClick={() => setActiveSection('orders')}
                              className="px-3 py-1.5 rounded-lg border border-border bg-background hover:bg-muted text-xs font-semibold text-primary"
                            >
                              Details
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="py-8 text-center text-secondary text-xs">
                      <p>No orders placed yet. Explore our trending products to get started!</p>
                      <Link to="/products" className="mt-3 inline-block font-bold text-accent hover:underline">
                        Explore Catalog →
                      </Link>
                    </div>
                  )}
                </div>

                {/* Personalized Shopper Recommendations */}
                {recommendations.length > 0 && (
                  <div className="rounded-2xl border border-border bg-surface p-6 shadow-xs">
                    <div className="flex items-center justify-between border-b border-border pb-4 mb-4">
                      <div className="flex items-center gap-2">
                        <Sparkles className="h-4 w-4 text-amber-500" />
                        <h3 className="text-sm font-bold text-primary">Recommended For You</h3>
                      </div>
                      <Link to="/products" className="text-xs font-bold text-accent hover:underline">
                        Browse More
                      </Link>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                      {recommendations.map((prod) => (
                        <ProductCard key={prod.slug} product={prod} compact />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* SECTION 2: MY ORDERS & TRACKING */}
            {activeSection === 'orders' && (
              <div className="rounded-2xl border border-border bg-surface p-6 sm:p-8 shadow-xs space-y-6 animate-in fade-in">
                <div className="flex items-center justify-between border-b border-border pb-4">
                  <div>
                    <h2 className="text-lg font-black text-primary">My Orders &amp; Live Tracking</h2>
                    <p className="text-xs text-secondary mt-0.5">View full order receipts, shipment stages, and return eligibility.</p>
                  </div>
                  <button
                    type="button"
                    onClick={loadCustomerData}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-border bg-background text-xs font-semibold text-secondary hover:text-primary"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
                    Refresh
                  </button>
                </div>

                {orders.length > 0 ? (
                  <div className="space-y-6">
                    {orders.map((order) => (
                      <div key={order.id} className="rounded-xl border border-border bg-background/50 p-5 shadow-xs space-y-4">
                        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-3">
                          <div>
                            <span className="text-xs font-bold text-primary">Order ID: #{order.id}</span>
                            <span className="text-xs text-secondary ml-3">
                              {new Date(order.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-bold text-emerald-600 dark:text-emerald-400 capitalize">
                              ● {order.status}
                            </span>
                            <span className="text-sm font-black text-primary">
                              ₹{Number(order.total_price).toLocaleString('en-IN')}
                            </span>
                          </div>
                        </div>

                        {/* Shipment Tracking Progress Stepper */}
                        <div className="py-2">
                          <div className="flex items-center justify-between text-[11px] font-bold text-secondary mb-2">
                            <span className={order.status ? 'text-accent font-black' : ''}>1. Placed</span>
                            <span className={['processing', 'shipped', 'delivered'].includes(order.status) ? 'text-accent font-black' : ''}>2. Processing</span>
                            <span className={['shipped', 'delivered'].includes(order.status) ? 'text-accent font-black' : ''}>3. Shipped</span>
                            <span className={order.status === 'delivered' ? 'text-emerald-600 dark:text-emerald-400 font-black' : ''}>4. Delivered</span>
                          </div>
                          <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                            <div
                              className="h-full bg-accent transition-all duration-500 rounded-full"
                              style={{
                                width: order.status === 'delivered' ? '100%' : order.status === 'shipped' ? '75%' : order.status === 'processing' ? '50%' : '25%',
                              }}
                            />
                          </div>
                        </div>

                        {/* Order Items */}
                        <div className="space-y-2 pt-2">
                          {order.items?.map((item) => (
                            <div key={item.id} className="flex items-center justify-between gap-4 py-2 border-t border-border/40">
                              <div className="flex items-center gap-3">
                                <img
                                  src={productImage(item.product) || PRODUCT_FALLBACK_IMAGE}
                                  alt={item.product?.name || 'Product'}
                                  className="h-12 w-12 rounded-lg object-cover"
                                />
                                <div>
                                  <p className="text-xs font-bold text-primary line-clamp-1">{item.product?.name || 'Item'}</p>
                                  <p className="text-[11px] text-secondary">Qty: {item.quantity} × ₹{Number(item.price).toLocaleString('en-IN')}</p>
                                </div>
                              </div>
                              <button
                                type="button"
                                onClick={() => addToCart(item.product, 1)}
                                className="px-3 py-1.5 rounded-lg bg-accent/10 hover:bg-accent hover:text-white text-accent text-xs font-bold transition-colors"
                              >
                                Buy Again
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-12 text-center text-secondary">
                    <Package className="h-10 w-10 text-muted mx-auto mb-3" />
                    <h3 className="text-sm font-bold text-primary">No orders placed yet</h3>
                    <p className="text-xs text-secondary mt-1">When you order from RazorHub, your items and tracking updates will appear here in real-time.</p>
                    <Link
                      to="/products"
                      className="mt-4 inline-flex items-center gap-2 rounded-xl bg-accent px-4 py-2 text-xs font-bold text-white shadow-md"
                    >
                      Start Shopping
                    </Link>
                  </div>
                )}
              </div>
            )}

            {/* SECTION 3: MY WISHLIST */}
            {activeSection === 'wishlist' && (
              <div className="rounded-2xl border border-border bg-surface p-6 sm:p-8 shadow-xs space-y-6 animate-in fade-in">
                <div className="flex items-center justify-between border-b border-border pb-4">
                  <div>
                    <h2 className="text-lg font-black text-primary">My Saved Wishlist ({wishlist.length})</h2>
                    <p className="text-xs text-secondary mt-0.5">Products you saved for later. Move them to cart anytime with 1-click.</p>
                  </div>
                  <button
                    type="button"
                    onClick={loadCustomerData}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-border bg-background text-xs font-semibold text-secondary hover:text-primary"
                  >
                    <RefreshCw className="h-3.5 w-3.5" />
                    Refresh
                  </button>
                </div>

                {wishlist.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                    {wishlist.map((prod) => (
                      <div key={prod.id} className="rounded-xl border border-border bg-background p-4 flex flex-col justify-between gap-3 group">
                        <div className="relative aspect-[4/3] rounded-lg overflow-hidden bg-muted">
                          <img
                            src={productImage(prod)}
                            alt={prod.name}
                            className="h-full w-full object-cover object-center group-hover:scale-105 transition-transform"
                          />
                          <button
                            type="button"
                            onClick={() => handleRemoveWishlist(prod.id)}
                            className="absolute top-2 right-2 h-7 w-7 rounded-full bg-white/90 dark:bg-zinc-900/90 text-red-500 flex items-center justify-center shadow-md hover:scale-110 transition-transform"
                            title="Remove from wishlist"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                        <div>
                          <p className="text-[10px] uppercase font-bold text-accent">{prod.category?.name || 'General'}</p>
                          <h4 className="text-xs font-bold text-primary line-clamp-1 mt-0.5">{prod.name}</h4>
                          <p className="text-sm font-black text-primary mt-1">{formatPrice(price(prod))}</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            addToCart(prod, 1);
                            showToast('success', 'Moved to Cart', `Added ${prod.name} to cart.`);
                          }}
                          className="w-full flex items-center justify-center gap-2 rounded-xl bg-accent px-3 py-2 text-xs font-bold text-white shadow-xs hover:opacity-90 transition-all"
                        >
                          <ShoppingBag className="h-3.5 w-3.5" /> Move to Cart
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-12 text-center text-secondary">
                    <Heart className="h-10 w-10 text-muted mx-auto mb-3" />
                    <h3 className="text-sm font-bold text-primary">Your wishlist is empty</h3>
                    <p className="text-xs text-secondary mt-1">Explore our product catalog and click the heart icon on any product to save it here.</p>
                    <Link
                      to="/products"
                      className="mt-4 inline-flex items-center gap-2 rounded-xl bg-accent px-4 py-2 text-xs font-bold text-white shadow-md"
                    >
                      Explore Products
                    </Link>
                  </div>
                )}
              </div>
            )}

            {/* SECTION 4: SAVED ADDRESSES */}
            {activeSection === 'addresses' && (
              <div className="rounded-2xl border border-border bg-surface p-6 sm:p-8 shadow-xs space-y-6 animate-in fade-in">
                <div className="flex items-center justify-between border-b border-border pb-4">
                  <div>
                    <h2 className="text-lg font-black text-primary">Saved Delivery Addresses ({addresses.length})</h2>
                    <p className="text-xs text-secondary mt-0.5">Manage residential and work addresses for fast doorstep delivery.</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setIsAddressModalOpen(true)}
                    className="flex items-center gap-2 rounded-xl bg-accent px-3.5 py-2 text-xs font-bold text-white shadow-xs hover:opacity-90"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    Add Address
                  </button>
                </div>

                {addresses.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {addresses.map((addr) => (
                      <div key={addr.id} className="rounded-xl border border-border bg-background p-5 space-y-2 relative">
                        <div className="flex items-center justify-between">
                          <span className="flex items-center gap-1.5 text-xs font-bold text-primary">
                            <MapPin className="h-4 w-4 text-accent" />
                            Delivery Address #{addr.id}
                          </span>
                          <button
                            type="button"
                            onClick={() => handleDeleteAddress(addr.id)}
                            className="text-secondary hover:text-red-500 p-1"
                            title="Delete address"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                        <p className="text-xs text-primary font-medium">{addr.address_line1}</p>
                        {addr.address_line2 && <p className="text-xs text-secondary">{addr.address_line2}</p>}
                        <p className="text-xs text-secondary">{addr.city}, {addr.state} - {addr.postal_code}</p>
                        <p className="text-xs font-semibold text-accent">{addr.country || 'India'}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-10 text-center text-secondary">
                    <MapPin className="h-10 w-10 text-muted mx-auto mb-3" />
                    <h3 className="text-sm font-bold text-primary">No saved addresses yet</h3>
                    <p className="text-xs text-secondary mt-1">Add your home or office address for fast 1-click checkout.</p>
                    <button
                      type="button"
                      onClick={() => setIsAddressModalOpen(true)}
                      className="mt-4 inline-flex items-center gap-2 rounded-xl bg-accent px-4 py-2 text-xs font-bold text-white shadow-md"
                    >
                      <Plus className="h-3.5 w-3.5" /> Add Delivery Address
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* SECTION 5: PROFILE & SECURITY */}
            {activeSection === 'profile' && (
              <div className="rounded-2xl border border-border bg-surface p-6 sm:p-8 shadow-xs space-y-6 animate-in fade-in">
                <div className="border-b border-border pb-4">
                  <h2 className="text-lg font-black text-primary">Profile &amp; Account Settings</h2>
                  <p className="text-xs text-secondary mt-0.5">Manage your personal information, phone number, and avatar in the database.</p>
                </div>

                {/* Avatar Selection */}
                <div className="rounded-xl border border-border bg-background p-5 flex flex-col sm:flex-row items-center gap-6">
                  <div className="relative group shrink-0">
                    <img
                      src={avatarUrl}
                      alt="Avatar"
                      className="h-20 w-20 rounded-2xl object-cover border-2 border-accent shadow-md"
                    />
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          const reader = new FileReader();
                          reader.onload = (ev) => {
                            const url = ev.target?.result as string;
                            setAvatarUrl(url);
                            localStorage.setItem('razorhub_user_avatar', url);
                          };
                          reader.readAsDataURL(file);
                        }
                      }}
                    />
                  </div>
                  <div className="space-y-2 text-center sm:text-left">
                    <span className="text-xs font-bold uppercase tracking-wider text-secondary">Choose Preset Avatar:</span>
                    <div className="flex flex-wrap gap-2 justify-center sm:justify-start">
                      {PRESET_AVATARS.map((p, i) => (
                        <button
                          key={i}
                          type="button"
                          onClick={() => {
                            setAvatarUrl(p);
                            localStorage.setItem('razorhub_user_avatar', p);
                          }}
                          className={`h-9 w-9 rounded-full overflow-hidden border-2 transition-all ${avatarUrl === p ? 'border-accent ring-2 ring-accent/30' : 'border-transparent'}`}
                        >
                          <img src={p} alt={`Avatar ${i + 1}`} className="h-full w-full object-cover" />
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Profile Form */}
                <form onSubmit={handleSaveProfile} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-1">First Name</label>
                      <input
                        type="text"
                        value={profileForm.firstName}
                        onChange={(e) => setProfileForm({ ...profileForm, firstName: e.target.value })}
                        className="w-full h-11 rounded-xl border border-border bg-background px-3 text-xs font-semibold text-primary outline-none focus:border-accent"
                        placeholder="First name"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-1">Last Name</label>
                      <input
                        type="text"
                        value={profileForm.lastName}
                        onChange={(e) => setProfileForm({ ...profileForm, lastName: e.target.value })}
                        className="w-full h-11 rounded-xl border border-border bg-background px-3 text-xs font-semibold text-primary outline-none focus:border-accent"
                        placeholder="Last name"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-1">Email Address</label>
                      <input
                        type="email"
                        value={profileForm.email}
                        onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                        className="w-full h-11 rounded-xl border border-border bg-background px-3 text-xs font-semibold text-primary outline-none focus:border-accent"
                        placeholder="you@example.com"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold uppercase tracking-wider text-secondary mb-1">Phone Number</label>
                      <input
                        type="tel"
                        value={profileForm.phone}
                        onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                        className="w-full h-11 rounded-xl border border-border bg-background px-3 text-xs font-semibold text-primary outline-none focus:border-accent"
                        placeholder="+91 98765 43210"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="flex items-center gap-2 rounded-xl bg-accent px-5 py-2.5 text-xs font-bold text-white shadow-md hover:opacity-90"
                  >
                    <Save className="h-4 w-4" /> Save Profile Details
                  </button>
                </form>
              </div>
            )}

            {/* SECTION 6: PREFERENCES & SETTINGS */}
            {activeSection === 'preferences' && (
              <div className="rounded-2xl border border-border bg-surface p-6 sm:p-8 shadow-xs space-y-6 animate-in fade-in">
                <div className="border-b border-border pb-4">
                  <h2 className="text-lg font-black text-primary">Preferences &amp; Application Theme</h2>
                  <p className="text-xs text-secondary mt-0.5">Customize your shopping experience, notifications, and dark aesthetics.</p>
                </div>

                <div className="space-y-4">
                  {/* Theme Switcher */}
                  <div className="flex items-center justify-between rounded-xl border border-border bg-background p-4">
                    <div>
                      <span className="text-xs font-bold text-primary">Theme Appearance</span>
                      <p className="text-[11px] text-secondary">Switch between dark mode and light theme</p>
                    </div>
                    <button
                      type="button"
                      onClick={toggleTheme}
                      className="flex items-center gap-2 rounded-xl border border-border bg-surface px-3 py-1.5 text-xs font-bold text-primary shadow-xs"
                    >
                      {theme === 'dark' ? <Moon className="h-4 w-4 text-accent" /> : <Sun className="h-4 w-4 text-amber-500" />}
                      <span className="capitalize">{theme} Theme</span>
                    </button>
                  </div>

                  {/* Currency */}
                  <div className="flex items-center justify-between rounded-xl border border-border bg-background p-4">
                    <div>
                      <span className="text-xs font-bold text-primary">Currency</span>
                      <p className="text-[11px] text-secondary">Default pricing denomination</p>
                    </div>
                    <span className="text-xs font-bold text-accent">Indian Rupee (₹ INR)</span>
                  </div>

                  {/* Notifications */}
                  <div className="flex items-center justify-between rounded-xl border border-border bg-background p-4">
                    <div>
                      <span className="text-xs font-bold text-primary">Order SMS &amp; WhatsApp Updates</span>
                      <p className="text-[11px] text-secondary">Receive real-time shipment updates on your phone</p>
                    </div>
                    <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-bold text-emerald-600 dark:text-emerald-400">
                      Enabled
                    </span>
                  </div>
                </div>
              </div>
            )}

          </main>
        </div>
      </div>

      {/* ── Add Address Modal ── */}
      {isAddressModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4 animate-in fade-in">
          <div className="w-full max-w-md rounded-2xl border border-border bg-surface p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <h3 className="text-base font-bold text-primary">Add Delivery Address</h3>
              <button
                type="button"
                onClick={() => setIsAddressModalOpen(false)}
                className="rounded-lg p-1 text-secondary hover:bg-muted"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleSaveAddress} className="space-y-3">
              <div>
                <label className="block text-[11px] font-bold uppercase text-secondary mb-1">Street Address / Flat / Building</label>
                <input
                  type="text"
                  required
                  value={addressForm.addressLine1}
                  onChange={(e) => setAddressForm({ ...addressForm, addressLine1: e.target.value })}
                  className="w-full h-10 rounded-xl border border-border bg-background px-3 text-xs text-primary outline-none focus:border-accent"
                  placeholder="e.g. 402, Lotus Towers, MG Road"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold uppercase text-secondary mb-1">Area / Landmark (Optional)</label>
                <input
                  type="text"
                  value={addressForm.addressLine2}
                  onChange={(e) => setAddressForm({ ...addressForm, addressLine2: e.target.value })}
                  className="w-full h-10 rounded-xl border border-border bg-background px-3 text-xs text-primary outline-none focus:border-accent"
                  placeholder="Near City Mall"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-bold uppercase text-secondary mb-1">City</label>
                  <input
                    type="text"
                    required
                    value={addressForm.city}
                    onChange={(e) => setAddressForm({ ...addressForm, city: e.target.value })}
                    className="w-full h-10 rounded-xl border border-border bg-background px-3 text-xs text-primary outline-none focus:border-accent"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold uppercase text-secondary mb-1">Pincode</label>
                  <input
                    type="text"
                    required
                    value={addressForm.postalCode}
                    onChange={(e) => setAddressForm({ ...addressForm, postalCode: e.target.value })}
                    className="w-full h-10 rounded-xl border border-border bg-background px-3 text-xs text-primary outline-none focus:border-accent"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full h-11 mt-2 rounded-xl bg-accent text-xs font-bold text-white shadow-md hover:opacity-90"
              >
                Save Delivery Address
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
