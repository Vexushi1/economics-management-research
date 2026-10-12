"""Phase 3 inert economic model facts and bounded expression-DSL validator.

Untrusted document/LLM strings are *never* interpreted as Python or SymPy
expressions. Inputs must already be structured JSON-compatible data; valid
syntax does not imply economically valid assumptions, an optimum, or a proof.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from importlib.resources import files
from typing import Any, Literal

from jsonschema import Draft202012Validator, ValidationError

MAX_MODEL_BYTES = 65_536
MAX_EXPRESSION_NODES = 512
MAX_EXPRESSION_DEPTH = 24


class GameSpecValidationError(ValueError):
    """The model is structurally unsafe, incomplete, or temporally inconsistent."""


ModelClassification = Literal[
    "static_sequential_game", "stochastic_sequential_game",
    "static_simultaneous_game", "stochastic_simultaneous_game",
]


@dataclass(frozen=True, slots=True)
class ValidatedGameSpec:
    """A validated, inert model snapshot, not a solved game or proof."""

    _payload: str
    classification: ModelClassification
    warnings: tuple[str, ...]

    @property
    def data(self) -> dict[str, Any]:
        """Return a fresh copy: callers cannot mutate a previously audited snapshot."""
        return json.loads(self._payload)


@dataclass(frozen=True, slots=True)
class BestResponseTask:
    """A proposed backward-induction step, explicitly not a best response."""

    player_id: str
    stage: int
    control_symbol: str
    information_set: str
    status: Literal["NOT_SOLVED"] = "NOT_SOLVED"


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    """Load only a bundled schema, with no network-based reference resolution."""
    schema = json.loads(
        files("emr").joinpath("schemas/model-spec.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    if schema.get("x-audit-limits") != {
        "max_json_bytes": MAX_MODEL_BYTES,
        "max_expr_nodes": MAX_EXPRESSION_NODES,
        "max_expr_depth": MAX_EXPRESSION_DEPTH,
        "max_total_symbols": 64,
        "max_stage_count": 12,
        "numeric_encoding": "bounded decimal strings; exact conversion via decimal.Decimal",
        "operators": ["const", "symbol", "neg", "add", "mul", "sub", "div", "pow"],
    }:
        raise GameSpecValidationError("model schema and runtime expression limits diverged")
    return Draft202012Validator(schema)


def _bounded_json(data: Mapping[str, Any]) -> dict[str, Any]:
    """Reject host-language objects and oversized models before schema traversal."""
    if not isinstance(data, Mapping):
        raise GameSpecValidationError("model must be a structured JSON object")
    try:
        encoded = json.dumps(data, ensure_ascii=False, allow_nan=False, sort_keys=True)
        if len(encoded.encode("utf-8")) > MAX_MODEL_BYTES:
            raise GameSpecValidationError("model exceeds byte budget")
        result = json.loads(encoded)
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        if isinstance(exc, GameSpecValidationError):
            raise
        raise GameSpecValidationError("model is not bounded JSON data") from exc
    if not isinstance(result, dict):
        raise GameSpecValidationError("model root must be an object")
    return result


def _expression_nodes(model: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Walk only designated AST roots; cap depth/count *before* JSON Schema recursion."""
    roots: list[Any] = []
    for player in model.get("players", []):
        if isinstance(player, dict):
            roots.append(player.get("objective"))
    for condition in model.get("constraints", []):
        if isinstance(condition, dict):
            roots.extend((condition.get("lhs"), condition.get("rhs")))
    found: list[dict[str, Any]] = []
    pending = [(root, 1) for root in roots]
    while pending:
        current, depth = pending.pop()
        if depth > MAX_EXPRESSION_DEPTH:
            raise GameSpecValidationError("expression depth budget exceeded")
        if not isinstance(current, dict):
            raise GameSpecValidationError("expression must be a structured AST node")
        found.append(current)
        if len(found) > MAX_EXPRESSION_NODES:
            raise GameSpecValidationError("expression node budget exceeded")
        operation = current.get("op")
        if operation in ("add", "mul"):
            children = current.get("args", [])
        elif operation in ("sub", "div"):
            children = [current.get("left"), current.get("right")]
        elif operation == "neg":
            children = [current.get("arg")]
        elif operation == "pow":
            children = [current.get("base")]
        else:
            children = []
        if not isinstance(children, list) or len(children) > 6:
            raise GameSpecValidationError("expression has invalid child count")
        pending.extend((child, depth + 1) for child in children)
    return found


def _decimal(value: str) -> Decimal:
    """Parse schema-validated bounded decimal notation, never a Python expression."""
    try:
        result = Decimal(value)
    except (TypeError, InvalidOperation) as exc:
        raise GameSpecValidationError("invalid domain boundary") from exc
    if not result.is_finite():
        raise GameSpecValidationError("nonfinite domain boundary")
    return result


