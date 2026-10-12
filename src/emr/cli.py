"""Safe CLI for static inspection, planning and schema validation."""

from __future__ import annotations

import argparse
import json
import sys
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
    paper = commands.add_parser("paper", help="offline, source-grounded PDF literature operations")
    pdf_commands = paper.add_subparsers(dest="paper_action", required=True)
    scan = pdf_commands.add_parser("scan", help="extract unverified candidates from local PDF")
    scan.add_argument("source", type=Path)
    matrix = pdf_commands.add_parser("matrix", help="combine existing paper-record JSON files")
    matrix.add_argument("records", nargs="+", type=Path)
    model = commands.add_parser("model", help="validate inert JSON model facts")
    model_commands = model.add_subparsers(dest="model_action", required=True)
    for action in ("validate", "tasks"):
        model_commands.add_parser(
            action, help="check model facts" if action == "validate" else "plan unexecuted response tasks"
        ).add_argument("source", type=Path)
    args = parser.parse_args(argv)

    if args.command == "inspect":
        print(json.dumps({"version": __version__, "mode": "phase2-offline-pdf"}))
        return 0

    if args.command == "paper":
        from emr.adapters.pdf_extract import PdfExtractionError, extract_pdf
        from jsonschema.exceptions import ValidationError

        from emr.core.papers import (
            literature_matrix,
            paper_record,
            validate_literature_matrix,
            validate_paper_record,
        )

        try:
            if args.paper_action == "scan":
                output = paper_record(extract_pdf(args.source))
                validate_paper_record(output)
            else:
                from emr.core.state import MAX_STATE_BYTES, _no_duplicates, _reject_number_constant

                records = []
                for source in args.records:
                    with source.open("rb") as stream:
                        raw = stream.read(MAX_STATE_BYTES + 1)
                    if len(raw) > MAX_STATE_BYTES:
                        raise ValueError("oversized record")
                    record = json.loads(
                        raw.decode("utf-8"),
                        object_pairs_hook=_no_duplicates,
                        parse_constant=_reject_number_constant,
                    )
                    validate_paper_record(record)
                    records.append(record)
                output = literature_matrix(records)
                validate_literature_matrix(output)
            print(json.dumps(output, ensure_ascii=False, indent=2))
            return 0
        except (PdfExtractionError, OSError, ValueError, KeyError, UnicodeError, ValidationError):
            print(f"paper operation failed: invalid or unreadable input", file=sys.stderr)
            return 2

    if args.command == "model":
        from emr.core.state import _no_duplicates, _reject_number_constant
        from emr.domain.game import (
            MAX_MODEL_BYTES, GameSpecValidationError, build_best_response_tasks,
            validate_game_spec,
        )

        try:
            if args.source.is_symlink() or not args.source.is_file():
                raise GameSpecValidationError("model must be a regular local JSON file")
            with args.source.open("rb") as handle:
                raw = handle.read(MAX_MODEL_BYTES + 1)
            if len(raw) > MAX_MODEL_BYTES:
                raise GameSpecValidationError("model exceeds size limit")
            data = json.loads(
                raw.decode("utf-8"), object_pairs_hook=_no_duplicates,
                parse_constant=_reject_number_constant,
            )
            checked = validate_game_spec(data)
            output = {"classification": checked.classification, "warnings": checked.warnings,
                      "status": "STRUCTURALLY_VALID_NOT_SOLVED"}
            if args.model_action == "tasks":
                output["tasks"] = [asdict(t) for t in build_best_response_tasks(checked)]
            print(json.dumps(output, indent=2))
            return 0
        except (OSError, UnicodeError, ValueError, RecursionError):
            print("model operation failed: invalid or unsafe input", file=sys.stderr)
            return 2

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
