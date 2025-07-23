from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm
from .models import SupportMessage
from django.contrib.auth.decorators import login_required
from shop.models import Product, ProductReview
from news.models import Post
from django.utils.timezone import now


def homepage(request):
    products = Product.objects.filter(featured=True, is_active=True, status="publish")[
        :4
    ]

    reviews = ProductReview.objects.select_related("product", "user").order_by("?")[:3]
    blog_posts = Post.objects.filter(publish_date__lte=now()).order_by("-publish_date")[
        :3
    ]
    featured_product = Product.objects.filter(
        featured=True, is_active=True, status="publish"
    ).first()
    return render(
        request,
        "core/homepage.html",
        {
            "products": products,
            "reviews": reviews,
            "blog_posts": blog_posts,
            "featured_product": featured_product,
        },
    )


def privacy_view(request):
    template_name = "policy/privacy.html"
    return render(request, template_name)


def terms_view(request):
    template_name = "policy/terms-conditions.html"
    return render(request, template_name)


def cookie_view(request):
    template_name = "policy/cookies.html"
    return render(request, template_name)


def content_view(request):
    template_name = "policy/contents.html"
    return render(request, template_name)


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