def _check_domain(symbol: dict[str, Any]) -> None:
    domain = symbol["domain"]
    lower = _decimal(domain["lower"]) if domain["lower"] is not None else None
    upper = _decimal(domain["upper"]) if domain["upper"] is not None else None
    if lower is not None and upper is not None:
        if lower > upper or (lower == upper and not (domain["lower_closed"] and domain["upper_closed"])):
            raise GameSpecValidationError("empty or inverted strategy/parameter domain")
    kind = symbol["quantity_type"]
    if kind in ("probability", "price", "effort", "demand"):
        if lower is None or lower < 0:
            raise GameSpecValidationError(f"{kind} requires a nonnegative lower bound")
    if kind == "probability" and (upper is None or upper > 1):
        raise GameSpecValidationError("probability must have an upper bound no greater than one")
    if symbol["stochastic"]:
        if symbol["role"] != "state" or symbol["distribution_status"] == "NOT_APPLICABLE":
            raise GameSpecValidationError("stochastic status must describe a state with distribution status")
    elif symbol["distribution_status"] != "NOT_APPLICABLE":
        raise GameSpecValidationError("deterministic symbol cannot claim a stochastic distribution")


Unit = tuple[int, int, int]
ZERO_UNIT: Unit = (0, 0, 0)


def _check_denominators(nodes: list[dict[str, Any]], symbols: dict[str, dict[str, Any]]) -> None:
    """Fail closed on denominators whose nonzero property is not structurally known."""
    for node in nodes:
        if node.get("op") != "div":
            continue
        divisor = node["right"]
        if divisor["op"] == "const":
            if _decimal(divisor["value"]) == 0:
                raise GameSpecValidationError("literal division by zero")
            continue
        if divisor["op"] != "symbol":
            raise GameSpecValidationError("complex nonzero denominator requires later verification")
        symbol = symbols[divisor["name"]]
        domain = symbol["domain"]
        lower = _decimal(domain["lower"]) if domain["lower"] is not None else None
        upper = _decimal(domain["upper"]) if domain["upper"] is not None else None
        strictly_positive = lower is not None and (
            lower > 0 or (lower == 0 and not domain["lower_closed"])
        )
        strictly_negative = upper is not None and (
            upper < 0 or (upper == 0 and not domain["upper_closed"])
        )
        if symbol["role"] != "parameter" or not (strictly_positive or strictly_negative):
            raise GameSpecValidationError("potential zero denominator")


def _expr_unit(node: dict[str, Any], symbol_units: dict[str, Unit]) -> Unit:
    """Infer physical dimensions on a *bounded validated* AST, not numeric values."""
    op = node["op"]
    if op == "const":
        return ZERO_UNIT
    if op == "symbol":
        try:
            return symbol_units[node["name"]]
        except KeyError as exc:
            raise GameSpecValidationError("undeclared symbol in AST") from exc
    if op == "neg":
        return _expr_unit(node["arg"], symbol_units)
    if op in ("add", "sub"):
        args = node["args"] if op == "add" else [node["left"], node["right"]]
        dims = [_expr_unit(expr, symbol_units) for expr in args]
        if len(set(dims)) != 1:
            raise GameSpecValidationError("dimensionally inconsistent sum/subtraction")
        return dims[0]
    if op == "mul":
        dims = [_expr_unit(expr, symbol_units) for expr in node["args"]]
        return tuple(sum(d[i] for d in dims) for i in range(3))  # type: ignore[return-value]
    if op == "div":
        left, right = _expr_unit(node["left"], symbol_units), _expr_unit(
            node["right"], symbol_units
        )
        if node["right"]["op"] == "const" and _decimal(node["right"]["value"]) == 0:
            raise GameSpecValidationError("literal division by zero")
        return tuple(left[i] - right[i] for i in range(3))  # type: ignore[return-value]
    if op == "pow":
        dims = _expr_unit(node["base"], symbol_units)
        return tuple(x * node["exponent"] for x in dims)  # type: ignore[return-value]
    raise GameSpecValidationError("unsupported expression operation")


def check_information_sequence(model: Mapping[str, Any]) -> None:
    """Check that a decision cannot observe another action or state from the future.

    Only explicit signals are observable; unknown, undeclared or same-stage
    decision signals are rejected. A forecast would require a separately
    specified forecasting process and is not silently treated as a realization.
    """
    decisions = {d["id"]: d for d in model["decisions"]}
    infos = {i["id"]: i for i in model["information_sets"]}
    states = {s["name"] for s in model["symbols"] if s["role"] == "state"}
    signals = {s["id"]: s for s in model["signals"]}
    for signal in signals.values():
        if signal["kind"] == "decision":
            decision = decisions.get(signal["decision_id"])
            if decision is None or signal["available_stage"] <= decision["stage"]:
                raise GameSpecValidationError("decision signal cannot be observed in its own stage")
        elif signal["symbol"] not in states:
            raise GameSpecValidationError("state signal does not reference a declared state")
    for decision in decisions.values():
        info = infos.get(decision["information_set"])
        if info is None:
            raise GameSpecValidationError("missing decision information set")
        if info["player"] != decision["player"] or info["stage"] != decision["stage"]:
            raise GameSpecValidationError("information set owner or stage mismatch")
        if len(set(info["observes"])) != len(info["observes"]):
            raise GameSpecValidationError("duplicate observations in information set")
        for signal_id in info["observes"]:
            sig = signals.get(signal_id)
            if sig is None:
                raise GameSpecValidationError("information set contains unknown signal")
            if sig["available_stage"] > decision["stage"]:
                raise GameSpecValidationError("decision observes future state/action")


