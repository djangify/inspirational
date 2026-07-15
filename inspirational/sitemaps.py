from django.contrib.sitemaps import Sitemap
from django.urls import reverse, NoReverseMatch
from news.models import Post
from news.models import Category as NewsCategory
from shop.models import Category, Product
from prompt.models import PromptCategory


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "weekly"

    def items(self):
        candidates = [
            "core:homepage",
            "core:get_out_of_a_rut",
            "core:personal_development_resources",
            "core:diane_corriette",
            "core:category",
            "core:support",
            "shop:product_list",
            "shop:category_hub",
            "tools:index",  # Mindful Tools index page (/tools/)
            "tools:alive_list_builder",
            "tools:calming_game",
            "tools:tap_to_calm",
            "prompt:journal_prompt_generator",
            "core:privacy_policy",
            "core:cookie_policy",
            "core:terms_conditions",
            "core:ai_disclaimer",
            "core:affiliate",
        ]
        # Only include names that currently resolve, so a stale or renamed
        # entry can never take down the whole sitemap.
        resolvable = []
        for name in candidates:
            try:
                reverse(name)
            except NoReverseMatch:
                continue
            resolvable.append(name)
        return resolvable

    def location(self, item):
        return reverse(item)


class NewsSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5

    def items(self):
        return Post.objects.filter(status="published")

    def lastmod(self, obj):
        return obj.updated


class NewsCategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return NewsCategory.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()


class ShopCategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

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
        from shop.models import OneTimeOffer
        return Product.objects.filter(
            status="publish", is_active=True
        ).exclude(id__in=OneTimeOffer.hidden_product_ids())

    def lastmod(self, obj):
        return obj.updated


class PromptCategorySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return PromptCategory.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()
