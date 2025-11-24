import hmac
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Form, Header, HTTPException
from jose import jwt
from pydantic import BaseModel

try:
    from google.cloud import firestore  # type: ignore
except Exception:
    firestore = None

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
except Exception:
    PasswordHasher = None
    VerifyMismatchError = Exception


# Attempt to load clients from AUTH_CLIENTS_JSON env var or from Secret Manager
def _load_clients() -> dict:
    # 1) ENV override (useful for local/dev): JSON map {"client_id": "secret"}
    env = os.environ.get("AUTH_CLIENTS_JSON")
    if env:
        try:
            return json.loads(env)
        except Exception:
            pass

    # 2) Secret Manager: secret id 'opteryx-auth-clients' storing JSON payload
    try:
        from google.cloud import secretmanager  # type: ignore

        client = secretmanager.SecretManagerServiceClient()
        project = os.environ.get("GCP_PROJECT")
        logging.getLogger(__name__).info("_load_clients: GCP_PROJECT=%s", project)
        if project:
            secret_name = (
                f"projects/{project}/secrets/opteryx-auth-clients/versions/latest"
            )
            logging.getLogger(__name__).info("_load_clients: attempting to read secret %s", secret_name)
            resp = client.access_secret_version(request={"name": secret_name})
            payload = resp.payload.data.decode()
            return json.loads(payload)
    except Exception as exc:
        # Fall back silently to dev default below but log the error for debugging
        logging.getLogger(__name__).warning("_load_clients: secretmanager read failed: %s", exc)

    # 3) Dev fallback
    return {"m2m-client": "secret123"}


_PH = PasswordHasher() if PasswordHasher is not None else None


def _check_client_secret_hash(secret_hash: str, provided: str) -> bool:
    # Use Argon2 verify when available; otherwise fallback to constant-time compare
    if _PH is not None:
        try:
            return _PH.verify(secret_hash, provided)
        except VerifyMismatchError:
            return False
        except Exception:
            return False
    # fallback (not recommended for production)
    try:
        return hmac.compare_digest(str(secret_hash), str(provided))
    except Exception:
        return False


# Firestore-backed client cache
_CLIENT_CACHE: dict = {}
_CLIENT_CACHE_TTL = int(os.environ.get("CLIENT_CACHE_TTL", "60"))


def _get_firestore_client():
    logger = logging.getLogger(__name__)
    if firestore is None:
        logger.info("_get_firestore_client: google-cloud-firestore not installed")
        return None
    try:
        project = os.environ.get("GCP_PROJECT")
        logger.info("_get_firestore_client: GCP_PROJECT=%s", project)
        db = firestore.Client()
        return db
    except Exception as exc:
        logger.warning("_get_firestore_client: failed to create client: %s", exc)
        return None


def _get_client_record(client_id: str) -> Optional[dict]:
    # Check cache first
    now = time.time()
    entry = _CLIENT_CACHE.get(client_id)
    if entry and now - entry[1] < _CLIENT_CACHE_TTL:
        return entry[0]

    # Try Firestore if available and GCP project is set
    db = _get_firestore_client()
    if db is not None and os.environ.get("GCP_PROJECT"):
        try:
            doc = db.collection("auth_clients").document(client_id).get()
            if doc.exists:
                data = doc.to_dict()
                _CLIENT_CACHE[client_id] = (data, now)
                return data
        except Exception:
            # Firestore unavailable or permissions; fall back below
            pass

    # Fallback to in-memory or secret-based clients
    # CLIENTS is loaded at startup from env/Secret Manager
    if CLIENTS and client_id in CLIENTS:
        data = {"secret_hash": CLIENTS[client_id], "status": "active"}
        _CLIENT_CACHE[client_id] = (data, now)
        return data
    return None


app = FastAPI(title="Opteryx Auth Service")

# client_id -> client_secret mapping (loaded at startup)
CLIENTS = _load_clients()
KID = "dev-key-1"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/jwks")
def jwks():
    # Return a standards-compliant JWKS constructed from known rotated keys.
    keys_mod = __import__(
        "auth.keys",
        fromlist=["list_known_kids", "public_jwk_for_date", "ensure_key_for_date"],
    )
    kids = keys_mod.list_known_kids()
    if not kids:
        # Ensure today's key exists
        today = __import__("datetime").date.today()
        keys_mod.ensure_key_for_date(today)
        kids = keys_mod.list_known_kids()

    keys_list = []
    for kid in kids:
        jwk = keys_mod.public_jwk_for_date(kid)
        if jwk:
            keys_list.append(jwk)
    return {"keys": keys_list}


@app.post("/keys/ensure")
def ensure_key(days_ahead: int = 0, key_date: str | None = None):
    """Ensure a key exists for the requested date.

    Provide either `key_date` (YYYY-MM-DD) or `days_ahead` (int). Returns the `kid`.
    """
    import datetime as _dt

    if key_date:
        try:
            use_date = _dt.date.fromisoformat(key_date)
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail="invalid key_date format; use YYYY-MM-DD"
            ) from exc
    else:
        use_date = _dt.date.today() + _dt.timedelta(days=int(days_ahead or 0))

    kid = __import__("auth.keys", fromlist=["ensure_key_for_date"]).ensure_key_for_date(
        use_date
    )
    return {"kid": kid}


