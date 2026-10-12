"""Small, local, write-once artifact store and in-memory invalidation DAG.

Phase 1 deliberately does not implement distributed synchronization, locks or
content-addressed caches. The file creation uses a same-directory temporary
file and atomic hard-link to avoid replacing a pre-existing destination.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from emr.core.contracts import ArtifactRef, ArtifactStatus


class ArtifactStore:
    """Write immutable bytes under a trusted root and record stale dependents.

    The root is assumed to be a repository-owned directory, not writable by
    untrusted users. Paths from PDFs and LLMs still require explicit approval.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._states: dict[str, ArtifactStatus] = {}
        self._downstream: dict[str, set[str]] = defaultdict(set)

    def _safe_path(self, relative: str) -> Path:
        candidate = Path(relative)
        if not relative or candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("artifact path must be nonempty and repository-relative")
        dest = (self.root / candidate).resolve()
        if not dest.is_relative_to(self.root) or dest == self.root:
            raise ValueError("artifact path escapes trusted root")
        return dest

    def write(
        self,
        relative: str,
        content: bytes,
        *,
        created_by: str,
        schema_version: str = "1",
    ) -> ArtifactRef:
        """Create once, never overwrite, and return a SHA-256 provenance ref."""
        if not created_by.strip():
            raise ValueError("created_by is required")
        destination = self._safe_path(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(destination)
        temporary: str | None = None
        try:
            with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
                temporary = stream.name
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temporary, destination)
        finally:
            if temporary is not None:
                Path(temporary).unlink(missing_ok=True)
        self._states[relative] = ArtifactStatus.VALID
        return ArtifactRef(
            uri=relative,
            sha256=hashlib.sha256(content).hexdigest(),
            schema_version=schema_version,
            created_by=created_by,
            created_at=datetime.now(UTC).isoformat(),
        )

    def add_dependency(self, parent: str, child: str) -> None:
        """Record one dependency: changes in parent stale its descendants."""
        if parent not in self._states or child not in self._states:
            raise KeyError("dependency endpoints must already exist")
        if parent == child:
            raise ValueError("self-dependency is not allowed")
        # A dependency graph must remain acyclic for deterministic staleness.
        pending = [child]
        visited: set[str] = set()
        while pending:
            current = pending.pop()
            if current == parent:
                raise ValueError("cyclic artifact dependency")
            if current not in visited:
                visited.add(current)
                pending.extend(self._downstream[current])
        self._downstream[parent].add(child)

    def status(self, relative: str) -> ArtifactStatus:
        """Return the tracked state or reject an unknown artifact."""
        return self._states[relative]

    def invalidate(self, relative: str, *, revoke: bool = False) -> frozenset[str]:
        """Mark the selected artifact and its transitive descendants stale.

        Only the selected artifact may be REVOKED. This changes metadata but
        does not delete immutable files; persisted state is a later-phase task.
        """
        if relative not in self._states:
            raise KeyError(relative)
        changed: set[str] = set()
        pending = [relative]
        while pending:
            current = pending.pop()
            if current in changed:
                continue
            changed.add(current)
            self._states[current] = (
                ArtifactStatus.REVOKED
                if revoke and current == relative
                else ArtifactStatus.STALE
            )
            pending.extend(self._downstream[current])
        return frozenset(changed)
