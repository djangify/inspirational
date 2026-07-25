from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from shop.cart import Cart
from django.conf import settings
from .models import Post, Category
from django.utils import timezone


def latest_published_posts(limit=3):
    """Most recent published posts — reused by homepage and dashboard."""
    return (
        Post.objects.filter(status="published", publish_date__lte=timezone.now())
        .select_related("category")
        .order_by("-publish_date")[:limit]
    )


def browse_categories():
    """Published-post categories with counts, for the sidebar browse list."""
    return (
        Category.objects.annotate(
            num_posts=Count(
                "post",
                filter=Q(
                    post__status="published",
                    post__publish_date__lte=timezone.now(),
                ),
            )
        )
        .filter(num_posts__gt=0)
        .order_by("name")
    )


# Format sections — map the ?type= slug to content_type values.
# Anything NOT listed here is treated as a Tag slug (topic) instead.
FORMAT_FILTERS = {
    "writing": ["article"],
    "bites":   ["bite"],
    "video":   ["video"],
    "audio":   ["audio"],
}

# Tab definitions for templates — (label, type_value).
# "choices" and "updates" are Tag slugs; any other tab whose slug is a Tag
# slug will filter by topic automatically.
SECTION_TABS = [
    ("All",       None),
    ("Audio",     "audio"),
    ("Bites",     "bites"),
    ("Choices",   "choices"),
    ("Alive",     "alive"),
    ("Updates",   "updates"),
    ("Videos",    "video"),
    ("Writing",   "writing"),
]


def news_list(request):
    active_type = request.GET.get("type", "").strip().lower() or None
    query = request.GET.get("q", "").strip()

    qs = Post.objects.filter(
        status="published", publish_date__lte=timezone.now()
    ).select_related("category")

    # Apply the active tab filter: format tabs filter by content_type,
    # everything else is treated as a topic Tag slug.
    if active_type:
        if active_type in FORMAT_FILTERS:
            qs = qs.filter(content_type__in=FORMAT_FILTERS[active_type])
        elif Category.objects.filter(slug=active_type).exists():
            # Tab slug matches a Category (e.g. "alive" = Alive List) — filter by topic.
            qs = qs.filter(category__slug=active_type)
        else:
            qs = qs.filter(tags__slug=active_type).distinct()

    # Keyword search across title and body
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(content__icontains=query))

    qs = qs.order_by("-publish_date")

    # Featured hero posts — only on the "All" tab and when not searching
    if active_type is None and not query:
        featured_posts = list(qs.filter(featured=True)[:5])
        featured_ids = [p.id for p in featured_posts]
        regular_posts = qs.exclude(id__in=featured_ids)
    else:
        featured_posts = []
        regular_posts = qs

    paginator = Paginator(regular_posts, 12)
    page = request.GET.get("page")
    posts_page = paginator.get_page(page)

    context = {
        "posts": posts_page,
        "categories": browse_categories(),
        "featured_posts": featured_posts,
        "active_type": active_type,
        "query": query,
        "total_results": paginator.count,
        "section_tabs": SECTION_TABS,
        "title": "Blog",
        "meta_description": "Latest posts from Inspirational Guidance",
        "debug": settings.DEBUG,
    }
    response = render(request, "news/list.html", context)
    response["X-PWA-Cacheable"] = "1"  # allow offline reading (PWA)
    return response


def category_list(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(
        category=category, status="published", publish_date__lte=timezone.now()
    ).order_by("-publish_date")

    context = {
        "category": category,
        "posts": posts,
        "categories": browse_categories(),
        "title": f"{category.name} - Blog",
        "meta_description": f"Latest posts about {category.name} from Inspirational Guidance",
    }
    response = render(request, "news/category.html", context)
    response["X-PWA-Cacheable"] = "1"  # allow offline reading (PWA)
    return response


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
        "categories": browse_categories(),
        "title": post.meta_title or post.title,
        "meta_description": post.meta_description,
        "meta_keywords": post.meta_keywords,
        "user": request.user,
        "cart": Cart(request),
    }
    response = render(request, "news/detail.html", context)
    is_preview = request.user.is_staff and request.GET.get("preview") == "1"
    if not is_preview:
        response["X-PWA-Cacheable"] = "1"  # allow offline reading (PWA)
    return response
