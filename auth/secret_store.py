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

import os
from pathlib import Path
from typing import Optional, Tuple

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
    return (KEY_DIR / f"{kid}_private.pem", KEY_DIR / f"{kid}_public.pem")


def store_key(kid: str, priv_pem: str, pub_pem: str) -> None:
    """Store key material. Filesystem fallback used in most cases."""
    # Prefer GCP Secret Manager if explicitly enabled and available
    use_gcp = _want_gcp()
    if use_gcp:
        try:
            from google.cloud import secretmanager  # type: ignore
        except Exception:
            # GCP requested but client library not available; fall back to filesystem
            use_gcp = False

    if use_gcp:
        # Minimal GCP stub: store two secrets named {kid}-private and {kid}-public
        client = secretmanager.SecretManagerServiceClient()
        project = os.environ.get("GCP_PROJECT")
        for name, payload in ((f"{kid}-private", priv_pem), (f"{kid}-public", pub_pem)):
            parent = f"projects/{project}"
            # create secret if missing (best-effort)
            try:
                client.create_secret(request={"parent": parent, "secret_id": name, "secret": {"replication": {"automatic": {}}}})
            except Exception:
                pass
            client.add_secret_version(request={"parent": f"projects/{project}/secrets/{name}", "payload": {"data": payload.encode()}})
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

    if use_gcp:
        client = secretmanager.SecretManagerServiceClient()
        project = os.environ.get("GCP_PROJECT")
        try:
            priv_name = f"projects/{project}/secrets/{kid}-private/versions/latest"
            pub_name = f"projects/{project}/secrets/{kid}-public/versions/latest"
            priv = client.access_secret_version(request={"name": priv_name}).payload.data.decode()
            pub = client.access_secret_version(request={"name": pub_name}).payload.data.decode()
            return priv, pub
        except Exception:
            return None

    priv_path, pub_path = _fs_path_for(kid)
    if not priv_path.exists() or not pub_path.exists():
        return None
    return priv_path.read_text(), pub_path.read_text()
