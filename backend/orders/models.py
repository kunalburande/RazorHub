from django.db import models
from django.conf import settings
from products.models import Product

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    )
    
    PAYMENT_RAZORPAY = "razorpay"
    PAYMENT_COD = "cod"
    PAYMENT_CHOICES = (
        (PAYMENT_RAZORPAY, "Razorpay (Test Mode)"),
        (PAYMENT_COD, "Cash on Delivery"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES, default=PAYMENT_RAZORPAY)
    delivery_eta = models.CharField(max_length=100, blank=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=50)
    promo_code = models.CharField(max_length=50, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField(blank=True)
    customer_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order {self.id} - {self.user.email}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2) # price at time of purchase
    
    def __str__(self):
        return f"{self.quantity} of {self.product.name}"


class Payment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_AUTHORIZED = "authorized"
    STATUS_PAID = "paid"
    STATUS_FAILED = "failed"
    STATUS_REFUNDED = "refunded"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_AUTHORIZED, "Authorized"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
        (STATUS_REFUNDED, "Refunded"),
    )

    order = models.OneToOneField(Order, on_delete=models.CASCADE, null=True, blank=True, related_name="payment")
    method = models.CharField(max_length=50, choices=Order.PAYMENT_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    provider_reference = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order_id or 'Standalone'} - {self.method} - {self.status}"

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    actor_type = models.CharField(max_length=50, default='human')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

class IdempotencyRecord(models.Model):
    key = models.CharField(max_length=100, unique=True)
    request_hash = models.CharField(max_length=128)
    response_status = models.IntegerField()
    response_body = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

class TransactionDecision(models.Model):
    DECISION_CHOICES = (
        ('ALLOW', 'Allow'),
        ('DENY', 'Deny'),
        ('REVIEW', 'Review'),
        ('REQUIRE_USER_CONFIRMATION', 'Require User Confirmation'),
    )
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True, blank=True)
    decision = models.CharField(max_length=50, choices=DECISION_CHOICES)
    risk_score = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    reason_codes = models.JSONField(default=list)
    actor_type = models.CharField(max_length=50)
    actor_id = models.CharField(max_length=100, blank=True)
    policy_version = models.CharField(max_length=50)
    inventory_snapshot = models.JSONField(default=dict)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class Consent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    transaction_decision = models.ForeignKey(TransactionDecision, on_delete=models.CASCADE)
    consent_type = models.CharField(max_length=50)
    granted_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)


class Refund(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSED = "processed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSED, "Processed"),
        (STATUS_FAILED, "Failed"),
    )

    REASON_CHOICES = (
        ("defective_product", "Defective Product / Hardware Issue"),
        ("late_delivery", "Late Delivery / Missed SLA"),
        ("customer_refusal", "Customer Refusal / Changed Mind"),
        ("sizing_issue", "Sizing / Fitment Mismatch"),
        ("duplicate_order", "Duplicate Order Placed"),
        ("suspected_fraud", "Suspected Fraud / Risk Intercept"),
    )

    refund_id = models.CharField(max_length=64, unique=True, db_index=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="refunds")
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name="refunds")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    reason = models.CharField(max_length=50, choices=REASON_CHOICES, default="customer_refusal")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PROCESSED)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.refund_id} - ₹{self.amount} ({self.status})"


class Payout(models.Model):
    STATUS_QUEUED = "queued"
    STATUS_PROCESSING = "processing"
    STATUS_PROCESSED = "processed"
    STATUS_REVERSED = "reversed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_QUEUED, "Queued"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_PROCESSED, "Processed"),
        (STATUS_REVERSED, "Reversed"),
        (STATUS_FAILED, "Failed"),
    )

    MODE_CHOICES = (
        ("NEFT", "NEFT"),
        ("RTGS", "RTGS"),
        ("IMPS", "IMPS"),
        ("UPI", "UPI"),
    )

    payout_id = models.CharField(max_length=64, unique=True, db_index=True)
    store = models.ForeignKey("sellers.Store", on_delete=models.SET_NULL, null=True, blank=True, related_name="payouts")
    recipient_name = models.CharField(max_length=150)
    recipient_account = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default="NEFT")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PROCESSED)
    utr = models.CharField(max_length=100, blank=True)
    narration = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.payout_id} - {self.recipient_name} - ₹{self.amount} ({self.status})"


class Settlement(models.Model):
    STATUS_CREATED = "created"
    STATUS_PROCESSED = "processed"
    STATUS_DELAYED = "delayed"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_CREATED, "Created"),
        (STATUS_PROCESSED, "Processed"),
        (STATUS_DELAYED, "Delayed"),
        (STATUS_FAILED, "Failed"),
    )

    settlement_id = models.CharField(max_length=64, unique=True, db_index=True)
    store = models.ForeignKey("sellers.Store", on_delete=models.SET_NULL, null=True, blank=True, related_name="settlements")
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Gross settlement volume")
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Gateway fee deduction")
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="GST on gateway fee")
    net_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Net credited amount")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PROCESSED)
    utr = models.CharField(max_length=100, blank=True)
    settlement_date = models.DateField()
    is_delayed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-settlement_date", "-created_at"]

    def __str__(self):
        return f"{self.settlement_id} - Net ₹{self.net_amount} ({self.status})"
