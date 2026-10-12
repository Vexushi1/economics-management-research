"""Schema-validated, write-once JSON research snapshots.

Research snapshots are inert data, not formulas, code, or trusted assertions.
Files are immutable once saved; revisions use new names and remain auditable.
The store assumes a trusted, single-writer directory. Cross-process locks,
symlink races in attacker-writable directories and distributed synchronization
are deliberately *outside* this stage's guarantees.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from importlib.resources import files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

MAX_STATE_BYTES = 1024 * 1024
_RFC3339 = re.compile(
    r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})$"
)


def _is_rfc3339_datetime(value: object) -> bool:
    """Strict timestamp check independent of optional format packages."""
    if not isinstance(value, str) or _RFC3339.fullmatch(value) is None:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


_FORMAT_CHECKER = FormatChecker()
_FORMAT_CHECKER.checks("date-time")(_is_rfc3339_datetime)


class StateValidationError(ValueError):
    """A research state is invalid or contains unsafe/ambiguous JSON."""


@dataclass(frozen=True, slots=True)
class StateSnapshot:
    """Stable identifier and checksum of a persisted snapshot."""

    name: str
    sha256: str
    length: int


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate keys, which otherwise create ambiguous research state."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise StateValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_number_constant(value: str) -> None:
    """Reject nonstandard NaN/Infinity JSON number constants."""
    raise StateValidationError(f"invalid JSON number: {value}")


def _validator() -> Draft202012Validator:
    """Load only our bundled, reviewed schema; never fetch remote schemas."""
    source = files("emr").joinpath("schemas/research-state.schema.json")
    schema = json.loads(source.read_text(encoding="utf-8"))
    if "$ref" in str(schema):
        raise StateValidationError("external or internal references are not supported")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=_FORMAT_CHECKER)


def validate_research_state(state: Mapping[str, Any]) -> dict[str, Any]:
    """Validate metadata and return JSON-normalized data, without executing text.

    Enforces Draft 2020-12 JSON Schema including formats. Unknown keys fail.
    JSON serialization is limited to 1 MiB. This does not claim the evidence,
    formulas or scientific assertions in the metadata have been proven.
    """
    try:
        text = json.dumps(state, ensure_ascii=False, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError, RecursionError) as exc:
        raise StateValidationError("state is not bounded, valid JSON") from exc
    if len(text.encode("utf-8")) > MAX_STATE_BYTES:
        raise StateValidationError("state exceeds maximum serialized size")
    try:
        normalized = json.loads(
            text, object_pairs_hook=_no_duplicates, parse_constant=_reject_number_constant
        )
        _validator().validate(normalized)
    except (RecursionError, ValueError) as exc:
        if isinstance(exc, StateValidationError):
            raise
        raise StateValidationError("state validation failed") from exc
    except Exception as exc:
        # jsonschema.ValidationError / SchemaError: no raw data in messages.
        raise StateValidationError("research-state schema rejected input") from exc
    return normalized


class ResearchStateStore:
    """Save/read immutable snapshots beneath a caller-owned directory.

    The caller selects a per-revision JSON name. Existing files are never
    silently overwritten. Verification compares the stored bytes to an
    optional expected SHA-256; local disk contents are always revalidated.
    """

    def __init__(self, root: Path, *, create: bool = True) -> None:
        self.root = root.resolve()
        if create:
            self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        candidate = Path(name)
        if (
            not name
            or candidate.is_absolute()
            or ".." in candidate.parts
            or candidate.suffix != ".json"
        ):
            raise ValueError("state name must be a relative .json path")
        path = (self.root / candidate).resolve()
        if path == self.root or not path.is_relative_to(self.root):
            raise ValueError("state path escapes trusted root")
        return path

    def save(self, name: str, state: Mapping[str, Any]) -> StateSnapshot:
        """Atomically create a validated, immutable file with SHA-256 checksum.

        Uses a temp file + same-filesystem hard link, not os.replace, so an
        existing version cannot be accidentally overwritten. Single writer
        and trusted directory are preconditions, not enforced distributed locks.
        """
        normalized = validate_research_state(state)
        content = (json.dumps(normalized, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode(
            "utf-8"
        )
        if len(content) > MAX_STATE_BYTES:
            raise StateValidationError("serialized snapshot exceeds size limit")
        path = self._path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() or path.is_symlink():
            raise FileExistsError(path)
        tmp: str | None = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
                tmp = stream.name
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(tmp, path)
        finally:
            if tmp is not None:
                Path(tmp).unlink(missing_ok=True)
        return StateSnapshot(name=name, sha256=hashlib.sha256(content).hexdigest(), length=len(content))

    def load(self, name: str, *, expected_sha256: str | None = None) -> dict[str, Any]:
        """Read and validate a snapshot, optionally checking exact byte integrity."""
        path = self._path(name)
        if (self.root / name).is_symlink() or not path.is_file():
            raise ValueError("state must be a regular, non-symlink JSON file")
        with path.open("rb") as handle:
            raw = handle.read(MAX_STATE_BYTES + 1)
        if len(raw) > MAX_STATE_BYTES:
            raise StateValidationError("stored snapshot exceeds size limit")
        sha = hashlib.sha256(raw).hexdigest()
        if expected_sha256 is not None and sha != expected_sha256:
            raise StateValidationError("research state SHA-256 mismatch")
        try:
            data = json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=_no_duplicates,
                parse_constant=_reject_number_constant,
            )
        except StateValidationError:
            raise
        except (UnicodeDecodeError, ValueError, RecursionError) as exc:
            raise StateValidationError("invalid stored JSON") from exc
        if not isinstance(data, dict):
            raise StateValidationError("research state must be an object")
        return validate_research_state(data)
