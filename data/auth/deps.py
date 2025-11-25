import os
import time
from typing import Dict

import requests
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPBearer
from jose import JWTError
from jose import jwt

security = HTTPBearer()
_jwks_cache: Dict = {"keys": None, "fetched_at": 0}
CACHE_TTL = 60  # seconds


def fetch_jwks():
    now = time.time()
    if _jwks_cache["keys"] and now - _jwks_cache["fetched_at"] < CACHE_TTL:
        return _jwks_cache["keys"]
    auth_url = os.environ.get("AUTH_URL", "http://localhost:8081")
    try:
        r = requests.get(f"{auth_url}/jwks", timeout=2)
        r.raise_for_status()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Cannot fetch JWKS"
        ) from exc
    jwks = r.json()
    _jwks_cache["keys"] = jwks
    _jwks_cache["fetched_at"] = now
    return jwks


def require_bearer_token(token: str = Depends(security)):
    jwks = fetch_jwks()
    # Expect a JWKS structure: {"keys": [ {kty, kid, n, e, ...} ] }
    keys = jwks.get("keys") if isinstance(jwks, dict) else None
    if not keys:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No JWKS available"
        )
    # Determine which JWK to use by reading the token header `kid`.
    try:
        header = jwt.get_unverified_header(token.credentials)
    except Exception as _exc:
        header = {}
    kid = header.get("kid")

    jwk = None
    if kid:
        for k in keys:
            if k.get("kid") == kid:
                jwk = k
                break
    # Fallback to first key if no matching kid found
    if jwk is None:
        jwk = keys[0]
    n_b64 = jwk.get("n")
    e_b64 = jwk.get("e")
    if not n_b64 or not e_b64:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Invalid JWK")

    # Convert base64url values to integers
    def _b64url_to_int(s: str) -> int:
        import base64

        padding = "=" * ((4 - len(s) % 4) % 4)
        data = base64.urlsafe_b64decode(s + padding)
        return int.from_bytes(data, "big")

    n = _b64url_to_int(n_b64)
    e = _b64url_to_int(e_b64)

    # Build PEM from numbers
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    pub_numbers = rsa.RSAPublicNumbers(e, n)
    pub_key = pub_numbers.public_key()
    public_pem = pub_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    try:
        payload = jwt.decode(
            token.credentials,
            public_pem,
            algorithms=["RS256"],
            audience=os.environ.get("DATA_AUDIENCE", "opteryx-api"),
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc
    return payload
