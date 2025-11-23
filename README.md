# opteryx.app - Minimal FastAPI example

This repository contains a tiny FastAPI app and supporting files to build a container and deploy to Google Cloud Run.

## Run locally

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Or using Docker:

```bash
docker build -t opteryx-app:latest .
docker run -p 8080:8080 opteryx-app:latest
```

## Deploy to Cloud Run (manual)

```bash
# build and push image to Google Container Registry
PROJECT=your-gcp-project
IMAGE_NAME=opteryx-app
REGION=us-central1

gcloud builds submit --tag gcr.io/$PROJECT/$IMAGE_NAME

gcloud run deploy $IMAGE_NAME --image gcr.io/$PROJECT/$IMAGE_NAME --platform managed --region $REGION --allow-unauthenticated
```


## Cloud Build (monorepo)

This repository includes a `cloudbuild.yaml` that can build the `data` and `auth`
images from the repository root. It uses a substitution `_SERVICE` to control
which images to build; default is `all`.

Examples:

Build both services (default):
```bash
gcloud builds submit --config=cloudbuild.yaml .
```

Build only `data` (useful for service-specific triggers):
```bash
gcloud builds submit --config=cloudbuild.yaml --substitutions=_SERVICE=data .
```

When creating Cloud Build triggers, set path filters to scope triggers to only
fire on changes relevant to the service (e.g. `^data/`, `^auth/`, `^common/`,
`^pyproject.toml`). Triggers should set the `_SERVICE` substitution to `data`
or `auth` as appropriate.

