"""Remote trust unavailable means NO release, not soft warning or self-hash fallback."""

from emr.adapters.checkpoint import ProtectedCheckpointClient
from emr.core.security import SecurityBoundaryError
from emr.services.g6_application import audit_with_protected_checkpoint


def test_offline_g6_external_trust_fails_closed():
    def dead(*args, **kwargs):
        raise OSError("connection refused")

    client = ProtectedCheckpointClient("https://independent.example/v1/trust-policy",
                                       b"z" * 32, 1, transport=dead)
    result = audit_with_protected_checkpoint(client)
    assert result.status == "BLOCKED" and result.upstream_status == "STALE"
    assert result.findings[0].code == "CRITICAL_LEDGER_CORRUPTION"
    assert result.findings[0].severity == "CRITICAL"


def test_untrusted_override_is_rejected_even_if_network_is_down():
    client = ProtectedCheckpointClient("https://independent.example/v1/trust-policy",
                                       b"z" * 32, 1)
    try:
        audit_with_protected_checkpoint(client, trust="forged")
    except SecurityBoundaryError:
        pass
    else:
        raise AssertionError("caller controlled protected trust")
