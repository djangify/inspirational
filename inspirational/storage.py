# stream/storage.py
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os


class SecureFileStorage(FileSystemStorage):
    def __init__(self):
        secure_root = os.path.join(settings.MEDIA_ROOT, "secure_downloads")
        super().__init__(location=secure_root)

    def get_valid_name(self, name):
        name = super().get_valid_name(name)
        return name.replace("public/", "")


class PublicMediaStorage(FileSystemStorage):
    def __init__(self):
        public_root = os.path.join(settings.MEDIA_ROOT, "public")
        super().__init__(location=public_root, base_url=settings.MEDIA_URL + "public/")

    def get_valid_name(self, name):
        name = super().get_valid_name(name)
        return name.replace("public/", "")

    def url(self, name):
        url = super().url(name)
        if not url.startswith(settings.MEDIA_URL):
            url = settings.MEDIA_URL.rstrip("/") + "/public/" + name.lstrip("/")

        return url


# Create instances
secure_storage = SecureFileStorage()
public_storage = PublicMediaStorage()
