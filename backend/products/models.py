from django.db import models
from django.utils.text import slugify
from django.conf import settings

# ── pgvector: graceful fallback for SQLite dev ──────────────────────────
try:
    from pgvector.django import VectorField
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False


class Category(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Brand(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    name = models.CharField(max_length=300, db_index=True)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    store = models.ForeignKey("sellers.Store", on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    description = models.TextField()
    specifications = models.TextField(blank=True, help_text="One spec per line, format: Key: Value")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    colors = models.JSONField(default=list, blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    tag = models.CharField(max_length=50, blank=True, null=True)
    delivery_time_estimate = models.CharField(max_length=100, default="1-2 business days")
    base_delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=150.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ── RazorHubSeller AI-Commerce Fields ──────────────────────────────────
    price_paise = models.BigIntegerField(
        default=0,
        help_text="Selling price in paisa (1/100 of currency unit). Auto-computed from price on save."
    )
    cost_paise = models.BigIntegerField(
        default=0,
        help_text="Cost price in paisa. Auto-computed from cost_price on save."
    )
    margin_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        help_text="Gross margin percentage. Auto-computed: ((price - cost) / price) * 100."
    )
    currency = models.CharField(max_length=3, default="INR")
    ai_metadata = models.JSONField(
        default=dict, blank=True,
        help_text="AI-specific metadata (e.g., embedding model version, last vectorized timestamp)."
    )
    # pgvector embedding — 1536 dimensions for text-embedding-3-small
    if HAS_PGVECTOR:
        embedding = VectorField(
            dimensions=1536, null=True, blank=True,
            help_text="Semantic embedding vector for AI-powered similarity search."
        )
    else:
        # SQLite fallback: store as JSON text (no vector ops)
        embedding = models.JSONField(
            null=True, blank=True,
            help_text="Semantic embedding vector (JSON fallback for non-PostgreSQL)."
        )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "is_featured"]),
            models.Index(fields=["is_active", "-created_at"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["brand", "is_active"]),
            models.Index(fields=["store", "is_active"]),
        ]

    def __str__(self):
        return self.name

    @property
    def current_price(self):
        return self.discount_price or self.price

    def _compute_paise_and_margin(self):
        """Auto-compute paisa-denominated fields and margin from Decimal price fields."""
        from decimal import Decimal, ROUND_HALF_UP

        # Coerce to Decimal — tests and seed scripts may pass int or float
        def _to_decimal(val):
            if val is None:
                return None
            if isinstance(val, Decimal):
                return val
            return Decimal(str(val))

        selling_raw = self.discount_price if self.discount_price else self.price
        selling = _to_decimal(selling_raw)
        cost = _to_decimal(self.cost_price)

        # price_paise: current selling price in paisa
        if selling is not None:
            self.price_paise = int((selling * 100).to_integral_value(rounding=ROUND_HALF_UP))
        else:
            self.price_paise = 0

        # cost_paise
        if cost is not None:
            self.cost_paise = int((cost * 100).to_integral_value(rounding=ROUND_HALF_UP))
        else:
            self.cost_paise = 0

        # margin_pct: ((selling - cost) / selling) * 100
        if selling and cost is not None and selling > 0:
            margin = ((selling - cost) / selling) * Decimal("100")
            self.margin_pct = margin.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            self.margin_pct = Decimal("0.00")

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            suffix = 2
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{suffix}"
                suffix += 1
            self.slug = slug
        # Auto-compute AI-commerce fields
        self._compute_paise_and_margin()
        super().save(*args, **kwargs)

    def get_specs_list(self):
        if not self.specifications:
            return []
        specs = []
        for line in self.specifications.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                specs.append({"key": key.strip(), "value": value.strip()})
        return specs

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField(max_length=500)
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"

class ImageCurationRating(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="curation_rating")
    rating = models.CharField(max_length=50, choices=[('good', 'Good'), ('could_be_better', 'Could be better'), ('wrong', 'Wrong')])
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.rating}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="reviews")
    name = models.CharField(max_length=120)
    rating = models.PositiveSmallIntegerField(default=5)
    title = models.CharField(max_length=160, blank=True)
    comment = models.TextField()
    image_url = models.URLField(blank=True, null=True, help_text="Optional image URL for the review")
    video_url = models.URLField(blank=True, null=True, help_text="Optional video URL for the review")
    is_verified_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.product.name} review by {self.name}"


class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="inventory")
    sku = models.CharField(max_length=120, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    reserved_quantity = models.PositiveIntegerField(default=0)
    # ── RazorHubSeller: warehouse/location tracking ──
    location = models.CharField(
        max_length=128, blank=True,
        help_text="Warehouse or storage location identifier."
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Inventory"

    def __str__(self):
        return f"{self.product.name} inventory"

    @property
    def available_quantity(self):
        return max(self.quantity - self.reserved_quantity, 0)


# ── RazorHubSeller: Structured Product Attributes for AI filtering ──────────

class ProductAttribute(models.Model):
    """
    Structured key-value attributes for AI-powered filtering and comparison.
    Ported from RazorHubSeller product_attributes table.

    Examples:
        key="RAM", value="16GB"
        key="screen_size", value="15.6 inches"
        key="battery_life", value="10 hours"
    """
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="ai_attributes"
    )
    key = models.CharField(max_length=128)
    value = models.CharField(max_length=255)

    class Meta:
        unique_together = ("product", "key")
        verbose_name = "Product Attribute"
        verbose_name_plural = "Product Attributes"

    def __str__(self):
        return f"{self.product.name}: {self.key}={self.value}"
