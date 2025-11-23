from fastapi import FastAPI, Form, HTTPException
from datetime import datetime, timedelta
from jose import jwt
from pydantic import BaseModel
import os

# key management now provided by auth.keys module functions (imported dynamically)

app = FastAPI(title="Opteryx Auth Service")

# Simple in-memory client store for dev
CLIENTS = {"m2m-client": "secret123"}
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
    keys_mod = __import__("auth.keys", fromlist=["list_known_kids", "public_jwk_for_date", "ensure_key_for_date"]) 
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
            raise HTTPException(status_code=400, detail="invalid key_date format; use YYYY-MM-DD") from exc
    else:
        use_date = _dt.date.today() + _dt.timedelta(days=int(days_ahead or 0))

    kid = __import__("auth.keys", fromlist=["ensure_key_for_date"]).ensure_key_for_date(use_date)
    return {"kid": kid}


@app.post("/token", response_model=TokenResponse)
def token_endpoint(grant_type: str = Form(...), client_id: str = Form(...), client_secret: str = Form(...), scope: str = Form(None), key_date: str = Form(None), days_ahead: int = Form(0)):
    if grant_type != "client_credentials":
        raise HTTPException(status_code=400, detail="unsupported grant_type")
    if CLIENTS.get(client_id) != client_secret:
        raise HTTPException(status_code=401, detail="invalid client")
    # Determine which signing key to use: explicit key_date (YYYY-MM-DD) or days_ahead
    import datetime as _dt

    if key_date:
        try:
            use_date = _dt.date.fromisoformat(key_date)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="invalid key_date format; use YYYY-MM-DD") from exc
    else:
        use_date = _dt.date.today() + _dt.timedelta(days=int(days_ahead or 0))

    kid = __import__("auth.keys", fromlist=["ensure_key_for_date"]).ensure_key_for_date(use_date)
    private_pem = __import__("auth.keys", fromlist=["get_private_pem_for_date"]).get_private_pem_for_date(kid)
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
