import json
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import Sum, Max
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from .models import (
    ExperimentWeek,
    ExperimentGoal,
    MilestoneReflection,
    AliveListItem,
    HostedTool,
)


def experiment_results(request):
    weeks = ExperimentWeek.objects.filter(is_published=True).order_by("-week_date")

    goals_qs = ExperimentGoal.objects.all()
    goals_by_milestone = {
        "30": goals_qs.filter(milestone="30"),
        "60": goals_qs.filter(milestone="60"),
        "90": goals_qs.filter(milestone="90"),
    }

    reflections = {r.milestone: r for r in MilestoneReflection.objects.all()}

    totals = weeks.aggregate(
        total_revenue=Sum("revenue_this_week"),
        total_true_fans=Sum("transactions"),
        total_posts_rewritten=Sum("blog_posts_rewritten"),
    )

    latest_email_total = weeks.filter(
        email_list_total__isnull=False
    ).values_list("email_list_total", flat=True).first()

    context = {
        "weeks": weeks,
        "goals_by_milestone": goals_by_milestone,
        "reflections": reflections,
        "total_revenue": totals["total_revenue"] or 0,
        "total_true_fans": totals["total_true_fans"] or 0,
        "total_posts_rewritten": totals["total_posts_rewritten"] or 0,
        "latest_email_total": latest_email_total or 0,
    }
    return render(request, "tools/experiment_results.html", context)


def tools_home(request):
    return render(request, "tools/index.html")


def calming_game(request):
    return render(request, "tools/calming_game.html")


def tap_to_calm(request):
    return render(request, "tools/tap_to_calm.html")


