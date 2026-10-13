"""Versioned content-addressed deterministic execution cache metadata.

No executable payloads or untrusted pickle files. Every cache hit requires
fresh, independently calculated dependency digests. A change invalidates only
consumers of that dependency; upstream literature extraction remains intact.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


class CacheIntegrityError(ValueError):
    """Missing/stale cache dependency or unsupported artifact encoding."""


def _bytes(value: Any) -> bytes:
    try:
        raw = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise CacheIntegrityError("cache content must be bounded plain JSON") from exc
    if len(raw) > 65536:
        raise CacheIntegrityError("cache artifact exceeds size budget")
    return raw


def fingerprint(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


@dataclass(frozen=True, slots=True)
class CacheEntry:
    task: str
    implementation_version: str
    artifact_sha256: str
    dependencies: tuple[tuple[str, str], ...]
    artifact_json: str


class ExecutionCache:
    """In-memory content-addressed cache; not a trusted evidence store."""

    def __init__(self) -> None:
        self._entries: dict[str, CacheEntry] = {}

    def put(self, task: str, version: str, artifact: Any,
            dependencies: Mapping[str, str]) -> CacheEntry:
        if (not task or len(task) > 128 or not version or len(version) > 32
            or len(dependencies) > 64 or not all(
                isinstance(key, str) and key and isinstance(sha, str) and len(sha) == 64
                and all(c in "0123456789abcdef" for c in sha)
                for key, sha in dependencies.items())):
            raise CacheIntegrityError("invalid cache identity or dependency hash")
        raw = _bytes(artifact)
        entry = CacheEntry(task, version, hashlib.sha256(raw).hexdigest(),
                           tuple(sorted(dependencies.items())), raw.decode("utf-8"))
        self._entries[task] = entry
        return entry

    def get(self, task: str, version: str, dependencies: Mapping[str, str]) -> tuple[str, Any | None]:
        entry = self._entries.get(task)
        if entry is None:
            return "MISS", None
        if entry.implementation_version != version or entry.dependencies != tuple(sorted(dependencies.items())):
            return "STALE", None
        if hashlib.sha256(entry.artifact_json.encode("utf-8")).hexdigest() != entry.artifact_sha256:
            raise CacheIntegrityError("cached artifact mutated")
        return "HIT", json.loads(entry.artifact_json)
