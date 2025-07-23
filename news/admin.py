# news/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import requests
from .models import Category, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "status",
        "featured",
        "publish_date",
        "display_thumbnail",
    ]
    list_editable = ["featured"]
    list_filter = ["status", "category", "featured", "created", "publish_date"]

    search_fields = ["title", "content", "featured", "meta_title", "meta_description"]
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "publish_date"
    readonly_fields = ["display_media"]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "category",
                    "content",
                    "status",
                    "publish_date",
                    "featured",
                ),
            },
        ),
        (
            "Media",
            {
                "fields": (
                    "image",
                    "external_image_url",
                    "youtube_url",
                    "thumbnail",
                    "display_media",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Advertisement",
            {
                "fields": ("ad_type", "ad_code", "ad_image", "ad_url"),
                "classes": ("collapse",),
            },
        ),
        (
            "Resource",
            {
                "fields": ("resource_type", "resource_title", "resource"),
                "classes": ("collapse",),
            },
        ),
        (
            "SEO",
            {
                "fields": ("meta_title", "meta_description", "meta_keywords"),
                "classes": ("collapse",),
            },
        ),
    )

    def display_thumbnail(self, obj):
        image_url = obj.get_thumbnail_url()
        if image_url:
            return format_html('<img src="{}" width="50" />', image_url)
        return "-"

    display_thumbnail.short_description = "Thumbnail"

    def display_media(self, obj):
        html = []
        image_url = obj.get_image_url()
        youtube_url = obj.get_youtube_embed_url()

        if image_url:
            html.append(
                f'<div class="mb-4">'
                f"<strong>Image:</strong><br/>"
                f'<img src="{image_url}" width="200" />'
                f"</div>"
            )

        if youtube_url:
            html.append(
                f'<div class="mb-4">'
                f"<strong>YouTube Video:</strong><br/>"
                f'<iframe width="400" height="225" src="{youtube_url}" '
                f'frameborder="0" allowfullscreen></iframe>'
                f"</div>"
            )

        return format_html("".join(html)) if html else "-"

    display_media.short_description = "Media Preview"

    def clean_external_image_url(self, url):
        if not url:
            return url

        validator = URLValidator()
        try:
            validator(url)
        except ValidationError:
            raise ValidationError("Invalid URL format")

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

    def save_model(self, request, obj, form, change):
        if "external_image_url" in form.changed_data:
            obj.external_image_url = self.clean_external_image_url(
                obj.external_image_url
            )
        super().save_model(request, obj, form, change)
