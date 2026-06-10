# pseo/admin.py
import datetime
from django.contrib import admin
from django.contrib import messages
from django.urls import path, reverse
from django.shortcuts import render, redirect, get_object_or_404
from django import forms
from django.utils import timezone
from django.utils.html import format_html, strip_tags
from tinymce.widgets import TinyMCE
from .models import ProgrammaticPage
from .csv_import import CSVImportForm, import_csv


class ProgrammaticPageForm(forms.ModelForm):
    class Meta:
        model = ProgrammaticPage
        fields = "__all__"
        widgets = {
            "master_template": TinyMCE(),
            "generated_content": TinyMCE(),
        }


class BulkGenerateForm(forms.Form):
    master_template = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 20, "style": "width:100%; font-family: monospace;"}),
        label="Master template",
        help_text="Use [Topic] wherever you want the keyword inserted. HTML is supported.",
    )
    cta_text = forms.CharField(
        max_length=200,
        required=False,
        label="CTA text (optional)",
        help_text="The pitch line shown at the bottom of each page. Use [Topic] for substitution. Leave blank to keep each page's existing CTA.",
    )
    cta_url = forms.URLField(
        required=False,
        label="CTA URL (optional)",
        help_text="The link the CTA button points to. Leave blank to keep each page's existing URL.",
    )


def _apply_substitution(template, keyword):
    """Replace [Topic] with keyword; return empty string if template is empty."""
    if not template:
        return ""
    return template.replace("[Topic]", keyword)


def _generate_for_page(page, master_template, cta_text="", cta_url=""):
    """Apply generation logic to a single page."""
    content = _apply_substitution(master_template, page.keyword)
    page.master_template = master_template
    page.generated_content = content

    if not page.h1_heading:
        page.h1_heading = page.keyword
    if not page.meta_title:
        page.meta_title = page.keyword[:60]
    if not page.meta_description:
        plain_text = " ".join(strip_tags(content).split())
        page.meta_description = plain_text[:160]

    if cta_text:
        page.cta_text = _apply_substitution(cta_text, page.keyword)
    elif page.cta_text:
        page.cta_text = _apply_substitution(page.cta_text, page.keyword)

    if cta_url:
        page.cta_url = cta_url

    page.status = "pending_review"
    page.save()


