"""Generic full-CRUD engine for the Inspirational Guidance MCP connector.

Gives Claude create / read / update / delete over *every* piece of site content
through six generic tools, backed by a registry (``RESOURCES``) that maps a
friendly resource key (e.g. ``product``, ``blog_post``, ``coupon``) to a Django
model plus its writable fields. Reading is automatic (every concrete field is
serialised); writing is whitelisted per resource, so only intended fields can be
set. Adding a new manageable model later is a few lines in ``RESOURCES``.

The six tools:
  * list_resource_types  — discover what can be managed + each resource's fields
  * list_items           — list/search rows of a resource
  * get_item             — read one row in full
  * create_item          — create a row
  * update_item          — edit a row (only the fields you pass)
  * delete_item          — delete a row

File/image fields cannot be set over MCP (uploads happen in the admin); they are
read-only here and shown as their stored path.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from asgiref.sync import sync_to_async

# Reuse the logging + error helpers from the blog tools module.
from mcp_server.tools import ToolInputError, _ms, _record

import time


# ---------------------------------------------------------------------------
# Field spec helper
# ---------------------------------------------------------------------------
def F(type_, required=False, choices=None, model=None, lookup=None, create_missing=False, help=""):
    return {
        "type": type_,
        "required": required,
        "choices": choices,
        "model": model,
        "lookup": lookup or [],
        "create_missing": create_missing,
        "help": help,
    }


AUTH_USER = "AUTH_USER"  # sentinel for the site's user model

M30 = ["30", "60", "90"]


# ---------------------------------------------------------------------------
# The registry — every manageable resource.
# ---------------------------------------------------------------------------
def _resources() -> dict:
    return {
        # ---- Blog (news app) -------------------------------------------------
        "blog_post": {
            "model": "news.Post", "label": "Blog post", "search": ["title", "slug"],
            "fields": {
                "title": F("str", required=True),
                "slug": F("slug", help="Auto-filled from title if blank."),
                "content": F("html", required=True),
                "category": F("fk", required=True, model="news.Category", lookup=["slug", "name"]),
                "status": F("choice", choices=["draft", "published"]),
                "featured": F("bool"),
                "content_type": F("choice", choices=["article", "alive", "bite", "video", "audio"]),
                "tags": F("m2m", model="news.Tag", lookup=["name"], create_missing=True),
                "publish_date": F("datetime"),
                "content_updated": F("datetime"),
                "meta_title": F("str"), "meta_description": F("str"), "meta_keywords": F("str"),
                "video_url": F("str"), "audio_url": F("str"), "youtube_url": F("str"),
                "ad_type": F("choice", choices=["none", "adsense", "banner"]),
                "ad_code": F("text"), "ad_url": F("str"),
                "resource_type": F("choice", choices=["none", "pdf", "worksheet", "guide", "other"]),
                "resource_title": F("str"),
            },
        },
        "blog_category": {
            "model": "news.Category", "label": "Blog category", "search": ["name", "slug"],
            "fields": {"name": F("str", required=True), "slug": F("slug", required=True), "description": F("text")},
        },
        "blog_tag": {
            "model": "news.Tag", "label": "Blog tag/topic", "search": ["name", "slug"],
            "fields": {"name": F("str", required=True), "slug": F("slug")},
        },

        # ---- Shop ------------------------------------------------------------
        "product": {
            "model": "shop.Product", "label": "Shop product", "search": ["title", "slug"],
            "fields": {
                "title": F("str", required=True),
                "slug": F("slug"),
                "category": F("fk", required=True, model="shop.Category", lookup=["slug", "name"]),
                "description": F("html", required=True),
                "section_description": F("text"),
                "long_description": F("html"),
                "product_type": F("choice", choices=["download", "tool"]),
                "number_of_pages": F("int"),
                "status": F("choice", choices=["publish", "soon", "full", "draft"]),
                "is_active": F("bool"),
                "price_pence": F("int", required=True, help="Price in pence, e.g. 700 = £7.00"),
                "sale_price_pence": F("int"),
                "price_per_hour": F("int"),
                "external_image_url": F("str"), "external_preview_url": F("str"),
                "video_url": F("str"),
                "download_limit": F("int"), "featured": F("bool"), "order": F("int"),
                "hosted_tool": F("fk", model="tools.HostedTool", lookup=["slug", "title"]),
            },
        },
        "shop_category": {
            "model": "shop.Category", "label": "Shop category", "search": ["name", "slug"],
            "fields": {"name": F("str", required=True), "slug": F("slug", required=True), "description": F("text")},
        },
        "coupon": {
            "model": "shop.Coupon", "label": "Discount coupon", "search": ["code"],
            "fields": {
                "code": F("str", required=True),
                "discount_type": F("choice", choices=["percentage", "fixed"]),
                "discount_value": F("decimal", required=True, help="e.g. 10 for 10% or 5 for £5"),
                "is_active": F("bool"),
                "valid_from": F("datetime"), "valid_to": F("datetime"),
                "usage_limit": F("int"), "minimum_order_pence": F("int"),
            },
        },
        "order_bump": {
            "model": "shop.OrderBump", "label": "Checkout order bump", "search": ["headline"],
            "fields": {
                "bump_product": F("fk", required=True, model="shop.Product", lookup=["slug", "title"]),
                "trigger_product": F("fk", model="shop.Product", lookup=["slug", "title"]),
                "headline": F("str"), "description": F("text"),
                "is_active": F("bool"), "order": F("int"),
            },
        },
        "review": {
            "model": "shop.ProductReview", "label": "Product review", "search": ["comment"],
            "no_create": True,  # reviews need a real purchasing user; moderate only
            "fields": {"rating": F("int"), "comment": F("text"), "verified_purchase": F("bool")},
        },
        "order": {
            "model": "shop.Order", "label": "Customer order", "search": ["order_id", "email"],
            "no_create": True,  # orders come from checkout, not MCP
            "fields": {
                "status": F("choice", choices=["pending", "completed", "failed", "cancelled"]),
                "paid": F("bool"), "email": F("str"), "coupon_code": F("str"),
            },
        },

        # ---- Settings (singletons) -------------------------------------------
        "site_settings": {
            "model": "shop.SiteSettings", "label": "Site settings", "singleton": True,
            "fields": {
                "google_analytics_id": F("str"), "google_search_console_verification": F("str"),
                "facebook_app_id": F("str"),
                "currency_code": F("choice", choices=["GBP", "USD", "EUR"]),
                "currency_symbol": F("str"),
                "active_theme": F("choice", choices=["classic", "editorial", "minimal", "spotlight"]),
                "sidebar_heading": F("str"), "sidebar_product_count": F("int"),
            },
        },
        "shop_settings": {
            "model": "shop.ShopSettings", "label": "Shop settings", "singleton": True,
            "fields": {
                "show_digital_withdrawal_consent": F("bool"),
                "digital_withdrawal_consent_text": F("str"),
            },
        },
        "one_time_offer": {
            "model": "shop.OneTimeOffer", "label": "One-time offer (tripwire)", "singleton": True,
            "fields": {
                "enabled": F("bool"), "title": F("str"),
                "price_pence": F("int"), "compare_at_pence": F("int"), "download_limit": F("int"),
                "headline": F("str"), "subheadline": F("str"), "body": F("html"),
                "button_text": F("str"), "decline_text": F("str"),
                "show_timer": F("bool"), "timer_minutes": F("int"),
                "included_products": F("m2m", model="shop.Product", lookup=["slug", "title"]),
            },
        },

        # ---- Hosted tools + experiment (tools app) ---------------------------
        "hosted_tool": {
            "model": "tools.HostedTool", "label": "Hosted tool (HTML artifact)", "search": ["title", "slug"],
            "fields": {
                "title": F("str", required=True), "slug": F("slug"),
                "description": F("text"), "link_text": F("str"), "link_url": F("str"),
                "access": F("choice", choices=["free", "paid"]), "published": F("bool"),
            },
            "note": "The .html file itself is uploaded in the admin (not over MCP).",
        },
        "experiment_week": {
            "model": "tools.ExperimentWeek", "label": "Experiment week", "search": ["milestone_label"],
            "fields": {
                "week_date": F("date", required=True), "week_number": F("int", required=True),
                "is_milestone": F("bool"), "milestone_label": F("str"),
                "blog_posts_rewritten": F("int"), "pinterest_pins": F("int"), "youtube_audio": F("int"),
                "substack_posts": F("int"), "emails_added": F("int"), "ga4_sessions": F("int"),
                "what_i_did": F("text"), "what_i_noticed": F("text"), "what_changed": F("text"),
                "went_well_wednesday": F("text"),
                "revenue_this_week": F("decimal"), "transactions": F("int"), "email_list_total": F("int"),
                "is_published": F("bool"),
            },
        },
        "experiment_goal": {
            "model": "tools.ExperimentGoal", "label": "Experiment goal", "search": ["goal_text"],
            "fields": {
                "milestone": F("choice", required=True, choices=M30),
                "goal_text": F("str", required=True), "is_achieved": F("bool"), "order": F("int"),
            },
        },
        "milestone_reflection": {
            "model": "tools.MilestoneReflection", "label": "Milestone reflection", "search": ["reflection_text"],
            "fields": {
                "milestone": F("choice", required=True, choices=M30),
                "reflection_text": F("text", required=True), "published_date": F("date"),
            },
        },

        # ---- AI mentor bots --------------------------------------------------
        "bot": {
            "model": "bots.BotProduct", "label": "AI mentor bot", "search": ["bot_name"],
            "fields": {
                "product": F("fk", required=True, model="shop.Product", lookup=["slug", "title"]),
                "bot_name": F("str", required=True),
                "welcome_message": F("text", required=True),
                "system_prompt": F("text", required=True),
                "message_limit": F("int"), "access_days": F("int"),
                "model": F("choice", choices=["claude-haiku-4-5-20251001", "claude-sonnet-4-5"]),
                "max_tokens": F("int"), "is_active": F("bool"),
            },
        },
        "bot_knowledge": {
            "model": "bots.BotKnowledge", "label": "Bot knowledge file", "search": ["title"],
            "no_create": True,  # the PDF is uploaded in the admin
            "fields": {
                "bot_product": F("fk", model="bots.BotProduct", lookup=["bot_name"]),
                "title": F("str"), "order": F("int"),
            },
            "note": "The PDF file is uploaded in the admin (not over MCP).",
        },

        # ---- Journaling prompts (prompt app) ---------------------------------
        "writing_prompt": {
            "model": "prompt.WritingPrompt", "label": "Journaling prompt", "search": ["text"],
            "fields": {
                "text": F("text", required=True),
                "category": F("fk", required=True, model="prompt.PromptCategory", lookup=["slug", "name"]),
                "difficulty": F("choice", choices=["easy", "medium", "deep"]),
                "prompt_type": F("choice", choices=["journal", "memoir", "both"]),
                "active": F("bool"),
                "tags": F("m2m", model="prompt.Tag", lookup=["name"], create_missing=True),
                "writing_styles": F("m2m", model="prompt.WritingStyle", lookup=["name"]),
            },
        },
        "prompt_category": {
            "model": "prompt.PromptCategory", "label": "Prompt category", "search": ["name", "slug"],
            "fields": {
                "name": F("str", required=True), "slug": F("slug", required=True),
                "description": F("text"), "sub_category": F("str"),
            },
        },
        "prompt_tag": {
            "model": "prompt.Tag", "label": "Prompt tag", "search": ["name"],
            "fields": {"name": F("str", required=True)},
        },
        "writing_style": {
            "model": "prompt.WritingStyle", "label": "Writing style", "search": ["name"],
            "fields": {"name": F("str", required=True), "description": F("text")},
        },

        # ---- Member resources (accounts app) ---------------------------------
        "member_resource": {
            "model": "accounts.MemberResource", "label": "Member resource (free download)", "search": ["title"],
            "no_create": True,  # the file + thumbnail are uploaded in the admin
            "fields": {"title": F("str"), "description": F("text"), "is_active": F("bool"), "order": F("int")},
            "note": "The file and thumbnail are uploaded in the admin (not over MCP).",
        },
    }


# ---------------------------------------------------------------------------
# Model + resource resolution
# ---------------------------------------------------------------------------
def _get_model(dotted: str):
    from django.apps import apps

    if dotted == AUTH_USER:
        from django.contrib.auth import get_user_model

        return get_user_model()
    app_label, model_name = dotted.split(".")
    return apps.get_model(app_label, model_name)


def _resource(key: str) -> dict:
    res = _resources().get(key)
    if res is None:
        keys = ", ".join(sorted(_resources().keys()))
        raise ToolInputError(f"Unknown resource '{key}'. Valid resources: {keys}.")
    return res


# ---------------------------------------------------------------------------
# Serialisation (read every field automatically)
# ---------------------------------------------------------------------------
def _to_json(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _serialize(obj) -> dict:
    from django.db.models import FileField

    data = {}
    for f in obj._meta.concrete_fields:
        if f.is_relation:
            rel = getattr(obj, f.name, None)
            data[f.name] = {"id": rel.pk, "label": str(rel)} if rel is not None else None
        elif isinstance(f, FileField):
            fv = getattr(obj, f.name, None)
            data[f.name] = (fv.name or None) if fv else None
        else:
            data[f.name] = _to_json(getattr(obj, f.attname, None))
    for m in obj._meta.many_to_many:
        try:
            data[m.name] = [{"id": r.pk, "label": str(r)} for r in getattr(obj, m.name).all()]
        except Exception:
            data[m.name] = []
    return data


# ---------------------------------------------------------------------------
# Coercion + relation resolution
# ---------------------------------------------------------------------------
def _resolve_one(spec: dict, value: Any):
    Model = _get_model(spec["model"])
    if isinstance(value, dict):
        value = value.get("id") or value.get("label")
    inst = None
    if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
        inst = Model.objects.filter(pk=int(value)).first()
    if inst is None and isinstance(value, str):
        for lk in spec["lookup"]:
            inst = Model.objects.filter(**{f"{lk}__iexact": value}).first()
            if inst:
                break
    if inst is None and spec.get("create_missing") and isinstance(value, str) and spec["lookup"]:
        inst = Model.objects.create(**{spec["lookup"][0]: value.strip()})
    if inst is None:
        raise ToolInputError(f"No {spec['model']} matched '{value}'.")
    return inst


def _coerce_scalar(field_name: str, spec: dict, value: Any):
    t = spec["type"]
    if value is None:
        return None
    if t in ("str", "text", "html", "slug"):
        return str(value)
    if t == "int":
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ToolInputError(f"{field_name} must be a whole number.")
    if t == "bool":
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on")
        return bool(value)
    if t == "decimal":
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ToolInputError(f"{field_name} must be a number.")
    if t == "choice":
        v = str(value)
        if spec["choices"] and v not in spec["choices"]:
            raise ToolInputError(f"{field_name} must be one of {spec['choices']}.")
        return v
    if t in ("date", "datetime"):
        from django.utils.dateparse import parse_date, parse_datetime

        parsed = parse_datetime(str(value)) if t == "datetime" else parse_date(str(value))
        if parsed is None:
            raise ToolInputError(
                f"{field_name} must be an ISO {'datetime' if t == 'datetime' else 'date'} "
                f"(e.g. {'2026-08-11T09:00:00' if t == 'datetime' else '2026-08-11'})."
            )
        return parsed
    return value


def _apply_fields(obj, res: dict, fields: dict, creating: bool):
    """Set scalar + FK fields on obj; return (m2m_ops, changed_names)."""
    allowed = res["fields"]
    m2m_ops = {}
    changed = []
    for name, value in fields.items():
        if name not in allowed:
            raise ToolInputError(
                f"'{name}' is not writable on {res['label']}. "
                f"Writable fields: {', '.join(sorted(allowed))}."
            )
        spec = allowed[name]
        if spec["type"] == "m2m":
            m2m_ops[name] = value
            changed.append(name)
            continue
        if spec["type"] == "fk":
            setattr(obj, name, _resolve_one(spec, value) if value is not None else None)
        else:
            setattr(obj, name, _coerce_scalar(name, spec, value))
        changed.append(name)
    return m2m_ops, changed


def _apply_m2m(obj, res: dict, m2m_ops: dict):
    for name, value in m2m_ops.items():
        spec = res["fields"][name]
        if value is None:
            continue
        if not isinstance(value, (list, tuple)):
            value = [value]
        insts = [_resolve_one(spec, v) for v in value if v not in (None, "")]
        getattr(obj, name).set(insts)


def _check_required(res: dict, fields: dict):
    missing = [n for n, s in res["fields"].items() if s["required"] and n not in fields]
    if missing:
        raise ToolInputError(f"Missing required field(s) for {res['label']}: {', '.join(missing)}.")


def _get_instance(res: dict, item_id):
    Model = _get_model(res["model"])
    if res.get("singleton"):
        obj, _ = Model.objects.get_or_create(pk=1)
        return obj
    obj = Model.objects.filter(pk=item_id).first()
    if obj is None:
        raise ToolInputError(f"No {res['label']} found with id {item_id}.")
    return obj


# ---------------------------------------------------------------------------
# Sync implementations
# ---------------------------------------------------------------------------
def _list_resource_types_impl() -> dict:
    out = []
    for key, res in sorted(_resources().items()):
        caps = ["read"]
        if not res.get("singleton") and not res.get("no_create"):
            caps.append("create")
        caps.append("update")
        if not res.get("singleton"):
            caps.append("delete")
        fields = {}
        for fn, sp in res["fields"].items():
            info = {"type": sp["type"], "required": sp["required"]}
            if sp["choices"]:
                info["choices"] = sp["choices"]
            if sp["model"]:
                info["refers_to"] = sp["model"]
            fields[fn] = info
        entry = {"resource": key, "label": res["label"], "can": caps, "fields": fields}
        if res.get("singleton"):
            entry["singleton"] = True
        if res.get("note"):
            entry["note"] = res["note"]
        out.append(entry)
    return {"resources": out}


def _list_items_impl(resource, search=None, filters=None, limit=25) -> dict:
    res = _resource(resource)
    Model = _get_model(res["model"])
    qs = Model.objects.all()
    if filters:
        clean = {k: v for k, v in filters.items() if k in res["fields"] and res["fields"][k]["type"] not in ("m2m",)}
        try:
            qs = qs.filter(**clean)
        except Exception as exc:
            raise ToolInputError(f"Invalid filter: {exc}")
    if search and res.get("search"):
        from django.db.models import Q

        q = Q()
        for fld in res["search"]:
            q |= Q(**{f"{fld}__icontains": search})
        qs = qs.filter(q)
    try:
        limit = max(1, min(int(limit), 200))
    except (TypeError, ValueError):
        limit = 25
    items = [_serialize(o) for o in qs[:limit]]
    return {"resource": resource, "count": len(items), "items": items}


def _get_item_impl(resource, item_id=None) -> dict:
    res = _resource(resource)
    return _serialize(_get_instance(res, item_id))


def _create_item_impl(resource, fields) -> dict:
    res = _resource(resource)
    if res.get("singleton"):
        raise ToolInputError(f"{res['label']} is a single settings record — use update_item, not create_item.")
    if res.get("no_create"):
        raise ToolInputError(f"{res['label']} cannot be created over MCP ({res.get('note', 'created elsewhere')}).")
    fields = fields or {}
    _check_required(res, fields)
    Model = _get_model(res["model"])
    obj = Model()
    m2m_ops, _ = _apply_fields(obj, res, fields, creating=True)
    try:
        obj.save()
        _apply_m2m(obj, res, m2m_ops)
        if m2m_ops:
            obj.save()
    except Exception as exc:
        raise ToolInputError(f"Could not create {res['label']}: {exc}")
    obj.refresh_from_db()
    return _serialize(obj)


def _update_item_impl(resource, item_id=None, fields=None) -> dict:
    res = _resource(resource)
    fields = fields or {}
    if not fields:
        raise ToolInputError("Pass at least one field to change in 'fields'.")
    obj = _get_instance(res, item_id)
    m2m_ops, changed = _apply_fields(obj, res, fields, creating=False)
    try:
        obj.save()
        _apply_m2m(obj, res, m2m_ops)
    except Exception as exc:
        raise ToolInputError(f"Could not update {res['label']}: {exc}")
    obj.refresh_from_db()
    result = _serialize(obj)
    result["updated_fields"] = changed
    return result


def _delete_item_impl(resource, item_id=None) -> dict:
    res = _resource(resource)
    if res.get("singleton"):
        raise ToolInputError(f"{res['label']} is a settings record and cannot be deleted.")
    obj = _get_instance(res, item_id)
    label = str(obj)
    try:
        obj.delete()
    except Exception as exc:
        raise ToolInputError(f"Could not delete {res['label']} (it may be referenced by other records): {exc}")
    return {"deleted": True, "resource": resource, "id": item_id, "label": label}


# ---------------------------------------------------------------------------
# Async tools (what FastMCP registers)
# ---------------------------------------------------------------------------
async def _run(name, impl, summary, *a, **kw):
    start = time.monotonic()
    try:
        result = await sync_to_async(impl, thread_sensitive=True)(*a, **kw)
    except Exception as exc:
        await _record(name, False, args_summary=summary, error=str(exc), duration_ms=_ms(start))
        raise
    await _record(name, True, args_summary=summary, duration_ms=_ms(start))
    return result


async def list_resource_types() -> dict:
    """List every kind of content Claude can manage on this site (blog posts,
    products, coupons, hosted tools, AI mentor bots, journaling prompts,
    experiment weeks, settings, and more), with what you can do to each
    (create/read/update/delete) and each resource's writable fields, types and
    allowed choices. Call this first to discover resource keys and field names
    for the other tools. Read-only."""
    return await _run("list_resource_types", _list_resource_types_impl, "")


async def list_items(
    resource: str,
    search: str | None = None,
    filters: dict[str, Any] | None = None,
    limit: int = 25,
) -> dict:
    """List rows of a resource (see list_resource_types for keys), newest/default
    order, each with its ``id`` and all fields. ``search`` matches the resource's
    text fields; ``filters`` is an optional dict of exact field matches (e.g.
    {"status": "draft"}). ``limit`` defaults to 25 (max 200). Read-only."""
    return await _run("list_items", _list_items_impl, f"{resource} search={search}",
                      resource, search=search, filters=filters, limit=limit)


async def get_item(resource: str, item_id: int | None = None) -> dict:
    """Read one row in full by ``resource`` + ``item_id``. For settings
    singletons (site_settings, shop_settings, one_time_offer) the id is ignored.
    Read-only."""
    return await _run("get_item", _get_item_impl, f"{resource} id={item_id}", resource, item_id=item_id)


async def create_item(resource: str, fields: dict[str, Any]) -> dict:
    """Create a new row of ``resource``. ``fields`` is a dict of field→value
    (see list_resource_types for the writable fields, required ones, types and
    choices). Relations accept a name/slug/id; blog/prompt tags are created if
    missing. Returns the created row including its new id. Not allowed for
    settings singletons or records whose file is uploaded in the admin."""
    return await _run("create_item", _create_item_impl, f"{resource}", resource, fields)


async def update_item(resource: str, item_id: int | None = None, fields: dict[str, Any] | None = None) -> dict:
    """Edit a row: pass ``resource``, ``item_id`` and a ``fields`` dict of only
    the fields to change (anything omitted is untouched). For settings singletons
    the id is ignored. m2m fields (e.g. tags) replace the whole set. Returns the
    updated row and which fields changed."""
    return await _run("update_item", _update_item_impl, f"{resource} id={item_id}", resource, item_id=item_id, fields=fields)


async def delete_item(resource: str, item_id: int) -> dict:
    """Permanently delete a row by ``resource`` + ``item_id``. This cannot be
    undone. Fails clearly if the row is protected by references from other
    records (e.g. a category that still has products). Settings singletons cannot
    be deleted."""
    return await _run("delete_item", _delete_item_impl, f"{resource} id={item_id}", resource, item_id=item_id)
