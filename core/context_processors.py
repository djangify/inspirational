# core/context_processors.py

from django.conf import settings


def site_author(request):
    """
    Injects site-wide author and social constants into every template context.
    Used by the author bio box on article pages and by JSON-LD schema blocks.
    """
    return {
        "author_name": settings.AUTHOR_NAME,
        "author_short_bio": settings.AUTHOR_SHORT_BIO,
        "author_photo": settings.AUTHOR_PHOTO,
        "author_url": settings.AUTHOR_URL,
        "social_youtube": settings.SOCIAL_YOUTUBE,
        "social_pinterest": settings.SOCIAL_PINTEREST,
        "social_substack": settings.SOCIAL_SUBSTACK,
        "social_substack_profile": settings.SOCIAL_SUBSTACK_PROFILE,
        "site_name": settings.SITE_NAME,
        "site_url": settings.SITE_URL,
    }
