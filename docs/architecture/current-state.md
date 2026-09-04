# RazorHub — Current State Architecture

## 1. Technology Stack

| Layer | Technology | Version |
|---|---|---|
| **Backend Framework** | Django + Django REST Framework | Django 6.0, DRF 3.17 |
| **Frontend Framework** | React + TypeScript + Vite | React 19, Vite 8 |
| **Database** | SQLite (dev) / PostgreSQL (prod via `dj-database-url`) | |
| **Auth** | JWT via `djangorestframework-simplejwt`, Google OAuth2 | SimpleJWT 5.5 |
| **Media** | Cloudinary (prod), local `/media/` (dev) | |
| **CSS** | Tailwind CSS 4 | |
| **Error Tracking** | Sentry (backend + frontend) | |
| **Deployment** | Backend: Render (Gunicorn), Frontend: Vercel | |
| **Caching** | `django.core.cache.backends.locmem.LocMemCache` | |

---

## 2. Backend App Structure

```
backend/
├── core/          # Django project root (settings, urls, wsgi, asgi)
├── users/         # User model, auth (JWT+OTP, Google OAuth), profiles, addresses
├── products/      # Product, Category, Brand, ProductImage, Review, Inventory
├── orders/        # Order, OrderItem, Payment
├── sellers/       # SellerProfile, Store
├── crm/           # CustomerRecord, SellerRecord, Lead, Ticket, Message, Notification, ActivityLog
├── wishlist/      # Wishlist (M2M with Product)
└── scripts/       # Seed scripts
```

---

## 3. Existing Database Models

### Products Domain
- **Category**: name, slug, description, order
- **Brand**: name, slug
- **Product**: name, slug, store(FK→Store), category(FK), brand(FK), description, specifications, price, discount_price, cost_price, stock, sku, colors(JSON), is_featured, is_active, rating, tag, delivery_time_estimate, base_delivery_fee
- **ProductImage**: product(FK), image_url, alt_text, is_primary, order
- **Review**: product(FK), user(FK), name, rating, title, comment, image_url, video_url, is_verified_purchase
- **Inventory**: product(OneToOne), sku, quantity, low_stock_threshold, reserved_quantity (available_quantity property)

### Orders Domain
- **Order**: user(FK), status(pending/processing/shipped/delivered/cancelled), payment_method(razorpay/cod), delivery_eta, delivery_fee, promo_code, discount_amount, total_price, shipping_address, customer_note
- **OrderItem**: order(FK), product(FK), quantity, price (at time of purchase)
- **Payment**: order(OneToOne), method, status(pending/authorized/paid/failed/refunded), amount, provider_reference

### Users Domain
- **User**: extends AbstractUser, email(unique), role(customer/seller/admin), phone, address, otp_code, otp_created_at
- **CustomerProfile**: user(OneToOne), full_name, notes, lifetime_value
- **Address**: user(FK), label, address_type, full_name, phone, line1, line2, city, state, postal_code, country, is_default

### Sellers Domain
- **SellerProfile**: user(OneToOne), business_name, phone, tax_id, status(pending/verified/suspended)
- **Store**: seller(OneToOne), name, slug, description, logo_url, banner_url, address, area

### CRM Domain
- **CustomerRecord**, **SellerRecord**, **Lead**, **Ticket**, **Message**, **Notification**, **ActivityLog**

### Models That DO NOT Exist
- ProductVariant, Warehouse, Cart/CartItem (server-side), Coupon/Discount models, Campaign, Subscription

---

## 4. Existing API Endpoints

### Authentication: `/api/token/`, `/api/token/verify-2fa/`, `/api/token/refresh/`, `/api/auth/google/`, `/api/auth/register/`, `/api/auth/me/`
### Products: `/api/products/items/` (CRUD), `/api/products/categories/`, `/api/products/brands/`, `/api/products/reviews/`, `/api/products/suggestions/`, `/api/products/ai/chat/`, `/api/products/homepage/`
### Orders: `/api/orders/` (CRUD), `/api/orders/{id}/status/`, `/api/orders/summary/`, `/api/orders/calculate_delivery/`
### Sellers: `/api/sellers/profiles/`, `/api/sellers/profiles/dashboard/`, `/api/sellers/stores/`
### CRM: `/api/crm/overview/`, `/api/crm/customers/`, `/api/crm/tickets/`, `/api/crm/notifications/`, `/api/crm/activity/`

---

## 5. Payment Integration Status
- Payment model stores status and provider_reference
- Frontend loads Razorpay JS SDK, creates payment client-side
- **No backend Razorpay SDK** (not in requirements.txt)
- **No webhook handling**
- **No server-side signature verification**
- Promo codes: hardcoded dict in serializers

## 6. Event/Audit System
- **ActivityLog** model in CRM — captures actor, verb, target_type, target_id, metadata(JSON)
- **Notification** model — order/status notifications
- No event bus, no background queues, no Django signals

## 7. Cart
- Entirely client-side (CartContext + localStorage). No server-side cart model.
