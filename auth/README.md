# Auth Service

Purpose
- Issues RS256 JWTs for machine-to-machine authentication and exposes a JWKS endpoint for verification.

Local run
- `make run` starts this service on `AUTH_PORT` (default `8081`).
- Or from repo root:
  - `uvicorn auth.main:app --reload --host 0.0.0.0 --port 8081`

Build (Docker / Cloud Build)
- Built by Cloud Build using `auth/pyproject.toml` and `auth/Dockerfile`.
- To build locally from repo root (build context must be repo root):
  - `docker build -f auth/Dockerfile -t gcr.io/$PROJECT_ID/opteryx-auth .`

Endpoints
- `POST /token` — client_credentials token issuance (dev clients in code). Accepts optional `key_date` or `days_ahead` to request a specific signing key.
- `GET /jwks` — returns the JWKS with rotated keys (kid per-date).
- `POST /keys/ensure` — admin endpoint to create keys for a future date.

Notes
- Key material is stored using `auth/secret_store.py` (filesystem fallback; can use GCP Secret Manager when `GCP_PROJECT` is set and the client library is available).
