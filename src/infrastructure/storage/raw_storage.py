"""Raw HTML / Web Payload Storage implementation using File System and Database fallback."""

import hashlib
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import get_settings
from src.core.exceptions import RawStorageError
from src.core.logging import get_logger
from src.infrastructure.db.models.product import RawPayloadORM
from src.interfaces.raw_storage import RawHTMLStorageInterface

logger = get_logger(__name__)


class FileSystemRawStorage(RawHTMLStorageInterface):
    """File System raw payload storage indexed by SHA256 content hashes."""

    def __init__(
        self,
        base_dir: Path | str | None = None,
        db_session: AsyncSession | None = None,
    ) -> None:
        settings = get_settings()
        self.base_dir = Path(base_dir or settings.RAW_STORAGE_DIR)
        self.db_session = db_session
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_raw_html(self, url: str, site_id: str, html_content: str) -> str:
        """Save raw HTML payload to file system indexed by content hash key.

        Args:
            url: Page canonical URL.
            site_id: Site identifier.
            html_content: Raw HTML text string.

        Returns:
            SHA256 hex string storage ID.
        """
        try:
            content_hash = hashlib.sha256(html_content.encode("utf-8")).hexdigest()
            site_dir = self.base_dir / site_id
            site_dir.mkdir(parents=True, exist_ok=True)

            file_path = site_dir / f"{content_hash}.html"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            # DB fallback storage if session provided
            if self.db_session:
                raw_orm = RawPayloadORM(
                    id=content_hash,
                    site_id=site_id,
                    url=url,
                    html_content=html_content,
                )
                self.db_session.add(raw_orm)
                await self.db_session.flush()

            logger.debug("Saved raw HTML payload", storage_id=content_hash, site_id=site_id)
            return content_hash

        except Exception as exc:
            raise RawStorageError(
                f"Failed to save raw HTML payload for URL {url}", details={"error": str(exc)}
            ) from exc

    async def get_raw_html(self, storage_id: str) -> str | None:
        """Retrieve raw HTML content by storage ID hash key."""
        try:
            # Search file system across site subdirectories
            for file_path in self.base_dir.rglob(f"{storage_id}.html"):
                if file_path.exists():
                    with open(file_path, encoding="utf-8") as f:
                        return f.read()

            # DB fallback check if session provided
            if self.db_session:
                stmt = RawPayloadORM.__table__.select().where(RawPayloadORM.id == storage_id)
                res = await self.db_session.execute(stmt)
                row = res.fetchone()
                if row:
                    return str(row.html_content)

            return None
        except Exception as exc:
            raise RawStorageError(
                f"Failed to read raw HTML payload {storage_id}", details={"error": str(exc)}
            ) from exc

    async def exists(self, storage_id: str) -> bool:
        """Check if raw HTML payload exists in storage."""
        for file_path in self.base_dir.rglob(f"{storage_id}.html"):
            if file_path.exists():
                return True
        return False
