"""
Export draft news posts to JSON, optionally redirecting their URLs to the
blog list and/or deleting them once exported.

Usage:
    # Dry run — just list drafts, nothing written or changed
    python manage.py export_draft_posts

    # Export drafts to a JSON file
    python manage.py export_draft_posts --output=draft_posts.json

    # Export, add a redirect (old-slug -> /blog/) for each drafted post,
    # then delete the drafts from the database
    python manage.py export_draft_posts --output=draft_posts.json --redirect --delete
"""
import json

from django.contrib.redirects.models import Redirect
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.utils import timezone

from news.models import Post


class Command(BaseCommand):
    help = "List/export draft news posts, with optional redirect + delete."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default=None,
            help="Write the drafts to this JSON file (e.g. draft_posts.json).",
        )
        parser.add_argument(
            "--redirect",
            action="store_true",
            help="Create a 301 redirect from each draft's URL to /blog/ "
            "(uses django.contrib.redirects, already installed on this site).",
        )
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete the drafts after exporting (and redirecting, if requested). "
            "Requires --output to have been used at least once already — "
            "this flag will not run without --output in the same call.",
        )

    def handle(self, *args, **options):
        output = options["output"]
        do_redirect = options["redirect"]
        do_delete = options["delete"]

        if do_delete and not output:
            self.stderr.write(
                self.style.ERROR(
                    "--delete requires --output so you keep a copy of what's removed."
                )
            )
            return

        drafts = Post.objects.filter(status="draft").order_by("title")

        if not drafts.exists():
            self.stdout.write("No draft posts found.")
            return

        self.stdout.write(f"Found {drafts.count()} draft post(s):\n")
        for p in drafts:
            self.stdout.write(f"  [{p.id}] {p.slug}  —  {p.title}")

        if not output:
            self.stdout.write(
                "\n(Dry run — pass --output=filename.json to export these.)"
            )
            return

        data = []
        for p in drafts:
            data.append(
                {
                    "id": p.id,
                    "title": p.title,
                    "slug": p.slug,
                    "status": p.status,
                    "content": p.content,
                    "content_type": p.content_type,
                    "category": p.category.name if p.category_id else None,
                    "category_slug": p.category.slug if p.category_id else None,
                    "tags": list(p.tags.values_list("name", flat=True)),
                    "featured": p.featured,
                    "created": p.created.isoformat() if p.created else None,
                    "updated": p.updated.isoformat() if p.updated else None,
                    "publish_date": p.publish_date.isoformat()
                    if p.publish_date
                    else None,
                    "image_url": p.get_image_url(),
                    "external_image_url": p.external_image_url,
                    "thumbnail_url": p.get_thumbnail_url(),
                    "youtube_url": p.youtube_url,
                    "video_url": p.video_url,
                    "audio_url": p.audio_url,
                    "audio_file": p.audio_file.url if p.audio_file else None,
                    "resource_url": p.get_resource_url(),
                    "resource_title": p.resource_title,
                    "resource_type": p.resource_type,
                    "meta_title": p.meta_title,
                    "meta_description": p.meta_description,
                    "meta_keywords": p.meta_keywords,
                }
            )

        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(f"\nExported {len(data)} draft(s) to {output}"))

        if do_redirect:
            site = Site.objects.get_current()
            created_count = 0
            for p in drafts:
                old_path = f"/{p.slug}/"
                redirect, created = Redirect.objects.update_or_create(
                    site=site,
                    old_path=old_path,
                    defaults={"new_path": "/blog/"},
                )
                created_count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Added/updated {created_count} redirect(s) -> /blog/"
                )
            )

        if do_delete:
            count = drafts.count()
            drafts.delete()
            self.stdout.write(
                self.style.SUCCESS(f"Deleted {count} draft post(s) from the database.")
            )
