from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from shop.cart import Cart
from django.conf import settings
from .models import Post, Category
from django.utils import timezone


# Maps the ?type= query param to content_type values
SECTION_FILTERS = {
    "writing": ["article", "bite"],
    "video":   ["video"],
    "audio":   ["audio"],
}

# Tab definitions for templates — (label, type_value)
SECTION_TABS = [
    ("All",     None),
    ("Writing", "writing"),
    ("Videos",  "video"),
    ("Audio",   "audio"),
]


def news_list(request):
    active_type = request.GET.get("type", "").strip().lower() or None

    qs = Post.objects.filter(
        status="published", publish_date__lte=timezone.now()
    ).select_related("category")

    # Apply content-type filter when a tab is active
    if active_type and active_type in SECTION_FILTERS:
        qs = qs.filter(content_type__in=SECTION_FILTERS[active_type])

    qs = qs.order_by("-publish_date")

    # Featured hero posts — only on the "All" tab
    if active_type is None:
        featured_posts = list(qs.filter(featured=True)[:5])
        featured_ids = [p.id for p in featured_posts]
        regular_posts = qs.exclude(id__in=featured_ids)
    else:
        featured_posts = []
        regular_posts = qs

    paginator = Paginator(regular_posts, 33)
    page = request.GET.get("page")
    posts_page = paginator.get_page(page)

    context = {
        "posts": posts_page,
        "categories": Category.objects.all(),
        "featured_posts": featured_posts,
        "active_type": active_type,
        "section_tabs": SECTION_TABS,
        "title": "Blog",
        "meta_description": "Latest posts from Inspirational Guidance",
        "debug": settings.DEBUG,
    }
    return render(request, "news/list.html", context)


def category_list(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(
        category=category, status="published", publish_date__lte=timezone.now()
    ).order_by("-publish_date")

    context = {
        "category": category,
        "posts": posts,
        "categories": Category.objects.all(),
        "title": f"{category.name} - Blog",
        "meta_description": f"Latest posts about {category.name} from Inspirational Guidance",
    }
    return render(request, "news/category.html", context)


def post_detail(request, slug):
    if request.user.is_staff and request.GET.get("preview") == "1":
        post = get_object_or_404(Post, slug=slug)
    else:
        post = get_object_or_404(
            Post, slug=slug, status="published", publish_date__lte=timezone.now()
        )

    next_post = (
        Post.objects.filter(
            status="published",
            publish_date__lte=timezone.now(),
            publish_date__gt=post.publish_date,
        )
        .order_by("publish_date")
        .first()
    )

    previous_post = (
        Post.objects.filter(
            status="published",
            publish_date__lte=timezone.now(),
            publish_date__lt=post.publish_date,
        )
        .order_by("-publish_date")
        .first()
    )

    related_posts = (
        Post.objects.filter(
            status="published", publish_date__lte=timezone.now(), category=post.category
        )
        .exclude(id=post.id)
        .select_related("category")[:8]
    )

    context = {
        "post": post,
        "next_post": next_post,
        "previous_post": previous_post,
        "related_posts": related_posts,
        "categories": Category.objects.all(),
        "title": post.meta_title or post.title,
        "meta_description": post.meta_description,
        "meta_keywords": post.meta_keywords,
        "user": request.user,
        "cart": Cart(request),
    }
    return render(request, "news/detail.html", context)
