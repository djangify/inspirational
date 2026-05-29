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
        "site_name": settings.SITE_NAME,
        "site_url": settings.SITE_URL,
    }
