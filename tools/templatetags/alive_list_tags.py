import json

from django import template

from tools.models import AliveListItem

register = template.Library()


@register.simple_tag(takes_context=True)
def alive_list_existing_items_json(context):
    """
    Returns the requesting user's saved ALIVE List items as a JSON string,
    or "[]" for guests. Lets the alive-list-builder component work off a
    plain {% include %} on any page (e.g. the homepage) without that page's
    view needing to pass extra context -- same data the dedicated
    tools:alive_list_builder view already provides its own template.
    """
    request = context.get("request")
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return "[]"

    items = list(
        AliveListItem.objects.filter(user=user).values(
            "id", "item_text", "category", "is_living_it", "order"
        )
    )
    return json.dumps(items)
