import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import RootLayout from './layouts/RootLayout';
import { CartProvider } from './context/CartContext';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { LocaleProvider } from './i18n/LocaleContext';
import ProtectedRoute from './components/ProtectedRoute';
import ScrollToTop from './components/ScrollToTop';
import CookieConsent from './components/CookieConsent';
import { ErrorBoundary } from './components/ErrorBoundary';
import { GOOGLE_OAUTH_CLIENT_ID, HAS_GOOGLE_OAUTH } from './lib/googleAuth';

const Home = lazy(() => import('./pages/Home'));
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const Products = lazy(() => import('./pages/Products'));
const Cart = lazy(() => import('./pages/Cart'));
const ProductDetails = lazy(() => import('./pages/ProductDetails'));
const Checkout = lazy(() => import('./pages/Checkout'));
const DashboardLayout = lazy(() => import('./layouts/DashboardLayout'));
const DashboardHome = lazy(() => import('./pages/DashboardHome'));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));
const CRMPage = lazy(() => import('./pages/CRMPage'));
const OrdersPage = lazy(() => import('./pages/OrdersPage'));
const AdminUsersPage = lazy(() => import('./pages/AdminUsersPage'));
const StoreDetails = lazy(() => import('./pages/StoreDetails'));
const AiShopping = lazy(() => import('./pages/AiShopping'));
const PrivacyPolicy = lazy(() => import('./pages/PrivacyPolicy'));
const TermsOfService = lazy(() => import('./pages/TermsOfService'));

const SellerPortal = lazy(() => import('./seller/SellerPortal'));
const DocsPage = lazy(() => import('./seller/pages/support/DocsPage'));
const ApiPage = lazy(() => import('./seller/pages/support/ApiPage'));
const HelpPage = lazy(() => import('./seller/pages/support/HelpPage'));
const CookiesPage = lazy(() => import('./seller/pages/legal/CookiesPage'));

const AgentStudioHome = lazy(() => import('./pages/agents/AgentStudioHome'));
const AgentMarketplace = lazy(() => import('./pages/agents/AgentMarketplace'));
const AgentBuilder = lazy(() => import('./pages/agents/AgentBuilder'));
const AgentDetails = lazy(() => import('./pages/agents/AgentDetails'));
const AgentConfigurationPage = lazy(() => import('./pages/agents/AgentConfigurationPage'));
const AgentExecutionsPage = lazy(() => import('./pages/agents/AgentExecutionsPage'));
const AgentAuditPage = lazy(() => import('./pages/agents/AgentAuditPage'));
const RefundSpikeAnalyzerPage = lazy(() => import('./pages/agents/RefundSpikeAnalyzerPage'));



function RouteFallback() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="animate-pulse space-y-4">
        <div className="h-8 w-48 rounded bg-muted" />
        <div className="h-40 rounded-lg bg-muted" />
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[1, 2, 3, 4].map((item) => (
            <div key={item} className="h-48 rounded-lg bg-muted" />
          ))}
        </div>
      </div>
    </div>
  );
}

function App() {
  const app = (
    <LocaleProvider>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <CartProvider>
              <ScrollToTop />
              <CookieConsent />
              <Suspense fallback={<RouteFallback />}>
                <ErrorBoundary>
                  <Routes>
                    <Route path="/" element={<RootLayout />}>
                      <Route index element={<Home />} />
                      <Route path="login" element={<Login />} />
                      <Route path="register" element={<Register />} />
                      <Route path="products" element={<Products />} />
                      <Route path="product/:slug" element={<ProductDetails />} />
                      <Route path="store/:slug" element={<StoreDetails />} />
                      <Route path="ai" element={<AiShopping />} />
                      <Route path="cart" element={<Cart />} />
                      <Route path="checkout" element={<Checkout />} />
                      <Route path="privacy" element={<PrivacyPolicy />} />
                      <Route path="terms" element={<TermsOfService />} />
                      <Route path="docs" element={<DocsPage />} />
                      <Route path="documentation" element={<DocsPage />} />
                      <Route path="api-reference" element={<ApiPage />} />
                      <Route path="help-center" element={<HelpPage />} />
                      <Route path="cookie-policy" element={<CookiesPage />} />
                      <Route path="cookies" element={<CookiesPage />} />
                    </Route>

                    {/* Customer Dashboard */}
                    <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
                      <Route path="/dashboard" element={<DashboardHome />} />
                      <Route path="/dashboard/orders" element={<OrdersPage mode="customer" />} />
                      <Route path="/dashboard/tickets" element={<CRMPage />} />
                    </Route>

                    {/* Full Seller Suite */}
                    <Route
                      path="/seller/*"
                      element={
                        <ProtectedRoute roles={['seller', 'admin']}>
                          <SellerPortal />
                        </ProtectedRoute>
                      }
                    />

                    {/* Agent Studio Suite */}
                    <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
                      <Route path="/agents" element={<AgentStudioHome />} />
                      <Route path="/agents/marketplace" element={<AgentMarketplace />} />
                      <Route path="/agents/create" element={<AgentBuilder />} />
                      <Route path="/agents/refund-spike-analyzer" element={<RefundSpikeAnalyzerPage />} />
                      <Route path="/agents/:id" element={<AgentDetails />} />
                      <Route path="/agents/:id/configuration" element={<AgentConfigurationPage />} />
                      <Route path="/agents/:id/executions" element={<AgentExecutionsPage />} />
                      <Route path="/agents/:id/audit" element={<AgentAuditPage />} />
                    </Route>


                    {/* Admin Portal */}
                    <Route element={<ProtectedRoute roles={['admin']}><DashboardLayout /></ProtectedRoute>}>

                      <Route path="/admin" element={<AdminDashboard />} />
                      <Route path="/admin/users" element={<AdminUsersPage />} />
                      <Route path="/admin/orders" element={<OrdersPage mode="admin" />} />
                      <Route path="/admin/crm" element={<CRMPage />} />
                      <Route path="/admin/settings" element={<AdminDashboard />} />
                    </Route>
                  </Routes>
                </ErrorBoundary>
              </Suspense>
            </CartProvider>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </LocaleProvider>
  );

  return (
    <GoogleOAuthProvider clientId={GOOGLE_OAUTH_CLIENT_ID}>
      {app}
    </GoogleOAuthProvider>
  );
}

export default App;
