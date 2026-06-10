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
