# Web Service (static)

Purpose
- A static site served by nginx. Intended to be hosted at `https://opteryx.app`.

Local run
- `make run` serves the `web/static` directory on port `8080` by default.
- Or run the container:
  - `docker build -f web/Dockerfile -t opteryx-web .`
  - `docker run -p 8080:80 opteryx-web`

Build & Deploy
- Built by Cloud Build and deployed from `cloudbuild.yaml` as `opteryx-web`.
- Domain mapping is controlled by `_MAP_DOMAINS` and `_WEB_DOMAIN` substitutions in `cloudbuild.yaml`.