@app.post("/token", response_model=TokenResponse)
def token_endpoint(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    scope: str = Form(None),
    key_date: str = Form(None),
    days_ahead: int = Form(0),
):
    if grant_type != "client_credentials":
        raise HTTPException(status_code=400, detail="unsupported grant_type")

    rec = _get_client_record(client_id)
    if not rec:
        raise HTTPException(status_code=401, detail="invalid client")

    # check status
    status = rec.get("status", "active")
    if status != "active":
        raise HTTPException(status_code=403, detail=f"client not active: {status}")

    secret_hash = rec.get("secret_hash")
    if not secret_hash or not _check_client_secret_hash(secret_hash, client_secret):
        raise HTTPException(status_code=401, detail="invalid client")
    # Determine which signing key to use: explicit key_date (YYYY-MM-DD) or days_ahead
    import datetime as _dt

    if key_date:
        try:
            use_date = _dt.date.fromisoformat(key_date)
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail="invalid key_date format; use YYYY-MM-DD"
            ) from exc
    else:
        use_date = _dt.date.today() + _dt.timedelta(days=int(days_ahead or 0))

    kid = __import__("auth.keys", fromlist=["ensure_key_for_date"]).ensure_key_for_date(
        use_date
    )
    private_pem = __import__(
        "auth.keys", fromlist=["get_private_pem_for_date"]
    ).get_private_pem_for_date(kid)
    if not private_pem:
        raise HTTPException(status_code=500, detail="signing key not available")

    now = datetime.utcnow()
    exp = now + timedelta(minutes=15)
    payload = {
        "sub": client_id,
        "iss": os.environ.get("AUTH_URL", "http://localhost:8081"),
        "aud": os.environ.get("DATA_AUDIENCE", "opteryx-api"),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "scope": scope or "",
    }
    token = jwt.encode(payload, private_pem, algorithm="RS256", headers={"kid": kid})
    return {"access_token": token, "expires_in": 15 * 60, "kid": kid}


def _require_admin(token: Optional[str]) -> None:
    admin_token = os.environ.get("AUTH_ADMIN_TOKEN")
    if not admin_token:
        raise HTTPException(status_code=403, detail="admin actions not permitted")
    if not token or not hmac.compare_digest(str(token), str(admin_token)):
        raise HTTPException(status_code=403, detail="invalid admin token")


@app.post("/admin/register")
def admin_register(
    client_id: str = Form(...),
    client_secret: str = Form(None),
    status: str = Form("not-activated"),
    x_admin_token: Optional[str] = Header(None),
):
    """Register a new client. Requires header `X-Admin-Token` matching `AUTH_ADMIN_TOKEN`."""
    _require_admin(x_admin_token)
    if not client_secret:
        # generate a random secret
        import secrets

        client_secret = secrets.token_urlsafe(32)

    # hash secret with Argon2 if available
    if _PH is None:
        secret_hash = client_secret
    else:
        secret_hash = _PH.hash(client_secret)

    # store in Firestore if available
    db = _get_firestore_client()
    if db is not None and os.environ.get("GCP_PROJECT"):
        db.collection("auth_clients").document(client_id).set(
            {
                "secret_hash": secret_hash,
                "status": status,
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )
    else:
        # update in-memory fallback
        CLIENTS[client_id] = secret_hash

    return {"client_id": client_id, "client_secret": client_secret, "status": status}


@app.post("/admin/reset")
def admin_reset(
    client_id: str = Form(...),
    new_secret: str = Form(None),
    x_admin_token: Optional[str] = Header(None),
):
    _require_admin(x_admin_token)
    if not new_secret:
        import secrets

        new_secret = secrets.token_urlsafe(32)

    if _PH is None:
        secret_hash = new_secret
    else:
        secret_hash = _PH.hash(new_secret)

    db = _get_firestore_client()
    if db is not None and os.environ.get("GCP_PROJECT"):
        doc_ref = db.collection("auth_clients").document(client_id)
        doc_ref.update(
            {"secret_hash": secret_hash, "updated_at": firestore.SERVER_TIMESTAMP}
        )
    else:
        CLIENTS[client_id] = secret_hash

    return {"client_id": client_id, "client_secret": new_secret}


@app.delete("/admin/clients/{client_id}")
def admin_delete(client_id: str, x_admin_token: Optional[str] = Header(None)):
    _require_admin(x_admin_token)
    db = _get_firestore_client()
    if db is not None and os.environ.get("GCP_PROJECT"):
        db.collection("auth_clients").document(client_id).delete()
    else:
        CLIENTS.pop(client_id, None)
    return {"deleted": client_id}


@app.patch("/admin/clients/{client_id}/status")
def admin_set_status(
    client_id: str, status: str = Form(...), x_admin_token: Optional[str] = Header(None)
):
    _require_admin(x_admin_token)
    allowed = [
        "active",
        "not-activated",
        "billing-suspended",
        "abuse-suspended",
        "inactive-suspended",
        "soft-deleted",
    ]
    if status not in allowed:
        raise HTTPException(
            status_code=400, detail=f"invalid status; allowed: {allowed}"
        )
    db = _get_firestore_client()
    if db is not None and os.environ.get("GCP_PROJECT"):
        db.collection("auth_clients").document(client_id).update(
            {"status": status, "updated_at": firestore.SERVER_TIMESTAMP}
        )
    else:
        rec = CLIENTS.get(client_id)
        if rec is None:
            raise HTTPException(status_code=404, detail="client not found")
        # if CLIENTS holds plain secret, convert to dict
        if isinstance(rec, str):
            CLIENTS[client_id] = {"secret_hash": rec, "status": status}
        else:
            CLIENTS[client_id]["status"] = status
    return {"client_id": client_id, "status": status}
