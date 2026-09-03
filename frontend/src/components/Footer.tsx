import { useTranslation } from '../i18n/LocaleContext';
import { Mail, MapPin, BookOpen, HelpCircle, Shield, FileText, Bot, Building2, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import BrandLogo from './BrandLogo';

export default function Footer() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const accountLink = user ? '/dashboard' : '/login';
  const accountLabel = user ? t('footer.account', { defaultValue: 'Dashboard' }) : t('footer.login', { defaultValue: 'Login' });
  const secondaryAccountLink = user ? '/dashboard/orders' : '/register';
  const secondaryAccountLabel = user ? t('footer.orders', { defaultValue: 'Orders' }) : t('footer.register', { defaultValue: 'Register' });

  return (
    <footer className="mt-16 border-t border-border bg-surface text-primary transition-colors">
      <div className="mx-auto max-w-[1360px] w-full px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-5">
          
          {/* Col 1: Brand & Bio */}
          <div className="space-y-4 sm:col-span-2 lg:col-span-1">
            <Link to="/" className="inline-block group">
              <BrandLogo size="lg" />
            </Link>
            <p className="text-xs sm:text-sm leading-relaxed text-secondary">
              Next-generation agentic commerce, autonomous corporate treasury, and verified storefront catalog.
            </p>
            <div className="pt-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Live Cloud Sync • NeonDB
              </span>
            </div>
          </div>

          {/* Col 2: Storefront & Shop */}
          <div>
            <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-primary">
              {t('footer.shopTitle', { defaultValue: 'Shop' })}
            </h3>
            <ul className="space-y-2 text-xs sm:text-sm text-secondary">
              <li><Link to="/products" className="hover:text-primary transition-colors">{t('footer.allProducts', { defaultValue: 'All Products' })}</Link></li>
              <li><Link to="/products?category=mobiles" className="hover:text-primary transition-colors">{t('footer.mobiles', { defaultValue: 'Mobiles & Tech' })}</Link></li>
              <li><Link to="/products?category=fashion" className="hover:text-primary transition-colors">{t('footer.fashion', { defaultValue: 'Fashion & Apparel' })}</Link></li>
              <li><Link to="/products?category=groceries" className="hover:text-primary transition-colors">{t('footer.groceries', { defaultValue: 'Groceries' })}</Link></li>
              <li><Link to="/products?sort=discount" className="hover:text-accent font-semibold transition-colors">🔥 Flash Deals</Link></li>
            </ul>
          </div>

          {/* Col 3: Platform & AI */}
          <div>
            <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-primary">
              Platform & AI
            </h3>
            <ul className="space-y-2 text-xs sm:text-sm text-secondary">
              <li>
                <Link to="/banking" className="hover:text-primary transition-colors flex items-center gap-1.5">
                  <Building2 className="h-3.5 w-3.5 text-indigo-500" />
                  <span>Business Banking</span>
                </Link>
              </li>
              <li>
                <Link to="/agents" className="hover:text-primary transition-colors flex items-center gap-1.5">
                  <Bot className="h-3.5 w-3.5 text-indigo-500" />
                  <span>Agent Studio</span>
                </Link>
              </li>
              <li>
                <Link to="/ai" className="hover:text-primary transition-colors flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                  <span>AI Shopping</span>
                </Link>
              </li>
              <li><Link to="/seller" className="hover:text-primary transition-colors">Seller Central</Link></li>
              <li><Link to="/cart" className="hover:text-primary transition-colors">{t('footer.cart', { defaultValue: 'My Cart' })}</Link></li>
              <li><Link to={accountLink} className="hover:text-primary transition-colors">{accountLabel}</Link></li>
            </ul>
          </div>

          {/* Col 4: Documentation & Resources */}
          <div>
            <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-primary">
              Documentation
            </h3>
            <ul className="space-y-2 text-xs sm:text-sm text-secondary">
              <li>
                <Link to="/docs" className="hover:text-accent font-semibold transition-colors flex items-center gap-1.5">
                  <BookOpen className="h-3.5 w-3.5 text-accent" />
                  <span>Documentation</span>
                </Link>
              </li>
              <li>
                <Link to="/api-reference" className="hover:text-primary transition-colors flex items-center gap-1.5">
                  <FileText className="h-3.5 w-3.5 text-secondary" />
                  <span>API Reference</span>
                </Link>
              </li>
              <li>
                <Link to="/help-center" className="hover:text-accent font-semibold transition-colors flex items-center gap-1.5">
                  <HelpCircle className="h-3.5 w-3.5 text-accent" />
                  <span>Help Center</span>
                </Link>
              </li>
              <li>
                <Link to="/privacy" className="hover:text-primary transition-colors flex items-center gap-1.5">
                  <Shield className="h-3.5 w-3.5 text-secondary" />
                  <span>{t('footer.privacyPolicy', { defaultValue: 'Privacy Policy' })}</span>
                </Link>
              </li>
              <li><Link to="/terms" className="hover:text-primary transition-colors">Terms of Service</Link></li>
              <li><Link to="/cookies" className="hover:text-primary transition-colors">Cookie Policy</Link></li>
            </ul>
          </div>

          {/* Col 5: Support & Contact */}
          <div>
            <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-primary">
              {t('footer.contactTitle', { defaultValue: 'Contact & Support' })}
            </h3>
            <ul className="space-y-2.5 text-xs sm:text-sm text-secondary">
              <li className="flex items-start gap-2">
                <MapPin className="h-4 w-4 text-accent shrink-0 mt-0.5" />
                <span>Bengaluru, Karnataka, India</span>
              </li>
              <li className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-accent shrink-0" />
                <a href="mailto:support@razorhub.in" className="hover:text-primary transition-colors">
                  support@razorhub.in
                </a>
              </li>
              <li className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-accent shrink-0" />
                <a href="mailto:razorhubofficial@gmail.com" className="hover:text-primary transition-colors truncate">
                  razorhubofficial@gmail.com
                </a>
              </li>
              <li className="pt-1">
                <Link
                  to="/help-center"
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-accent hover:underline"
                >
                  <HelpCircle className="h-3.5 w-3.5" />
                  <span>Visit 24/7 Help Center →</span>
                </Link>
              </li>
              {user && (
                <li>
                  <Link
                    to="/dashboard/tickets"
                    className="inline-flex items-center gap-1 text-xs font-semibold text-secondary hover:text-primary"
                  >
                    <span>View Support Tickets →</span>
                  </Link>
                </li>
              )}
            </ul>
          </div>

        </div>

        {/* Bottom Bar */}
        <div className="mt-12 flex flex-col sm:flex-row items-center justify-between border-t border-border pt-6 text-xs text-secondary gap-4">
          <span>&copy; {new Date().getFullYear()} RazorHub Commerce Technologies Inc. All rights reserved.</span>
          <div className="flex flex-wrap items-center gap-4">
            <Link to="/privacy" className="hover:text-primary transition-colors">{t('footer.privacyPolicy', { defaultValue: 'Privacy Policy' })}</Link>
            <span>•</span>
            <Link to="/terms" className="hover:text-primary transition-colors">Terms of Service</Link>
            <span>•</span>
            <Link to="/docs" className="hover:text-primary transition-colors">Docs</Link>
            <span>•</span>
            <Link to="/help-center" className="hover:text-primary transition-colors">Help Center</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}

