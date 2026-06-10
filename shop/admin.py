from django.contrib import admin
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.contrib.admin.widgets import AdminSplitDateTime
import requests
from .models import (
    Category,
    Product,
    ProductImage,
    Order,
    OrderItem,
    ProductReview,
    Purchase,
    ShopSettings,
    OrderBump,
    Coupon,
    SiteSettings,
)
from django import forms


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "description"]


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["image", "alt_text", "order"]
    ordering = ["order"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "status",
        "price",
        "sale_price",
        "product_type",
        "purchase_count",
        "featured",
        "display_thumbnail",
        "order",
    ]
    list_filter = ["status", "category", "product_type", "featured", "created"]
    search_fields = ["title", "description", "public_id"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["public_id", "purchase_count", "display_preview"]
    list_editable = [
        "order",
        "featured",
    ]
    inlines = [ProductImageInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "public_id",
                    "title",
                    "slug",
                    "category",
                    "product_type",
                    "number_of_pages",
                    "status",
                    "is_active",
                )
            },
        ),
        (
            "Sales Copy",
            {
                "fields": (
                    "description",
                    "long_description",
                )
            },
        ),
        (
            "Pricing",
            {
                "fields": (
                    "price_pence",
                    "sale_price_pence",
                    "price_per_hour",
                )
            },
        ),
        (
            "Media",
            {
                "fields": (
                    "preview_image",
                    "external_image_url",
                    "files",
                    "preview_file",
                    "external_preview_url",
                    "video_file",
                    "video_url",
                ),
            },
        ),
        (
            "Settings",
            {
                "fields": (
                    "download_limit",
                    "featured",
                    "purchase_count",
                    "order",
                )
            },
        ),
    )

    def price(self, obj):
        return f"${obj.price:.2f}"

    def sale_price(self, obj):
        if obj.sale_price_pence:
            return f"${obj.sale_price:.2f}"
        return "-"

    def display_thumbnail(self, obj):
        image_url = obj.get_image_url()
        if image_url:
            return format_html(
                '<img src="{}" width="50" class="admin-thumbnail" style="border-radius: 3px;" />',
                image_url,
            )
        return "-"

    display_thumbnail.short_description = "Thumbnail"

    def display_preview(self, obj):
        html = []
        image_url = obj.get_image_url()
        if image_url:
            html.append(
                f'<div class="mb-4"><strong>Preview Image:</strong><br/>'
                f'<img src="{image_url}" width="200" style="border-radius: 5px; '
                f'box-shadow: 0 2px 5px rgba(0,0,0,0.1);" /></div>'
            )
        return format_html("".join(html)) if html else "-"

    display_preview.short_description = "Preview"

    def clean_external_preview_url(self, url):
        if not url:
            return url

        # Validate URL format
        validator = URLValidator()
        try:
            validator(url)
        except ValidationError:
            raise ValidationError("Invalid URL format")

        # Check if URL exists and is a PDF
        try:
            response = requests.head(url, allow_redirects=True)
            content_type = response.headers.get("content-type", "").lower()

            if not content_type == "application/pdf":
                raise ValidationError("URL must point to a PDF file")

        except requests.RequestException:
            raise ValidationError("Could not validate preview URL")

        return url

    def save_model(self, request, obj, form, change):
        if "external_image_url" in form.changed_data:
            obj.external_image_url = self.clean_external_image_url(
                obj.external_image_url
            )
        if "external_preview_url" in form.changed_data:
            obj.external_preview_url = self.clean_external_preview_url(
                obj.external_preview_url
            )
        super().save_model(request, obj, form, change)

    def clean_external_image_url(self, url):
        if not url:
            return url

        # Validate URL format
        validator = URLValidator()
        try:
            validator(url)
        except ValidationError:
            raise ValidationError("Invalid URL format")

        # Check if URL exists and is an image
        try:
            response = requests.head(url, allow_redirects=True)
            content_type = response.headers.get("content-type", "").lower()

            if not content_type.startswith("image/"):
                raise ValidationError("URL must point to an image file")

            if not any(content_type.endswith(ext) for ext in ["/jpeg", "/jpg", "/png"]):
                raise ValidationError("Only JPG and PNG images are allowed")

        except requests.RequestException:
            raise ValidationError("Could not validate image URL")

        return url


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ["product"]
    fields = ["product", "quantity", "price_paid_pence"]
    readonly_fields = ["downloads_remaining"]
    ordering = ["id"]
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_id", "user", "email", "paid", "created", "get_customer_name"]
    list_filter = ["paid", "created", "status"]
    search_fields = [
        "order_id",
        "user__username",
        "email",
    ]
    inlines = [OrderItemInline]
    readonly_fields = ["order_id", "payment_intent_id"]

    def get_customer_name(self, obj):
        if obj.user:
            # Access first_name and last_name directly on the User model
            if obj.user.first_name and obj.user.last_name:
                return f"{obj.user.first_name} {obj.user.last_name}"
            elif obj.user.first_name:
                return obj.user.first_name
            else:
                return obj.user.username

        return "No user assigned"

    get_customer_name.short_description = "Customer"

    fieldsets = (
        (None, {"fields": ("order_id", "user", "email", "status", "paid")}),
        (
            "Payment Information",
            {"fields": ("payment_intent_id",), "classes": ("collapse",)},
        ),
    )


