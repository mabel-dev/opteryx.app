FROM python:3.13-slim

# Create a non-root user 'norris'
RUN useradd --create-home norris
WORKDIR /home/norris

# Install build dependencies and cleanup
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject (expected to exist) and install dependencies using `uv` CLI
# Install `uv` first, then run `uv install` to populate the environment
COPY pyproject.toml ./
RUN pip install --no-cache-dir uv \
    && uv install || (echo "uv install failed; ensure pyproject.toml is present and valid" && exit 1)

COPY app ./app
RUN chown -R norris:norris /home/norris
USER norris

ENV PORT=8080
EXPOSE 8080

CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
