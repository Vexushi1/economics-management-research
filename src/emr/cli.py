"""Safe CLI for Phase 1 static inspection, planning and structural checks."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from emr import __version__
from emr.core.contracts import ResearchRequest, ResearchType
from emr.core.registry import default_registry
from emr.core.router import route_request


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint; no external commands, API requests or model execution."""
    parser = argparse.ArgumentParser(prog="emr", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("inspect", help="show interface version and implementation status")
    commands.add_parser("validate", help="check registry and schema document structure")
    plan = commands.add_parser("plan", help="generate a static planning DAG")
    plan.add_argument("--type", required=True, choices=[t.value for t in ResearchType])
    plan.add_argument("--description", required=True)
    args = parser.parse_args(argv)

    if args.command == "inspect":
        print(json.dumps({"version": __version__, "mode": "phase1-skeleton"}))
        return 0

    registry = default_registry()
    registry.validate()
    if args.command == "validate":
        # This only checks that the bundled JSON document is well formed and
        # has the expected schema identity. It is NOT a complete JSON Schema
        # validator; a full standards-compliant validator comes later.
        schema_path = Path(__file__).resolve().parents[2] / "schemas" / "research-state.schema.json"
        if not schema_path.exists():
            # Editable/installed distributions need a package resource strategy
            # before claiming schema availability. Phase 1 CI runs editable.
            raise FileNotFoundError("research-state schema is unavailable")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        if "$schema" not in schema or "properties" not in schema:
            raise ValueError("research-state schema lacks required fields")
        print(json.dumps({"registry": "valid", "schema_document": "well_formed_only"}))
        return 0

    request = ResearchRequest(
        research_type=ResearchType(args.type),
        description=args.description,
    )
    result = route_request(request, registry)
    print(json.dumps(asdict(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
