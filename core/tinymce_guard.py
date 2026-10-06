"""
Stop the admin rich text editor from deleting <script> and <style> code.

TinyMCE removes both tags when the admin form is saved, even if the editor was
never touched (changing a category and pressing Save is enough). When a field
already holds either tag, show it as a plain text box instead, so nothing is
rewritten on save. Every other field keeps the normal editor.
"""
import re

from django import forms
from django.utils.html import format_html
from tinymce.widgets import TinyMCE

_CUSTOM_CODE_RE = re.compile(r"<\s*(script|style)\b", re.IGNORECASE)
_original_render = TinyMCE.render


def _guarded_render(self, name, value, attrs=None, renderer=None):
    if value and _CUSTOM_CODE_RE.search(str(value)):
        textarea_attrs = {**(attrs or {}), **self.attrs}
        textarea_attrs.update(
            {"rows": 30, "style": "width:100%;font-family:monospace;font-size:13px;"}
        )
        textarea = forms.Textarea(attrs=textarea_attrs).render(
            name, value, renderer=renderer
        )
        return format_html(
            '<p style="margin:0 0 8px;padding:10px 12px;background:#fff5e0;'
            'border:1px solid #d9962a;border-radius:6px;color:#583a00;">'
            "This page contains custom code (a style block or a script). "
            "The visual editor is switched off for this field so saving "
            "does not delete that code. Edit the HTML here, or ask your AI "
            "assistant to edit it through the MCP connector.</p>{}",
            textarea,
        )
    return _original_render(self, name, value, attrs, renderer)


def install():
    if not getattr(TinyMCE, "_custom_code_guard", False):
        TinyMCE.render = _guarded_render
        TinyMCE._custom_code_guard = True
