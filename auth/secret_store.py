"""Secret store abstraction for dev (filesystem) or GCP Secret Manager.

This module provides a minimal interface: `store_key(kid, priv_pem, pub_pem)` and
`load_key(kid)` returning `(priv_pem, pub_pem)` or `None` if missing.

Behavior:
- If running on Cloud Run (or any environment that sets `GCP_PROJECT`), this
    module will prefer using GCP Secret Manager when the GCP client library is
    importable. A local override is available via the `USE_GCP_SECRET_MANAGER`
    environment variable (truthy values enable, falsy values disable).
- Otherwise it falls back to storing files under `auth/keys/` (the dev default).

This is intentionally a simple stub — production code should handle
authentication, permissions, secret naming and versions more robustly.
"""

import datetime
import json
import os
from pathlib import Path
from typing import Optional
from typing import Tuple

KEY_DIR = Path(__file__).parent / "keys" / "rotated"
KEY_DIR.mkdir(parents=True, exist_ok=True)


def _is_truthy(val: str | None) -> bool:
    if val is None:
        return False
    return str(val).strip().lower() in ("1", "true", "yes", "y", "t")


def _want_gcp() -> bool:
    """Decide whether to use GCP Secret Manager.

    Priority:
    - If `USE_GCP_SECRET_MANAGER` is set, its truthiness decides.
    - Otherwise, if `GCP_PROJECT` is present (Cloud Run sets this), prefer GCP.
    - If neither is present, do not use GCP.
    """
    explicit = os.environ.get("USE_GCP_SECRET_MANAGER")
    if explicit is not None:
        return _is_truthy(explicit)
    # Use GCP when GCP_PROJECT is set (Cloud Run sets this automatically)
    return bool(os.environ.get("GCP_PROJECT"))


def _fs_path_for(kid: str) -> Tuple[Path, Path]:
    # filesystem fallback: keep per-week directories to avoid proliferating top-level files
    week_start = _week_start_for_kid(kid)
    week_dir = KEY_DIR / f"week_{week_start.strftime('%Y%m%d')}"
    week_dir.mkdir(parents=True, exist_ok=True)
    return (week_dir / f"{kid}_private.pem", week_dir / f"{kid}_public.pem")


def _week_start_for_kid(kid: str) -> datetime.date:
    """Return the Monday (week-start) date for the given kid (YYYYMMDD)."""
    try:
        dt = datetime.datetime.strptime(kid, "%Y%m%d").date()
    except Exception:
        # If parsing fails, fall back to today
        dt = datetime.date.today()
    # Monday is weekday 0
    week_start = dt - datetime.timedelta(days=dt.weekday())
    return week_start


def _week_secret_id_for_kid(kid: str, suffix: str) -> str:
    """Return a secret id string for the week containing `kid` and given suffix ('private'|'public')."""
    week_start = _week_start_for_kid(kid)
    return f"{week_start.strftime('%Y%m%d')}-{suffix}"


def store_key(kid: str, priv_pem: str, pub_pem: str) -> None:
    """Store key material. Filesystem fallback used in most cases."""
    # Prefer GCP Secret Manager if explicitly enabled and available
    use_gcp = _want_gcp()
    if use_gcp:
        try:
            from google.api_core import exceptions as gcp_exc  # type: ignore
            from google.cloud import secretmanager  # type: ignore
        except Exception:
            # GCP requested but client library not available; fall back to filesystem
            use_gcp = False
            gcp_exc = None

    if use_gcp:
        client = secretmanager.SecretManagerServiceClient()
        # Prefer explicit GCP_PROJECT otherwise use fallback env var
        project = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project:
            # If project is not set, don't attempt GCP operations; fall back to FS
            use_gcp = False

    if use_gcp:
        # Store versions under a weekly secret (one secret per week) to avoid creating
        # a secret resource per day. Each version payload contains JSON {"kid":..., "pem":...}.
        for suffix, pem in (("private", priv_pem), ("public", pub_pem)):
            secret_id = _week_secret_id_for_kid(kid, suffix)
            parent = f"projects/{project}"
            # Attempt to create the secret resource if it doesn't exist.
            try:
                client.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": secret_id,
                        "secret": {"replication": {"automatic": {}}},
                    }
                )
            except Exception as exc:
                # Only ignore if secret already exists, otherwise let it propagate
                if gcp_exc is not None and isinstance(exc, gcp_exc.AlreadyExists):
                    pass
                else:
                    # Re-raise non-AlreadyExists exceptions so callers can detect failures
                    raise

            payload = json.dumps({"kid": kid, "pem": pem})
            try:
                client.add_secret_version(
                    request={
                        "parent": f"projects/{project}/secrets/{secret_id}",
                        "payload": {"data": payload.encode()},
                    }
                )
            except Exception as exc:
                # If the add version fails due to NotFound, attempt to create secret and retry once
                if gcp_exc is not None and isinstance(exc, gcp_exc.NotFound):
                    try:
                        client.create_secret(
                            request={
                                "parent": parent,
                                "secret_id": secret_id,
                                "secret": {"replication": {"automatic": {}}},
                            }
                        )
                    except Exception:
                        # ignore create failure
                        pass
                    # retry add_secret_version; allow exceptions to bubble up if they continue
                    client.add_secret_version(
                        request={
                            "parent": f"projects/{project}/secrets/{secret_id}",
                            "payload": {"data": payload.encode()},
                        }
                    )
                else:
                    # Re-raise non-NotFound errors for callers to handle
                    raise
        return

    # Filesystem fallback
    priv_path, pub_path = _fs_path_for(kid)
    priv_path.write_bytes(priv_pem.encode())
    pub_path.write_bytes(pub_pem.encode())


