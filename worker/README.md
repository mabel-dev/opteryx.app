# Worker Service

Purpose
- Background worker API that accepts job submissions. Intended to be hosted behind IAP at `https://worker.opteryx.app`.

Local run
- `make run` starts this service on `WORKER_PORT` (default `8082`).
- Or from repo root:
  - `uvicorn worker.main:app --reload --host 0.0.0.0 --port 8082`

Build (Docker / Cloud Build)
- Built by Cloud Build using `worker/pyproject.toml` and `worker/Dockerfile`.
- To build locally from repo root:
  - `docker build -f worker/Dockerfile -t gcr.io/$PROJECT_ID/opteryx-worker .`

Endpoints
- `POST /api/v1/submit` — accepts JSON `{ "job_ref": "..." }` and returns `{ "accepted": true, "job_ref": "..." }`.

Security / IAP
- The Cloud Build deploy config deploys the worker without anonymous access (`--no-allow-unauthenticated`). To place the service behind IAP you should:
  - Configure an HTTPS Load Balancer in front of the Cloud Run service (or single-region service) and enable IAP for that load balancer.
  - Ensure the Cloud Build service account has permission to create/modify load balancers and IAP settings.
