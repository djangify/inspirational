"""Call logging for the MCP connector.

One row per tool call. Gives the owner visibility into what Claude did through
the connector. Deliberately stores only a short, non-sensitive summary of
arguments, never full tool payloads.

Imports nothing heavy (just Django) so the main Django process can load this app
without pulling in the MCP/Starlette stack.
"""

from django.conf import settings
from django.db import models


class MCPCallLog(models.Model):
    """One row per MCP tool invocation."""

    tool = models.CharField(max_length=100)
    ok = models.BooleanField(default=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mcp_calls",
    )
    # OAuth client that presented the token (e.g. the Claude connector app).
    client_id = models.CharField(max_length=100, blank=True)
    # Short, non-sensitive summary of the arguments — never the full payload.
    args_summary = models.CharField(max_length=500, blank=True)
    error = models.TextField(blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "MCP call log"
        verbose_name_plural = "MCP call log"

    def __str__(self):
        state = "ok" if self.ok else "fail"
        return f"{self.tool} · {state} · {self.created:%Y-%m-%d %H:%M}"
