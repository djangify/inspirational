# inspirational / shop / models.py
from django.db import models
from django.urls import reverse
from django.conf import settings
import uuid
from decimal import Decimal
from inspirational.storage import secure_storage, public_storage
from inspirational.utils import custom_slugify
from tinymce.models import HTMLField


def generate_public_id(instance, *args, **kwargs):
    title = instance.title
    unique_id_short = uuid.uuid4().hex[:5]
    if not title:
        return unique_id_short
    slug = custom_slugify(title)
    return f"{slug}-{unique_id_short}"


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("shop:category", kwargs={"slug": self.slug})


class Product(models.Model):
    STATUS_CHOICES = [
        ("publish", "Published"),
        ("soon", "Coming Soon"),
        ("full", "Fully Booked"),
        ("draft", "Draft"),
    ]
    PRODUCT_TYPES = [("download", "Digital Download")]

    # Basic Fields
    public_id = models.CharField(max_length=130, blank=True, null=True, db_index=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = HTMLField()
    section_description = models.TextField(blank=True, null=True)
    long_description = HTMLField(blank=True, null=True)
    product_type = models.CharField(
        max_length=20, choices=PRODUCT_TYPES, default="download"
    )
    number_of_pages = models.PositiveIntegerField(
        null=True, blank=True, help_text="Number of pages for digital downloads"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    external_image_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="External URL for product image (jpg/png only)",
    )
    external_preview_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="External URL for preview file (PDF only)",
    )
    is_active = models.BooleanField(default=True)

    # Pricing
    price_pence = models.PositiveIntegerField(help_text="Price in pence")
    sale_price_pence = models.PositiveIntegerField(
        null=True, blank=True, help_text="Sale price in pence"
    )
    price_per_hour = models.PositiveIntegerField(
        null=True, blank=True, help_text="Coaching price per hour in pence"
    )

    # Media
    files = models.FileField(
        upload_to="products/files/",
        null=True,
        blank=True,
        storage=secure_storage,
        help_text="Upload a PDF or ZIP file. Use ZIP for bundles.",
    )
    preview_file = models.FileField(
        upload_to="products/previews/", null=True, blank=True, storage=public_storage
    )
    preview_image = models.ImageField(
        upload_to="products/images/", null=True, blank=True, storage=public_storage
    )
    video_url = models.URLField(
        blank=True,
        null=True,
        help_text="Optional YouTube or Vimeo URL to display on the product page",
    )
    video_file = models.FileField(
        upload_to="products/videos/",
        blank=True,
        null=True,
        storage=public_storage,  # uses same storage as images/PDFs
        help_text="Upload a short MP4 file to display as product video",
    )
    # Settings
    download_limit = models.PositiveIntegerField(default=5)
    featured = models.BooleanField(default=False)
    purchase_count = models.PositiveIntegerField(default=0)
    order = models.IntegerField(default=0)

    # Timestamps
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "-created"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.slug:
            self.slug = custom_slugify(self.title)
        if not self.public_id:
            self.public_id = generate_public_id(self)

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("shop:product_detail", kwargs={"slug": self.slug})

    def get_image_url(self):
        """Get the URL for the main image"""
        try:
            if self.external_image_url:
                return self.external_image_url
            if self.preview_image:
                return self.preview_image.url  # Don't replace anything here
            return None
        except Exception:
            return None

    def get_thumbnail_url(self):
        """Get thumbnail URL - falls back to main image if no thumbnail"""
        return self.get_image_url()

    def get_preview_url(self):
        """Get the URL for the preview file"""
        try:
            if self.external_preview_url:
                return self.external_preview_url
            if self.preview_file:
                return self.preview_file.url
            return None
        except Exception:
            return None

    def get_download_url(self):
        if self.files:
            return self.files.url
        return None

    @property
    def price(self):
        """Return price in pounds"""
        return Decimal(self.price_pence) / 100

    @property
    def sale_price(self):
        """Return sale price in pounds if it exists"""
        if self.sale_price_pence:
            return Decimal(self.sale_price_pence) / 100
        return None

    @property
    def current_price(self):
        """Return the current applicable price in pounds"""
        if self.sale_price_pence:
            return self.sale_price
        return self.price

    @property
    def is_on_sale(self):
        return bool(self.sale_price_pence)

    @property
    def is_coming_soon(self):
        return self.status == "soon"

    @property
    def is_fully_booked(self):
        return self.status == "full"

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return sum(review.rating for review in reviews) / reviews.count()
        return 0

    @property
    def total_reviews(self):
        return self.reviews.count()

    def can_review(self, user):
        # Superusers can always review
        if user.is_superuser:
            return True

        # For regular users, check purchase and review status
        has_purchased = OrderItem.objects.filter(
            order__user=user, product=self, order__status="completed"
        ).exists()
        has_reviewed = self.reviews.filter(user=user).exists()
        return has_purchased and not has_reviewed


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]


