import { useState, useEffect, useRef } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  Menu,
  Search,
  ShoppingBag,
  Sparkles,
  User,
  X,
  MapPin,
  Store,
  Heart,
  ChevronDown,
  ArrowRight,
  Flame,
  Bot,
  Building2,
  Package,
  ShieldCheck,
} from 'lucide-react';

import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import ThemeToggle from './ThemeToggle';
import { useTheme } from '../context/ThemeContext';
import { API_BASE } from '../lib/api';
import { useTranslation } from '../i18n/LocaleContext';
import BrandLogo from './BrandLogo';

const NAV_CATEGORIES = [
  { name: 'Air Conditioners', slug: 'appliances', icon: '❄️' },
  { name: 'Mobiles & Tablets', slug: 'mobiles', icon: '📱' },
  { name: 'Laptops & Computing', slug: 'gaming', icon: '💻' },
  { name: 'Home Appliances', slug: 'appliances', icon: '🏠' },
  { name: 'Kitchen & Dining', slug: 'appliances', icon: '🍳' },
  { name: 'TV & Entertainment', slug: 'gaming', icon: '📺' },
  { name: 'Fashion & Apparel', slug: 'fashion', icon: '👕' },
  { name: 'Groceries', slug: 'groceries', icon: '🛒' },
  { name: 'Flash Deals', slug: 'flash-deals', isHot: true },
];

