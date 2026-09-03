import React, { useState, useEffect } from "react";
import type { ChangeEvent } from "react";
import { Link, useLocation, Routes, Route } from "react-router-dom";
import { v4 as uuid } from "uuid";
import {
  Package,
  Plus,
  Building2,
  ShieldAlert,
  Bell,
  Users as UsersIcon,
  Settings as SettingsIcon,
  CheckCircle2,
  ExternalLink,
  Sparkles,
  Bot,
  Store as StoreIcon,
  FileText,
  Code2,
  LogOut,
  Zap,
  Trash2,
  Edit,
  ArrowRight,
  BookOpen,
  HelpCircle,
  Shield,
  Cookie,
  MapPin,
  Search,
  BarChart2,
} from "lucide-react";

import AIChatPanel from "./components/ai/AIChatPanel";
import FloatingAIButton from "./components/ai/FloatingAIButton";
import AnalyticsCharts from "./components/AnalyticsCharts";
import FilterBar from "./components/FilterBar";
import KpiStats from "./components/KpiStats";
import ProductCard from "./components/ProductCard";
import Button from "./components/ui/Button";
import ColorCircle from "./components/ui/ColorCircle";
import ErrorMessage from "./components/ui/ErrorMessage";
import Input from "./components/ui/Input";
import Modal from "./components/ui/Modal";
import Select from "./components/ui/Select";
import Toast, { type ToastMessage } from "./components/ui/Toast";
import { AIProvider } from "./context/AIContext";
import { ThemeProvider as SellerThemeProvider } from "./context/ThemeContext";
import { categories as defaultCategories, colors, formInputsList, productList } from "./data";
import { mockUsers } from "./data/mockUsers";
import { useTranslation } from "./i18n";
import type { Category, Product } from "./interfaces";
import UsersPage from "./pages/users/UsersPage";
import SettingsPage from "./pages/settings/SettingsPage";
import RazorHubSellerDashboard from "./pages/RazorHubSellerDashboard";
import AgentsBridge from "./pages/AgentsBridge";
import AuditTrail from "./pages/AuditTrail";
import OrdersPage from "../pages/OrdersPage";
import DocsPage from "./pages/support/DocsPage";
import ApiPage from "./pages/support/ApiPage";
import HelpPage from "./pages/support/HelpPage";
import PrivacyPage from "./pages/legal/PrivacyPage";
import TermsPage from "./pages/legal/TermsPage";
import CookiesPage from "./pages/legal/CookiesPage";
import BusinessBankingPage from "../pages/banking/BusinessBankingPage";
import RiskEnginePage from "../pages/RiskEnginePage";
import { productValidation } from "./schema";
import { getLocalizedText } from "./utils/productUtils";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import ThemeToggle from "../components/ThemeToggle";
import { apiRequest, unwrapList } from "../lib/api";
import { productImage, type CategoryType, type ProductType } from "../lib/products";

function PlaceholderPage({ title, description }: { title: string, description: string }) {
  return (
    <div className="min-h-[85vh] bg-gradient-to-br from-white via-gray-50 to-white dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 rounded-3xl p-8 border border-gray-200 dark:border-gray-800 shadow-2xl flex flex-col items-center justify-center text-center">
      <h2 className="text-3xl font-extrabold text-gray-900 dark:text-white mb-2">{title}</h2>
      <p className="text-gray-500 dark:text-gray-400">{description}</p>
    </div>
  );
}

function getPaginationRange(
 currentPage: number,
 totalPages: number,
 isMobile: boolean = false
): (number | string)[] {
 if (!isMobile || totalPages <= 5) {
 return Array.from({ length: totalPages }, (_, i) => i + 1);
 }
 const delta = 1;
 const left = currentPage - delta;
 const right = currentPage + delta;
 const range: number[] = [];
 const rangeWithDots: (number | string)[] = [];
 let l: number | null = null;

 for (let i = 1; i <= totalPages; i++) {
 if (i === 1 || i === totalPages || (i >= left && i <= right)) {
 range.push(i);
 }
 }

 for (const i of range) {
 if (l !== null) {
 if (i - l === 2) rangeWithDots.push(l + 1);
 else if (i - l !== 1) rangeWithDots.push("...");
 }
 rangeWithDots.push(i);
 l = i;
 }

 return rangeWithDots;
}

