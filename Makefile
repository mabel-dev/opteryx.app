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
	"$(UV)" pip install -r pyproject.toml

run: install
	@echo "Starting application (loads .env if present) using virtualenv '$(VENV)'..."
	@set -a; [ -f .env ] && . .env || true; set +a; \
	"$(UVICORN)" app.main:app --reload --host 0.0.0.0 --port $${PORT:-8000}
