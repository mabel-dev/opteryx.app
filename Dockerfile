FROM python:3.11-slim

# Create a non-root user
RUN useradd --create-home appuser
WORKDIR /home/appuser

# Install build dependencies and cleanup
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
RUN chown -R appuser:appuser /home/appuser
USER appuser

ENV PORT=8080
EXPOSE 8080

CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
