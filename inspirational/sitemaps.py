from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from news.models import Post
from shop.models import Category, Product
from prompt.models import PromptCategory


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        return ["pages:home", "privacy_policy", "cookie_policy", "terms_conditions"]

    def location(self, item):
        return reverse(item)


class NewsSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Post.objects.filter(status="published")

    def lastmod(self, obj):
        return obj.updated


class ShopCategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Category.objects.all()

    def lastmod(self, obj):
        # Get the latest product update in this category
        latest_product = (
            Product.objects.filter(category=obj, status="publish")
            .order_by("-updated")
            .first()
        )
        return latest_product.updated if latest_product else None


class ShopProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Product.objects.filter(status="publish", is_active=True)

    def lastmod(self, obj):
        return obj.updated


class PromptCategorySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return PromptCategory.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()
