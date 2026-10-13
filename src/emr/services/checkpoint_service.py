"""Read-only signed checkpoint HTTP service. No signing material or write routes.

Deployment policy JSON is provisioned by an independent issuer. This process
merely serves the immutable signed snapshot; G6 verifies the pinned root key.
"""
from __future__ import annotations

import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from emr.core.security import SecurityBoundaryError, parse_json_record


class CheckpointHandler(BaseHTTPRequestHandler):
    checkpoint_bytes: bytes = b""

    def do_GET(self) -> None:
        if self.path != "/v1/trust-policy":
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(self.checkpoint_bytes)))
        self.end_headers()
        self.wfile.write(self.checkpoint_bytes)

    def do_POST(self) -> None:
        self.send_error(405)

    def do_PUT(self) -> None:
        self.send_error(405)

    def do_DELETE(self) -> None:
        self.send_error(405)

    def log_message(self, fmt: str, *args: object) -> None:
        # Do not log arbitrary untrusted URLs or values.
        return


def serve() -> None:
    path = Path(os.environ["EMR_SIGNED_POLICY_PATH"])
    if path.is_symlink() or not path.is_file():
        raise SecurityBoundaryError("checkpoint must be a regular provisioned file")
    body = path.read_bytes()
    data = parse_json_record(body)
    if set(data) != {"policy", "signature"}:
        raise SecurityBoundaryError("checkpoint is not a signed envelope")
    CheckpointHandler.checkpoint_bytes = body
    server = ThreadingHTTPServer(("0.0.0.0", 8080), CheckpointHandler)
    server.serve_forever()


if __name__ == "__main__":
    serve()
