"""SHA-256 based JSON cache for CV extraction results.

We key on the file content hash (not the filename) so that renamed files or
duplicated CVs also hit the cache. Cache entries are plain JSON files under
``.cvsagent_cache/`` and are safe to delete at any time.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .console import console


class ExtractionCache:
    """Minimal file-backed cache. Each entry is one JSON file per file-hash."""

    def __init__(self, cache_dir: Path, enabled: bool = True) -> None:
        self.cache_dir = Path(cache_dir)
        self.enabled = enabled
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    # --- lookup helpers ---------------------------------------------------
    def _path_for(self, sha: str) -> Path:
        return self.cache_dir / f"{sha}.json"

    def get(self, sha: Optional[str]) -> Optional[Dict[str, Any]]:
        if not self.enabled or not sha:
            return None
        path = self._path_for(sha)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            console.warn("Cache", f"Corrupt cache entry {path.name}: {exc}")
            return None

    def set(self, sha: Optional[str], data: Dict[str, Any]) -> None:
        if not self.enabled or not sha or not data:
            return
        path = self._path_for(sha)
        try:
            path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
        except OSError as exc:
            console.warn("Cache", f"Failed to write cache entry {path.name}: {exc}")

    def clear(self) -> int:
        """Delete every cached entry. Returns the number of files removed."""
        if not self.cache_dir.exists():
            return 0
        removed = 0
        for path in self.cache_dir.glob("*.json"):
            try:
                path.unlink()
                removed += 1
            except OSError:
                pass
        return removed
