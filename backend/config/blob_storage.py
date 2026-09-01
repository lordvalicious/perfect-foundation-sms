"""Django storage backend backed by Vercel Blob.

Uploaded files are stored in the project's Vercel Blob store instead of the
local filesystem (which is read‑only on the serverless runtime). The public
URL returned by the Blob store is stored as the file name so ``url()`` can
resolve it without an extra API call. Access is public but unguessable
(random pathname suffix).
"""

import os

import vercel_blob
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

_PUT_TIMEOUT = 45
_BLOB_HOST_SUFFIX = ".blob.vercel-storage.com"


@deconstructible
class VercelBlobStorage(Storage):
    """Django storage that saves files to a Vercel Blob store.

    The connection token is read from the ``BLOB_READ_WRITE_TOKEN`` environment
    variable. Uploads use ``addRandomSuffix`` so pathnames are unique; the full
    public URL is stored as the file name so ``url()`` can rebuild it without
    extra requests.
    """

    def __init__(self, **options):
        self._token = os.environ.get("BLOB_READ_WRITE_TOKEN", "")
        if not self._token:
            raise ImproperlyConfigured(
                "BLOB_READ_WRITE_TOKEN must be set to use VercelBlobStorage."
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_url(self, name):
        """Return the full HTTP URL for a stored file name."""
        if name.startswith(("http://", "https://")):
            return name
        return settings.MEDIA_URL.rstrip("/") + "/" + name.replace("\\", "/")

    def _is_blob_url(self, url):
        """True if the URL points to a Vercel Blob object."""
        if not url:
            return False
        host = url.split("/")[2].lower()  # netloc after scheme
        return host.endswith(_BLOB_HOST_SUFFIX)

    # ------------------------------------------------------------------
    # Storage API
    # ------------------------------------------------------------------

    def _open(self, name, mode="rb"):
        """Read a file from the blob store and return a Django ContentFile."""
        url = self._resolve_url(name)
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return ContentFile(resp.content)

    def _save(self, name, content):
        """Upload the given content to the Vercel Blob store."""
        content.seek(0)
        data = content.read()
        result = vercel_blob.put(
            name.replace("\\", "/"),
            data,
            {"addRandomSuffix": True},
            timeout=_PUT_TIMEOUT,
        )
        return result["url"]

    def url(self, name):
        """Return the absolute URL for a stored file."""
        return self._resolve_url(name)

    def delete(self, name):
        """Remove the file from the blob store (if it is a blob URL)."""
        url = self._resolve_url(name)
        if self._is_blob_url(url):
            vercel_blob.delete([url])

    def exists(self, name):
        """Return True if the file exists in the blob store."""
        url = self._resolve_url(name)
        if not self._is_blob_url(url):
            return False
        try:
            vercel_blob.head(url)
            return True
        except Exception:  # includes BlobRequestError, network errors
            return False

    def size(self, name):
        """Return the file size in bytes from the blob metadata."""
        url = self._resolve_url(name)
        if self._is_blob_url(url):
            return int(vercel_blob.head(url).get("size", 0))
        raise ValueError(f"Unknown file size for {name}")

    def get_available_name(self, name, max_length=None):
        # Every upload gets a random pathname suffix from the Blob store,
        # so there is never a collision to avoid.
        return name

    def path(self, name):
        raise NotImplementedError(
            "VercelBlobStorage has no local path; use url() instead."
        )