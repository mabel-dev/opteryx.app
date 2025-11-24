#!/usr/bin/env python3
"""Create a client document in Firestore with Argon2-hashed secret.

Usage:
  python auth/scripts/create_client.py <client_id>
  It will prompt for a secret (hidden). If blank, a random secret will be generated.

Note: requires GOOGLE_APPLICATION_CREDENTIALS or being on GCP with proper IAM.
"""

import getpass
import secrets
import sys

try:
    from google.cloud import firestore  # type: ignore
except Exception:
    print("google-cloud-firestore not installed or not available")
    raise

try:
    from argon2 import PasswordHasher
except Exception:
    print("argon2-cffi not installed")
    raise


def main():
    if len(sys.argv) < 2:
        print("Usage: create_client.py <client_id>")
        raise SystemExit(2)
    client_id = sys.argv[1]
    secret = getpass.getpass("Client secret (leave empty to generate): ")
    if not secret:
        secret = secrets.token_urlsafe(32)
        print(f"Generated secret: {secret}")

    ph = PasswordHasher()
    secret_hash = ph.hash(secret)

    db = firestore.Client()
    db.collection("auth_clients").document(client_id).set(
        {
            "secret_hash": secret_hash,
            "status": "not-activated",
        }
    )
    print(f"Created client {client_id} with status not-activated")


if __name__ == "__main__":
    main()
