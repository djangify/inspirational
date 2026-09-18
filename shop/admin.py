from django.contrib import admin, messages
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.contrib.admin.widgets import AdminSplitDateTime
from django.urls import path, reverse
from django.shortcuts import redirect, get_object_or_404
from django.template.response import TemplateResponse
import requests
from .models import (
    Category,
    Product,
    ProductImage,
    ProductKnowledge,
    ProductQuestion,
    Order,
    OrderItem,
    ProductReview,
    Purchase,
    ShopSettings,
    OrderBump,
    Coupon,
    SiteSettings,
    OneTimeOffer,
)
from .ai_knowledge import generate_knowledge_draft, KnowledgeDraftError
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


class ProductKnowledgeInline(admin.StackedInline):
    model = ProductKnowledge
    max_num = 1
    can_delete = True
    verbose_name = "Product Knowledge (AI/search discoverability)"
    verbose_name_plural = "Product Knowledge (AI/search discoverability)"
    fields = ["problem_solved", "target_audience", "differentiator", "search_keywords"]


class ProductQuestionInline(admin.TabularInline):
    model = ProductQuestion
    extra = 1
    fields = ["question", "answer", "order"]
    ordering = ["order"]
    verbose_name = "Question (FAQ)"
    verbose_name_plural = "Questions (FAQ), shown on the product page and in FAQ schema"


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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Only PAID hosted tools may be sold, so the picker must never list free
        # tools. Keep any tool already attached to this product selectable too.
        if db_field.name == "hosted_tool":
            from tools.models import HostedTool

            kwargs["queryset"] = HostedTool.objects.filter(access="paid")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        # Hide the internal one-time-offer download record from the product list.
        return super().get_queryset(request).filter(one_time_offer__isnull=True)

    readonly_fields = ["public_id", "purchase_count", "display_preview", "ai_knowledge_link"]
    list_editable = [
        "order",
        "featured",
    ]
    inlines = [ProductImageInline, ProductKnowledgeInline, ProductQuestionInline]
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
            "AI Discoverability",
            {
                "fields": ("ai_knowledge_link",),
                "description": (
                    "The Product Knowledge and Q&A below (saved after the inline "
                    "sections further down) are what AI systems like ChatGPT and "
                    "Claude read to understand, recommend and cite this product. "
                    "Save this product first, then use the link below to draft "
                    "them with AI."
                ),
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
            "Hosted Tool",
            {
                "fields": ("hosted_tool",),
                "description": (
                    "Attach a Hosted Tool to sell it as this product. Buyers open "
                    "the live tool from their downloads area, and the tool's public "
                    "page becomes purchase-only. Leave blank for a normal download. "
                    "Tip: set Product type to 'Hosted Tool' and leave the file blank."
                ),
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

    def ai_knowledge_link(self, obj):
        if not obj.pk:
            return "Save the product first to draft Product Knowledge with AI."
        url = reverse("admin:shop_product_ai_knowledge", args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">Draft Product Knowledge &amp; Q&amp;A with AI &raquo;</a>',
            url,
        )

    ai_knowledge_link.short_description = "AI draft"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:product_id>/ai-knowledge/",
                self.admin_site.admin_view(self.ai_knowledge_view),
                name="shop_product_ai_knowledge",
            ),
        ]
        return custom + urls

    def ai_knowledge_view(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        knowledge = product.get_knowledge()
        existing_questions = list(product.questions.all())

        draft = None
        if request.method == "POST" and request.POST.get("action") == "generate":
            try:
                draft = generate_knowledge_draft(product)
            except KnowledgeDraftError as exc:
                messages.error(request, str(exc))

        elif request.method == "POST" and request.POST.get("action") == "save":
            knowledge, _ = ProductKnowledge.objects.get_or_create(product=product)
            knowledge.problem_solved = request.POST.get("problem_solved", "").strip()
            knowledge.target_audience = request.POST.get("target_audience", "").strip()
            knowledge.differentiator = request.POST.get("differentiator", "").strip()
            knowledge.search_keywords = request.POST.get("search_keywords", "").strip()
            knowledge.save()

            product.questions.all().delete()
            order = 0
            for i in range(1, 9):
                q = request.POST.get(f"question_{i}", "").strip()
                a = request.POST.get(f"answer_{i}", "").strip()
                if q:
                    ProductQuestion.objects.create(
                        product=product, question=q, answer=a, order=order
                    )
                    order += 1

            messages.success(request, "Product Knowledge and Q&A saved.")
            return redirect(reverse("admin:shop_product_change", args=[product.pk]))

        fields = {
            "problem_solved": (draft or {}).get(
                "problem_solved", knowledge.problem_solved if knowledge else ""
            ),
            "target_audience": (draft or {}).get(
                "target_audience", knowledge.target_audience if knowledge else ""
            ),
            "differentiator": (draft or {}).get(
                "differentiator", knowledge.differentiator if knowledge else ""
            ),
            "search_keywords": (draft or {}).get(
                "search_keywords", knowledge.search_keywords if knowledge else ""
            ),
        }
        if draft is not None:
            questions = draft["questions"]
        else:
            questions = [
                {"question": q.question, "answer": q.answer} for q in existing_questions
            ]
        # Pad to 8 rows for the form.
        questions = (questions + [{"question": "", "answer": ""}] * 8)[:8]

        context = {
            **self.admin_site.each_context(request),
            "title": f"AI Product Knowledge: {product.title}",
            "product": product,
            "fields": fields,
            "questions": questions,
            "opts": self.model._meta,
        }
        return TemplateResponse(
            request, "admin/shop/product/ai_knowledge.html", context
        )

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


@admin.register(OneTimeOffer)
class OneTimeOfferAdmin(admin.ModelAdmin):
    """Singleton admin for the post-registration one-time offer."""

    list_display = ["__str__", "enabled", "product", "updated", "preview_link"]
    list_editable = ["enabled"]

    def _preview_url(self):
        from django.urls import reverse
        return f"{reverse('shop:one_time_offer')}?preview=1"

    def view_on_site(self, obj):
        return self._preview_url()

    def preview_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank">Preview</a>', self._preview_url()
        )

    preview_link.short_description = "Preview"

    fieldsets = (
        ("Offer", {
            "fields": (
                "enabled",
                "title",
                "price_pence",
                "compare_at_pence",
                "file",
                "image",
                "download_limit",
            ),
            "description": (
                "Write the offer here — there's no store product to pick. Give it a "
                "title, set the price in pence (4700 = £47.00). The file is an optional "
                "bonus download; the main value is the bundle below. This offer is never "
                "shown in the shop. Tick 'enabled' to switch it on."
            ),
        }),
        ("Bundle — products included in this offer", {
            "fields": ("included_products",),
            "description": (
                "Tick the products this offer includes. On purchase the buyer gets each "
                "product's download AND its existing AI coach automatically — you don't "
                "re-upload anything."
            ),
        }),
        ("Copy", {
            "fields": (
                "headline",
                "subheadline",
                "body",
                "button_text",
                "decline_text",
            ),
        }),
        ("Urgency", {
            "fields": ("show_timer", "timer_minutes"),
            "classes": ("collapse",),
        }),
    )

    filter_horizontal = ("included_products",)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "included_products":
            # Don't offer the offer's own hidden record as a choice.
            kwargs["queryset"] = Product.objects.filter(one_time_offer__isnull=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def has_add_permission(self, request):
        if OneTimeOffer.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False


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
