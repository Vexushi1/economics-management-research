"""Read-only G6 trust-preflight service. Does not expose a publish endpoint.

Business callers must run emr.domain.submission.audit_submission with the
TrustPolicy returned by this independently authenticated client. No request
can invoke signing, mutate the ledger, or bypass the Phase 8 G6 audit.
"""
from __future__ import annotations

import base64
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from emr.adapters.checkpoint import ProtectedCheckpointClient
from emr.core.security import SecurityBoundaryError


def load_protected_policy():
    path = Path(os.environ["EMR_ROOT_PUBLIC_KEY_PATH"])
    if not path.is_file() or path.is_symlink():
        raise SecurityBoundaryError("missing pinned root public key")
    pub = base64.b64decode(path.read_text(encoding="ascii").strip(), validate=True)
    return ProtectedCheckpointClient(
        url=os.environ["EMR_CHECKPOINT_URL"], root_public_key=pub,
        minimum_sequence=int(os.environ["EMR_MIN_SEQUENCE"]),
        allow_insecure_internal_http=os.environ.get("EMR_INTERNAL_HTTP_FOR_DEV") == "1",
    ).fetch()


class G6HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/ready":
            self.send_error(404)
            return
        try:
            load_protected_policy()
        except (SecurityBoundaryError, KeyError, ValueError, OSError):
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b"TRUST_UNAVAILABLE: G6 publication blocked\n")
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"TRUST_PREFLIGHT_OK: publication still requires G6 audit\n")

    def do_POST(self) -> None:
        self.send_error(405)

    def log_message(self, fmt: str, *args: object) -> None:
        return


def serve() -> None:
    ThreadingHTTPServer(("0.0.0.0", 8081), G6HealthHandler).serve_forever()


if __name__ == "__main__":
    serve()
