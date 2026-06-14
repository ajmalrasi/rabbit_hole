"""On-disk RSS feed cache with TTL and HTTP conditional-request support.

Why: fetching all 8 feeds on every pipeline run is wasteful and slow.
This cache layer:
  - saves raw feed content to disk after each successful fetch
  - skips re-downloading when the cached copy is younger than TTL
  - sends ``If-Modified-Since`` / ``If-None-Match`` (ETag) headers so feeds
    that haven't changed return 304 with zero payload transfer
  - falls back to a stale cached copy when the upstream is unreachable
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.logging_config import get_logger

logger = get_logger(__name__)

_META_SUFFIX = ".meta.json"


class FeedCache:
    """Manages a directory of raw feed XML files and their metadata.

    Each feed is stored as two files:
        <cache_dir>/<slug>.xml          – raw XML/Atom/RSS bytes
        <cache_dir>/<slug>.meta.json    – {fetched_at, etag, last_modified}
    """

    def __init__(self, cache_dir: str | Path, ttl_minutes: int = 60) -> None:
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._ttl_seconds = ttl_minutes * 60

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _slug(name: str) -> str:
        """Turn a source name into a safe filename component."""
        return "".join(c if c.isalnum() else "_" for c in name.lower()).strip("_")

    def _xml_path(self, name: str) -> Path:
        return self._dir / f"{self._slug(name)}.xml"

    def _meta_path(self, name: str) -> Path:
        return self._dir / f"{self._slug(name)}{_META_SUFFIX}"

    def _load_meta(self, name: str) -> dict:
        path = self._meta_path(name)
        if path.exists():
            try:
                return json.loads(path.read_text())
            except Exception:
                pass
        return {}

    def _save_meta(self, name: str, meta: dict) -> None:
        self._meta_path(name).write_text(json.dumps(meta))

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def is_fresh(self, name: str) -> bool:
        """True if the cached copy exists and is within TTL."""
        meta = self._load_meta(name)
        fetched_at = meta.get("fetched_at")
        if not fetched_at:
            return False
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(fetched_at)).total_seconds()
        return age < self._ttl_seconds

    def get_cached(self, name: str) -> Optional[str]:
        """Return cached XML string or None if missing."""
        path = self._xml_path(name)
        if path.exists():
            return path.read_text(encoding="utf-8", errors="replace")
        return None

    def get_conditional_headers(self, name: str) -> dict[str, str]:
        """Return HTTP headers for a conditional GET (304 support)."""
        meta = self._load_meta(name)
        headers: dict[str, str] = {}
        if meta.get("etag"):
            headers["If-None-Match"] = meta["etag"]
        if meta.get("last_modified"):
            headers["If-Modified-Since"] = meta["last_modified"]
        return headers

    def save(self, name: str, content: str, etag: str = "", last_modified: str = "") -> None:
        """Persist new feed content and update metadata."""
        self._xml_path(name).write_text(content, encoding="utf-8")
        self._save_meta(name, {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "etag": etag,
            "last_modified": last_modified,
        })
        logger.debug("RSS cache saved for '%s'", name)

    def mark_unchanged(self, name: str) -> None:
        """Update ``fetched_at`` without rewriting the content (304 response)."""
        meta = self._load_meta(name)
        meta["fetched_at"] = datetime.now(timezone.utc).isoformat()
        self._save_meta(name, meta)
        logger.debug("RSS cache 304-refreshed for '%s'", name)

    def cache_path(self) -> Path:
        return self._dir
