#!/usr/bin/env python3
"""
Simple smoke-test script for Opteryx auth + data endpoints.

This script will:
  - Request a client credentials token from the Auth service (/token)
  - Submit a SQL statement to the Data service (/api/v1/statements)
  - Poll the statement status and cancel it

Environment variables used (defaults shown):
  AUTH_URL=http://localhost:8081
  DATA_URL=http://localhost:8000
  CLIENT_ID=m2m-client
  CLIENT_SECRET=secret123
  KEY_DATE (optional): YYYY-MM-DD - selects the signing key date
  SCOPE (optional)

Example usage:
  AUTH_URL=http://localhost:8081 DATA_URL=http://localhost:8000 CLIENT_ID=m2m-client \
    CLIENT_SECRET=secret123 ./scripts/smoke_test.py

"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Any
from typing import Dict
from typing import Optional

import requests

DEFAULT_AUTH_URL = "https://auth.opteryx.app"
DEFAULT_DATA_URL = "https://data.opteryx.app"
DEFAULT_CLIENT_ID = os.environ.get("CLIENT_ID", "m2m-client")
DEFAULT_CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "secret123")


def fatal(msg: str) -> None:
    print("ERROR:", msg, file=sys.stderr)
    sys.exit(2)


class SmokeTestResult:
    def __init__(self) -> None:
        self.steps = []

    def ok(self, msg: str) -> None:
        print("✅", msg)
        self.steps.append((True, msg))

    def fail(self, msg: str) -> None:
        print("❌", msg)
        self.steps.append((False, msg))

    def all_ok(self) -> bool:
        return all(ok for ok, _ in self.steps)


def get_token(
    auth_url: str,
    client_id: str,
    client_secret: str,
    scope: Optional[str] = None,
    key_date: Optional[str] = None,
) -> str:
    url = f"{auth_url.rstrip('/')}/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    if scope:
        data["scope"] = scope
    if key_date:
        data["key_date"] = key_date

    r = requests.post(url, data=data, timeout=10)
    if r.status_code != 200:
        raise RuntimeError(f"token endpoint returned status {r.status_code}: {r.text}")
    body = r.json()
    token = body.get("access_token")
    if not token:
        raise RuntimeError("token endpoint returned no access_token")
    return token


def create_statement(
    data_url: str, token: str, sql: str = "SELECT 1", describe_only: bool | None = None
) -> Dict[str, Any]:
    url = f"{data_url.rstrip('/')}/api/v1/statements"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload: Dict[str, Any] = {"sqlText": sql}
    if describe_only is not None:
        payload["describeOnly"] = describe_only

    r = requests.post(url, json=payload, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()


def get_statement_status(data_url: str, token: str, handle: str) -> Dict[str, Any]:
    url = f"{data_url.rstrip('/')}/api/v1/statements/{handle}"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()


def cancel_statement(data_url: str, token: str, handle: str) -> Dict[str, Any]:
    url = f"{data_url.rstrip('/')}/api/v1/statements/{handle}/cancel"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Basic smoke test for Opteryx services")
    p.add_argument(
        "--auth-url",
        default=os.environ.get("AUTH_URL", DEFAULT_AUTH_URL),
        help="Auth service base URL",
    )
    p.add_argument(
        "--data-url",
        default=os.environ.get("DATA_URL", DEFAULT_DATA_URL),
        help="Data service base URL",
    )
    p.add_argument(
        "--client-id",
        default=os.environ.get("CLIENT_ID", DEFAULT_CLIENT_ID),
        help="Client ID for client_credentials grant",
    )
    p.add_argument(
        "--client-secret",
        default=os.environ.get("CLIENT_SECRET", DEFAULT_CLIENT_SECRET),
        help="Client secret",
    )
    p.add_argument(
        "--sql",
        default=os.environ.get("SMOKE_SQL", "SELECT 1"),
        help="SQL to submit as smoke statement",
    )
    p.add_argument("--scope", default=os.environ.get("SCOPE", None), help="Optional token scope")
    p.add_argument(
        "--key-date",
        default=os.environ.get("KEY_DATE", None),
        help="Optional key_date to request a signing key; YYYY-MM-DD",
    )
    p.add_argument("--no-cancel", action="store_true", help="If set, do not call cancel endpoint")
    p.add_argument(
        "--poll-interval", type=float, default=0.5, help="Seconds between statement status polls"
    )
    p.add_argument(
        "--poll-timeout",
        type=float,
        default=5.0,
        help="Total time seconds to poll before giving up",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    result = SmokeTestResult()

    try:
        print("→ Requesting client credentials token...")
        token = get_token(
            args.auth_url, args.client_id, args.client_secret, args.scope, args.key_date
        )
        result.ok("Obtained access token")
    except requests.RequestException as exc:
        result.fail(f"Failed to obtain token: {exc}")
        print("See environment defaults or check AUTH_URL and client credentials.")
        return 1

    # Create statement
    try:
        print("→ Creating statement...")
        resp = create_statement(args.data_url, token, sql=args.sql)
        handle = resp.get("statementHandle")
        if not handle:
            raise RuntimeError("response missing statementHandle")
        result.ok(f"Statement created: {handle}")
    except requests.RequestException as exc:
        result.fail(f"Failed to create statement: {exc}")
        return 1

    # Poll status
    try:
        print("→ Polling statement status...")
        start = time.time()
        last_status = None
        while True:
            resp = get_statement_status(args.data_url, token, handle)
            last_status = resp.get("status", {})
            state = last_status.get("state") if isinstance(last_status, dict) else None
            print(f"  status -> {state}", end="\r")
            if state in ("SUCCESS", "FAILED", "CANCELLED", "SUBMITTED", "RUNNING"):
                # We'll treat successful fetch as OK. Data service may be a stub and not actually run work.
                break
            if time.time() - start > args.poll_timeout:
                raise RuntimeError("timed out waiting for terminal status")
            time.sleep(args.poll_interval)
        print()
        result.ok(f"Fetched statement status: {state}")
    except requests.RequestException as exc:
        result.fail(f"Failed to fetch statement status: {exc}")

    # Cancel statement (optional)
    if not args.no_cancel:
        try:
            print("→ Cancelling statement...")
            resp = cancel_statement(args.data_url, token, handle)
            cancelled = resp.get("cancelled")
            status = (
                resp.get("status", {}).get("state")
                if isinstance(resp.get("status"), dict)
                else None
            )
            result.ok(f"Cancel response: cancelled={cancelled} status={status}")
        except requests.RequestException as exc:
            result.fail(f"Failed to cancel statement: {exc}")

    print()
    if result.all_ok():
        print("Smoke test completed: all checks passed")
        return 0
    else:
        print("Smoke test completed: some checks failed")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
