# inspirational / shop / models.py

from django.db import models
from django.urls import reverse
from django.conf import settings
import uuid
from decimal import Decimal
from inspirational.storage import secure_storage, public_storage
from inspirational.utils import custom_slugify
from tinymce.models import HTMLField
from inspirational.utils import convert_image_to_webp


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
    PRODUCT_TYPES = [("download", "Digital Download"), ("coaching", "Coaching Hours")]

    # Basic Fields
    public_id = models.CharField(max_length=130, blank=True, null=True, db_index=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = HTMLField()
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
        upload_to="products/files/", null=True, blank=True, storage=secure_storage
    )
    preview_file = models.FileField(
        upload_to="products/previews/", null=True, blank=True, storage=public_storage
    )
    preview_image = models.ImageField(
        upload_to="products/images/", null=True, blank=True, storage=public_storage
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

    from inspirational.utils import convert_image_to_webp

    def save(self, *args, **kwargs):
        # Convert uploaded preview_image to webp
        if self.preview_image and not str(self.preview_image.name).endswith(".webp"):
            filename, webp_image = convert_image_to_webp(self.preview_image)
            self.preview_image.save(filename, webp_image, save=False)

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
                return self.preview_image.url.replace("/media/public/", "/media/")
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
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
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
    downloads_remaining = models.PositiveIntegerField(default=5)
    download_count = models.PositiveIntegerField(default=0)

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
