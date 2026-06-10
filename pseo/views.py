# pseo/views.py
from django.shortcuts import render, get_object_or_404
from .models import ProgrammaticPage


def programmatic_page_detail(request, slug):
    is_preview = request.GET.get("preview") == "1" and request.user.is_staff

    if is_preview:
        page = get_object_or_404(ProgrammaticPage, slug=slug)
    else:
        page = get_object_or_404(ProgrammaticPage, slug=slug, status="published")

    context = {
        "page": page,
        "title": page.meta_title or page.h1_heading or page.keyword,
        "meta_description": page.meta_description,
    }

    return render(request, "pseo/detail.html", context)
