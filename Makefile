.PHONY: install run

# Virtual environment directory
VENV ?= .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UV := $(VENV)/bin/uv
UVICORN := $(VENV)/bin/uvicorn

install:
	@echo "Creating virtualenv at '$(VENV)' (if missing) and installing dependencies with 'uv'."
	@if [ ! -f pyproject.toml ]; then \
		echo "Error: pyproject.toml not found in project root."; \
		exit 1; \
	fi; \
	if [ ! -d "$(VENV)" ]; then \
		python3 -m venv "$(VENV)"; \
	fi; \
	"$(PIP)" install --upgrade pip setuptools wheel; \
	"$(PIP)" install uv; \
	# Install runtime deps directly into the venv so dev run works reliably
	"$(PIP)" install fastapi uvicorn[standard] python-jose[cryptography] cryptography requests python-multipart

run: install
	@echo "Starting auth and data services (loads .env if present) using virtualenv '$(VENV)'..."
	@set -a; [ -f .env ] && . .env || true; set +a; \
	# compute URLs (fall back to provided PORT or service defaults)
	AUTH_URL=http://localhost:$${AUTH_PORT:-$${PORT:-8081}}; \
	DATA_URL=http://localhost:$${DATA_PORT:-$${PORT:-8000}}; \
	echo "AUTH: $$AUTH_URL"; \
	echo "DATA: $$DATA_URL"; \
	# start services in background and wait (shell expands ${...:-...})
	"$(UVICORN)" auth.main:app --reload --host 0.0.0.0 --port $${AUTH_PORT:-$${PORT:-8081}} & \
	"$(UVICORN)" data.main:app --reload --host 0.0.0.0 --port $${DATA_PORT:-$${PORT:-8000}} & \
	wait
