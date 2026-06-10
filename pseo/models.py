# pseo/models.py
from django.db import models
from django.utils.text import slugify


class ProgrammaticPage(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending_review", "Pending Review"),
        ("published", "Published"),
    ]
    SOURCE_CHOICES = [
        ("manual", "Manual"),
        ("csv_import", "CSV Import"),
    ]

    keyword = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    master_template = models.TextField(
        help_text="Write your core content once. Use [Topic] as the placeholder — "
                  "it will be replaced with the keyword when content is generated."
    )
    generated_content = models.TextField(blank=True, null=True)
    h1_heading = models.CharField(max_length=200, blank=True)
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    cta_text = models.CharField(
        max_length=200,
        blank=True,
        help_text="The pitch line shown at the bottom of the page. Supports [Topic] substitution.",
    )
    cta_url = models.URLField(
        blank=True,
        help_text="The link the CTA button points to.",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="draft"
    )
    source = models.CharField(
        max_length=20, choices=SOURCE_CHOICES, default="manual"
    )
    noindex = models.BooleanField(
        default=False,
        help_text="Tick to hide this page from search engines (adds noindex meta tag).",
    )
    publish_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Set a future date/time to auto-publish. Leave blank to publish manually.",
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Programmatic Page"
        verbose_name_plural = "Programmatic Pages"

    def __str__(self):
        return self.keyword

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.keyword)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("pseo:detail", kwargs={"slug": self.slug})
