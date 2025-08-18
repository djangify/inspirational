from django.utils.text import slugify as django_slugify
import re


def sanitize_text(text):
    """Sanitize text for latin1 compatibility while preserving meaning"""
    if not isinstance(text, str):
        return text

    replacements = {
        '"': '"',  # Smart quotes to straight quotes
        """: "'",  # Smart apostrophes to straight
        """: "'",
        "…": "...",  # Ellipsis
        "–": "-",  # En dash
        "—": "-",  # Em dash
        "•": "*",  # Bullet
        ",": ",",  # Standard comma
        "\u201a": ",",  # Single low-9 quotation mark (looks like comma)
        "\u2039": ",",  # Single left-pointing angle quotation mark
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def custom_slugify(text):
    """Create URL-friendly slugs while preserving apostrophes"""
    text = sanitize_text(text)
    text = re.sub(r"([a-zA-Z])'([a-zA-Z])", r"\1-\2", text)
    return django_slugify(text)
