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
from django.http import Http404
from django.core.paginator import Paginator


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
    ).order_by("-created")
    latest_products = base_products[:4]
    latest_ids = latest_products.values_list("id", flat=True)

    # --- Featured 2 products ---
    featured_products = Product.objects.filter(
        featured=True, is_active=True, status="publish"
    ).order_by("order", "-created")[:2]

    # --- Category-based sections ---
    live_with_purpose = Product.objects.filter(
        category__slug="live-with-purpose", is_active=True, status="publish"
    ).order_by("-created")[:4]

    planner_inserts = Product.objects.filter(
        category__slug="printable-planner-inserts", is_active=True, status="publish"
    ).order_by("-created")[:4]

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
            "planner_inserts": planner_inserts,
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
    category_slug = "momentum"  # Change this to your desired category slug

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
        "Allow: /",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


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
    news_category = get_object_or_404(NewsCategory, slug="my-turn-now")
    shop_category = get_object_or_404(ShopCategory, slug="my-turn-now")

    posts = Post.objects.filter(category=news_category, status="published").order_by(
        "-publish_date"
    )[:6]
    products = Product.objects.filter(category=shop_category, is_active=True).order_by(
        "-created"
    )[:8]

    return render(
        request,
        "core/my-turn-now.html",
        {
            "posts": posts,
            "products": products,
            "category": news_category,
            "shop_category": shop_category,
        },
    )


def category_hub(request):
    categories = Category.objects.all()
    return render(request, "core/category.html", {"categories": categories})