@admin.register(ProgrammaticPage)
class ProgrammaticPageAdmin(admin.ModelAdmin):
    form = ProgrammaticPageForm
    list_display = ["keyword", "slug", "status", "noindex", "publish_date", "source", "created"]
    list_filter = ["status", "source", "noindex"]
    search_fields = ["keyword"]
    prepopulated_fields = {"slug": ("keyword",)}
    actions = ["approve_and_publish", "bulk_set_template_and_generate", "schedule_daily_publish"]

    def get_readonly_fields(self, request, obj=None):
        base = ["created", "updated"]
        if obj and obj.pk:
            buttons = ["view_page_button"]
            if obj.status == "draft" and not obj.generated_content:
                buttons.append("generate_content_button")
            return buttons + base
        return base

    def get_fieldsets(self, request, obj=None):
        if obj and obj.pk:
            top_fields = ["keyword", "slug", "view_page_button"]
            if obj.status == "draft" and not obj.generated_content:
                top_fields.append("generate_content_button")
            top_fields += ["status", "publish_date", "source"]
        else:
            top_fields = ["keyword", "slug", "status", "publish_date", "source"]

        fieldsets = [
            (None, {"fields": top_fields}),
            ("Content", {"fields": ["master_template", "generated_content"]}),
            ("SEO", {"fields": ["h1_heading", "meta_title", "meta_description", "noindex"]}),
            ("Call to Action", {"fields": ["cta_text", "cta_url"]}),
        ]
        if obj and obj.pk:
            fieldsets.append(
                ("Timestamps", {"fields": ["created", "updated"], "classes": ["collapse"]})
            )
        return fieldsets

    def view_page_button(self, obj):
        if obj.status == "published":
            url = f"/discover/{obj.slug}/"
            label = "View Live Page"
        else:
            url = f"/discover/{obj.slug}/?preview=1"
            label = "Preview Page"
        return format_html(
            '<a href="{}" target="_blank" class="button">{}</a>',
            url, label,
        )
    view_page_button.short_description = ""

    def generate_content_button(self, obj):
        url = reverse("admin:pseo_programmaticpage_generate", args=[obj.pk])
        return format_html(
            '<a href="{}" class="button default">Generate Content</a>', url,
        )
    generate_content_button.short_description = ""

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import-csv/",
                self.admin_site.admin_view(self.csv_import_view),
                name="pseo_programmaticpage_csv_import",
            ),
            path(
                "<int:object_id>/generate/",
                self.admin_site.admin_view(self.generate_content_view),
                name="pseo_programmaticpage_generate",
            ),
            path(
                "bulk-generate/",
                self.admin_site.admin_view(self.bulk_generate_view),
                name="pseo_programmaticpage_bulk_generate",
            ),
        ]
        return custom_urls + urls

    def csv_import_view(self, request):
        if request.method == "POST":
            form = CSVImportForm(request.POST, request.FILES)
            if form.is_valid():
                result = import_csv(request.FILES["csv_file"])
                if result["created"]:
                    self.message_user(request, f"{len(result['created'])} page(s) imported as drafts.", messages.SUCCESS)
                if result["duplicates"]:
                    self.message_user(request, f"{len(result['duplicates'])} duplicate(s) skipped: {', '.join(result['duplicates'])}", messages.WARNING)
                for error in result["errors"]:
                    self.message_user(request, error, messages.ERROR)
                return redirect("admin:pseo_programmaticpage_changelist")
        else:
            form = CSVImportForm()

        context = {
            **self.admin_site.each_context(request),
            "title": "Import pages from CSV",
            "form": form,
            "opts": self.model._meta,
        }
        return render(request, "admin/pseo/csv_import.html", context)

    def generate_content_view(self, request, object_id):
        page = get_object_or_404(ProgrammaticPage, pk=object_id)

        if not page.master_template:
            self.message_user(request, "Cannot generate content: master_template is empty.", messages.ERROR)
            return redirect("admin:pseo_programmaticpage_change", object_id)

        _generate_for_page(page, page.master_template)
        self.message_user(
            request,
            f"Content generated for \"{page.keyword}\" — status set to Pending Review.",
            messages.SUCCESS,
        )
        return redirect("admin:pseo_programmaticpage_change", object_id)

    @admin.action(description="Set template and generate content for selected pages")
    def bulk_set_template_and_generate(self, request, queryset):
        selected_ids = ",".join(str(pk) for pk in queryset.values_list("pk", flat=True))
        url = reverse("admin:pseo_programmaticpage_bulk_generate")
        return redirect(f"{url}?ids={selected_ids}")

    def bulk_generate_view(self, request):
        raw_ids = request.GET.get("ids", "") or request.POST.get("ids", "")
        try:
            ids = [int(i) for i in raw_ids.split(",") if i.strip()]
        except ValueError:
            ids = []

        pages = ProgrammaticPage.objects.filter(pk__in=ids)

        if not pages.exists():
            self.message_user(request, "No pages found. Please select pages from the list first.", messages.ERROR)
            return redirect("admin:pseo_programmaticpage_changelist")

        if request.method == "POST":
            form = BulkGenerateForm(request.POST)
            if form.is_valid():
                master_template = form.cleaned_data["master_template"]
                cta_text = form.cleaned_data.get("cta_text", "")
                cta_url = form.cleaned_data.get("cta_url", "")
                processed = 0
                for page in pages:
                    _generate_for_page(page, master_template, cta_text=cta_text, cta_url=cta_url)
                    processed += 1
                self.message_user(
                    request,
                    f"Content generated for {processed} page(s) — all set to Pending Review.",
                    messages.SUCCESS,
                )
                return redirect("admin:pseo_programmaticpage_changelist")
        else:
            form = BulkGenerateForm()

        context = {
            **self.admin_site.each_context(request),
            "title": "Set template and generate content",
            "form": form,
            "pages": pages,
            "ids": raw_ids,
            "opts": self.model._meta,
        }
        return render(request, "admin/pseo/bulk_generate.html", context)

    @admin.action(description="Schedule for daily publish (one per day from tomorrow)")
    def schedule_daily_publish(self, request, queryset):
        eligible = queryset.filter(status="pending_review").order_by("created")
        count = eligible.count()

        if count == 0:
            self.message_user(
                request,
                "No Pending Review pages selected. Only pages with status 'Pending Review' can be scheduled.",
                messages.WARNING,
            )
            return

        tomorrow = timezone.now().date() + datetime.timedelta(days=1)
        summary = []

        for i, page in enumerate(eligible):
            publish_dt = timezone.make_aware(
                datetime.datetime.combine(
                    tomorrow + datetime.timedelta(days=i),
                    datetime.time(9, 0, 0),
                )
            )
            page.publish_date = publish_dt
            page.save(update_fields=["publish_date"])
            summary.append(f"{page.keyword} → {publish_dt.strftime('%d %b %Y')}")

        self.message_user(
            request,
            f"{count} page(s) scheduled: {' | '.join(summary)}",
            messages.SUCCESS,
        )

    @admin.action(description="Approve and publish selected pages")
    def approve_and_publish(self, request, queryset):
        updated = queryset.update(status="published")
        self.message_user(request, f"{updated} page(s) approved and published successfully.")
