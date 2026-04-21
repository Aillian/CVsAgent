"""Small utility helpers used across the package."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, List, Optional


def join_list(lst: Optional[Iterable[str]], separator: str = ", ") -> str:
    """Join an iterable of strings with a separator, handling None/empty safely."""
    if not lst:
        return ""
    return separator.join(str(x) for x in lst if x is not None and str(x) != "")


def file_sha256(path: Path, chunk_size: int = 65536) -> str:
    """Compute the SHA-256 of a file. Used for the extraction cache key."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def mask_api_key(key: Optional[str]) -> str:
    """Return a safely-masked representation of an API key for logging."""
    if not key:
        return "<unset>"
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}…{key[-4:]}"


def truncate(text: str, max_chars: int = 120) -> str:
    """Truncate long strings for display in logs."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"


def human_count(xs: List) -> str:
    """Return a human-friendly count string."""
    n = len(xs)
    return f"{n} item" if n == 1 else f"{n} items"
