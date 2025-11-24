FROM python:3.11-slim

RUN useradd --create-home worker
WORKDIR /home/worker

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
RUN chown -R worker:worker /home/worker
USER worker

ENV PORT=8082
EXPOSE 8082

CMD uvicorn worker.main:app --host 0.0.0.0 --port $PORT
