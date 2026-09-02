import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from orders.models import Order, Payment

print("="*60)
print(f"Total Orders in DB: {Order.objects.count()}, Total Payments in DB: {Payment.objects.count()}")
for o in Order.objects.all():
    p = getattr(o, 'payment', None)
    p_status = p.status if p else 'no-payment-record'
    p_ref = p.provider_reference if p else 'none'
    print(f"Order #{o.id} | User: {o.user.email} | Status: {o.status} | Method: {o.payment_method} | Payment Status: {p_status} | Ref: {p_ref} | Total: INR {o.total_price}")
print("="*60)
