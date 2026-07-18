from django import template
from ..models import MemberResource

register = template.Library()


@register.inclusion_tag("partials/public_resources_preview.html", takes_context=True)
def public_resources_preview(context):
    resources = MemberResource.objects.filter(is_active=True).order_by("-created_at")[
        :3
    ]
    return {"resources": resources, "user": context.get("user")}
