from .cart import Cart


def cart(request):
    return {'cart': Cart(request)}


def site_settings(request):
    try:
        from .models import SiteSettings
        settings_obj = SiteSettings.objects.first()
    except Exception:
        settings_obj = None
    return {"site_settings": settings_obj}


def sidebar_products(request):
    """
    Inject published products and sidebar heading into every template context.
    Featured products appear first; falls back to all published if none are featured.
    """
    try:
        from .models import Product, SiteSettings
        settings_obj = SiteSettings.objects.first()
        count = settings_obj.sidebar_product_count if settings_obj else 5
        heading = settings_obj.sidebar_heading if settings_obj else "Featured Products"
        # featured first, then fill with other published products
        products = list(
            Product.objects.filter(status="publish")
            .order_by("-featured", "id")[:count]
        )
    except Exception:
        products = []
        heading = "Featured Products"
    return {
        "sidebar_products": products,
        "sidebar_heading": heading,
    }
