"""
news/templatetags/news_tags.py

Smart URL-to-embed converter for blog posts with audio/video content.

Supports:
  Video  — YouTube, Vimeo
  Audio  — SoundCloud, Spotify (tracks/episodes/shows),
            Buzzsprout, Anchor / Spotify for Podcasters

Usage in templates:
  {% load news_tags %}
  {% get_embed_url post.video_url as embed %}
  {% if embed %}<iframe src="{{ embed }}" ...></iframe>{% endif %}

  {% video_embed post.video_url %}
  {% audio_embed post.audio_url %}
"""

import re
from django import template
from urllib.parse import urlparse, parse_qs, quote

register = template.Library()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _yt_embed(url: str) -> str | None:
    parsed = urlparse(url)
    vid = None
    if "youtu.be" in parsed.netloc:
        vid = parsed.path.lstrip("/").split("?")[0]
    elif "youtube.com" in parsed.netloc:
        qs = parse_qs(parsed.query)
        vid = qs.get("v", [None])[0]
        if not vid and "/shorts/" in parsed.path:
            vid = parsed.path.split("/shorts/")[1].split("/")[0]
        if not vid and "/embed/" in parsed.path:
            return url
    if vid:
        return f"https://www.youtube.com/embed/{vid}"
    return None


def _vimeo_embed(url: str) -> str | None:
    parsed = urlparse(url)
    if "vimeo.com" not in parsed.netloc:
        return None
    match = re.search(r"/(\d+)", parsed.path)
    if match:
        return f"https://player.vimeo.com/video/{match.group(1)}"
    return None


def _soundcloud_embed(url: str) -> str | None:
    if "soundcloud.com" not in url:
        return None
    encoded = quote(url, safe="")
    return (
        f"https://w.soundcloud.com/player/?url={encoded}"
        "&color=%23ff5500&auto_play=false&hide_related=false"
        "&show_comments=false&show_user=true&show_reposts=false"
        "&show_teaser=false&visual=true"
    )


def _spotify_embed(url: str) -> str | None:
    parsed = urlparse(url)
    if "spotify.com" not in parsed.netloc:
        return None
    path = parsed.path
    if path.startswith("/embed"):
        return url
    parts = path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] in ("track", "episode", "show", "album", "playlist"):
        return f"https://open.spotify.com/embed/{'/'.join(parts)}?utm_source=generator"
    return None


def _buzzsprout_embed(url: str) -> str | None:
    if "buzzsprout.com" not in url:
        return None
    match = re.search(r"buzzsprout\.com/(\d+)/(\d+)", url)
    if match:
        pod_id, ep_id = match.group(1), match.group(2)
        return (
            f"https://www.buzzsprout.com/{pod_id}/{ep_id}"
            "?client_source=small_player&iframe=true"
        )
    match = re.search(r"buzzsprout\.com/(\d+)", url)
    if match:
        return f"https://www.buzzsprout.com/{match.group(1)}?client_source=small_player&iframe=true"
    return None


def _anchor_embed(url: str) -> str | None:
    if "anchor.fm" not in url and "podcasters.spotify.com" not in url:
        return None
    parsed = urlparse(url)
    path = parsed.path
    if "/embed/" in path:
        return url
    if "/episodes/" in path:
        new_path = path.replace("/episodes/", "/embed/episodes/", 1)
        return f"{parsed.scheme}://{parsed.netloc}{new_path}"
    return None


# ── Core resolver ─────────────────────────────────────────────────────────────

DETECTORS = [
    _yt_embed,
    _vimeo_embed,
    _soundcloud_embed,
    _spotify_embed,
    _buzzsprout_embed,
    _anchor_embed,
]


def resolve_embed_url(url: str) -> str | None:
    if not url:
        return None
    url = url.strip()
    for detector in DETECTORS:
        result = detector(url)
        if result:
            return result
    return None


def _is_audio_platform(url: str) -> bool:
    audio_domains = ("soundcloud.com", "buzzsprout.com", "anchor.fm", "podcasters.spotify.com")
    return any(d in url for d in audio_domains)


def _is_spotify_audio(url: str) -> bool:
    if "spotify.com" not in url:
        return False
    return any(k in url for k in ("/episode/", "/show/"))


# ── Template tags & filters ───────────────────────────────────────────────────

@register.simple_tag
def get_embed_url(url):
    """{% get_embed_url post.video_url as embed_url %}"""
    return resolve_embed_url(url) if url else None


@register.filter
def embed_url(url):
    """{{ post.video_url|embed_url }}"""
    return resolve_embed_url(url) if url else None


@register.simple_tag
def audio_embed_url(url):
    """{% audio_embed_url post.audio_url as embed %}"""
    return resolve_embed_url(url) if url else None


@register.filter(name="is_audio_url")
def is_audio_url_filter(url):
    """{{ post.audio_url|is_audio_url }}"""
    if not url:
        return False
    return _is_audio_platform(url) or _is_spotify_audio(url)


@register.inclusion_tag("news/components/video_embed.html")
def video_embed(url, css_class=""):
    """{% video_embed post.video_url %}"""
    embed = resolve_embed_url(url) if url else None
    return {"embed_url": embed, "css_class": css_class}


@register.inclusion_tag("news/components/audio_embed.html")
def audio_embed(url, css_class=""):
    """{% audio_embed post.audio_url %}"""
    embed = resolve_embed_url(url) if url else None
    return {"embed_url": embed, "original_url": url, "css_class": css_class}