def load_key(kid: str) -> Optional[Tuple[str, str]]:
    """Load key material for `kid`. Returns (priv_pem, pub_pem) or None."""
    use_gcp = _want_gcp()
    if use_gcp:
        try:
            from google.cloud import secretmanager  # type: ignore
        except Exception:
            use_gcp = False
            gcp_exc = None

    if use_gcp:
        try:
            from google.api_core import exceptions as gcp_exc  # type: ignore
            from google.cloud import secretmanager  # type: ignore
        except Exception:
            use_gcp = False
            gcp_exc = None

    if use_gcp:
        client = secretmanager.SecretManagerServiceClient()
        project = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project:
            use_gcp = False

    if use_gcp:
        # Look up in the weekly secrets for the week that contains kid. Search versions newest->oldest
        priv_secret_id = _week_secret_id_for_kid(kid, "private")
        pub_secret_id = _week_secret_id_for_kid(kid, "public")
        try:
            # helper to find pem for secret id
            def _find_pem(secret_id: str, desired_kid: str) -> Optional[str]:
                parent = f"projects/{project}/secrets/{secret_id}"
                # list versions
                try:
                    versions = client.list_secret_versions(request={"parent": parent})
                except Exception as exc:
                    # If the secret resource doesn't exist (NotFound), attempt to create it so future writes succeed
                    try:
                        if gcp_exc is not None and isinstance(exc, gcp_exc.NotFound):
                            parent = f"projects/{project}"
                            # Try to create the two weekly secrets (private/public) if missing
                            for suffix in ("private", "public"):
                                secret_id = _week_secret_id_for_kid(kid, suffix)
                                try:
                                    client.create_secret(
                                        request={
                                            "parent": parent,
                                            "secret_id": secret_id,
                                            "secret": {"replication": {"automatic": {}}},
                                        }
                                    )
                                except Exception:
                                    # ignore any errors creating the resource, best-effort
                                    pass
                    except Exception:
                        # ignore errors while attempting to create
                        pass
                    return None
                # iterate versions (API returns an iterator; convert to list to inspect newest first)
                vers = [v for v in versions]
                # sort by createTime descending if available
                try:
                    vers.sort(key=lambda v: v.create_time, reverse=True)
                except Exception:
                    pass
                for v in vers:
                    if v.state.name != "ENABLED":
                        continue
                    ver_name = v.name
                    try:
                        payload = client.access_secret_version(
                            request={"name": ver_name}
                        ).payload.data.decode()
                        data = json.loads(payload)
                        if data.get("kid") == desired_kid:
                            return data.get("pem")
                    except Exception:
                        continue
                return None

            priv = _find_pem(priv_secret_id, kid)
            pub = _find_pem(pub_secret_id, kid)
            if priv and pub:
                return priv, pub
            return None
        except Exception:
            return None

    priv_path, pub_path = _fs_path_for(kid)
    if not priv_path.exists() or not pub_path.exists():
        return None
    return priv_path.read_text(), pub_path.read_text()
