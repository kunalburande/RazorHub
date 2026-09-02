import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Banknote,
  CreditCard,
  MapPin,
  Search,
  ShieldCheck,
  Zap,
  X,
  Smartphone,
  Building2,
} from 'lucide-react';
import { useCart } from '../context/CartContext';
import { formatPrice, price, productImage } from '../lib/products';
import { useAuth } from '../context/AuthContext';
import { apiRequest } from '../lib/api';
import {
  getCitySuggestions,
  promoCodes,
  resolvePromoCode,
} from '../lib/checkout';
import { useTranslation } from '../i18n/LocaleContext';

declare global {
  interface Window {
    Razorpay?: any;
  }
}

type PaymentMethodId = 'razorpay' | 'cod';

interface DeliveryCalculationResponse {
  total_fee?: string | number;
  delivery_fee?: string | number;
  estimated_time?: string;
  item_deliveries?: Record<string, { fee: string; eta: string }>;
}

export default function Checkout() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { items, totalPrice, clearCart } = useCart();
  const { token, user } = useAuth();
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethodId>('razorpay');
  const [deliveryEta, setDeliveryEta] = useState('2-4 days');
  const [deliveryFee, setDeliveryFee] = useState(50);
  const [isCalculatingDelivery, setIsCalculatingDelivery] = useState(false);
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);
  const [showRazorpayModal, setShowRazorpayModal] = useState(false);
  const [testMethodChoice, setTestMethodChoice] = useState<'upi' | 'card' | 'netbanking'>('upi');
  const [placed, setPlaced] = useState(false);
  const [error, setError] = useState('');
  const [promoCodeInput, setPromoCodeInput] = useState('');
  const [appliedPromoCode, setAppliedPromoCode] = useState('');
  const [promoMessage, setPromoMessage] = useState('');
  const [addressQuery, setAddressQuery] = useState('');
  const [addressDetail, setAddressDetail] = useState('');
  const [customerNote, setCustomerNote] = useState('');
  const [showAddressSuggestions, setShowAddressSuggestions] = useState(false);
  const [isLocating, setIsLocating] = useState(false);
  const [focusedSuggestionIndex, setFocusedSuggestionIndex] = useState(-1);
  const hasAutoLocated = useRef(false);
  const addressInputRef = useRef<HTMLInputElement>(null);
  const houseDetailRef = useRef<HTMLTextAreaElement>(null);
  const instructionsRef = useRef<HTMLTextAreaElement>(null);
  const promoCodeRef = useRef<HTMLInputElement>(null);

  const paymentMethods = useMemo(
    () => [
      {
        id: 'razorpay' as PaymentMethodId,
        label: t('checkout.paymentRazorpayLabel', { defaultValue: 'Razorpay (Test Mode)' }),
        description: t('checkout.paymentRazorpayDescription', {
          defaultValue: 'Pay with UPI, Credit/Debit Cards, NetBanking, Wallets',
        }),
        badge: 'Recommended',
        icon: CreditCard,
      },
      {
        id: 'cod' as PaymentMethodId,
        label: t('checkout.paymentCodLabel', { defaultValue: 'Cash on Delivery (COD)' }),
        description: t('checkout.paymentCodDescription', { defaultValue: 'Pay with cash upon delivery' }),
        badge: 'Cash',
        icon: Banknote,
      },
    ],
    [t]
  );

  const addressSuggestions = useMemo(() => getCitySuggestions(addressQuery), [addressQuery]);

  useEffect(() => {
    if (addressQuery.trim()) {
      setShowAddressSuggestions(true);
    }
  }, [addressQuery]);

  useEffect(() => {
    setFocusedSuggestionIndex(-1);
  }, [addressSuggestions]);

  // Autofill address on initial mount
  useEffect(() => {
    if (hasAutoLocated.current) return;
    hasAutoLocated.current = true;

    if (!addressQuery.trim()) {
      setAddressQuery('Indiranagar');
      setAddressDetail('100 Feet Road, Bengaluru');
    }
  }, [addressQuery]);

  // Delivery calculation debounce
  useEffect(() => {
    if (!addressQuery.trim() || items.length === 0) {
      setDeliveryFee(50);
      setDeliveryEta('2-4 days');
      return;
    }

    setIsCalculatingDelivery(true);
    const timer = setTimeout(async () => {
      try {
        const response = await apiRequest<DeliveryCalculationResponse>('/orders/calculate_delivery/', {
          method: 'POST',
          body: JSON.stringify({
            shipping_address: [addressQuery.trim(), addressDetail.trim()].filter(Boolean).join(', '),
            items: items.map(({ product, quantity }) => ({ product_id: product.id, quantity })),
          }),
        });

        const parsedFee = Number(response.total_fee ?? response.delivery_fee ?? 50);
        setDeliveryFee(Number.isFinite(parsedFee) ? parsedFee : 50);

        if (response.item_deliveries) {
          const uniqueEtas = Array.from(new Set(Object.values(response.item_deliveries).map((d) => d.eta)));
          setDeliveryEta(uniqueEtas.join(', '));
        } else {
          setDeliveryEta(response.estimated_time || '2-4 days');
        }
      } catch (err) {
        console.error('Failed to calculate delivery fee:', err);
      } finally {
        setIsCalculatingDelivery(false);
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [addressQuery, addressDetail, items]);

  const deliveryAddress = [addressQuery.trim(), addressDetail.trim()].filter(Boolean).join(', ');
  const shipping = deliveryFee;
  const promoRate = appliedPromoCode ? promoCodes[appliedPromoCode as keyof typeof promoCodes] || 0 : 0;
  const discountAmount = Math.round((totalPrice * promoRate) / 100);
  const total = Math.max(totalPrice + shipping - discountAmount, 0);

  async function handleGetCurrentLocation() {
    if (!('geolocation' in navigator)) {
      setError('Geolocation is not supported by your browser');
      return;
    }

    setIsLocating(true);
    setError('');
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`
          );
          if (res.ok) {
            const data = await res.json();
            const address = data.address || {};
            const area =
              address.suburb ||
              address.neighbourhood ||
              address.city_district ||
              address.city ||
              address.town ||
              address.state ||
              'Delhi';
            const detail = [address.road, address.house_number].filter(Boolean).join(', ') || data.display_name;

            setAddressQuery(area);
            setAddressDetail(detail);
            setShowAddressSuggestions(false);
            houseDetailRef.current?.focus();
          } else {
            setError('Could not fetch address for your location');
          }
        } catch (err) {
          console.error(err);
          setError('Failed to reverse geocode location');
        } finally {
          setIsLocating(false);
        }
      },
      (geoError) => {
        setIsLocating(false);
        if (geoError.code === geoError.PERMISSION_DENIED) {
          setError('Location permission denied. Please enter your address manually.');
        } else {
          setError('Unable to retrieve your location');
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  }

  function applyPromoCode(code = promoCodeInput) {
    const next = resolvePromoCode(code);
    if (!next.code) {
      setAppliedPromoCode('');
      setPromoMessage('');
      return;
    }

    if (!next.valid) {
      setAppliedPromoCode('');
      setPromoMessage(t('checkout.promoInvalid', { defaultValue: 'Promo code is not valid.' }));
      return;
    }

    setAppliedPromoCode(next.code);
    setPromoCodeInput(next.code);
    setPromoMessage(t('checkout.promoApplied', { defaultValue: 'Promo code applied.' }));
  }

  function removePromoCode() {
    setPromoCodeInput('');
    setAppliedPromoCode('');
    setPromoMessage('');
  }

  async function submitOrderPayload(providerReference?: string, paymentStatus: 'paid' | 'failed' | 'pending' = 'paid') {
    await apiRequest('/orders/', {
      token,
      method: 'POST',
      body: JSON.stringify({
        payment_method: paymentMethod,
        provider_reference: providerReference || '',
        payment_status: paymentStatus,
        promo_code: appliedPromoCode,
        shipping_address: deliveryAddress,
        customer_note: customerNote.trim(),
        items: items.map(({ product, quantity }) => ({ product_id: product.id, quantity })),
      }),
    });

    if (paymentStatus === 'paid' || (paymentMethod === 'cod' && paymentStatus !== 'failed')) {
      setPlaced(true);
      clearCart();
      window.setTimeout(() => navigate('/dashboard/orders'), 1800);
    }
  }

  function openOfficialRazorpay(keyId: string) {
    if (typeof window.Razorpay !== 'function') {
      // If SDK not loaded, use test simulator modal
      setShowRazorpayModal(true);
      return;
    }

    const options = {
      key: keyId,
      amount: Math.round(total * 100), // in paise
      currency: 'INR',
      name: 'RazorHub',
      description: 'Order Payment (Test Mode)',
      image: '/favicon.png',
      prefill: {
        name: [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.username || user?.email || '',
        email: user?.email || '',
        contact: user?.phone || '9999999999',
      },
      theme: {
        color: '#0b66c2',
      },
      handler: async function (response: any) {
        try {
          const paymentId = response.razorpay_payment_id || `rzp_test_${Date.now()}`;
          await submitOrderPayload(paymentId, 'paid');
        } catch (err) {
          console.error(err);
          setError('Failed to record completed payment.');
        } finally {
          setIsProcessingPayment(false);
        }
      },
      modal: {
        ondismiss: function () {
          setIsProcessingPayment(false);
          setError('Payment window was closed.');
        },
      },
    };

    try {
      const rzpInstance = new window.Razorpay(options);
      rzpInstance.on('payment.failed', async function (response: any) {
        setIsProcessingPayment(false);
        const failRef = response.error?.metadata?.payment_id || `pay_failed_${Date.now()}`;
        try {
          await submitOrderPayload(failRef, 'failed');
        } catch (_) {}
        setError(`Payment failed: ${response.error?.description || 'Transaction declined'} (Recorded in database)`);
      });
      rzpInstance.open();
    } catch (rzpErr) {
      console.error(rzpErr);
      setShowRazorpayModal(true);
    }
  }

  async function handlePlaceOrder() {
    if (!user || !token) {
      navigate('/login', { state: { from: '/checkout' } });
      return;
    }

    if (!addressQuery.trim()) {
      setError(t('checkout.selectAreaFirst', { defaultValue: 'Please enter or select a delivery area/city first.' }));
      return;
    }

    setError('');

    if (paymentMethod === 'razorpay') {
      const envKey = (import.meta.env.VITE_RAZORPAY_KEY_ID || '').trim();
      // If a real Razorpay test key is provided in .env, launch official Razorpay
      if (envKey.startsWith('rzp_test_') && envKey.length > 15 && !envKey.includes('placeholder') && !envKey.includes('51gB6g7NqK9K7K')) {
        setIsProcessingPayment(true);
        openOfficialRazorpay(envKey);
      } else {
        // Open the Razorpay Test Simulator Modal
        setShowRazorpayModal(true);
      }
    } else {
      // Cash on Delivery
      try {
        setIsProcessingPayment(true);
        await submitOrderPayload('', 'pending');
      } catch (err) {
        setError(t('checkout.couldNotPlaceOrder', { defaultValue: 'Could not place order' }));
      } finally {
        setIsProcessingPayment(false);
      }
    }
  }

  async function handleSimulatedPaymentSuccess() {
    setIsProcessingPayment(true);
    setShowRazorpayModal(false);
    try {
      const prefix = testMethodChoice === 'upi' ? 'pay_upi_test_' : testMethodChoice === 'card' ? 'pay_card_test_' : 'pay_nb_test_';
      const fakePaymentId = `${prefix}${Math.random().toString(36).substring(2, 10)}${Date.now().toString(36)}`;
      await submitOrderPayload(fakePaymentId, 'paid');
    } catch (err) {
      setError('Could not place order with simulated payment.');
    } finally {
      setIsProcessingPayment(false);
    }
  }

  async function handleSimulatedPaymentFailure() {
    setIsProcessingPayment(true);
    setShowRazorpayModal(false);
    try {
      const fakeFailedId = `pay_failed_${Date.now().toString(36)}`;
      await submitOrderPayload(fakeFailedId, 'failed');
      setError('Payment was declined in test sandbox and recorded in database.');
    } catch (err) {
      setError('Could not record failed transaction in database.');
    } finally {
      setIsProcessingPayment(false);
    }
  }

  if (items.length === 0 && !placed) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-24 text-center">
        <h1 className="text-3xl font-black tracking-tight">{t('checkout.title', { defaultValue: 'Checkout' })}</h1>
        <p className="mt-3 text-secondary">{t('cart.emptyTitle', { defaultValue: 'Your cart is empty.' })}</p>
        <Link to="/products" className="mt-6 inline-flex rounded-md bg-accent px-5 py-3 font-semibold text-background">
          {t('cart.browseCatalog', { defaultValue: 'Browse products' })}
        </Link>
      </div>
    );
  }

  if (placed) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-24 text-center">
        <CheckCircle2 className="mx-auto h-16 w-16 text-green-500 animate-bounce" />
        <h1 className="mt-6 text-3xl font-black tracking-tight">
          {t('checkout.orderPlacedTitle', { defaultValue: 'Order placed successfully!' })}
        </h1>
        <p className="mt-3 text-secondary">
          {t('checkout.paymentMethodLabel', { defaultValue: 'Payment method:' })}{' '}
          <span className="font-semibold text-primary">
            {paymentMethod === 'razorpay' ? 'Razorpay (Test Mode)' : 'Cash on Delivery'}
          </span>
        </p>
        <p className="mt-2 text-sm text-secondary">
          {t('checkout.orderPlacedCopy', { defaultValue: 'You will be redirected to your order history.' })}
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1360px] w-full px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <Link
        to="/cart"
        className="mb-5 inline-flex items-center gap-2 text-sm font-semibold text-secondary hover:text-primary transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        {t('checkout.backToCart', { defaultValue: 'Back to cart' })}
      </Link>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_400px]">
        {/* Left Column: Form Steps */}
        <section className="space-y-6">
          <div className="rounded-xl border border-border bg-surface p-5 shadow-sm sm:p-6">
            <h1 className="text-2xl font-black tracking-tight sm:text-3xl">
              {t('checkout.title', { defaultValue: 'Checkout' })}
            </h1>
            <p className="mt-1 text-sm text-secondary">
              {t('checkout.copy', { defaultValue: 'Delivery, payment, and order review.' })}
            </p>
          </div>

          {/* 1. Delivery Address */}
          <div className="rounded-xl border border-border bg-surface p-5 shadow-sm sm:p-6">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MapPin className="h-5 w-5 text-accent" />
                <h2 className="text-lg font-bold">{t('checkout.deliveryAddress', { defaultValue: 'Delivery Address' })}</h2>
              </div>
              <button
                type="button"
                onClick={handleGetCurrentLocation}
                disabled={isLocating}
                className="text-xs font-semibold text-accent hover:underline disabled:opacity-50"
              >
                {isLocating ? 'Locating...' : 'Use Current Location'}
              </button>
            </div>

            <div className="space-y-4">
              <div className="relative">
                <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-secondary">
                  {t('checkout.searchArea', { defaultValue: 'City / Area' })}
                </label>
                <div className="relative">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-secondary" />
                  <input
                    ref={addressInputRef}
                    value={addressQuery}
                    onChange={(e) => {
                      setAddressQuery(e.target.value);
                      setShowAddressSuggestions(true);
                    }}
                    onFocus={() => setShowAddressSuggestions(true)}
                    onBlur={() => setTimeout(() => setShowAddressSuggestions(false), 200)}
                    placeholder={t('checkout.searchHint', { defaultValue: 'Type Delhi, Mumbai, Bengaluru, Hyderabad...' })}
                    className="w-full rounded-lg border border-border bg-background py-2.5 pl-9 pr-3 text-sm text-primary focus:border-accent focus:outline-none"
                  />
                </div>

                {showAddressSuggestions && addressSuggestions.length > 0 && (
                  <div className="absolute z-20 mt-1 max-h-56 w-full overflow-y-auto rounded-lg border border-border bg-surface py-1 shadow-lg">
                    {addressSuggestions.map((item: any, idx: number) => (
                      <button
                        key={`${item.city}-${item.label}`}
                        type="button"
                        className={`w-full px-4 py-2 text-left text-sm hover:bg-muted transition-colors ${
                          idx === focusedSuggestionIndex ? 'bg-muted' : ''
                        }`}
                        onMouseDown={() => {
                          setAddressQuery(`${item.label}, ${item.city}`);
                          setShowAddressSuggestions(false);
                          houseDetailRef.current?.focus();
                        }}
                      >
                        <span className="font-semibold text-primary">{item.label}</span>
                        <span className="ml-2 text-xs text-secondary">{item.city}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-secondary">
                  {t('checkout.houseLabel', { defaultValue: 'House / Flat / Street / Landmark' })}
                </label>
                <textarea
                  ref={houseDetailRef}
                  value={addressDetail}
                  onChange={(e) => setAddressDetail(e.target.value)}
                  placeholder={t('checkout.housePlaceholder', { defaultValue: 'Flat/House number, building name, street, landmark' })}
                  rows={2}
                  className="w-full rounded-lg border border-border bg-background p-3 text-sm text-primary focus:border-accent focus:outline-none"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-secondary">
                  {t('checkout.instructionsLabel', { defaultValue: 'Delivery Instructions (Optional)' })}
                </label>
                <textarea
                  ref={instructionsRef}
                  value={customerNote}
                  onChange={(e) => setCustomerNote(e.target.value)}
                  placeholder={t('checkout.instructionsPlaceholder', { defaultValue: 'Call on arrival, leave at reception, gate code, etc.' })}
                  rows={2}
                  className="w-full rounded-lg border border-border bg-background p-3 text-sm text-primary focus:border-accent focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* 2. Payment Method */}
          <div className="rounded-xl border border-border bg-surface p-5 shadow-sm sm:p-6">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-accent" />
                <h2 className="text-lg font-bold">{t('checkout.paymentMethod', { defaultValue: 'Payment Method' })}</h2>
              </div>
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                <Zap className="h-3.5 w-3.5" /> Razorpay Test Gateway
              </span>
            </div>

            <div className="space-y-3">
              {paymentMethods.map((method) => {
                const IconComponent = method.icon;
                const isSelected = paymentMethod === method.id;
                return (
                  <button
                    key={method.id}
                    type="button"
                    onClick={() => setPaymentMethod(method.id)}
                    className={`flex w-full items-start justify-between rounded-xl border p-4 text-left transition-all ${
                      isSelected
                        ? 'border-accent bg-accent/5 ring-1 ring-accent'
                        : 'border-border bg-background hover:border-border-hover'
                    }`}
                  >
                    <div className="flex items-start gap-3.5">
                      <div className={`mt-0.5 rounded-lg p-2 ${isSelected ? 'bg-accent text-background' : 'bg-muted text-secondary'}`}>
                        <IconComponent className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-primary">{method.label}</span>
                          {method.badge && (
                            <span className="rounded-md bg-accent/15 px-2 py-0.5 text-[10px] font-bold text-accent">
                              {method.badge}
                            </span>
                          )}
                        </div>
                        <p className="mt-1 text-xs text-secondary">{method.description}</p>
                      </div>
                    </div>
                    <div className="mt-1 flex h-5 w-5 items-center justify-center rounded-full border border-border">
                      {isSelected && <div className="h-2.5 w-2.5 rounded-full bg-accent" />}
                    </div>
                  </button>
                );
              })}
            </div>

            {paymentMethod === 'razorpay' && (
              <div className="mt-4 rounded-xl border border-accent/20 bg-accent/5 p-4 text-xs text-secondary space-y-1.5">
                <div className="flex items-center gap-2 text-primary font-bold">
                  <Zap className="h-4 w-4 text-accent" />
                  <span>Razorpay Payment Gateway</span>
                </div>
                <p>
                  Pay securely with UPI, Credit/Debit Cards, NetBanking, or Wallets.
                </p>
              </div>
            )}
          </div>
        </section>

        {/* Right Column: Order Summary */}
        <aside className="space-y-6">
          <div className="rounded-xl border border-border bg-surface p-5 shadow-sm sm:p-6">
            <h2 className="text-lg font-bold">{t('checkout.orderSummary', { defaultValue: 'Order Summary' })}</h2>

            <div className="mt-4 divide-y divide-border">
              {items.map(({ product, quantity }) => (
                <div key={product.id} className="flex items-center gap-3 py-3">
                  <img
                    src={productImage(product) || '/placeholder.png'}
                    alt={product.name}
                    className="h-12 w-12 rounded-md object-cover"
                  />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-primary">{product.name}</p>
                    <p className="text-xs text-secondary">
                      {quantity} × {formatPrice(price(product))}
                    </p>
                  </div>
                  <span className="text-sm font-bold">{formatPrice(price(product) * quantity)}</span>
                </div>
              ))}
            </div>

            {/* Promo code */}
            <div className="mt-4 border-t border-border pt-4">
              <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-secondary">
                {t('checkout.promoCode', { defaultValue: 'Promo Code' })}
              </label>
              <div className="flex gap-2">
                <input
                  ref={promoCodeRef}
                  value={promoCodeInput}
                  onChange={(e) => setPromoCodeInput(e.target.value)}
                  placeholder={t('checkout.promoPlaceholder', { defaultValue: 'e.g. AURA10' })}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm uppercase text-primary focus:border-accent focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => applyPromoCode()}
                  className="rounded-lg bg-muted px-4 py-2 text-xs font-bold text-primary hover:bg-border transition-colors"
                >
                  {t('checkout.apply', { defaultValue: 'Apply' })}
                </button>
              </div>
              {appliedPromoCode && (
                <div className="mt-2 flex items-center justify-between text-xs text-green-500">
                  <span>Code {appliedPromoCode.toUpperCase()} applied ({promoRate}% OFF)</span>
                  <button type="button" onClick={removePromoCode} className="text-red-400 hover:underline">
                    Remove
                  </button>
                </div>
              )}
              {promoMessage && !appliedPromoCode && (
                <p className="mt-1 text-xs text-red-400">{promoMessage}</p>
              )}
            </div>

            {/* Cost Breakdown */}
            <div className="mt-4 space-y-2 border-t border-border pt-4 text-sm">
              <div className="flex justify-between text-secondary">
                <span>{t('checkout.subtotal', { defaultValue: 'Subtotal' })}</span>
                <span className="font-semibold text-primary">{formatPrice(totalPrice)}</span>
              </div>
              <div className="flex justify-between text-secondary">
                <span>
                  {t('checkout.delivery', { defaultValue: 'Delivery Fee' })}
                  {deliveryEta ? ` (${deliveryEta})` : ''}
                </span>
                <span className="font-semibold text-primary">
                  {isCalculatingDelivery ? 'Calculating...' : formatPrice(shipping)}
                </span>
              </div>
              {discountAmount > 0 && (
                <div className="flex justify-between text-emerald-500">
                  <span>{t('checkout.promoDiscount', { defaultValue: 'Promo Discount' })}</span>
                  <span className="font-semibold">-{formatPrice(discountAmount)}</span>
                </div>
              )}
              <div className="flex justify-between border-t border-border pt-3 text-base font-black text-primary">
                <span>{t('checkout.total', { defaultValue: 'Total' })}</span>
                <span className="text-accent">{formatPrice(total)}</span>
              </div>
            </div>

            {error && <p className="mt-4 text-xs font-semibold text-red-500">{error}</p>}

            <button
              type="button"
              onClick={handlePlaceOrder}
              disabled={isProcessingPayment || items.length === 0}
              className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-accent py-3.5 text-sm font-bold text-white shadow-md hover:opacity-95 active:scale-[0.99] transition-all disabled:opacity-50"
            >
              {isProcessingPayment ? (
                'Processing...'
              ) : (
                <>
                  <span>
                    {paymentMethod === 'razorpay' ? `Pay ${formatPrice(total)} with Razorpay` : `Place COD Order (${formatPrice(total)})`}
                  </span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
        </aside>
      </div>

      {/* Razorpay Test Modal Overlay */}
      {showRazorpayModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="relative w-full max-w-md rounded-2xl border border-border bg-surface p-6 shadow-2xl">
            <button
              type="button"
              onClick={() => {
                setShowRazorpayModal(false);
                setIsProcessingPayment(false);
              }}
              className="absolute right-4 top-4 rounded-lg p-1.5 text-secondary hover:bg-muted hover:text-primary transition-colors"
            >
              <X className="h-5 w-5" />
            </button>

            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#0C2340] text-white font-black text-lg">
                <span className="text-[#3395FF]">R</span>
              </div>
              <div>
                <h3 className="text-lg font-black tracking-tight text-primary">Razorpay Checkout</h3>
                <span className="inline-block rounded bg-amber-500/10 px-2 py-0.5 text-[11px] font-bold text-amber-600 dark:text-amber-400">
                  Sandbox Test Mode
                </span>
              </div>
            </div>

            <div className="mt-5 rounded-xl border border-border bg-muted/40 p-4 text-center">
              <span className="text-xs uppercase tracking-wider text-secondary">Payable Amount</span>
              <p className="mt-1 text-3xl font-black text-primary">{formatPrice(total)}</p>
            </div>

            <div className="mt-5 space-y-3">
              <p className="text-xs font-bold uppercase tracking-wider text-secondary">Select Test Payment Method</p>

              <button
                type="button"
                onClick={() => setTestMethodChoice('upi')}
                className={`flex w-full items-center justify-between rounded-xl border p-3.5 text-left transition-all ${
                  testMethodChoice === 'upi'
                    ? 'border-accent bg-accent/5 ring-1 ring-accent'
                    : 'border-border bg-background hover:bg-muted/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Smartphone className="h-5 w-5 text-accent" />
                  <div>
                    <p className="text-sm font-bold text-primary">UPI (Google Pay / PhonePe / Paytm)</p>
                    <p className="text-xs text-secondary">Test VPA: success@razorpay</p>
                  </div>
                </div>
                <div className="flex h-4 w-4 items-center justify-center rounded-full border border-border">
                  {testMethodChoice === 'upi' && <div className="h-2 w-2 rounded-full bg-accent" />}
                </div>
              </button>

              <button
                type="button"
                onClick={() => setTestMethodChoice('card')}
                className={`flex w-full items-center justify-between rounded-xl border p-3.5 text-left transition-all ${
                  testMethodChoice === 'card'
                    ? 'border-accent bg-accent/5 ring-1 ring-accent'
                    : 'border-border bg-background hover:bg-muted/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <CreditCard className="h-5 w-5 text-accent" />
                  <div>
                    <p className="text-sm font-bold text-primary">Credit / Debit Card</p>
                    <p className="text-xs text-secondary">Test Card: 4111 •••• •••• 4444</p>
                  </div>
                </div>
                <div className="flex h-4 w-4 items-center justify-center rounded-full border border-border">
                  {testMethodChoice === 'card' && <div className="h-2 w-2 rounded-full bg-accent" />}
                </div>
              </button>

              <button
                type="button"
                onClick={() => setTestMethodChoice('netbanking')}
                className={`flex w-full items-center justify-between rounded-xl border p-3.5 text-left transition-all ${
                  testMethodChoice === 'netbanking'
                    ? 'border-accent bg-accent/5 ring-1 ring-accent'
                    : 'border-border bg-background hover:bg-muted/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Building2 className="h-5 w-5 text-accent" />
                  <div>
                    <p className="text-sm font-bold text-primary">Net Banking</p>
                    <p className="text-xs text-secondary">HDFC / ICICI / SBI / Axis</p>
                  </div>
                </div>
                <div className="flex h-4 w-4 items-center justify-center rounded-full border border-border">
                  {testMethodChoice === 'netbanking' && <div className="h-2 w-2 rounded-full bg-accent" />}
                </div>
              </button>
            </div>

            <div className="mt-6 flex flex-col gap-2">
              <button
                type="button"
                onClick={handleSimulatedPaymentSuccess}
                disabled={isProcessingPayment}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-600 py-3 text-sm font-bold text-white shadow hover:bg-emerald-700 transition-colors disabled:opacity-50"
              >
                <CheckCircle2 className="h-4 w-4" />
                <span>Simulate Successful Payment ({formatPrice(total)})</span>
              </button>

              <button
                type="button"
                onClick={handleSimulatedPaymentFailure}
                disabled={isProcessingPayment}
                className="w-full rounded-xl border border-red-500/20 py-2.5 text-xs font-semibold text-red-500 hover:bg-red-500/10 transition-colors disabled:opacity-50"
              >
                Simulate Payment Failure (Record Failed Txn)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
