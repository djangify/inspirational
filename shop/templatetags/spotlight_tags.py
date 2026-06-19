"""
Template tags used by the Spotlight theme.

Read-only helpers that surface featured and recent products for the
Spotlight shop layout. They mirror the visibility filter used by the
shop product_list view (is_active + published-ish status) so the rows
never show drafts or inactive items.
"""

from django import template

from shop.models import Product

register = template.Library()

# Same statuses the product_list view treats as publicly visible.
VISIBLE_STATUSES = ["publish", "soon", "full"]


@register.simple_tag
def featured_products(count=4):
    """Return up to `count` products flagged as featured (shown large)."""
    return list(
        Product.objects.filter(
            is_active=True,
            status__in=VISIBLE_STATUSES,
            featured=True,
        ).order_by("order", "-created")[:count]
    )


@register.simple_tag
def recent_products(count=4):
    """
    Return the most recently created visible products, EXCLUDING any that
    are featured — so a featured product never also appears in the latest row.
    """
    return list(
        Product.objects.filter(
            is_active=True,
            status__in=VISIBLE_STATUSES,
            featured=False,
        ).order_by("-created")[:count]
    )
