FROM python:3.13-slim

# Create a non-root user 'norris'
RUN useradd --create-home norris
WORKDIR /home/norris

# Install build deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project pyproject and install with uv
COPY pyproject.toml ./
RUN pip install --no-cache-dir uv \
    && uv sync || (echo "uv sync failed; ensure pyproject.toml is present and valid" && exit 1)

# Copy service code
COPY data ./data
RUN chown -R norris:norris /home/norris
USER norris

ENV PORT=8080
EXPOSE 8080

CMD uvicorn data.main:app --host 0.0.0.0 --port $PORT