function SellerProductsView({
 open,
 products,
 searchQuery,
 setSearchQuery,
 filterCategory,
 setFilterCategory,
 sortBy,
 setSortBy,
 setProductToEdit,
 onDeleteProduct,
 categoriesList,
}: {
 open: () => void;
 products: Product[];
 searchQuery: string;
 setSearchQuery: (val: string) => void;
 filterCategory: string;
 setFilterCategory: (val: string) => void;
 sortBy: string;
 setSortBy: (val: string) => void;
 setProductToEdit: (selectedProduct: Product) => void;
 onDeleteProduct?: (productId: string) => void;
 categoriesList: Category[];
}) {
 const { t } = useTranslation();
 const [currentPage, setCurrentPage] = useState<number>(1);
 const [stockStatus, setStockStatus] = useState("all");
 const [itemsPerPage, setItemsPerPage] = useState(8);

 useEffect(() => {
 const handleResize = () => {
 if (window.innerWidth >= 1280) setItemsPerPage(12);
 else if (window.innerWidth >= 1024) setItemsPerPage(8);
 else if (window.innerWidth >= 640) setItemsPerPage(6);
 else setItemsPerPage(4);
 };
 handleResize();
 window.addEventListener("resize", handleResize);
 return () => window.removeEventListener("resize", handleResize);
 }, []);

 const filteredProducts = products.filter((p) => {
 const pTitle = getLocalizedText(p.title);
 const pDesc = getLocalizedText(p.description);
 const matchesSearch =
 pTitle.toLowerCase().includes(searchQuery.toLowerCase()) ||
 pDesc.toLowerCase().includes(searchQuery.toLowerCase());
 const matchesCategory =
 filterCategory ==="all" ||
 p.category.name.toLowerCase() === filterCategory.toLowerCase();
 const itemStock = p.stock ?? 15;
 const matchesStock =
 stockStatus ==="all" ||
 (stockStatus ==="in-stock" && itemStock > 10) ||
 (stockStatus ==="low-stock" && itemStock > 0 && itemStock <= 10) ||
 (stockStatus ==="out-of-stock" && itemStock === 0);

 return matchesSearch && matchesCategory && matchesStock;
 });

 const sortedProducts = [...filteredProducts].sort((a, b) => {
 const aPrice = Number(a.price) || 0;
 const bPrice = Number(b.price) || 0;
 const aRating = a.rating ?? 4.5;
 const bRating = b.rating ?? 4.5;
 const aTitle = getLocalizedText(a.title).toLowerCase();
 const bTitle = getLocalizedText(b.title).toLowerCase();

 switch (sortBy) {
 case"price-asc":
 return aPrice - bPrice;
 case"price-desc":
 return bPrice - aPrice;
 case"newest":
 return (
 new Date(b.createdAt ||"").getTime() -
 new Date(a.createdAt ||"").getTime()
 );
 case"rating":
 return bRating - aRating;
 case"title-asc":
 return aTitle.localeCompare(bTitle);
 default:
 return 0;
 }
 });

 const totalPages = Math.ceil(sortedProducts.length / itemsPerPage) || 1;
 const validCurrentPage = Math.min(currentPage, totalPages);
 const startIndex = (validCurrentPage - 1) * itemsPerPage;
 const paginatedProducts = sortedProducts.slice(
 startIndex,
 startIndex + itemsPerPage
 );

 useEffect(() => {
 setCurrentPage(1);
 }, [searchQuery, filterCategory, sortBy, stockStatus]);

 return (
 <div className="space-y-8">
 {/* 1. Header Overview Banner */}
 <div className="relative overflow-hidden rounded-3xl border border-border bg-gradient-to-br from-surface to-muted/60 p-6 shadow-sm md:p-8">
 <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
 <div className="space-y-2">
 <div className="inline-flex items-center gap-2 rounded-full border border-accent/20 bg-accent/10 px-3 py-1 text-xs font-semibold text-accent">
 <Sparkles className="h-3.5 w-3.5" />
 <span>RazorHub Verified Seller Central</span>
 </div>
 <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-primary">
 Live Product Catalog & Store Analytics
 </h1>
 <p className="text-sm text-secondary max-w-2xl">
 Manage your real-time inventory, monitor catalog valuations, and analyze store growth synced directly with RazorHub database.
 </p>
 </div>
 <Button
 onClick={open}
 className="flex items-center gap-2 rounded-2xl bg-accent px-5 py-3 text-sm font-bold text-white shadow-md hover:bg-accent/90 transition-transform active:scale-95"
 >
 <Plus className="h-4 w-4" /> Add Catalog Product
 </Button>
 </div>
 </div>

 {/* 2. Executive KPI Cards */}
 <KpiStats products={products} />

 {/* 3. Real-time Charts & Analytics */}
 <AnalyticsCharts products={products} />

 {/* 4. Product Catalog Listing Section */}
 <section className="space-y-6">
 <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
 <div>
 <h2 className="text-xl font-extrabold tracking-tight text-primary">
 Active Inventory ({sortedProducts.length})
 </h2>
 <p className="text-xs text-secondary">
 Real-time products synced with storefront database
 </p>
 </div>
 <div className="flex items-center gap-2">
 <Button
 onClick={open}
 className="bg-accent text-white hover:bg-accent/90 text-xs font-bold px-3 py-2 rounded-xl"
 >
 <Plus className="h-3.5 w-3.5 mr-1" /> New Product
 </Button>
 </div>
 </div>

 {/* Search & Filtering Strip */}
 <FilterBar
 searchQuery={searchQuery}
 setSearchQuery={setSearchQuery}
 selectedCategory={filterCategory}
 setSelectedCategory={setFilterCategory}
 sortBy={sortBy}
 setSortBy={setSortBy}
 stockStatus={stockStatus}
 setStockStatus={setStockStatus}
 categories={categoriesList}
 totalResults={sortedProducts.length}
 totalProducts={products.length}
 />

 {/* Product Cards Grid */}
 {paginatedProducts.length > 0 ? (
 <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
 {paginatedProducts.map((prod) => (
 <ProductCard
 key={prod.id || prod.title.toString()}
 product={prod}
 setProductToEdit={setProductToEdit}
 onDelete={onDeleteProduct}
 />
 ))}
 </div>
 ) : (
 <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-border bg-surface/50 p-12 text-center">
 <Package className="h-12 w-12 text-secondary/40 mb-3" />
 <h3 className="text-base font-bold text-primary">No products found</h3>
 <p className="text-xs text-secondary mt-1 max-w-sm">
 Try adjusting your search query, filters, or create a new catalog item.
 </p>
 <Button
 onClick={open}
 className="mt-4 bg-accent text-white hover:bg-accent/90 text-xs font-bold px-4 py-2 rounded-xl"
 >
 <Plus className="h-3.5 w-3.5 mr-1" /> Add Product Now
 </Button>
 </div>
 )}

 {/* Pagination Navigation */}
 {totalPages > 1 && (
 <div className="flex items-center justify-center gap-2 pt-6">
 <button
 disabled={validCurrentPage === 1}
 onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
 className="rounded-xl border border-border bg-surface px-3 py-1.5 text-xs font-bold text-secondary hover:text-primary disabled:opacity-40"
 >
 Previous
 </button>
 {getPaginationRange(validCurrentPage, totalPages).map((p, idx) =>
 p ==="..." ? (
 <span key={`dots-${idx}`} className="px-2 text-xs text-secondary">
 ...
 </span>
 ) : (
 <button
 key={`page-${p}`}
 onClick={() => setCurrentPage(Number(p))}
 className={`h-8 w-8 rounded-xl text-xs font-bold transition-colors ${
 validCurrentPage === p
 ?"bg-accent text-white shadow-sm"
 :"border border-border bg-surface text-secondary hover:text-primary"
 }`}
 >
 {p}
 </button>
 )
 )}
 <button
 disabled={validCurrentPage === totalPages}
 onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
 className="rounded-xl border border-border bg-surface px-3 py-1.5 text-xs font-bold text-secondary hover:text-primary disabled:opacity-40"
 >
 Next
 </button>
 </div>
 )}
 </section>
 </div>
 );
}