class GuestDetails(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.OneToOneField(
        "Order", on_delete=models.CASCADE, related_name="guest_details"
    )

    class Meta:
        verbose_name_plural = "Guest Details"

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    order_id = models.CharField(max_length=100, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    email = models.EmailField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_intent_id = models.CharField(max_length=250, blank=True)

    coupon_code = models.CharField(max_length=50, blank=True, default="")
    coupon_discount_pence = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"Order {self.order_id}"

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = f"ORD-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def get_total_cost(self):
        """Return total cost in pounds"""
        return sum(item.get_cost() for item in self.items.all())

    @property
    def total_price(self):
        return self.get_total_cost()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, related_name="order_items", on_delete=models.CASCADE
    )
    price_paid_pence = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)
    download_count = models.PositiveIntegerField(default=0)

    # ADD THIS:
    @property
    def downloads_remaining(self):
        return max(0, self.product.download_limit - self.download_count)

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        """Return cost in pounds"""
        return (self.price_paid_pence * self.quantity) / 100

    def get_price_in_pounds(self):
        return self.price_paid_pence / 100

    def get_download_url(self):
        """Get download URL for any product type"""
        return self.product.get_download_url()

    def has_downloadable_content(self):
        """Check if this item has any downloadable content"""
        return bool(self.product.files or self.product.get_download_url())

    @property
    def price(self):
        return self.get_price_in_pounds()

    @property
    def downloads_left(self):
        return max(self.product.download_limit - self.download_count, 0)


class ProductReview(models.Model):
    RATING_CHOICES = [
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
    ]
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    verified_purchase = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created"]
        # Ensure one review per user per product
        unique_together = ("product", "user")

    def __str__(self):
        return f"Review by {self.user.username} on {self.product.title}"

    @property
    def is_verified_purchase(self):
        return OrderItem.objects.filter(
            order__user=self.user, product=self.product, order__status="completed"
        ).exists()


class Purchase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey("Product", on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user.username} bought {self.product.title}"


class DownloadLog(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.order_item.id} - {self.downloaded_at}"


class ShopSettings(models.Model):
    show_digital_withdrawal_consent = models.BooleanField(
        default=False,
        help_text="Show the EU/UK digital withdrawal consent checkbox at checkout.",
    )
    digital_withdrawal_consent_text = models.CharField(
        max_length=500,
        default=(
            "I understand and agree that by completing this purchase I am requesting "
            "immediate access to digital content, and I therefore waive my right to "
            "withdraw from this contract under the EU/UK Consumer Rights Act "
            "(14-day cooling-off period)."
        ),
    )

    class Meta:
        verbose_name = "Shop Settings"
        verbose_name_plural = "Shop Settings"

    def __str__(self):
        return "Shop Settings"

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ============================================================
# ORDER BUMP
# ============================================================

class OrderBump(models.Model):
    """
    A special add-on offer shown at checkout.
    If trigger_product is set, the bump only appears when that product is in the cart.
    Leave trigger_product blank to show the bump for all checkouts.
    The bump_product must not already be in the cart for the offer to display.
    """

    trigger_product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_bump_triggers",
        help_text="Only show this bump when this product is in the cart. Leave blank to always show.",
    )
    bump_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="order_bumps",
        help_text="The product being offered as the bump add-on.",
    )
    headline = models.CharField(
        max_length=200,
        default="Special One-Time Offer!",
        help_text="Bold headline shown on the bump box.",
    )
    description = models.TextField(
        blank=True,
        help_text="Short pitch for why the customer should add this.",
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order if multiple bumps are active.",
    )

    class Meta:
        ordering = ["order"]
        verbose_name = "Order Bump"
        verbose_name_plural = "Order Bumps"

    def __str__(self):
        return f"{self.bump_product.title} (bump)"

    @property
    def bump_price(self):
        return self.bump_product.current_price

    @property
    def bump_price_pence(self):
        return self.bump_product.sale_price_pence or self.bump_product.price_pence


# ============================================================
# COUPON
# ============================================================

