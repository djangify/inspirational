"""Bring Django up inside the standalone sidecar process.

Import this module (or call :func:`setup_django`) *before* importing anything
that touches the ORM. ``settings.py`` does no request/template work at import
time, so ``django.setup()`` is enough to get full ORM access from a process
that never handles an HTTP request through Django itself.
"""

import os

_READY = False


def setup_django() -> None:
    """Idempotently configure Django settings + app registry for ORM use."""
    global _READY
    if _READY:
        return

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inspirational.settings")

    import django

    django.setup()
    _READY = True


# Run on import so ``from mcp_server import bootstrap`` is sufficient.
setup_django()
