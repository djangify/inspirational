"""MCP tool implementations for Inspirational Guidance.

Thin, safe wrappers over the site's own Django models. The write tools cover the
blog (the ``news.Post`` model) — create, edit and SEO — plus read helpers so
Claude can see what already exists and which categories/tags are valid.

FastMCP calls sync tool functions on the event loop, and Django's ORM refuses to
run there. So each tool is an ``async`` wrapper that pushes the real ORM work
onto a thread via ``sync_to_async``; the ``_impl`` functions below are ordinary
synchronous Django code and are what a test suite would call directly.
"""

import time
from datetime import datetime
from typing import Any

from asgiref.sync import sync_to_async

# Field limits mirrored from news.models.Post so we fail with a clear message
# instead of a truncated save or a database error.
TITLE_MAX = 200
META_TITLE_MAX = 60
META_DESCRIPTION_MAX = 160
META_KEYWORDS_MAX = 255

VALID_STATUS = {"draft", "published"}
VALID_CONTENT_TYPES = {"article", "alive", "bite", "video", "audio"}


# ---------------------------------------------------------------------------
# Call logging (best-effort — never breaks a tool call)
# ---------------------------------------------------------------------------
def _ms(start: float) -> int:
    return int((time.monotonic() - start) * 1000)


def _write_log_sync(tool, ok, owner_id, client_id, args_summary, error, duration_ms):
    try:
        from django.contrib.auth import get_user_model

        from mcp_server.models import MCPCallLog

        owner = None
        if owner_id:
            owner = get_user_model().objects.filter(pk=owner_id).first()
        MCPCallLog.objects.create(
            tool=tool,
            ok=ok,
            owner=owner,
            client_id=(client_id or "")[:100],
            args_summary=(args_summary or "")[:500],
            error=(error or "")[:5000],
            duration_ms=duration_ms,
        )
    except Exception:
        # Logging must never take down a tool call.
        pass


async def _record(tool, ok, args_summary="", error="", duration_ms=None):
    owner_id = None
    client_id = ""
    try:
        from mcp.server.auth.middleware.auth_context import get_access_token

        token = get_access_token()
        if token is not None:
            client_id = token.client_id or ""
            if token.subject:
                try:
                    owner_id = int(token.subject)
                except (TypeError, ValueError):
                    owner_id = None
    except Exception:
        pass
    await sync_to_async(_write_log_sync, thread_sensitive=True)(
        tool, ok, owner_id, client_id, args_summary, error, duration_ms
    )


class ToolInputError(ValueError):
    """Raised for bad tool input; surfaced to the caller as a clear message."""


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


async def _run(tool_name: str, impl, args_summary="", *args, **kwargs):
    """Shared async runner: push ORM work to a thread, log success/failure."""
    start = time.monotonic()
    try:
        result = await sync_to_async(impl, thread_sensitive=True)(*args, **kwargs)
    except Exception as exc:
        await _record(tool_name, False, args_summary=args_summary, error=str(exc), duration_ms=_ms(start))
        raise
    await _record(tool_name, True, args_summary=args_summary, duration_ms=_ms(start))
    return _jsonable(result)


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------
def _post_brief(post) -> dict:
    return {
        "id": post.id,
        "title": post.title,
        "slug": post.slug,
        "status": post.status,
        "content_type": post.content_type,
        "featured": post.featured,
        "category": post.category.name if post.category_id else None,
        "publish_date": post.publish_date,
        "updated": post.updated,
        "url": post.get_absolute_url(),
    }


def _post_full(post) -> dict:
    data = _post_brief(post)
    data.update(
        {
            "content": post.content,
            "tags": list(post.tags.values_list("name", flat=True)),
            "meta_title": post.meta_title,
            "meta_description": post.meta_description,
            "meta_keywords": post.meta_keywords,
            "video_url": post.video_url,
            "audio_url": post.audio_url,
            "youtube_url": post.youtube_url,
            "created": post.created,
            "content_updated": post.content_updated,
        }
    )
    return data


def _resolve_category(value):
    """Resolve a category by id, slug or (case-insensitive) name. Never creates."""
    from news.models import Category

    if value is None or value == "":
        raise ToolInputError("A category is required. Use list_categories to see the options.")
    qs = Category.objects.all()
    if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
        cat = qs.filter(pk=int(value)).first()
        if cat:
            return cat
    if isinstance(value, str):
        cat = qs.filter(slug__iexact=value).first() or qs.filter(name__iexact=value).first()
        if cat:
            return cat
    available = ", ".join(qs.values_list("name", flat=True)) or "(none defined yet)"
    raise ToolInputError(
        f"No category matched '{value}'. Available categories: {available}. "
        "Create the category in the admin first if it's new."
    )


