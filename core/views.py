from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm
from .models import SupportMessage
from django.contrib.auth.decorators import login_required
from shop.models import Product, ProductReview
from news.models import Category as NewsCategory
from shop.models import Category as ShopCategory
from news.models import Post, Category
from django.utils.timezone import now
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import Http404, FileResponse
from django.core.paginator import Paginator
from django.conf import settings
import os
import mimetypes
import logging

logger = logging.getLogger(__name__)


def homepage(request):
    """
    Inspirational Guidance homepage
    Sections:
    - 4 latest products at the top
    - 2 featured products (middle section)
    - Live With Purpose category (4 items)
    - Printable Planner Inserts category (4 items)
    - Blog posts (3 latest)
    - Random reviews
    """

    # --- Latest 4 products ---
    base_products = Product.objects.filter(
        is_active=True, status__in=["publish", "soon", "full"]
    ).order_by("order", "-created")
    latest_products = base_products[:4]
    latest_ids = latest_products.values_list("id", flat=True)

    # --- Featured 2 products ---
    featured_products = Product.objects.filter(
        featured=True, is_active=True, status="publish"
    ).order_by("order", "-created")[:2]

    # --- Category-based sections ---
    live_with_purpose = Product.objects.filter(
        category__slug="live-with-purpose", is_active=True, status="publish"
    ).order_by("order", "-created")[:4]

    guides = Product.objects.filter(
        category__slug="guides", is_active=True, status="publish"
    ).order_by("order", "-created")[:4]

    # --- Remaining products (not currently shown but kept for pagination) ---
    remaining_products = base_products.exclude(id__in=latest_ids)
    paginator = Paginator(remaining_products, 8)
    page = request.GET.get("page")
    products = paginator.get_page(page)

    # --- Reviews and Blog posts ---
    reviews = ProductReview.objects.select_related("product", "user").order_by("?")[:3]
    blog_posts = Post.objects.filter(
        publish_date__lte=now(), status="published"
    ).order_by("-publish_date")[:3]

    return render(
        request,
        "core/homepage.html",
        {
            "latest_products": latest_products,
            "featured_products": featured_products,
            "live_with_purpose": live_with_purpose,
            "guides": guides,
            "products": products,
            "reviews": reviews,
            "blog_posts": blog_posts,
        },
    )


def about(request):
    products = Product.objects.filter(featured=True, is_active=True, status="publish")[
        :4
    ]
    featured_product = Product.objects.filter(
        featured=True,
        is_active=True,
        status="publish",
    ).first()
    return render(
        request,
        "core/personal-development.html",
        {
            "products": products,
            "featured_product": featured_product,
        },
    )


@login_required
def support_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            # Save to the database only (admin area)
            SupportMessage.objects.create(
                name=form.cleaned_data["name"],
                email=form.cleaned_data["email"],
                subject=form.cleaned_data["subject"],
                message=form.cleaned_data["message"],
            )

            messages.success(
                request, "Thank you for your message. We'll respond within 24 hours."
            )
            return redirect("support")
    else:
        form = ContactForm()

    return render(request, "core/support.html", {"form": form})


def handler500(request):
    return render(request, "error/500.html", status=500)


def handler403(request, exception):
    return render(request, "error/403.html", status=403)


def handler404(request, exception):
    # Define which category to show (by slug)
    category_slug = "choose-yourself"  # Change this to your desired category slug

    try:
        # Try to get the category
        category = get_object_or_404(Category, slug=category_slug)

        # Get posts from the category
        category_posts = Post.objects.filter(
            category=category, status="published", publish_date__lte=timezone.now()
        ).order_by("-publish_date")[:4]

    except Http404:
        # Fallback to recent posts if category doesn't exist
        category_posts = Post.objects.filter(
            status="published", publish_date__lte=timezone.now()
        ).order_by("-publish_date")[:3]
        category = None

    context = {"category_posts": category_posts, "selected_category": category}

    return render(request, "error/404.html", context, status=404)


@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /shop/secure-download/",
        "Disallow: /media/secure_downloads/",
        # Raw member/blog/preview files are publicly served but are not pages;
        # keep bots from discovering them and inflating "not indexed" counts.
        "Disallow: /media/member_resources/",
        "Disallow: /media/news/resources/",
        "Disallow: /media/public/products/previews/",
        "Allow: /",
        "",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


# Free lead-magnet PDFs shown on the public /personal-development-resources page.
# They physically live in media/member_resources/ (which Caddy blocks from direct
# access so member-only resources stay gated), but these specific files are meant
# to be public. This no-login view streams them server-side, so the files never
# move and the gating on everything else is untouched. Whitelisted by exact
# filename so a gated resource can never be served here.
PUBLIC_FREEBIE_FILES = frozenset(
    {
        "clarify-your-values-your-life-your-way.pdf",
        "emotional-resilience-pause-framework.pdf",
        "empowering-questions-for-self-confidence.pdf",
        "find-your-purpose-live-with-purpose.pdf",
        "getting-started-inspirational-guidance2.pdf",
        "mental-fitness-starter-kit.pdf",
        "mind-over-matter-empowered-living.pdf",
        "momentum-tracker-free-pdf-inspirational-guidance_1.pdf",
        "small-steps-to-realignment.pdf",
        "small-steps-vs-micro-habits.pdf",
    }
)


@require_GET
def public_freebie_download(request, filename):
    # basename guards against path traversal; whitelist limits to public freebies.
    name = os.path.basename(filename)
    if name not in PUBLIC_FREEBIE_FILES:
        raise Http404("Resource not found.")

    file_path = os.path.join(settings.MEDIA_ROOT, "member_resources", name)
    if not os.path.exists(file_path):
        logger.error("Public freebie missing on disk: %s", file_path)
        raise Http404("File could not be found.")

    content_type, _ = mimetypes.guess_type(file_path)
    content_type = content_type or "application/octet-stream"
    response = FileResponse(open(file_path, "rb"), content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{name}"'
    return response


def quietly_you_page(request):
    # Blog logic only
    news_categories = NewsCategory.objects.filter(slug__in=["quietly-you"])
    posts = Post.objects.filter(
        category__in=news_categories, status="published"
    ).order_by("-publish_date")[:6]

    return render(
        request,
        "core/quietly-you.html",
        {
            "posts": posts,
            "category_slugs": ["quietly-you"],
        },
    )


def diane_corriette_page(request):
    # Blog logic only
    news_categories = NewsCategory.objects.filter(slug__in=["diane-corriette"])
    posts = Post.objects.filter(
        category__in=news_categories, status="published"
    ).order_by("-publish_date")[:9]

    return render(
        request,
        "core/diane-corriette.html",
        {
            "posts": posts,
            "category_slugs": ["diane-corriette"],
        },
    )


def my_turn_now_page(request):
    return render(
        request,
        "core/my-turn-now.html",
        {},
    )


def category_hub(request):
    return render(request, "core/category.html")
