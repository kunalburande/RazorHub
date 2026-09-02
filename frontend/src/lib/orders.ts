import type { ProductType } from './products';

export interface OrderItemType {
  id: number;
  product: ProductType;
  quantity: number;
  price: string;
}

export interface PaymentType {
  id: number;
  method: string;
  status: string;
  amount: string;
  provider_reference?: string;
}

export interface OrderType {
  id: number;
  customer_email: string;
  status: 'pending' | 'processing' | 'shipped' | 'delivered' | 'cancelled';
  payment_method: string;
  delivery_method?: string;
  delivery_eta?: string;
  delivery_fee: string;
  promo_code: string;
  discount_amount: string;
  total_price: string;
  shipping_address: string;
  customer_note: string;
  items: OrderItemType[];
  payment?: PaymentType;
  created_at: string;
  updated_at: string;
}

export const orderStatuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled'] as const;

export function paymentLabel(method: string) {
  const labels: Record<string, string> = {
    razorpay: 'Razorpay (Test Mode)',
    cod: 'Cash on Delivery (COD)',
    card: 'Card Payment',
  };

  return labels[method] || method;
}

export function deliveryLabel(method: string) {
  const labels: Record<string, string> = {
    standard: 'Standard delivery',
    overnight: 'Express delivery',
  };

  return labels[method] || method;
}

export function orderStatusLabel(status: string) {
  const labels: Record<string, string> = {
    pending: 'Pending',
    processing: 'Processing',
    shipped: 'Shipped',
    delivered: 'Delivered',
    cancelled: 'Cancelled',
  };

  return labels[status] || status;
}