def _distinct(sequence: list[str], label: str) -> None:
    if len(sequence) != len(set(sequence)):
        raise GameSpecValidationError(f"duplicate {label}")


def validate_game_spec(raw: Mapping[str, Any]) -> ValidatedGameSpec:
    """Validate closed structural schema, expression whitelist, units and timing.

    No AST is executed, differentiated or sent to SymPy. This confirms only
    *structural model facts* and explicit domains, never equilibrium existence,
    global optimality, probability normalization or scholarly correctness.
    """
    data = _bounded_json(raw)
    _expression_nodes(data)
    try:
        _validator().validate(data)
    except ValidationError as exc:
        raise GameSpecValidationError(
            "model-schema violation at " + "/".join(map(str, exc.absolute_path))
        ) from exc
    if data["time"]["kind"] != "discrete":
        raise GameSpecValidationError("continuous-time dynamics are unsupported in Phase 3")
    sources = data["source"]
    if sources["kind"] == "paper_anchor":
        if sources["file_sha256"] is None or sources["page"] is None:
            raise GameSpecValidationError("paper-anchored model requires PDF hash and page")
    elif sources["file_sha256"] is not None or sources["page"] is not None:
        raise GameSpecValidationError("synthetic/manual source cannot masquerade as anchored PDF")
    for field, label in (("symbols", "symbol"), ("players", "player"),
                         ("decisions", "decision"), ("information_sets", "information set"),
                         ("signals", "signal"), ("constraints", "constraint")):
        field_id = "name" if field == "symbols" else "id"
        _distinct([v[field_id] for v in data[field]], label)
    names = {x["name"]: x for x in data["symbols"]}
    units = {name: tuple(v["unit"].get(k, 0) for k in ("currency", "quantity", "time"))
             for name, v in names.items()}
    for sym in names.values():
        _check_domain(sym)
    for node in _expression_nodes(data):
        if node["op"] == "symbol" and node["name"] not in names:
            raise GameSpecValidationError("AST contains undeclared symbol")
    players = {x["id"] for x in data["players"]}
    used_controls: set[str] = set()
    player_controls: set[str] = set()
    stages: set[int] = set()
    for decision in data["decisions"]:
        if decision["player"] not in players:
            raise GameSpecValidationError("unknown controlling player")
        symbol = names.get(decision["symbol"])
        if symbol is None or symbol["role"] != "control":
            raise GameSpecValidationError("decision must refer to declared control")
        if decision["symbol"] in used_controls:
            raise GameSpecValidationError("control assigned to multiple decisions")
        used_controls.add(decision["symbol"])
        player_controls.add(decision["player"])
        stages.add(decision["stage"])
    if used_controls != {s["name"] for s in data["symbols"] if s["role"] == "control"}:
        raise GameSpecValidationError("control is missing from decisions")
    if player_controls != players:
        raise GameSpecValidationError("player with no decision")
    if stages != set(range(1, data["time"]["stages"] + 1)):
        raise GameSpecValidationError("decision stages must be contiguous and match timeline")
    for info in data["information_sets"]:
        if info["player"] not in players or info["stage"] > data["time"]["stages"]:
            raise GameSpecValidationError("orphan or out-of-range information set")
    check_information_sequence(data)
    _check_denominators(_expression_nodes(data), names)
    for player in data["players"]:
        _expr_unit(player["objective"], units)
    for condition in data["constraints"]:
        if _expr_unit(condition["lhs"], units) != _expr_unit(condition["rhs"], units):
            raise GameSpecValidationError("dimensionally inconsistent constraint")
    stochastic = any(s["stochastic"] for s in data["symbols"])
    sequential = data["time"]["stages"] > 1
    classification: ModelClassification
    if stochastic:
        classification = "stochastic_sequential_game" if sequential else "stochastic_simultaneous_game"
    else:
        classification = "static_sequential_game" if sequential else "static_simultaneous_game"
    warnings = ["MATHEMATICAL_VALIDITY_NOT_VERIFIED", "SOURCE_CLAIMS_NOT_VERIFIED"]
    if any(s["stochastic"] and s["distribution_status"] == "UNSPECIFIED" for s in data["symbols"]):
        warnings.append("STOCHASTIC_DISTRIBUTION_UNSPECIFIED")
    return ValidatedGameSpec(json.dumps(data, sort_keys=True), classification, tuple(warnings))


def build_best_response_tasks(model: ValidatedGameSpec) -> tuple[BestResponseTask, ...]:
    """Create inert reverse-stage task descriptions, without solving equations."""
    return tuple(
        BestResponseTask(d["player"], d["stage"], d["symbol"], d["information_set"])
        for d in sorted(model.data["decisions"], key=lambda d: (-d["stage"], d["id"]))
    )
