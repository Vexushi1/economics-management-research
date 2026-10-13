"""Entrypoint for the REAL Phase 8 G6 auditor using external trust policy.

The public checkpoint client never provides authority to write/checkpoint or
perform signing. A network/root failure is CRITICAL and always blocks release.
No caller-supplied TrustPolicy is accepted on this production-boundary route.
"""
from __future__ import annotations

from emr.adapters.checkpoint import ProtectedCheckpointClient
from emr.core.security import SecurityBoundaryError
from emr.domain.submission import G6Report, GateFinding, audit_submission


def audit_with_protected_checkpoint(client: ProtectedCheckpointClient, **g6_inputs: object) -> G6Report:
    """Load verified, non-expired policy BEFORE invoking the complete G6 audit."""
    if not isinstance(client, ProtectedCheckpointClient):
        raise TypeError("externally anchored checkpoint client required")
    if "trust" in g6_inputs:
        raise SecurityBoundaryError("caller cannot override remote trust policy")
    try:
        policy = client.fetch()
    except (SecurityBoundaryError, OSError, ValueError):
        return G6Report(
            "BLOCKED",
            (GateFinding("CRITICAL_LEDGER_CORRUPTION", "CRITICAL",
                         "publication locked: external trust checkpoint unavailable or invalid"),),
            None, "STALE",
        )
    return audit_submission(**g6_inputs, trust=policy)
