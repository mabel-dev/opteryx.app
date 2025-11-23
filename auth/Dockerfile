FROM python:3.13-slim

# Create a non-root user 'norris'
RUN useradd --create-home norris
WORKDIR /home/norris

# Install build deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project pyproject from repository root and install with uv.
# NOTE: when building this Dockerfile directly, set the build context to the
# repository root so `../pyproject.toml` is available. Example:
#   docker build -f auth/Dockerfile -t opteryx-auth .
COPY ../pyproject.toml ./
RUN pip install --no-cache-dir uv \
    && uv sync || (echo "uv sync failed; ensure pyproject.toml is present and valid and you built with the repo root as context" && exit 1)

# Copy service code
COPY auth ./auth
RUN chown -R norris:norris /home/norris
USER norris

ENV PORT=8081
EXPOSE 8081

CMD uvicorn auth.main:app --host 0.0.0.0 --port $PORT
