import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage

secure_storage = FileSystemStorage(
    location=os.path.join(settings.BASE_DIR, settings.PROTECTED_MEDIA_ROOT),
)
