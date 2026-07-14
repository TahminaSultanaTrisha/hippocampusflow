"""Image storage behind a tiny interface.

Today: files on local disk under uploads/{user_id}/{scan_id}.{ext}.
Later: swap the inside of this class for S3/R2 uploads -- the API routes
never know the difference. This is the 'cloud storage' seam from the
blueprint, implemented in its simplest correct form first.
"""
from pathlib import Path

from app.core.config import get_settings

_EXT_BY_TYPE = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


class LocalImageStorage:
    def __init__(self) -> None:
        self.root = Path(get_settings().upload_dir)

    @staticmethod
    def extension_for(content_type: str) -> str | None:
        return _EXT_BY_TYPE.get(content_type)

    def save(self, user_id: str, scan_id: str, data: bytes, ext: str) -> str:
        """Store the bytes; return the storage key recorded in the database."""
        key = f"{user_id}/{scan_id}.{ext}"
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def path_for(self, key: str) -> Path:
        return self.root / key


def get_storage() -> LocalImageStorage:
    return LocalImageStorage()
