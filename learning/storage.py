from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateMediaStorage(FileSystemStorage):
    """
    Store learning materials outside the public media directory.
    Files must be delivered through an authorized Django view.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "location",
            str(settings.PRIVATE_MEDIA_ROOT),
        )
        kwargs.setdefault("base_url", "/private-media/")
        super().__init__(*args, **kwargs)