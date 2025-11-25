import base64
import datetime
from pathlib import Path
from typing import Optional
from typing import Tuple

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from . import secret_store

KEY_DIR = Path(__file__).parent / "keys"
ROTATED_DIR = KEY_DIR / "rotated"
KEY_DIR.mkdir(parents=True, exist_ok=True)
ROTATED_DIR.mkdir(parents=True, exist_ok=True)


def _base64url_uint(i: int) -> str:
    # Encode integer as base64url without padding
    b = i.to_bytes((i.bit_length() + 7) // 8, "big") or b"\x00"
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def _kid_for_date(dt: datetime.date) -> str:
    return dt.strftime("%Y%m%d")


def _fs_paths_for(kid: str) -> Tuple[Path, Path]:
    return (ROTATED_DIR / f"{kid}_private.pem", ROTATED_DIR / f"{kid}_public.pem")


def generate_keypair() -> Tuple[str, str]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    pub = (
        key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    return priv, pub


def ensure_key_for_date(dt: Optional[datetime.date] = None) -> str:
    """Ensure a keypair exists for the given date. Returns the kid."""
    if dt is None:
        dt = datetime.date.today()
    kid = _kid_for_date(dt)
    existing = secret_store.load_key(kid)
    if existing:
        return kid
    priv, pub = generate_keypair()
    secret_store.store_key(kid, priv, pub)
    return kid


def load_key_for_date(kid: str) -> Optional[Tuple[str, str]]:
    return secret_store.load_key(kid)


def get_private_pem_for_date(kid: str) -> Optional[str]:
    kv = load_key_for_date(kid)
    return kv[0] if kv else None


def public_jwk_for_date(kid: str) -> Optional[dict]:
    kv = load_key_for_date(kid)
    if not kv:
        return None
    pub_pem = kv[1]
    pub = serialization.load_pem_public_key(pub_pem.encode())
    if not isinstance(pub, rsa.RSAPublicKey):
        return None
    numbers = pub.public_numbers()
    n = numbers.n
    e = numbers.e
    return {
        "kty": "RSA",
        "kid": kid,
        "use": "sig",
        "alg": "RS256",
        "n": _base64url_uint(n),
        "e": _base64url_uint(e),
    }


def list_known_kids() -> list:
    # List keys present in rotated dir
    kids = []
    for p in ROTATED_DIR.glob("*_private.pem"):
        kids.append(p.name.split("_")[0])
    return sorted(kids)


if __name__ == "__main__":
    ensure_key_for_date()
