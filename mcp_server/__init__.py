"""Inspirational Guidance MCP connector.

Lets the site owner connect this site to Claude as a custom connector. Django
(django-oauth-toolkit) is the OAuth Authorization Server; a small ASGI sidecar
(``mcp_server.app``) is the MCP Resource Server that Claude talks to on ``/mcp``.

Only ``models``/``admin``/``apps``/``views`` are imported by the main Django
process. ``app``/``auth``/``tools`` are imported only by the sidecar process,
which is the sole place the ``mcp`` / ``starlette`` / ``uvicorn`` packages need
to be present.
"""
