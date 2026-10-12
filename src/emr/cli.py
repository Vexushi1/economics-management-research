"""Safe CLI for static inspection, planning and schema validation."""

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
from emr.core.state import ResearchStateStore, _validator


def main(argv: Sequence[str] | None = None) -> int:
    """Offline CLI entrypoint; does not evaluate formulas or run external commands."""
    parser = argparse.ArgumentParser(prog="emr", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("inspect", help="show interface version and implementation status")
    validate = commands.add_parser("validate", help="validate Skill registry and research-state schema")
    validate.add_argument("--state", type=Path, help="optional state JSON to validate")
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
        _validator()
        if args.state is not None:
            ResearchStateStore(args.state.parent, create=False).load(args.state.name)
        print(json.dumps({"registry": "valid", "schema_document": "validated", "state": "valid" if args.state else "not_checked"}))
        return 0

    request = ResearchRequest(research_type=ResearchType(args.type), description=args.description)
    result = route_request(request, registry)
    print(json.dumps(asdict(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