def _apply_tags(post, tags):
    """Set a post's tags from a list of names (get-or-create each)."""
    from news.models import Tag

    resolved = []
    for name in tags:
        name = (name or "").strip()
        if not name:
            continue
        tag = Tag.objects.filter(name__iexact=name).first()
        if tag is None:
            tag = Tag.objects.create(name=name)
        resolved.append(tag)
    post.tags.set(resolved)


# ---------------------------------------------------------------------------
# get_site_overview
# ---------------------------------------------------------------------------
def _site_overview_impl() -> dict:
    from django.conf import settings

    from news.models import Category, Post, Tag

    recent = [_post_brief(p) for p in Post.objects.select_related("category")[:10]]
    return {
        "site": getattr(settings, "SITE_URL", ""),
        "posts": {
            "total": Post.objects.count(),
            "published": Post.objects.filter(status="published").count(),
            "draft": Post.objects.filter(status="draft").count(),
        },
        "categories": list(Category.objects.values_list("name", flat=True)),
        "tags": list(Tag.objects.values_list("name", flat=True)),
        "recent_posts": recent,
    }


async def get_site_overview() -> dict:
    """Overview of the blog: post counts (total/published/draft), the list of
    categories and tags, and the 10 most recent posts with their IDs. Start here
    to see what exists and get the IDs the other tools need. Read-only."""
    return await _run("get_site_overview", _site_overview_impl)


# ---------------------------------------------------------------------------
# list_categories / list_tags
# ---------------------------------------------------------------------------
def _list_categories_impl() -> dict:
    from news.models import Category

    return {
        "categories": [
            {"id": c.id, "name": c.name, "slug": c.slug} for c in Category.objects.all()
        ]
    }


async def list_categories() -> dict:
    """List every blog category (id, name, slug). Categories are required when
    creating a post and are not created automatically. Read-only."""
    return await _run("list_categories", _list_categories_impl)


def _list_tags_impl() -> dict:
    from news.models import Tag

    return {"tags": [{"id": t.id, "name": t.name, "slug": t.slug} for t in Tag.objects.all()]}


async def list_tags() -> dict:
    """List every blog tag/topic (id, name, slug). Read-only."""
    return await _run("list_tags", _list_tags_impl)


# ---------------------------------------------------------------------------
# list_posts
# ---------------------------------------------------------------------------
def _list_posts_impl(status=None, category=None, search=None, limit=20) -> dict:
    from news.models import Post

    qs = Post.objects.select_related("category").all()
    if status:
        if status not in VALID_STATUS:
            raise ToolInputError(f"status must be one of {sorted(VALID_STATUS)}.")
        qs = qs.filter(status=status)
    if category:
        cat = _resolve_category(category)
        qs = qs.filter(category=cat)
    if search:
        qs = qs.filter(title__icontains=search)
    try:
        limit = max(1, min(int(limit), 100))
    except (TypeError, ValueError):
        limit = 20
    return {"posts": [_post_brief(p) for p in qs[:limit]]}


