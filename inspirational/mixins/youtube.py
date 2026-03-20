# mixins/youtube.py
from django.db import models


class YouTubeVideoMixin(models.Model):
    youtube_url = models.URLField(blank=True, null=True)

    class Meta:
        abstract = True

    def get_video_id(self):
        if not self.youtube_url:
            return None

        url = self.youtube_url.strip()

        if "youtube.com/watch?v=" in url:
            return url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            return url.split("/")[-1].split("?")[0]
        elif "youtube.com/embed/" in url:
            return url.split("/embed/")[1].split("?")[0]

        return None

    def get_youtube_embed_url(self):
        video_id = self.get_video_id()
        if video_id:
            return f"https://www.youtube-nocookie.com/embed/{video_id}"
        return None

    def get_youtube_thumbnail(self):
        video_id = self.get_video_id()
        if video_id:
            return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        return None
