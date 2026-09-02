from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class ProductRelationship(models.Model):
    RELATIONSHIP_CHOICES = (
        ('frequently_bought_with', 'Frequently Bought With'),
        ('alternative_to', 'Alternative To'),
        ('upgrade_to', 'Upgrade To'),
        ('accessory_for', 'Accessory For'),
        # ── RazorHubSeller-ported relationship types ──
        ('complementary', 'Complementary'),
        ('compatible', 'Compatible'),
        ('substitute', 'Substitute'),
        ('frequently_bought_together', 'Frequently Bought Together'),
    )


    source_product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='outgoing_relationships')
    target_product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='incoming_relationships')
    relationship_type = models.CharField(max_length=50, choices=RELATIONSHIP_CHOICES)
    source = models.CharField(max_length=50, help_text="e.g., 'system_generated', 'merchant_defined'")
    confidence = models.DecimalField(max_digits=5, decimal_places=4, default=1.0)
    merchant_defined = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('source_product', 'target_product', 'relationship_type')

    def __str__(self):
        return f"{self.source_product.name} -> {self.relationship_type} -> {self.target_product.name}"


class RevenueOpportunity(models.Model):
    OPPORTUNITY_CHOICES = (
        ('upsell', 'Upsell'),
        ('cross_sell', 'Cross-sell'),
        ('bundle', 'Bundle'),
        ('stock_clearance', 'Stock Clearance'),
        ('abandoned_cart', 'Abandoned Cart'),
    )

    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='revenue_opportunities')
    target_product = models.ForeignKey('products.Product', on_delete=models.CASCADE, null=True, blank=True)
    opportunity_type = models.CharField(max_length=50, choices=OPPORTUNITY_CHOICES)
    score = models.DecimalField(max_digits=5, decimal_places=4, default=0.0)
    expected_revenue_impact = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    reason_codes = models.JSONField(default=list, blank=True)
    explanation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.opportunity_type} for {self.product.name}"


class CustomerIntent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    intent = models.CharField(max_length=100)
    confidence = models.DecimalField(max_digits=5, decimal_places=4, default=1.0)
    budget_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    preferences = models.JSONField(default=dict, blank=True)
    constraints = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class InventoryInsight(models.Model):
    RISK_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )

    product = models.OneToOneField('products.Product', on_delete=models.CASCADE, related_name='inventory_insight')
    available = models.PositiveIntegerField(default=0)
    velocity_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    estimated_days_remaining = models.PositiveIntegerField(null=True, blank=True)
    risk_level = models.CharField(max_length=20, choices=RISK_CHOICES, default='low')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Offer(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
        ('redeemed', 'Redeemed'),
    )

    offer_id = models.CharField(max_length=100, unique=True)
    offer_type = models.CharField(max_length=50)
    products = models.ManyToManyField('products.Product', related_name='offers')
    price = models.DecimalField(max_digits=12, decimal_places=2)
    original_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2)
    confidence = models.DecimalField(max_digits=5, decimal_places=4, default=1.0)
    reason_codes = models.JSONField(default=list, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.offer_type} - {self.offer_id}"


class OfferDecision(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='decisions')
    decision = models.CharField(max_length=50)
    reason_codes = models.JSONField(default=list, blank=True)
    policy_version = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Campaign(models.Model):
    DISCOUNT_CHOICES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    )

    name = models.CharField(max_length=200)
    campaign_type = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_limit = models.DecimalField(max_digits=12, decimal_places=2, default=50000.00, help_text="Budget cap for the campaign in INR")
    current_spend = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Total discount awarded so far in INR")
    auto_pause_at_budget = models.BooleanField(default=True, help_text="Automatically pause campaign when budget_limit is reached")
    segments = models.JSONField(default=list, blank=True, help_text="Target customer segments e.g. ['high_value', 'cart_abandoners']")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    eligible_products = models.ManyToManyField('products.Product', blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.status})"



class MerchantConfig(models.Model):
    """Singleton model for merchant AI configuration."""
    ai_recommendations_enabled = models.BooleanField(default=True)
    ai_checkout_enabled = models.BooleanField(default=True)
    max_ai_order_value = models.DecimalField(max_digits=12, decimal_places=2, default=50000.00)
    max_ai_quantity = models.PositiveIntegerField(default=10)
    max_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    auto_approval_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    allow_ai_negotiation = models.BooleanField(default=True)
    require_user_confirmation = models.BooleanField(default=True)
    free_shipping_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=999.00)
    risk_thresholds = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Merchant AI Config"


class AuditEvent(models.Model):
    event_id = models.CharField(max_length=50, unique=True)
    trace_id = models.CharField(max_length=100, blank=True)
    agent = models.CharField(max_length=64, null=True, blank=True)
    action = models.CharField(max_length=128)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=20)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_id} - {self.action} ({self.status})"

    class Meta:
        ordering = ['-created_at']


class RecoveryTask(models.Model):
    task_id = models.CharField(max_length=50, unique=True)
    customer_email = models.EmailField(blank=True)
    cart_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    status = models.CharField(max_length=32, default="Pending")
    agent_action = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.task_id} - {self.customer_email} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']