async def list_posts(
    status: str | None = None,
    category: str | None = None,
    search: str | None = None,
    limit: int = 20,
) -> dict:
    """List blog posts (newest first) with their IDs. Optionally filter by
    ``status`` ("draft" or "published"), by ``category`` (name/slug/id), or by a
    ``search`` term matched against the title. ``limit`` defaults to 20 (max
    100). Read-only."""
    return await _run(
        "list_posts",
        _list_posts_impl,
        f"status={status} category={category} search={search}",
        status=status,
        category=category,
        search=search,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# get_post
# ---------------------------------------------------------------------------
def _get_post_impl(post_id=None, slug=None) -> dict:
    from news.models import Post

    post = None
    if post_id:
        post = Post.objects.select_related("category").filter(pk=post_id).first()
    elif slug:
        post = Post.objects.select_related("category").filter(slug=slug).first()
    else:
        raise ToolInputError("Provide either post_id or slug.")
    if post is None:
        raise ToolInputError("No post found for that post_id/slug.")
    return _post_full(post)


async def get_post(post_id: int | None = None, slug: str | None = None) -> dict:
    """Get one blog post in full — content, tags, SEO fields and media — by
    ``post_id`` (preferred) or by ``slug``. Read-only."""
    return await _run("get_post", _get_post_impl, f"post_id={post_id} slug={slug}", post_id=post_id, slug=slug)


# ---------------------------------------------------------------------------
# create_post
# ---------------------------------------------------------------------------
def _create_post_impl(
    title,
    content,
    category,
    status="draft",
    content_type="article",
    tags=None,
    featured=False,
    meta_title="",
    meta_description="",
    meta_keywords="",
    video_url="",
    audio_url="",
    youtube_url="",
) -> dict:
    from news.models import Post

    title = (title or "").strip()
    if not title:
        raise ToolInputError("title is required.")
    if len(title) > TITLE_MAX:
        raise ToolInputError(f"title is {len(title)} chars; max is {TITLE_MAX}.")
    if not (content or "").strip():
        raise ToolInputError("content is required.")
    if status not in VALID_STATUS:
        raise ToolInputError(f"status must be one of {sorted(VALID_STATUS)}.")
    if content_type not in VALID_CONTENT_TYPES:
        raise ToolInputError(f"content_type must be one of {sorted(VALID_CONTENT_TYPES)}.")
    for name, val, cap in (
        ("meta_title", meta_title, META_TITLE_MAX),
        ("meta_description", meta_description, META_DESCRIPTION_MAX),
        ("meta_keywords", meta_keywords, META_KEYWORDS_MAX),
    ):
        if val and len(val) > cap:
            raise ToolInputError(f"{name} is {len(val)} chars; max is {cap}.")

    cat = _resolve_category(category)

    post = Post(
        title=title,
        content=content,
        category=cat,
        status=status,
        content_type=content_type,
        featured=bool(featured),
        meta_title=meta_title or "",
        meta_description=meta_description or "",
        meta_keywords=meta_keywords or "",
        video_url=video_url or "",
        audio_url=audio_url or "",
        youtube_url=youtube_url or "",
    )
    post.save()  # save() fills slug + publish_date on publish
    if tags:
        _apply_tags(post, tags)
    post.refresh_from_db()
    return _post_full(post)


async def create_post(
    title: str,
    content: str,
    category: str,
    status: str = "draft",
    content_type: str = "article",
    tags: list[str] | None = None,
    featured: bool = False,
    meta_title: str = "",
    meta_description: str = "",
    meta_keywords: str = "",
    video_url: str = "",
    audio_url: str = "",
    youtube_url: str = "",
) -> dict:
    """Create a new blog post.

    ``content`` is HTML (the blog uses a rich-text field). ``category`` is
    required — pass a name/slug/id that already exists (see list_categories;
    categories are not auto-created). ``status`` defaults to "draft" so nothing
    goes live until you set it to "published". ``content_type`` is one of
    article, alive, bite, video, audio. ``tags`` is a list of topic names
    (created if missing). The slug is generated from the title. Returns the
    created post including its new id and URL."""
    return await _run(
        "create_post",
        _create_post_impl,
        f"title={title!r} status={status}",
        title=title,
        content=content,
        category=category,
        status=status,
        content_type=content_type,
        tags=tags,
        featured=featured,
        meta_title=meta_title,
        meta_description=meta_description,
        meta_keywords=meta_keywords,
        video_url=video_url,
        audio_url=audio_url,
        youtube_url=youtube_url,
    )


# ---------------------------------------------------------------------------
# update_post
#
# Any argument left as None means "leave this field unchanged" (matching the
# rest of the connector). To clear a text field, pass an empty string "". For
# ``tags``, None leaves them alone; an empty list clears all tags.
# ---------------------------------------------------------------------------
def _update_post_impl(
    post_id,
    title=None,
    content=None,
    category=None,
    status=None,
    content_type=None,
    tags=None,
    featured=None,
    meta_title=None,
    meta_description=None,
    meta_keywords=None,
    video_url=None,
    audio_url=None,
    youtube_url=None,
) -> dict:
    from news.models import Post

    post = Post.objects.filter(pk=post_id).first()
    if post is None:
        raise ToolInputError("No post found for that post_id.")

    fields: list[str] = []

    if title is not None:
        title = title.strip()
        if not title:
            raise ToolInputError("title cannot be blank.")
        if len(title) > TITLE_MAX:
            raise ToolInputError(f"title is {len(title)} chars; max is {TITLE_MAX}.")
        post.title = title
        fields.append("title")
    if content is not None:
        if not content.strip():
            raise ToolInputError("content cannot be blank.")
        post.content = content
        fields.append("content")
    if category is not None:
        post.category = _resolve_category(category)
        fields.append("category")
    if status is not None:
        if status not in VALID_STATUS:
            raise ToolInputError(f"status must be one of {sorted(VALID_STATUS)}.")
        post.status = status
        fields.append("status")
    if content_type is not None:
        if content_type not in VALID_CONTENT_TYPES:
            raise ToolInputError(f"content_type must be one of {sorted(VALID_CONTENT_TYPES)}.")
        post.content_type = content_type
        fields.append("content_type")
    if featured is not None:
        post.featured = bool(featured)
        fields.append("featured")
    for name, val, cap in (
        ("meta_title", meta_title, META_TITLE_MAX),
        ("meta_description", meta_description, META_DESCRIPTION_MAX),
        ("meta_keywords", meta_keywords, META_KEYWORDS_MAX),
    ):
        if val is not None:
            if len(val) > cap:
                raise ToolInputError(f"{name} is {len(val)} chars; max is {cap}.")
            setattr(post, name, val)
            fields.append(name)
    for name, val in (
        ("video_url", video_url),
        ("audio_url", audio_url),
        ("youtube_url", youtube_url),
    ):
        if val is not None:
            setattr(post, name, val)
            fields.append(name)

    if not fields and tags is None:
        raise ToolInputError("Nothing to update — pass at least one field.")

    if fields:
        post.save()  # full save so slug/publish_date logic runs
    if tags is not None:
        _apply_tags(post, tags)
        fields.append("tags")

    post.refresh_from_db()
    result = _post_full(post)
    result["updated_fields"] = fields
    return result


async def update_post(
    post_id: int,
    title: str | None = None,
    content: str | None = None,
    category: str | None = None,
    status: str | None = None,
    content_type: str | None = None,
    tags: list[str] | None = None,
    featured: bool | None = None,
    meta_title: str | None = None,
    meta_description: str | None = None,
    meta_keywords: str | None = None,
    video_url: str | None = None,
    audio_url: str | None = None,
    youtube_url: str | None = None,
) -> dict:
    """Update an existing blog post. Pass ``post_id`` plus only the fields you
    want to change — anything left as None is untouched. Set ``status`` to
    "published" to publish a draft (the publish date is filled automatically).
    ``tags`` replaces the whole tag list (an empty list clears them). To clear a
    text field pass an empty string. Returns the updated post and which fields
    changed."""
    return await _run(
        "update_post",
        _update_post_impl,
        f"post_id={post_id}",
        post_id,
        title=title,
        content=content,
        category=category,
        status=status,
        content_type=content_type,
        tags=tags,
        featured=featured,
        meta_title=meta_title,
        meta_description=meta_description,
        meta_keywords=meta_keywords,
        video_url=video_url,
        audio_url=audio_url,
        youtube_url=youtube_url,
    )


# ---------------------------------------------------------------------------
# update_post_seo
# ---------------------------------------------------------------------------
def _update_post_seo_impl(post_id, meta_title=None, meta_description=None, meta_keywords=None) -> dict:
    from news.models import Post

    if meta_title is None and meta_description is None and meta_keywords is None:
        raise ToolInputError("Provide meta_title, meta_description and/or meta_keywords — nothing to update.")

    post = Post.objects.filter(pk=post_id).first()
    if post is None:
        raise ToolInputError("No post found for that post_id.")

    fields: list[str] = []
    for name, val, cap in (
        ("meta_title", meta_title, META_TITLE_MAX),
        ("meta_description", meta_description, META_DESCRIPTION_MAX),
        ("meta_keywords", meta_keywords, META_KEYWORDS_MAX),
    ):
        if val is not None:
            val = val.strip()
            if len(val) > cap:
                raise ToolInputError(f"{name} is {len(val)} chars; max is {cap}.")
            setattr(post, name, val)
            fields.append(name)

    post.save(update_fields=fields)
    return {"id": post.id, "title": post.title, "updated_fields": fields}


async def update_post_seo(
    post_id: int,
    meta_title: str | None = None,
    meta_description: str | None = None,
    meta_keywords: str | None = None,
) -> dict:
    """Update just the SEO fields on one blog post: ``meta_title`` (<=60),
    ``meta_description`` (<=160), ``meta_keywords`` (comma-separated, <=255).
    Pass only the ones you want to change."""
    return await _run(
        "update_post_seo",
        _update_post_seo_impl,
        f"post_id={post_id}",
        post_id,
        meta_title,
        meta_description,
        meta_keywords,
    )