class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ("percentage", "Percentage"),
        ("fixed", "Fixed Amount"),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default="percentage",
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Percentage (e.g. 10 for 10%) or fixed amount in pounds (e.g. 5 for £5).",
    )
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Max total uses. Leave blank for unlimited.",
    )
    times_used = models.PositiveIntegerField(default=0)
    minimum_order_pence = models.PositiveIntegerField(
        default=0,
        help_text="Minimum cart total (in pence) required for this coupon.",
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"

    def __str__(self):
        return self.code.upper()

    def is_valid(self, cart_total_pence=0):
        from django.utils import timezone
        now = timezone.now()
        if not self.is_active:
            return False, "This coupon is inactive."
        if self.valid_from and now < self.valid_from:
            return False, "This coupon is not yet valid."
        if self.valid_to and now > self.valid_to:
            return False, "This coupon has expired."
        if self.usage_limit is not None and self.times_used >= self.usage_limit:
            return False, "This coupon has reached its usage limit."
        if cart_total_pence < self.minimum_order_pence:
            min_pounds = self.minimum_order_pence / 100
            return False, f"A minimum order of £{min_pounds:.2f} is required."
        return True, "Valid"

    def calculate_discount_pence(self, cart_total_pence):
        if self.discount_type == "percentage":
            discount = int(round(cart_total_pence * float(self.discount_value) / 100))
        else:
            discount = int(round(float(self.discount_value) * 100))
        return min(discount, cart_total_pence)


# ============================================================
# SITE SETTINGS (singleton)
# ============================================================

class SiteSettings(models.Model):
    CURRENCY_CHOICES = [
        ("GBP", "British Pound (£)"),
        ("USD", "US Dollar ($)"),
        ("EUR", "Euro (€)"),
    ]

    THEME_CHOICES = [
        ("classic", "Classic — default site design"),
        ("editorial", "Editorial — warm tones, serif headings, magazine layout"),
        ("minimal", "Minimal — clean black & white, Substack-style"),
        ("spotlight", "Spotlight — featured products over a clean minimal feed"),
    ]

    google_analytics_id = models.CharField(
        max_length=30,
        blank=True,
        default="",
        help_text="Google Analytics measurement ID, e.g. G-XXXXXXXXXX.",
        verbose_name="Google Analytics ID",
    )
    google_search_console_verification = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Verification token from Google Search Console meta tag.",
        verbose_name="GSC Verification Token",
    )
    og_image = models.ImageField(
        upload_to="site/og/",
        blank=True,
        null=True,
        help_text="Default Open Graph image (1200x630 px recommended).",
        verbose_name="Default OG Image",
    )
    facebook_app_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Facebook App ID for Open Graph fb:app_id tag.",
        verbose_name="Facebook App ID",
    )
    currency_code = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default="GBP",
        verbose_name="Currency Code",
    )
    currency_symbol = models.CharField(
        max_length=5,
        default="£",
        verbose_name="Currency Symbol",
    )
    active_theme = models.CharField(
        "Site Theme",
        max_length=20,
        choices=THEME_CHOICES,
        default="classic",
        help_text=(
            "Choose the visual theme for the blog and shop. "
            "Classic uses your default design. Changes apply immediately."
        ),
    )
    sidebar_heading = models.CharField(
        "Blog Sidebar Heading",
        max_length=100,
        default="Featured Products",
        blank=True,
        help_text="Heading shown above the products sidebar on blog pages.",
    )
    sidebar_product_count = models.PositiveSmallIntegerField(
        "Blog Sidebar Product Count",
        default=5,
        help_text="Number of featured products to show in the blog sidebar.",
    )

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Site Settings"

    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            raise ValueError("Only one SiteSettings instance is allowed.")
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ============================================================
# ONE-TIME OFFER  (post-registration tripwire)
# ============================================================