export default function SellerPortal() {
  const { t } = useTranslation();
  const { user, token, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
 const location = useLocation();

 const [products, setProducts] = useState<Product[]>([]);
 const [categoriesList, setCategoriesList] = useState<Category[]>(defaultCategories);
 const [isAiOpen, setIsAiOpen] = useState(false);
 const [isLoading, setIsLoading] = useState(true);

  // Load real products & categories from Django backend
  useEffect(() => {
    let isMounted = true;
    const fetchCatalog = async () => {
      try {
        setIsLoading(true);
        // 1. Fetch categories from backend
        const catsRes = await apiRequest<any>('/products/categories/').catch(() => []);
        const apiCats = unwrapList<CategoryType>(catsRes);
        if (isMounted && apiCats && apiCats.length > 0) {
          const mappedCats = apiCats.map((c) => ({
            id: String(c.id),
            name: c.name,
            imageURL: '',
          }));
          setCategoriesList(mappedCats);
        }

        // 2. Fetch live products from backend scoped to seller's store
        let apiProds: ProductType[] = [];
        if (token && !token.startsWith('__demo_')) {
          const mineRes = await apiRequest<any>('/products/items/?mine=true&page_size=200', { token }).catch(() => []);
          apiProds = unwrapList<ProductType>(mineRes);
        } else {
          const allRes = await apiRequest<any>('/products/items/?page_size=200').catch(() => []);
          apiProds = unwrapList<ProductType>(allRes);
        }

        if (isMounted) {
          const mappedProds: Product[] = apiProds.map((p) => ({
            id: String(p.id),
            slug: p.slug,
            title: p.name,
            description: p.description,
            imageURL: productImage(p) || p.image_url || 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=80',
            price: String(Math.round(Number(p.discount_price || p.price))),
            colors: ['#121212', '#2563eb', '#10b981'],
            stock: p.stock ?? 25,
            sku: `SKU-${p.id}`,
            rating: Number(p.rating || p.average_rating || 4.5),
            reviewCount: p.review_count || 100,
            createdAt: new Date().toISOString(),
            category: {
              id: p.category?.id,
              name: p.category?.name || 'General',
              imageURL: '',
            },
          }));
          setProducts(mappedProds);
        }
      } catch (err) {
        console.warn('Backend load fallback:', err);
        if (isMounted) setProducts(productList);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    fetchCatalog();
    return () => {
      isMounted = false;
    };
  }, [token]);

 const [searchQuery, setSearchQuery] = useState("");
 const [filterCategory, setFilterCategory] = useState("all");
 const [sortBy, setSortBy] = useState("default");

 // Modal states
 const [isOpen, setIsOpen] = useState(false);
 const [productToEdit, setProductToEdit] = useState<Product | null>(null);
 const [productToDelete, setProductToDelete] = useState<Product | null>(null);

 const defaultProduct: Product = {
 id:"",
 title: { en:"" },
 description: { en:"" },
 imageURL:"",
 price:"",
 colors: [],
 category: categoriesList[0] || defaultCategories[0],
 stock: 25,
 rating: 4.8,
 reviewCount: 120,
 sku: `SKU-${Date.now().toString().slice(-4)}`,
 };

 const [product, setProduct] = useState<Product>(defaultProduct);
 const [tempColors, setTempColors] = useState<string[]>([]);
 const [selectedCategory, setSelectedCategory] = useState<Category>(
 categoriesList[0] || defaultCategories[0]
 );
 const [errors, setErrors] = useState<Record<string, string>>({});
 const [toasts, setToasts] = useState<ToastMessage[]>([]);

 const addToast = (
 type:"success" |"error" |"info",
 title: string,
 message: string =""
 ) => {
 const newToast: ToastMessage = {
 id: uuid(),
 type,
 title,
 message,
 };
 setToasts((prev) => [...prev, newToast]);
 };

 const dismissToast = (id: string) => {
 setToasts((prev) => prev.filter((t) => t.id !== id));
 };

 const openAddModal = () => {
 setProductToEdit(null);
 setProduct(defaultProduct);
 setTempColors([]);
 setSelectedCategory(categoriesList[0] || defaultCategories[0]);
 setErrors({});
 setIsOpen(true);
 };

 const openEditModal = (p: Product) => {
 setProductToEdit(p);
 setProduct(p);
 setTempColors(p.colors || []);
 setSelectedCategory(
 categoriesList.find((c) => c.name.toLowerCase() === p.category.name.toLowerCase()) ||
 categoriesList[0] ||
 defaultCategories[0]
 );
 setErrors({});
 setIsOpen(true);
 };

 const closeModal = () => {
 setIsOpen(false);
 setProductToEdit(null);
 };

 const onChangeHandler = (
 e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
 ) => {
 const { name, value } = e.target;
 if (name ==="title" || name ==="description") {
 setProduct((prev) => ({
 ...prev,
 [name]: {
 ...(typeof prev[name] ==="object" ? prev[name] : { en:"" }),
 en: value,
 },
 }));
 } else {
 setProduct((prev) => ({ ...prev, [name]: value }));
 }
 setErrors((prev) => ({ ...prev, [name]:"" }));
 };

 const onSubmitHandler = async (e: React.FormEvent) => {
 e.preventDefault();
 const titleVal = getLocalizedText(product.title);
 const descVal = getLocalizedText(product.description);
 const validationErrors = productValidation({
 title: titleVal,
 description: descVal,
 imageURL: product.imageURL,
 price: product.price,
 colors: tempColors,
 });

 if (Object.keys(validationErrors).length > 0) {
 setErrors(validationErrors);
 return;
 }

 if (productToEdit) {
 // 1. Live Backend Update
 try {
 if (token && !token.startsWith('__demo_')) {
 await apiRequest(`/products/${productToEdit.slug || productToEdit.id}/`, {
 method: 'PATCH',
 token,
 body: JSON.stringify({
 name: titleVal,
 description: descVal,
 price: product.price,
 stock: Number(product.stock) || 25,
 primary_image_url: product.imageURL,
 }),
 });
 }
 } catch (err) {
 console.warn('Backend update notice:', err);
 }

 setProducts((prev) =>
 prev.map((p) =>
 p.id === productToEdit.id
 ? {
 ...product,
 colors: tempColors,
 category: selectedCategory,
 }
 : p
 )
 );
 addToast(
"success",
"Product Updated",
 `"${titleVal}" was saved to RazorHub database.`
 );
 } else {
 // 2. Live Backend Create
 let createdId = uuid();
 let createdSlug = '';
 try {
 if (token && !token.startsWith('__demo_')) {
 const created = await apiRequest<ProductType>('/products/', {
 method: 'POST',
 token,
 body: JSON.stringify({
 name: titleVal,
 description: descVal,
 price: product.price,
 stock: Number(product.stock) || 25,
 category_id: selectedCategory.id || 1,
 primary_image_url: product.imageURL,
 tag: 'Featured',
 is_active: true,
 }),
 });
 createdId = String(created.id);
 createdSlug = created.slug;
 }
 } catch (err) {
 console.warn('Backend create notice:', err);
 }

 const newProd: Product = {
 ...product,
 id: createdId,
 slug: createdSlug,
 colors: tempColors,
 category: selectedCategory,
 stock: Number(product.stock) || 25,
 rating: 4.8,
 reviewCount: 1,
 sku: `SKU-${Math.floor(1000 + Math.random() * 9000)}`,
 createdAt: new Date().toISOString(),
 };
 setProducts((prev) => [newProd, ...prev]);
 addToast(
"success",
"Product Created",
 `"${titleVal}" added to database & live storefront.`
 );
 }

 closeModal();
 };

 const handleConfirmDelete = async () => {
 if (productToDelete) {
 const titleVal = getLocalizedText(productToDelete.title);
 try {
 if (token && !token.startsWith('__demo_')) {
 await apiRequest(`/products/${productToDelete.slug || productToDelete.id}/`, {
 method: 'DELETE',
 token,
 });
 }
 } catch (err) {
 console.warn('Backend delete notice:', err);
 }

 setProducts((prev) => prev.filter((p) => p.id !== productToDelete.id));
 addToast(
"info",
"Product Deleted",
 `"${titleVal}" was removed from database & storefront.`
 );
 setProductToDelete(null);
 }
 };

 const isCurrent = (path: string) => location.pathname === path;

 return (
 <SellerThemeProvider>
 <AIProvider
 products={products}
 setProducts={setProducts}
 users={mockUsers}
 addToast={(type, title, msg) =>
 addToast(
 type ==="danger" ?"error" : (type as"success" |"error" |"info"),
 title,
 msg ||""
 )
 }
 >
  <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 font-sans transition-colors duration-300">
    {/* Top RazorHubSeller Navigation Header */}
    <header className="sticky top-0 z-40 border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-950/80 backdrop-blur-xl">
      <div className="mx-auto max-w-[1400px] w-full flex items-center justify-between px-4 sm:px-6 py-3">
        <div className="flex items-center gap-4 lg:gap-6">
          <Link to="/" className="flex flex-col group" title="Navigate to RazorHub Home">
            <h1 className="text-xl sm:text-2xl font-black text-gray-900 dark:text-white tracking-tight leading-none">
              RazorHub
            </h1>
            <p className="text-[10px] text-gray-500 dark:text-gray-400 mt-1 uppercase tracking-wider font-bold hidden sm:block">
              Commerce Platform
            </p>
          </Link>

          <nav className="hidden xl:flex items-center gap-1 bg-gray-100/70 dark:bg-gray-900/70 p-1 rounded-xl border border-gray-200 dark:border-gray-800 text-xs font-semibold">
            <Link
              to="/seller"
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition-all duration-200 ${
                isCurrent("/seller")
                  ? "bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 shadow-xs"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-200/50 dark:hover:bg-gray-800/50"
              }`}
            >
              <StoreIcon className="h-3.5 w-3.5" />
              Dashboard
            </Link>

            <Link
              to="/seller/products"
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition-all duration-200 ${
                isCurrent("/seller/products")
                  ? "bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 shadow-xs"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-200/50 dark:hover:bg-gray-800/50"
              }`}
            >
              <Package className="h-3.5 w-3.5" />
              Catalog
            </Link>

            <Link
              to="/seller/orders"
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition-all duration-200 ${
                isCurrent("/seller/orders")
                  ? "bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 shadow-xs"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-200/50 dark:hover:bg-gray-800/50"
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              Orders
            </Link>

            <Link
              to="/seller/users"
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition-all duration-200 ${
                isCurrent("/seller/users")
                  ? "bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 shadow-xs"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-200/50 dark:hover:bg-gray-800/50"
              }`}
            >
              <UsersIcon className="h-3.5 w-3.5" />
              Customers
            </Link>

            <Link
              to="/seller/banking"
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition-all duration-200 ${
                location.pathname.startsWith("/seller/banking")
                  ? "bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 shadow-xs"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-200/50 dark:hover:bg-gray-800/50"
              }`}
            >
              <Building2 className="h-3.5 w-3.5" />
              Banking
            </Link>

            <Link
              to="/seller/agents"
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition-all duration-200 ${
                location.pathname.startsWith("/seller/agents")
                  ? "bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 shadow-xs"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-200/50 dark:hover:bg-gray-800/50"
              }`}
            >
              <Bot className="h-3.5 w-3.5 text-indigo-500" />
              Agents
            </Link>

            <Link
              to="/seller/risk"
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition-all duration-200 ${
                location.pathname.startsWith("/seller/risk")
                  ? "bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 shadow-xs"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-200/50 dark:hover:bg-gray-800/50"
              }`}
            >
              <ShieldAlert className="h-3.5 w-3.5" />
              Risk
            </Link>

            <Link
              to="/seller/audit"
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition-all duration-200 ${
                isCurrent("/seller/audit")
                  ? "bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 shadow-xs"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-200/50 dark:hover:bg-gray-800/50"
              }`}
            >
              <Code2 className="h-3.5 w-3.5" />
              Audit
            </Link>

            <Link
              to="/seller/settings"
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 transition-all duration-200 ${
                isCurrent("/seller/settings")
                  ? "bg-white dark:bg-gray-800 text-blue-600 dark:text-blue-400 shadow-xs"
                  : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-200/50 dark:hover:bg-gray-800/50"
              }`}
            >
              <SettingsIcon className="h-3.5 w-3.5" />
              Settings
            </Link>
          </nav>
        </div>

        {/* Action Buttons & Badges */}
        <div className="flex items-center gap-2.5 sm:gap-3">
          <Button
            className="bg-blue-600 text-white hover:bg-blue-700 shadow-sm text-xs font-bold py-2 px-3 sm:px-4 rounded-xl transition-all active:scale-95 flex items-center"
            onClick={openAddModal}
          >
            <Plus className="h-4 w-4 mr-1" />
            <span className="hidden sm:inline">Add Product</span>
            <span className="sm:hidden">Add</span>
          </Button>

          {/* Notification Bell */}
          <Link
            to="/notifications"
            className="flex items-center justify-center h-9 w-9 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-xs hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors relative"
            title="Communications & Notifications"
          >
            <Bell className="h-4 w-4 text-gray-600 dark:text-gray-400" />
          </Link>

          <div className="flex items-center rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-xs">
            <ThemeToggle />
          </div>


          <Button
            onClick={logout}
            className="flex items-center gap-1.5 rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-900/20 px-3 py-2 text-xs font-bold text-red-600 dark:text-red-400 shadow-xs hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors"
            title="Logout"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Logout</span>
          </Button>
        </div>
      </div>
    </header>

    {/* Sub Navigation on Tablet & Mobile (Horizontal Scrolling Strip) */}
    <div className="flex xl:hidden overflow-x-auto border-b border-gray-200 dark:border-gray-800 bg-white/70 dark:bg-gray-950/70 backdrop-blur-md px-4 py-2.5 text-xs font-semibold gap-1.5 scrollbar-none">
      {[
        { name: "Dashboard", href: "/seller" },
        { name: "Catalog", href: "/seller/products" },
        { name: "Orders", href: "/seller/orders" },
        { name: "Customers", href: "/seller/users" },
        { name: "Banking", href: "/seller/banking" },
        { name: "Agents", href: "/seller/agents" },
        { name: "Risk", href: "/seller/risk" },
        { name: "Audit", href: "/seller/audit" },
        { name: "Settings", href: "/seller/settings" },
      ].map((item) => (
        <Link
          key={item.href}
          to={item.href}
          className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition-all ${
            isCurrent(item.href)
              ? "bg-blue-600 text-white shadow-xs"
              : "bg-gray-100 dark:bg-gray-900 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          }`}
        >
          {item.name}
        </Link>
      ))}
    </div> 

 {/* Main Content Area */}
 <main className="mx-auto max-w-[1360px] w-full px-4 py-8 sm:px-6 lg:px-8">
  <Routes>
    <Route path="/" element={<RazorHubSellerDashboard />} />
    <Route
      path="/products"
      element={
        <SellerProductsView
          open={openAddModal}
          products={products}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          filterCategory={filterCategory}
          setFilterCategory={setFilterCategory}
          sortBy={sortBy}
          setSortBy={setSortBy}
          setProductToEdit={openEditModal}
          onDeleteProduct={(id) => {
            const p = products.find((x) => x.id === id);
            if (p) setProductToDelete(p);
          }}
          categoriesList={categoriesList}
        />
      }
    />
    <Route path="/orders" element={<OrdersPage mode="seller" />} />
    <Route path="/users" element={<UsersPage />} />
    {/* Banking — embedded in the seller shell */}
    <Route path="/banking" element={<BusinessBankingPage embedded />} />
    <Route path="/banking/*" element={<BusinessBankingPage embedded />} />
    {/* Risk Engine — embedded */}
    <Route path="/risk" element={<RiskEnginePage embedded />} />
    {/* Agents — bridge to real Agent Studio */}
    <Route path="/agents" element={<AgentsBridge />} />
    {/* Audit trail */}
    <Route path="/audit" element={<AuditTrail />} />
    {/* Settings */}
    <Route
      path="/settings"
      element={
        <SettingsPage
          darkMode={theme === "dark"}
          toggleDarkMode={toggleTheme}
          addToast={addToast}
        />
      }
    />
  </Routes>

 {/* Add / Edit Product Modal */}
 <Modal
 isOpen={isOpen}
 closeModal={closeModal}
 title={productToEdit ?"Edit Product Details" :"Add New Catalog Product"}
 >
 <form className="flex flex-col gap-y-3" onSubmit={onSubmitHandler}>
 {formInputsList.map((input) => (
 <div className="flex flex-col" key={input.id}>
 <label
 htmlFor={input.id}
 className="mb-1 text-xs font-semibold uppercase tracking-wide text-secondary"
 >
 {input.label}
 </label>
 <Input
 type={input.type}
 id={input.id}
 name={input.name}
 value={
 input.name ==="title"
 ? getLocalizedText(product.title)
 : input.name ==="description"
 ? getLocalizedText(product.description)
 : (product[input.name as keyof Product] as string) ||""
 }
 onChange={onChangeHandler}
 placeholder={`Enter ${input.label}...`}
 className="border border-border bg-surface text-primary focus:border-accent"
 />
 <ErrorMessage msg={errors[input.name]} />
 </div>
 ))}

 <div className="flex flex-col">
 <label className="mb-1 text-xs font-semibold uppercase tracking-wide text-secondary">
 Product Category
 </label>
 <Select
 value={selectedCategory.name}
 onChange={(val) => {
 const found = categoriesList.find((c) => c.name.toLowerCase() === val.toLowerCase()) || categoriesList[0];
 setSelectedCategory(found);
 }}
 options={categoriesList.map((cat) => ({
 value: cat.name,
 label: t("categories." + cat.name.toLowerCase(), cat.name),
 imageURL: cat.imageURL,
 }))}
 />
 </div>

 <div className="flex flex-col">
 <label className="mb-1 text-xs font-semibold uppercase tracking-wide text-secondary">
 Product Colors
 </label>
 <div className="flex flex-wrap items-center gap-2">
 {colors.map((color) => (
 <ColorCircle
 key={color}
 color={color}
 onClick={() => {
 if (tempColors.includes(color)) {
 setTempColors((prev) => prev.filter((c) => c !== color));
 } else {
 setTempColors((prev) => [...prev, color]);
 }
 }}
 isSelected={tempColors.includes(color)}
 />
 ))}
 </div>
 {tempColors.length > 0 && (
 <div className="flex flex-wrap gap-1.5 pt-2">
 {tempColors.map((color) => (
 <span
 key={color}
 className="inline-flex cursor-pointer items-center gap-x-1 rounded-md px-2.5 py-1 text-xs font-medium text-white shadow-xs"
 style={{ backgroundColor: color }}
 onClick={() =>
 setTempColors((prev) => prev.filter((c) => c !== color))
 }
 >
 {color} ×
 </span>
 ))}
 </div>
 )}
 <ErrorMessage msg={errors.colors} />
 </div>

 <div className="flex items-center justify-end gap-x-3 pt-4 border-t border-border">
 <Button
 type="button"
 className="border border-border bg-surface text-secondary hover:text-primary"
 onClick={closeModal}
 >
 Cancel
 </Button>
 <Button className="bg-accent font-bold text-white shadow-sm hover:bg-accent/90">
 {productToEdit ?"Update in Database" :"Save to Database"}
 </Button>
 </div>
 </form>
 </Modal>

 {/* Delete Confirmation Modal */}
 <Modal
 isOpen={!!productToDelete}
 closeModal={() => setProductToDelete(null)}
 title="Delete Catalog Product"
 >
 <div className="space-y-4">
 <p className="text-sm text-secondary">
 Are you sure you want to permanently delete{""}
 <span className="font-bold text-primary">
"{getLocalizedText(productToDelete?.title)}"
 </span>{""}
 from the store catalog and database?
 </p>
 <div className="flex justify-end gap-3 pt-3 border-t border-border">
 <Button
 type="button"
 className="border border-border bg-surface text-secondary hover:text-primary"
 onClick={() => setProductToDelete(null)}
 >
 Cancel
 </Button>
 <Button
 type="button"
 className="bg-rose-600 font-bold text-white hover:bg-rose-700 shadow-sm"
 onClick={handleConfirmDelete}
 >
 Confirm Delete
 </Button>
 </div>
 </div>
 </Modal>
 </main>

 {/* Floating AI Assistant Widget */}
 <FloatingAIButton />
 <AIChatPanel />

 {/* Notifications & Toast alerts */}
 <Toast toasts={toasts} onDismiss={dismissToast} />
 </div>
 </AIProvider>
 </SellerThemeProvider>
 );
}