function SearchBar({
  mobile = false,
  onSearch,
}: {
  mobile?: boolean;
  onSearch?: () => void;
}) {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [search, setSearch] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [mobileExpanded, setMobileExpanded] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handler = setTimeout(() => {
      if (search.trim().length > 1) {
        fetch(
          `${API_BASE}/products/suggestions/?q=${encodeURIComponent(
            search.trim()
          )}`
        )
          .then((res) => res.json())
          .then((data: { suggestions: string[] }) => {
            setSuggestions(data.suggestions || []);
            setFocusedIndex(-1);
            setIsOpen(true);
          })
          .catch(() => {
            setSuggestions([]);
            setFocusedIndex(-1);
          });
      } else {
        setSuggestions([]);
        setFocusedIndex(-1);
        setIsOpen(false);
      }
    }, 200);
    return () => clearTimeout(handler);
  }, [search]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setFocusedIndex(-1);
        if (mobile) setMobileExpanded(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [mobile]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (
        event.key === '/' &&
        document.activeElement?.tagName !== 'INPUT' &&
        document.activeElement?.tagName !== 'TEXTAREA'
      ) {
        event.preventDefault();
        if (mobile) setMobileExpanded(true);
        setTimeout(() => inputRef.current?.focus(), 10);
      }
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [mobile]);

  function submitSearch(event: FormEvent<HTMLFormElement> | string) {
    if (typeof event !== 'string') event.preventDefault();
    const query = typeof event === 'string' ? event : search;
    if (!query.trim()) return;

    navigate(`/products?q=${encodeURIComponent(query.trim())}`);
    setIsOpen(false);
    setFocusedIndex(-1);
    if (mobile) setMobileExpanded(false);
    if (onSearch) onSearch();
  }

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || suggestions.length === 0) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setFocusedIndex((prev) =>
        prev < suggestions.length - 1 ? prev + 1 : prev
      );
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setFocusedIndex((prev) => (prev > -1 ? prev - 1 : -1));
    } else if (e.key === 'Enter' && focusedIndex >= 0) {
      e.preventDefault();
      setSearch(suggestions[focusedIndex]);
      submitSearch(suggestions[focusedIndex]);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      setFocusedIndex(-1);
    }
  };

  const renderSuggestions = () => {
    if (!isOpen || suggestions.length === 0) return null;
    return (
      <div className="absolute left-0 right-0 top-full z-50 mt-1.5 overflow-hidden rounded-xl border border-border bg-surface shadow-2xl backdrop-blur-md">
        <ul className="max-h-[70vh] overflow-y-auto py-1">
          {suggestions.map((suggestion, index) => (
            <li key={index}>
              <button
                type="button"
                onClick={() => {
                  setSearch(suggestion);
                  submitSearch(suggestion);
                }}
                className={`w-full text-left flex items-center gap-3 px-4 py-2.5 transition-colors text-sm font-medium text-primary ${
                  index === focusedIndex
                    ? 'bg-accent/15 text-accent'
                    : 'hover:bg-muted'
                }`}
              >
                <Search className="h-4 w-4 text-secondary shrink-0" />
                <span className="truncate capitalize">{suggestion}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
    );
  };

  if (mobile) {
    return (
      <div ref={containerRef} className="flex w-full justify-end md:hidden">
        {!mobileExpanded ? (
          <button
            type="button"
            onClick={() => setMobileExpanded(true)}
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-border text-secondary hover:text-primary btn-press-effect"
            aria-label={t('nav.searchProducts', { defaultValue: 'Search products' })}
          >
            <Search className="h-4 w-4" />
          </button>
        ) : (
          <div className="relative w-full">
            <form onSubmit={submitSearch}>
              <div className="flex items-center gap-2 rounded-xl border border-border bg-background px-3 shadow-xs">
                <Search className="h-4 w-4 shrink-0 text-secondary" />
                <input
                  ref={inputRef}
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  onFocus={() => {
                    if (suggestions.length > 0) setIsOpen(true);
                  }}
                  onKeyDown={handleInputKeyDown}
                  className="h-10 min-w-0 flex-1 bg-transparent text-sm outline-none"
                  placeholder="Search for phone, TV, laptop, fashion..."
                  autoFocus
                />
                <button
                  type="button"
                  onClick={() => {
                    setSearch('');
                    setSuggestions([]);
                    setIsOpen(false);
                    setFocusedIndex(-1);
                    setMobileExpanded(false);
                  }}
                  className="flex h-8 w-8 items-center justify-center rounded-md text-secondary hover:text-primary btn-press-effect"
                  aria-label={t('nav.closeMenu', { defaultValue: 'Close search' })}
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </form>
            {renderSuggestions()}
          </div>
        )}
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative hidden min-w-0 flex-1 max-w-2xl mx-2 lg:mx-6 md:block">
      <form onSubmit={submitSearch} className="flex items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-secondary" />
          <input
            ref={inputRef}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            onFocus={() => {
              if (suggestions.length > 0) setIsOpen(true);
            }}
            onKeyDown={handleInputKeyDown}
            className="h-10.5 w-full rounded-full border border-border bg-muted/40 hover:bg-background focus:bg-background pl-10 pr-20 text-sm outline-none transition-all focus:border-accent focus:ring-2 focus:ring-accent/20"
            placeholder="Search for phone, TV, laptops, home appliances..."
          />
          <button
            type="submit"
            className="absolute right-1.5 top-1/2 -translate-y-1/2 h-7.5 px-3 rounded-full bg-accent text-white text-xs font-semibold hover:opacity-90 transition-opacity flex items-center gap-1"
          >
            Search
          </button>
        </div>
      </form>
      {renderSuggestions()}
    </div>
  );
}

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [locationModal, setLocationModal] = useState(false);
  const [pincode, setPincode] = useState(() => {
    return localStorage.getItem('user_pincode') || 'Mumbai, 400001';
  });
  const [inputPincode, setInputPincode] = useState('');

  const { totalCount } = useCart();
  const { user } = useAuth();
  const userRole = user?.effective_role || user?.role;
  const { theme } = useTheme();
  const { t } = useTranslation();
  const location = useLocation();

  function closeMenu() {
    setMenuOpen(false);
  }

  function handleSaveLocation(e: React.FormEvent) {
    e.preventDefault();
    if (inputPincode.trim()) {
      const loc = `PIN ${inputPincode.trim()}`;
      setPincode(loc);
      localStorage.setItem('user_pincode', loc);
      setLocationModal(false);
      setInputPincode('');
    }
  }

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-surface/95 backdrop-blur-md">
      {/* ── Main Top Navbar ── */}
      <div className="mx-auto max-w-[1360px] w-full px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between gap-3 md:gap-4">
          
          {/* 1. Brand Logo */}
          <Link
            to="/"
            className="group flex shrink-0 items-center py-1 transition-transform hover:opacity-95 active:scale-95"
            onClick={(e) => {
              if (location.pathname === '/') {
                e.preventDefault();
                window.location.reload();
              }
            }}
          >
            <BrandLogo size="md" />
          </Link>

          {/* 2. Location Selector (Vijay Sales / JioMart style) */}
          <button
            type="button"
            onClick={() => setLocationModal(true)}
            className="hidden lg:flex items-center gap-2 rounded-xl border border-border/80 bg-muted/40 hover:bg-muted px-3 py-1.5 text-left text-xs transition-colors shrink-0"
            title="Choose Delivery Location"
          >
            <MapPin className="h-4 w-4 text-accent shrink-0" />
            <div>
              <span className="block text-[10px] uppercase font-semibold text-secondary leading-tight">
                Deliver to
              </span>
              <span className="block font-bold text-primary truncate max-w-[110px] leading-tight">
                {pincode}
              </span>
            </div>
            <ChevronDown className="h-3 w-3 text-secondary ml-0.5" />
          </button>

          {/* 3. Centered Search Bar */}
          <SearchBar />

          {/* 4. Desktop Right Action Items */}
          <div className="ml-auto hidden items-center gap-4 lg:gap-6 md:flex shrink-0">
            <Link
              to="/products"
              className="hidden xl:flex items-center gap-1.5 text-xs font-semibold text-secondary hover:text-primary transition-colors"
            >
              <Store className="h-4 w-4 text-accent" />
              <span>Stores</span>
            </Link>


            <ThemeToggle />

            <Link
              to={user ? '/dashboard' : '/login'}
              className="flex items-center gap-1.5 text-xs font-semibold text-secondary hover:text-primary transition-colors"
            >
              <User className="h-4.5 w-4.5 text-primary" />
              <span className="hidden sm:inline">
                {user ? user.first_name || 'Account' : 'Sign In'}
              </span>
            </Link>

            <Link
              to="/cart"
              className="relative flex items-center gap-1 text-xs font-semibold text-secondary hover:text-primary transition-colors"
            >
              <div className="relative">
                <ShoppingBag className="h-5 w-5 text-primary" />
                {totalCount > 0 && (
                  <span className="absolute -right-2 -top-2 flex h-4 min-w-4 items-center justify-center rounded-full bg-accent px-1 text-[9px] font-black text-white">
                    {totalCount}
                  </span>
                )}
              </div>
              <span className="hidden sm:inline ml-1">Cart</span>
            </Link>
          </div>

          {/* 5. Mobile Controls */}
          <div className="ml-auto flex min-w-0 flex-1 items-center justify-end gap-2 md:hidden">
            <SearchBar mobile />
            <button
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-border text-secondary hover:text-primary"
              aria-label="Open menu"
            >
              {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* ── Sub-Header Category Navigation Ribbon (Vijay Sales / JioMart style) ── */}
      <div className="border-t border-border/60 bg-surface/50 hidden md:block">
        <div className="mx-auto max-w-[1360px] w-full px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between gap-4 overflow-x-auto py-2.5 text-xs font-medium scrollbar-hide">
            <div className="flex items-center gap-5 lg:gap-7 whitespace-nowrap">
              {NAV_CATEGORIES.map((cat) => (
                <Link
                  key={cat.name}
                  to={cat.slug === 'flash-deals' ? '/products?sort=discount' : `/products?category=${cat.slug}`}
                  className={`flex items-center gap-1.5 transition-colors ${
                    cat.isHot
                      ? 'font-bold text-accent hover:opacity-80'
                      : 'text-secondary hover:text-primary hover:font-semibold'
                  }`}
                >
                  {cat.isHot && <Flame className="h-3.5 w-3.5 text-accent animate-pulse" />}
                  <span>{cat.name}</span>
                </Link>
              ))}
            </div>

            <div className="flex items-center gap-3 shrink-0 pl-4 border-l border-border/60 text-xs font-semibold">
              {userRole === 'admin' && (
                <>
                  <Link
                    to="/banking"
                    className="flex items-center gap-1 text-indigo-600 dark:text-indigo-400 hover:text-accent font-bold transition-colors"
                  >
                    <Building2 className="h-3.5 w-3.5" />
                    <span>Banking</span>
                  </Link>
                  <Link
                    to="/agents"
                    className="flex items-center gap-1 text-secondary hover:text-accent transition-colors"
                  >
                    <Bot className="h-3.5 w-3.5 text-indigo-500" />
                    <span>Agent Studio</span>
                  </Link>
                  <Link
                    to="/seller"
                    className="text-secondary hover:text-accent transition-colors"
                  >
                    Seller Hub
                  </Link>
                  <Link
                    to="/admin"
                    className="flex items-center gap-1 text-accent hover:opacity-80 font-bold transition-colors"
                  >
                    <ShieldCheck className="h-3.5 w-3.5" />
                    <span>Admin Panel</span>
                  </Link>
                </>
              )}

              {userRole === 'seller' && (
                <>
                  <Link
                    to="/banking"
                    className="flex items-center gap-1 text-indigo-600 dark:text-indigo-400 hover:text-accent font-bold transition-colors"
                  >
                    <Building2 className="h-3.5 w-3.5" />
                    <span>Banking</span>
                  </Link>
                  <Link
                    to="/agents"
                    className="flex items-center gap-1 text-secondary hover:text-accent transition-colors"
                  >
                    <Bot className="h-3.5 w-3.5 text-indigo-500" />
                    <span>Agent Studio</span>
                  </Link>
                  <Link
                    to="/seller"
                    className="text-secondary hover:text-accent font-bold transition-colors"
                  >
                    Seller Hub
                  </Link>
                </>
              )}

              {userRole === 'customer' && (
                <>
                  <Link
                    to="/dashboard/orders"
                    className="flex items-center gap-1 text-secondary hover:text-primary transition-colors"
                  >
                    <Package className="h-3.5 w-3.5 text-accent" />
                    <span>My Orders</span>
                  </Link>
                  <Link
                    to="/wishlist"
                    className="flex items-center gap-1 text-secondary hover:text-primary transition-colors"
                  >
                    <Heart className="h-3.5 w-3.5 text-rose-500" />
                    <span>Wishlist</span>
                  </Link>
                  <Link
                    to="/seller"
                    className="text-secondary hover:text-accent font-semibold transition-colors"
                  >
                    Sell on RazorHub
                  </Link>
                </>
              )}

              {!userRole && (
                <>
                  <Link
                    to="/login"
                    className="flex items-center gap-1 text-secondary hover:text-primary transition-colors"
                  >
                    <Package className="h-3.5 w-3.5 text-accent" />
                    <span>Track Order</span>
                  </Link>
                  <Link
                    to="/wishlist"
                    className="flex items-center gap-1 text-secondary hover:text-primary transition-colors"
                  >
                    <Heart className="h-3.5 w-3.5 text-rose-500" />
                    <span>Wishlist</span>
                  </Link>
                  <Link
                    to="/seller"
                    className="text-secondary hover:text-accent font-semibold transition-colors"
                  >
                    Sell on RazorHub
                  </Link>
                </>
              )}
            </div>

          </div>
        </div>
      </div>

      {/* ── Delivery Location Modal ── */}
      {locationModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-xs p-4">
          <div className="w-full max-w-sm rounded-2xl border border-border bg-surface p-5 shadow-2xl animate-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <MapPin className="h-5 w-5 text-accent" />
                <h3 className="font-bold text-primary">Choose Delivery Location</h3>
              </div>
              <button
                onClick={() => setLocationModal(false)}
                className="rounded-lg p-1 text-secondary hover:bg-muted"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleSaveLocation} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-secondary uppercase mb-1">
                  Enter Pincode or City
                </label>
                <input
                  type="text"
                  placeholder="e.g. 400001 or Mumbai"
                  value={inputPincode}
                  onChange={(e) => setInputPincode(e.target.value)}
                  className="w-full h-10 rounded-xl border border-border bg-background px-3 text-sm text-primary outline-none focus:border-accent"
                  autoFocus
                />
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    const cities = ['Mumbai, 400001', 'Delhi, 110001', 'Bengaluru, 560001', 'Nagpur, 440001', 'Pune, 411001'];
                    const chosen = cities[Math.floor(Math.random() * cities.length)];
                    setPincode(chosen);
                    localStorage.setItem('user_pincode', chosen);
                    setLocationModal(false);
                  }}
                  className="flex-1 h-9 rounded-xl border border-border bg-muted/50 text-xs font-semibold text-secondary hover:bg-muted"
                >
                  📍 Detect GPS
                </button>
                <button
                  type="submit"
                  className="flex-1 h-9 rounded-xl bg-accent text-xs font-bold text-white hover:opacity-90"
                >
                  Apply Location
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Mobile Hamburger Drawer (Off-Canvas) ── */}
      {menuOpen && (
        <div className="fixed inset-0 z-[100] md:hidden">
          <div
            className="absolute inset-0 bg-background/80 backdrop-blur-xs"
            onClick={closeMenu}
          />
          <div className="absolute inset-y-0 right-0 w-4/5 max-w-xs border-l border-border bg-surface shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
            <div className="flex items-center justify-between border-b border-border p-4">
              <span className="text-base font-bold text-primary">Menu</span>
              <button
                type="button"
                onClick={closeMenu}
                className="flex h-9 w-9 items-center justify-center rounded-lg text-secondary hover:bg-muted"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              <button
                onClick={() => {
                  closeMenu();
                  setLocationModal(true);
                }}
                className="w-full flex items-center justify-between rounded-xl bg-muted/40 p-3 text-xs"
              >
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-accent" />
                  <span className="font-semibold text-primary">{pincode}</span>
                </div>
                <span className="text-accent text-[10px] font-bold">CHANGE</span>
              </button>

              <div className="space-y-1">
                <Link
                  onClick={closeMenu}
                  to="/"
                  className="block rounded-lg px-3 py-2 text-sm font-semibold text-primary hover:bg-muted"
                >
                  Home
                </Link>
                <Link
                  onClick={closeMenu}
                  to="/products"
                  className="block rounded-lg px-3 py-2 text-sm font-semibold text-primary hover:bg-muted"
                >
                  All Products
                </Link>
                <Link
                  onClick={closeMenu}
                  to="/cart"
                  className="flex items-center justify-between rounded-lg px-3 py-2 text-sm font-semibold text-primary hover:bg-muted"
                >
                  <span>My Cart</span>
                  {totalCount > 0 && (
                    <span className="rounded-full bg-accent px-2 py-0.5 text-xs font-bold text-white">
                      {totalCount}
                    </span>
                  )}
                </Link>

                {userRole === 'admin' && (
                  <>
                    <Link
                      onClick={closeMenu}
                      to="/banking"
                      className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-bold text-indigo-600 dark:text-indigo-400 hover:bg-muted"
                    >
                      <Building2 className="h-4 w-4" /> Business Banking
                    </Link>
                    <Link
                      onClick={closeMenu}
                      to="/agents"
                      className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-primary hover:bg-muted"
                    >
                      <Bot className="h-4 w-4 text-indigo-500" /> Agent Studio
                    </Link>
                    <Link
                      onClick={closeMenu}
                      to="/seller"
                      className="block rounded-lg px-3 py-2 text-sm font-semibold text-secondary hover:bg-muted"
                    >
                      Seller Dashboard
                    </Link>
                    <Link
                      onClick={closeMenu}
                      to="/admin"
                      className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-bold text-accent hover:bg-muted"
                    >
                      <ShieldCheck className="h-4 w-4" /> Admin Console
                    </Link>
                  </>
                )}

                {userRole === 'seller' && (
                  <>
                    <Link
                      onClick={closeMenu}
                      to="/banking"
                      className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-bold text-indigo-600 dark:text-indigo-400 hover:bg-muted"
                    >
                      <Building2 className="h-4 w-4" /> Business Banking
                    </Link>
                    <Link
                      onClick={closeMenu}
                      to="/agents"
                      className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-primary hover:bg-muted"
                    >
                      <Bot className="h-4 w-4 text-indigo-500" /> Agent Studio
                    </Link>
                    <Link
                      onClick={closeMenu}
                      to="/seller"
                      className="block rounded-lg px-3 py-2 text-sm font-semibold text-secondary hover:bg-muted"
                    >
                      Seller Dashboard
                    </Link>
                  </>
                )}

                {userRole === 'customer' && (
                  <>
                    <Link
                      onClick={closeMenu}
                      to="/dashboard/orders"
                      className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-primary hover:bg-muted"
                    >
                      <Package className="h-4 w-4 text-accent" /> My Orders
                    </Link>
                    <Link
                      onClick={closeMenu}
                      to="/wishlist"
                      className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-primary hover:bg-muted"
                    >
                      <Heart className="h-4 w-4 text-rose-500" /> Wishlist
                    </Link>
                    <Link
                      onClick={closeMenu}
                      to="/seller"
                      className="block rounded-lg px-3 py-2 text-sm font-semibold text-secondary hover:bg-muted"
                    >
                      Sell on RazorHub
                    </Link>
                  </>
                )}

                {!userRole && (
                  <>
                    <Link
                      onClick={closeMenu}
                      to="/login"
                      className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-primary hover:bg-muted"
                    >
                      <Package className="h-4 w-4 text-accent" /> Track Order
                    </Link>
                    <Link
                      onClick={closeMenu}
                      to="/wishlist"
                      className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-primary hover:bg-muted"
                    >
                      <Heart className="h-4 w-4 text-rose-500" /> Wishlist
                    </Link>
                    <Link
                      onClick={closeMenu}
                      to="/seller"
                      className="block rounded-lg px-3 py-2 text-sm font-semibold text-secondary hover:bg-muted"
                    >
                      Sell on RazorHub
                    </Link>
                  </>
                )}
              </div>


              <div className="border-t border-border pt-3">
                <span className="block text-[11px] font-bold uppercase tracking-wider text-secondary mb-2">
                  Popular Categories
                </span>
                <div className="grid grid-cols-2 gap-1.5 text-xs">
                  {NAV_CATEGORIES.slice(0, 6).map((cat) => (
                    <Link
                      key={cat.name}
                      onClick={closeMenu}
                      to={`/products?category=${cat.slug}`}
                      className="rounded-md bg-muted/30 px-2.5 py-2 text-secondary hover:text-primary font-medium truncate"
                    >
                      {cat.name}
                    </Link>
                  ))}
                </div>
              </div>

              <div className="border-t border-border pt-3">
                <Link
                  onClick={closeMenu}
                  to={user ? '/dashboard' : '/login'}
                  className="block rounded-lg px-3 py-2 text-sm font-semibold text-primary hover:bg-muted"
                >
                  {user ? 'My Account' : 'Sign In / Register'}
                </Link>
              </div>
            </div>

            <div className="border-t border-border bg-muted/20 p-4 flex items-center justify-between">
              <span className="text-xs font-semibold text-secondary">Dark Mode</span>
              <ThemeToggle />
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