class OneTimeOffer(models.Model):
    """
    Singleton. A post-registration one-time offer shown once, on a user's first
    login after email verification, instead of the dashboard.

    The offer is fully self-contained: you write the copy, set the price, and
    upload the downloadable file right here — there is NO store product to pick.
    Behind the scenes it keeps a single hidden, unpublished Product (`product`,
    set automatically and never edited directly) so that purchases, downloads
    and the customer's account all work through the existing order system. That
    hidden record is never shown in the shop.
    """

    enabled = models.BooleanField(
        default=False,
        help_text="Tick to show the one-time offer to eligible users on their next login.",
    )

    # ---- The offer itself (no store product needed) ----
    title = models.CharField(
        max_length=200,
        default="",
        help_text="Name of what they're buying (shown as the item title).",
    )
    price_pence = models.PositiveIntegerField(
        default=700,
        help_text="Price they pay, in pence (e.g. 700 = £7.00).",
    )
    compare_at_pence = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Optional 'normal' price in pence, shown with a line through it for contrast.",
    )
    file = models.FileField(
        upload_to="products/files/",
        null=True,
        blank=True,
        storage=secure_storage,
        help_text="The downloadable file (PDF or ZIP) the buyer receives. Upload it here.",
    )
    image = models.ImageField(
        upload_to="products/images/",
        null=True,
        blank=True,
        storage=public_storage,
        help_text="Optional image shown alongside the offer.",
    )
    download_limit = models.PositiveIntegerField(
        default=5,
        help_text="How many times the buyer can download the file.",
    )

    # Bundle: existing shop products this offer includes. Buyers get each
    # product's download AND its existing AI coach — nothing is re-uploaded.
    included_products = models.ManyToManyField(
        Product,
        blank=True,
        related_name="in_one_time_offers",
        help_text=(
            "Tick the products this offer includes. On purchase the buyer gets "
            "each product's download and its existing AI coach — no need to "
            "re-upload anything."
        ),
    )

    # Copy
    headline = models.CharField(
        max_length=200,
        default="A one-time offer, just for you",
    )
    subheadline = models.CharField(max_length=300, blank=True, default="")
    body = HTMLField(
        blank=True,
        help_text="Sales pitch shown under the headline.",
    )
    button_text = models.CharField(
        max_length=80,
        default="Yes, add this to my account",
    )
    decline_text = models.CharField(
        max_length=80,
        default="No thanks, take me to my dashboard",
    )

    # Urgency
    show_timer = models.BooleanField(
        default=False,
        help_text="Show a countdown timer on the offer page.",
    )
    timer_minutes = models.PositiveIntegerField(
        default=15,
        help_text="Countdown length in minutes (visual urgency only).",
    )

    # Internal: the hidden download record. Managed automatically — do not edit.
    product = models.OneToOneField(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="one_time_offer",
    )

    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "One-Time Offer"
        verbose_name_plural = "One-Time Offer"

    def __str__(self):
        return "One-Time Offer"

    def save(self, *args, **kwargs):
        # Enforce singleton
        if not self.pk and OneTimeOffer.objects.exists():
            raise ValueError("Only one OneTimeOffer instance is allowed.")
        super().save(*args, **kwargs)
        self._sync_hidden_product()

    def _sync_hidden_product(self):
        """
        Keep the hidden, unpublished Product in sync with the offer so the
        existing order/download/account system can deliver the file. The hidden
        product stays status='draft' and inactive, so it never appears in the
        shop, on the homepage, or under any category.
        """
        # A dedicated, unpublished holder category (reuse if it exists).
        category = (
            Category.objects.filter(slug="one-time-offer").first()
            or Category.objects.create(
                name="One-Time Offer", slug="one-time-offer",
                description="Internal — holds the one-time offer download. Not shown in the shop.",
            )
        )

        product = self.product or Product()
        product.title = self.title or "One-Time Offer"
        product.category = category
        product.product_type = "download"
        # status='draft' keeps it out of the shop everywhere (every catalog query
        # filters status in publish/soon/full). We keep is_active=True so the
        # bots system can attach an AI coach to it (bot_chat requires an active
        # product); 'draft' alone still guarantees it never shows in the shop.
        product.status = "draft"
        product.is_active = True
        product.featured = False
        product.price_pence = self.price_pence
        product.sale_price_pence = None
        product.download_limit = self.download_limit
        if not product.description:
            product.description = self.body or self.title or "One-Time Offer"
        # Point the hidden product at the same uploaded file/image (no copy).
        product.files.name = self.file.name if self.file else ""
        product.preview_image.name = self.image.name if self.image else ""
        product.save()

        if self.product_id != product.id:
            # Link without re-triggering the full save/sync loop.
            OneTimeOffer.objects.filter(pk=self.pk).update(product=product)
            self.product = product

    @property
    def price(self):
        """Charge amount in pounds."""
        return Decimal(self.price_pence) / 100

    @property
    def has_special_price(self):
        """True if a 'normal' compare-at price is set above the offer price."""
        return bool(self.compare_at_pence and self.compare_at_pence > self.price_pence)

    @property
    def normal_price(self):
        """The compare-at price in pounds, for the strikethrough."""
        if self.compare_at_pence:
            return Decimal(self.compare_at_pence) / 100
        return self.price

    def is_eligible_for(self, user):
        """
        Should this user see the offer right now?
        Gated so it can only ever show once (via UserProfile.oto_seen_at).
        """
        if not self.enabled:
            return False
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return False
        # The offer must deliver something: either its own file, or bundled
        # products. (The file is optional now that offers can be a bundle.)
        has_deliverable = bool(self.file) or self.included_products.exists()
        if not has_deliverable or not self.product:
            return False

        profile = getattr(user, "profile", None)
        if profile is not None and profile.oto_seen_at is not None:
            return False

        already_owns = OrderItem.objects.filter(
            order__user=user, product=self.product, order__status="completed"
        ).exists()
        if already_owns:
            return False

        return True

    @classmethod
    def hidden_product_ids(cls):
        """
        Product ids reserved for an enabled one-time offer. The hidden product
        is already unpublished/inactive (so excluded from the catalog), but we
        also exclude it explicitly as belt-and-braces.
        """
        return list(
            cls.objects.filter(product__isnull=False)
            .values_list("product_id", flat=True)
        )
