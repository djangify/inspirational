from django import template
import re

register = template.Library()


@register.filter
def youtube_id(url):
    """
    Extract YouTube video ID from common formats.
    """
    if not url:
        return ""
    patterns = [
        r"youtu\.be/([^\?&]+)",
        r"youtube\.com/watch\?v=([^\?&]+)",
        r"youtube\.com/embed/([^\?&]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""
