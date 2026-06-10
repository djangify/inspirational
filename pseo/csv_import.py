# pseo/csv_import.py
import csv
import io
from django import forms
from django.utils.text import slugify
from .models import ProgrammaticPage


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label="CSV file",
        help_text=(
            "Required column: keyword. "
            "Optional columns: meta_title, meta_description, cta_text, cta_url."
        ),
    )


def import_csv(file):
    """
    Process an uploaded CSV file and bulk-create ProgrammaticPage draft stubs.
    Returns dict: {created: list, duplicates: list, errors: list}
    """
    decoded = file.read().decode("utf-8-sig")  # utf-8-sig strips Excel BOM if present
    reader = csv.DictReader(io.StringIO(decoded))

    created = []
    duplicates = []
    errors = []

    for row_num, row in enumerate(reader, start=2):  # row 1 is the header
        keyword = row.get("keyword", "").strip()

        if not keyword:
            errors.append(f"Row {row_num}: empty keyword — skipped.")
            continue

        slug = slugify(keyword)

        if ProgrammaticPage.objects.filter(slug=slug).exists():
            duplicates.append(keyword)
            continue

        ProgrammaticPage.objects.create(
            keyword=keyword,
            slug=slug,
            master_template="",
            meta_title=row.get("meta_title", "").strip()[:60],
            meta_description=row.get("meta_description", "").strip()[:160],
            cta_text=row.get("cta_text", "").strip()[:200],
            cta_url=row.get("cta_url", "").strip(),
            status="draft",
            source="csv_import",
        )
        created.append(keyword)

    return {"created": created, "duplicates": duplicates, "errors": errors}
