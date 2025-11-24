FROM python:3.11-slim

# Use the same non-root user across services for consistency
RUN useradd --create-home norris
WORKDIR /home/norris

# Install runtime dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Use `pyproject.toml` with `uv` like other services so builds are consistent
COPY worker/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir uv \
    && uv sync || (echo "uv sync failed; ensure worker/pyproject.toml is present and valid in the build context" && exit 1)

# Copy app
COPY worker ./worker
RUN chown -R norris:norris /home/norris
USER norris

# Ensure virtualenv bin is on PATH and standardize port to 8080 like other services
ENV PATH=/home/norris/.venv/bin:$PATH
ENV PORT=8080
EXPOSE 8080

CMD uvicorn worker.main:app --host 0.0.0.0 --port $PORT