def alive_list_builder(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        action = data.get("action")

        if not request.user.is_authenticated:
            return JsonResponse({"requires_login": True}, status=401)

        if action == "save_item":
            item_text = data.get("item_text", "").strip()
            category = data.get("category", "").strip()
            if not item_text:
                return JsonResponse({"error": "item_text required"}, status=400)
            item = AliveListItem.objects.create(
                user=request.user,
                item_text=item_text,
                category=category,
            )
            return JsonResponse({"status": "ok", "item_id": item.id})

        elif action == "delete_item":
            item_id = data.get("item_id")
            item = get_object_or_404(AliveListItem, id=item_id, user=request.user)
            item.delete()
            return JsonResponse({"status": "ok"})

        elif action == "toggle_living_it":
            item_id = data.get("item_id")
            item = get_object_or_404(AliveListItem, id=item_id, user=request.user)
            item.is_living_it = not item.is_living_it
            item.save(update_fields=["is_living_it", "updated"])
            return JsonResponse({"status": "ok", "is_living_it": item.is_living_it})

        return JsonResponse({"error": "Unknown action"}, status=400)

    # GET
    existing_items = []
    if request.user.is_authenticated:
        existing_items = list(
            AliveListItem.objects.filter(user=request.user).values(
                "id", "item_text", "category", "is_living_it", "order"
            )
        )

    return render(request, "tools/alive_list_builder.html", {
        "existing_items_json": json.dumps(existing_items),
        "user_authenticated": request.user.is_authenticated,
    })


# -- Hosted Tools (upload-an-HTML-artifact) ----------------------------------

def _staff_preview(request):
    return request.GET.get("preview") == "1" and request.user.is_staff


# Anchor tags that carry a real, followable link. We deliberately keep this to
# http(s) and mailto so we surface the kind of link a tool author puts on a
# "button", and skip in-page anchors (#...), javascript: handlers and relative
# paths that mean nothing once the page is a saved PDF.
_ANCHOR_RE = re.compile(
    r'<a\b[^>]*\bhref\s*=\s*(["\'])(?P<href>.*?)\1[^>]*>(?P<label>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_MAX_HARVESTED_LINKS = 25


def _harvest_tool_links(html_bytes):
    """
    Pull followable links out of an uploaded artifact so they can be reprinted
    as plain "label — URL" text on the PDF attribution page.

    A tool author often adds a "button" that is really an <a href="..."> link.
    In a saved/printed PDF that button loses its destination, so here we scan
    the raw artifact HTML, collect each external link's visible text + URL,
    de-duplicate by URL and cap the count. Returns a list of (label, url)
    tuples (raw/unescaped -- the caller escapes them).

    NOTE: this only sees real <a href> links. A <button onclick="location=...">
    style button hides its URL inside JavaScript and is not harvested.
    """
    try:
        html = html_bytes.decode("utf-8", "ignore")
    except Exception:
        return []

    seen = set()
    links = []
    for m in _ANCHOR_RE.finditer(html):
        href = (m.group("href") or "").strip()
        low = href.lower()
        if not (low.startswith("http://") or low.startswith("https://") or low.startswith("mailto:")):
            continue
        if href in seen:
            continue
        seen.add(href)
        # Strip any inner tags (e.g. an icon <svg>) and collapse whitespace.
        label = _WS_RE.sub(" ", _TAG_RE.sub("", m.group("label") or "")).strip()
        if not label:
            label = href
        links.append((label, href))
        if len(links) >= _MAX_HARVESTED_LINKS:
            break
    return links


def _build_pdf_branding(links=None):
    """
    Build the HTML injected into every served hosted tool to give visitors a
    "Download PDF" button plus a branded attribution page.

    - On screen: only a small floating "Download PDF" button is visible.
    - When the visitor saves/prints to PDF: the button is hidden and a clean
      final page is appended carrying Inspirational Guidance's identity (site
      name, author, bio, URL) so they always remember where the PDF came from.

    Brand details come from Django settings (SITE_NAME / AUTHOR_*), so a missing
    value never breaks the tool -- the button always renders and the attribution
    block only includes the pieces that are available.
    """
    from django.conf import settings
    from django.utils.html import escape

    business = escape((getattr(settings, "SITE_NAME", "") or "").strip())
    author = escape((getattr(settings, "AUTHOR_NAME", "") or "").strip())
    bio = escape((getattr(settings, "AUTHOR_SHORT_BIO", "") or "").strip())
    url = (getattr(settings, "SITE_URL", "") or "").strip()
    author_url = (getattr(settings, "AUTHOR_URL", "") or "").strip()
    url_safe = escape(url)

    # AUTHOR_URL is stored as a path (e.g. "/diane-corriette"); make it absolute.
    if author_url.startswith("/") and url:
        about_safe = escape(url.rstrip("/") + author_url)
    else:
        about_safe = escape(author_url)

    parts = ['<section class="tool-pdf-attribution">', '<div class="tool-pdf-rule"></div>']
    if business:
        parts.append('<p class="biz">' + business + '</p>')
    if author:
        parts.append("<h2>Created by " + author + "</h2>")
    if bio:
        parts.append("<p>" + bio + "</p>")
    meta = []
    if url:
        meta.append('<a href="' + url_safe + '">' + url_safe + '</a>')
    if about_safe:
        meta.append('<a href="' + about_safe + '">About</a>')
    if meta:
        parts.append('<p class="meta">' + " &nbsp;&bull;&nbsp; ".join(meta) + "</p>")
    # Links the tool author put on the page (e.g. "buttons"), reprinted as
    # plain text + URL so they survive being saved as a PDF.
    if links:
        parts.append('<div class="tool-pdf-links">')
        parts.append('<p class="links-title">Links referenced in this tool</p>')
        parts.append("<ul>")
        for label, link_url in links:
            parts.append(
                '<li><span class="lbl">' + escape(label) + '</span><br>'
                '<a href="' + escape(link_url) + '">' + escape(link_url) + '</a></li>'
            )
        parts.append("</ul></div>")
    source = business or url_safe or "Inspirational Guidance"
    parts.append('<p class="meta">You received this from ' + source +
                 '. Thank you for your support.</p>')
    parts.append("</section>")
    attribution = "".join(parts)

    style = (
        '<style id="tool-pdf-style">'
        "@media screen{"
        ".tool-pdf-attribution{display:none;}"
        ".tool-pdf-btn{position:fixed;right:16px;bottom:16px;z-index:2147483647;"
        "font:600 14px/1 system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;"
        "padding:11px 18px;background:#0f766e;color:#fff;border:0;border-radius:9999px;"
        "box-shadow:0 3px 10px rgba(0,0,0,.25);cursor:pointer;}"
        ".tool-pdf-btn:hover{background:#134e4a;}"
        "}"
        "@media print{"
        ".tool-pdf-btn{display:none !important;}"
        ".tool-pdf-attribution{display:block !important;page-break-before:always;"
        "break-before:page;font-family:Georgia,'Times New Roman',serif;color:#111;"
        "padding:56px 40px;}"
        ".tool-pdf-attribution .tool-pdf-rule{height:3px;width:64px;background:#0f766e;"
        "margin:0 0 22px;}"
        ".tool-pdf-attribution .biz{font-size:13px;letter-spacing:.08em;"
        "text-transform:uppercase;color:#555;margin:0 0 6px;}"
        ".tool-pdf-attribution h2{font-size:22px;margin:0 0 14px;}"
        ".tool-pdf-attribution p{font-size:13px;line-height:1.6;margin:0 0 12px;"
        "max-width:540px;}"
        ".tool-pdf-attribution a{color:#0f766e;text-decoration:none;}"
        ".tool-pdf-attribution .meta{font-size:12px;color:#555;}"
        ".tool-pdf-attribution .tool-pdf-links{margin:22px 0 0;}"
        ".tool-pdf-attribution .tool-pdf-links .links-title{font-size:13px;"
        "letter-spacing:.06em;text-transform:uppercase;color:#555;margin:0 0 10px;}"
        ".tool-pdf-attribution .tool-pdf-links ul{list-style:none;padding:0;margin:0;}"
        ".tool-pdf-attribution .tool-pdf-links li{margin:0 0 11px;font-size:13px;"
        "line-height:1.5;word-break:break-all;}"
        ".tool-pdf-attribution .tool-pdf-links .lbl{font-weight:bold;color:#111;}"
        "}"
        "</style>"
    )
    button = (
        '<button class="tool-pdf-btn" type="button" onclick="window.print()" '
        'aria-label="Download this as a PDF">&#8595; Download PDF</button>'
    )
    return style + button + attribution


def _purchase_gate(request, tool):
    """
    Enforce the purchase wall for a tool that is sold via a shop product.

    Returns an HttpResponse to send instead (redirect) when the visitor may NOT
    see the tool, or None when access is allowed. Free tools (no linked product)
    and staff always pass.
    """
    if _staff_preview(request) or tool.user_has_access(request.user):
        return None

    product = tool.linked_product
    if not request.user.is_authenticated:
        messages.info(request, "Please sign in to access your purchased tool.")
        login_url = f"{reverse('accounts:login')}?next={request.path}"
        return redirect(login_url)

    # Authenticated but hasn't bought it — send them to the product page to buy.
    if product is not None and product.status == "publish" and product.is_active:
        messages.info(
            request,
            "This tool is part of a product. Purchase it to unlock access.",
        )
        return redirect("shop:product_detail", slug=product.slug)
    raise Http404("Tool not available.")


def hosted_tool_detail(request, slug):
    """
    Public wrapper page for an uploaded tool. Shows site chrome (nav/footer)
    and embeds the artifact in a sandboxed iframe pointing at the raw view.

    If the tool is sold via a shop product, it is purchase-gated: only the
    buyer (or staff) gets through; everyone else is sent to sign in / buy.
    """
    if _staff_preview(request):
        tool = get_object_or_404(HostedTool, slug=slug)
    else:
        tool = get_object_or_404(HostedTool, slug=slug, published=True)

    blocked = _purchase_gate(request, tool)
    if blocked is not None:
        return blocked
    return render(request, "tools/hosted_tool_detail.html", {"tool": tool})


@xframe_options_sameorigin
def hosted_tool_raw(request, slug):
    """
    Serve the raw artifact HTML so its JavaScript executes.

    Security model:
      - The file lives in secure_storage, so it is not directly web-served;
        this view is the only way to reach it.
      - It is only ever loaded inside the sandboxed iframe on the detail page
        (sandbox WITHOUT allow-same-origin => opaque origin => the artifact
        cannot read this site's cookies, session or DOM).
      - X-Frame-Options: SAMEORIGIN (decorator) lets our own page frame it
        while blocking other sites; frame-ancestors 'self' is the modern
        equivalent / belt-and-braces.
    """
    if _staff_preview(request):
        tool = get_object_or_404(HostedTool, slug=slug)
    else:
        tool = get_object_or_404(HostedTool, slug=slug, published=True)

    blocked = _purchase_gate(request, tool)
    if blocked is not None:
        return blocked

    if not tool.html_file:
        raise Http404("No file attached to this tool.")

    try:
        with tool.html_file.open("rb") as fh:
            html = fh.read()
    except (FileNotFoundError, ValueError):
        raise Http404("Tool file missing on server.")

    # Inject a tiny height-reporter so the parent page can size the iframe to
    # the content (no inner scroll). Runs inside the sandbox via allow-scripts;
    # only posts a number, so it needs no same-origin access.
    reporter = (
        b"<script>(function(){"
        b"var t;"
        b"function measure(){var h=Math.max("
        b"document.body?document.body.scrollHeight:0,"
        b"document.documentElement?document.documentElement.scrollHeight:0);"
        b"parent.postMessage({__toolHeight:h},'*');}"
        b"function r(){clearTimeout(t);t=setTimeout(measure,60);}"
        b"window.addEventListener('load',r);"
        b"window.addEventListener('resize',r);"
        b"if(window.ResizeObserver){var ro=new ResizeObserver(r);"
        b"if(document.body){ro.observe(document.body);}}"
        b"if(window.MutationObserver){new MutationObserver(r).observe("
        b"document.documentElement,{childList:true,subtree:true,attributes:true});}"
        b"document.addEventListener('click',function(){setTimeout(r,60);setTimeout(r,450);});"
        b"setTimeout(r,300);setTimeout(r,1200);"
        b"})();</script>"
    )
    # Branded "Download PDF" button + attribution page (appears only in the
    # saved/printed PDF). Reprint links so they survive being saved: first the
    # explicit link the owner added on the tool (URL name + URL link), then any
    # links the author put inside the artifact itself, de-duplicated.
    tool_links = _harvest_tool_links(html)
    if tool.link_text and tool.link_url:
        tool_links = [(tool.link_text, tool.link_url)] + [
            link for link in tool_links if link[1] != tool.link_url
        ]
    branding = _build_pdf_branding(tool_links).encode("utf-8")
    injected = reporter + branding

    if b"</body>" in html:
        head, sep, tail = html.rpartition(b"</body>")
        html = head + injected + sep + tail
    else:
        html = html + injected

    response = HttpResponse(html, content_type="text/html; charset=utf-8")
    response["Content-Security-Policy"] = "frame-ancestors 'self'"
    response["X-Content-Type-Options"] = "nosniff"
    return response
