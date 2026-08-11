"""ASGI entrypoint for the MCP sidecar (OAuth Resource Server).

Run from the repo root (same dir as manage.py), as a second process alongside
the main gunicorn/Django stack:

    uvicorn mcp_server.app:app --host 127.0.0.1 --port 8951

Env:
  MCP_OAUTH_ISSUER   base URL of the Django Authorization Server (this site),
                     e.g. https://www.inspirationalguidance.com — Claude
                     discovers the OAuth endpoints from here.
  MCP_RESOURCE_URL   public URL of this sidecar's /mcp endpoint,
                     e.g. https://www.inspirationalguidance.com/mcp
  MCP_DEV_TOKEN      optional — a static token for local/Inspector testing.
                     Leave unset in real deployments.
  MCP_ALLOWED_HOSTS  optional — comma-separated Host allowlist; when set, DNS
                     rebinding protection turns on.
"""

import os

# Django must be up before tools/auth import any models.
from mcp_server import bootstrap  # noqa: F401  (side effect: django.setup())

from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import AnyHttpUrl
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from mcp_server import crud, tools
from mcp_server.auth import MCP_SCOPE, DjangoOAuthTokenVerifier

_issuer = os.environ.get("MCP_OAUTH_ISSUER", "http://localhost:8000")
_resource = os.environ.get("MCP_RESOURCE_URL", "http://localhost:8951/mcp")

_allowed_hosts = [h.strip() for h in os.environ.get("MCP_ALLOWED_HOSTS", "").split(",") if h.strip()]
_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=bool(_allowed_hosts),
    allowed_hosts=_allowed_hosts,
    allowed_origins=[],
)

mcp = FastMCP(
    "Inspirational Guidance",
    instructions=(
        "Read and manage the whole Inspirational Guidance site. Two toolsets:\n"
        "1) Blog quick tools: get_site_overview, list_posts, get_post, "
        "create_post, update_post, update_post_seo, list_categories, list_tags.\n"
        "2) Full CRUD over everything else via generic tools — call "
        "list_resource_types first to see every manageable resource (products, "
        "shop/blog categories, coupons, order bumps, reviews, orders, hosted "
        "tools, AI mentor bots, journaling prompts, experiment weeks, site/shop "
        "settings, one-time offer, member resources...) with each resource's "
        "fields, types and choices. Then use list_items / get_item / create_item "
        "/ update_item / delete_item. Relations accept a name/slug/id; tags are "
        "created if missing. Rich-text/description fields are HTML. delete_item "
        "is permanent — confirm intent before deleting. Uploading images/PDF/HTML "
        "files and changing payment/email secrets are done by the owner in the "
        "admin; everything else can be done here."
    ),
    stateless_http=True,
    json_response=True,
    streamable_http_path="/mcp",
    transport_security=_security,
    token_verifier=DjangoOAuthTokenVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(_issuer),
        resource_server_url=AnyHttpUrl(_resource),
        required_scopes=[MCP_SCOPE],
    ),
)

mcp.add_tool(
    tools.get_site_overview,
    name="get_site_overview",
    title="Get site overview",
    annotations=ToolAnnotations(title="Get site overview", readOnlyHint=True, openWorldHint=False),
)

mcp.add_tool(
    tools.list_categories,
    name="list_categories",
    title="List categories",
    annotations=ToolAnnotations(title="List categories", readOnlyHint=True, openWorldHint=False),
)

mcp.add_tool(
    tools.list_tags,
    name="list_tags",
    title="List tags",
    annotations=ToolAnnotations(title="List tags", readOnlyHint=True, openWorldHint=False),
)

mcp.add_tool(
    tools.list_posts,
    name="list_posts",
    title="List blog posts",
    annotations=ToolAnnotations(title="List blog posts", readOnlyHint=True, openWorldHint=False),
)

mcp.add_tool(
    tools.get_post,
    name="get_post",
    title="Get blog post",
    annotations=ToolAnnotations(title="Get blog post", readOnlyHint=True, openWorldHint=False),
)

mcp.add_tool(
    tools.create_post,
    name="create_post",
    title="Create blog post",
    annotations=ToolAnnotations(
        title="Create blog post",
        readOnlyHint=False,
        destructiveHint=False,  # additive: creates a new post
        idempotentHint=False,   # calling again makes another post
        openWorldHint=False,
    ),
)

mcp.add_tool(
    tools.update_post,
    name="update_post",
    title="Update blog post",
    annotations=ToolAnnotations(
        title="Update blog post",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)

mcp.add_tool(
    tools.update_post_seo,
    name="update_post_seo",
    title="Update blog post SEO fields",
    annotations=ToolAnnotations(
        title="Update blog post SEO fields",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)


# --- Generic full-CRUD tools (cover every content model on the site) ---------
mcp.add_tool(
    crud.list_resource_types,
    name="list_resource_types",
    title="List manageable resource types",
    annotations=ToolAnnotations(title="List manageable resource types", readOnlyHint=True, openWorldHint=False),
)

mcp.add_tool(
    crud.list_items,
    name="list_items",
    title="List items of a resource",
    annotations=ToolAnnotations(title="List items of a resource", readOnlyHint=True, openWorldHint=False),
)

mcp.add_tool(
    crud.get_item,
    name="get_item",
    title="Get one item",
    annotations=ToolAnnotations(title="Get one item", readOnlyHint=True, openWorldHint=False),
)

mcp.add_tool(
    crud.create_item,
    name="create_item",
    title="Create an item",
    annotations=ToolAnnotations(
        title="Create an item",
        readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False,
    ),
)

mcp.add_tool(
    crud.update_item,
    name="update_item",
    title="Update an item",
    annotations=ToolAnnotations(
        title="Update an item",
        readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=False,
    ),
)

mcp.add_tool(
    crud.delete_item,
    name="delete_item",
    title="Delete an item",
    annotations=ToolAnnotations(
        title="Delete an item",
        readOnlyHint=False, destructiveHint=True, idempotentHint=True, openWorldHint=False,
    ),
)


async def health(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "inspirational-mcp"})


# The streamable-HTTP Starlette app carries the session-manager lifespan and the
# auth machinery (Protected Resource Metadata + bearer enforcement on /mcp).
# Reuse it directly; add an unauthenticated /health for process probes.
app = mcp.streamable_http_app()
app.router.routes.append(Route("/health", health, methods=["GET"]))