admin.site.register(Purchase)


@admin.register(OrderBump)
class OrderBumpAdmin(admin.ModelAdmin):
    list_display = ["bump_product", "trigger_product", "headline", "is_active", "order"]
    list_editable = ["is_active", "order"]
    list_filter = ["is_active"]
    search_fields = ["bump_product__title", "trigger_product__title", "headline"]

    fieldsets = (
        (None, {
            "fields": ("is_active", "order"),
        }),
        ("Trigger & Offer", {
            "fields": ("trigger_product", "bump_product"),
            "description": "Leave trigger product blank to show this bump on all checkouts.",
        }),
        ("Copy", {
            "fields": ("headline", "description"),
        }),
    )


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "discount_type",
        "discount_value",
        "is_active",
        "times_used",
        "usage_limit",
        "valid_from",
        "valid_to",
    ]
    list_editable = ["is_active"]
    list_filter = ["is_active", "discount_type"]
    search_fields = ["code"]
    readonly_fields = ["times_used"]

    fieldsets = (
        (None, {
            "fields": ("code", "is_active"),
        }),
        ("Discount", {
            "fields": ("discount_type", "discount_value", "minimum_order_pence"),
            "description": "For percentage, enter a number like 10 for 10%. For fixed, enter dollars like 5.00.",
        }),
        ("Usage Limits", {
            "fields": ("usage_limit", "times_used", "valid_from", "valid_to"),
        }),
    )


class ProductReviewAdminForm(forms.ModelForm):
    # Use a DIFFERENT name than the model field to avoid Django's
    # "non-editable field" check.
    created_override = forms.SplitDateTimeField(
        label="Created",
        widget=AdminSplitDateTime,
        required=True,
        help_text="Set the review’s created date/time.",
    )

    class Meta:
        model = ProductReview
        fields = "__all__"  # 'created' (the model field) will be excluded automatically

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.created:
            self.fields["created_override"].initial = self.instance.created

    def save(self, commit=True):
        obj = super().save(commit=False)
        # Write the chosen value back to the real model field
        obj.created = self.cleaned_data["created_override"]
        if commit:
            obj.save()
            self.save_m2m()
        return obj


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    form = ProductReviewAdminForm

    list_display = ["product", "user", "rating", "verified_purchase", "created"]
    list_filter = ["rating", "verified_purchase", "created"]
    search_fields = ["product__title", "user__username", "comment"]

    # IMPORTANT: reference the *form* field `created_override`, not the model field name.
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "product",
                    "user",
                    "rating",
                    "comment",
                    "created_override",  # editable proxy
                    "verified_purchase",
                )
            },
        ),
    )

    readonly_fields = []  # keep as you prefer

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(ShopSettings)
class ShopSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Legal & Compliance",
            {
                "fields": (
                    "show_digital_withdrawal_consent",
                    "digital_withdrawal_consent_text",
                )
            },
        ),
    )

    def has_add_permission(self, request):
        # Only allow one instance
        return not ShopSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "Analytics",
            {
                "fields": (
                    "google_analytics_id",
                    "google_search_console_verification",
                ),
                "description": (
                    "Changes here override the hardcoded values in base.html. "
                    "Leave blank to keep using the current hardcoded values."
                ),
            },
        ),
        (
            "Social / SEO",
            {
                "fields": (
                    "og_image",
                    "facebook_app_id",
                ),
            },
        ),
        (
            "Currency",
            {
                "fields": (
                    "currency_code",
                    "currency_symbol",
                ),
            },
        ),
        (
            "Blog & Shop Theme",
            {
                "fields": ("active_theme",),
                "description": (
                    "Select a visual theme for the blog and shop pages. "
                    "Classic keeps your current design. Editorial and Minimal "
                    "apply alternative layouts immediately — no restart needed."
                ),
            },
        ),
        (
            "Blog Sidebar",
            {
                "fields": ("sidebar_heading", "sidebar_product_count"),
                "description": (
                    "Controls the featured-products sidebar shown on blog pages."
                ),
            },
        ),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
