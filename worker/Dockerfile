FROM python:3.11-slim

RUN useradd --create-home worker
WORKDIR /home/worker

# Install runtime dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY worker/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY worker ./worker
RUN chown -R worker:worker /home/worker
USER worker

ENV PORT=8082
EXPOSE 8082

CMD uvicorn worker.main:app --host 0.0.0.0 --port $PORT
