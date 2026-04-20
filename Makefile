DEFAULT_VENV_NAME := .venv
PYTHON := $(DEFAULT_VENV_NAME)/bin/python3
PIP := $(DEFAULT_VENV_NAME)/bin/pip
MAIN := a_maze_ing.py
CONFIG ?= config.txt

.PHONY: help install build-pkg install-pkg run debug clean lint lint-strict

help:
	@echo "Available targets:"
	@echo "  make install      Detect or create a virtualenv and install dependencies"
	@echo "  make run          Run the project"
	@echo "  make debug        Run the project with pdb"
	@echo "  make clean        Remove caches and temporary files"
	@echo "  make lint         Run flake8 and required mypy checks"
	@echo "  make lint-strict  Run flake8 and mypy --strict"
	@echo "  make detect-venv  Show detected virtualenv name"

install:
	@set -eu; \
	find . -type d -name ".venv" -prune -exec rm -rf {} +; \
	echo "Creating clean virtual environment..."; \
	python3 -m venv $(DEFAULT_VENV_NAME); \
	echo "Installing dependencies..."; \
	$(PIP) install -r requirements.txt; \
	echo "Install to virtualenv $(DEFAULT_VENV_NAME) Successful."

build-pkg:
	@set -eu; \
	if [ ! -f $(PYTHON) ]; then \
		echo "Error: no valid virtualenv found. Run 'make install' first." >&2; \
		exit 1; \
	fi; \
	$(PYTHON) -m build --outdir .

install-pkg:
	@set -eu; \
	if [ ! -f $(PIP) ]; then \
		echo "Error: no valid virtualenv found. Run 'make install' first." >&2; \
		exit 1; \
	fi; \
	$(PIP) install mazegen-*.whl

run:
	@set -eu; \
	if [ ! -f $(PYTHON) ]; then \
		echo "Error: no valid virtualenv found. Run 'make install' first." >&2; \
		exit 1; \
	fi; \
	$(PYTHON) "$(MAIN)" "$(CONFIG)"

debug:
	@set -eu; \
	if [ ! -f $(PYTHON) ]; then \
		echo "Error: no valid virtualenv found. Run 'make install' first." >&2; \
		exit 1; \
	fi; \
	$(PYTHON) -m pdb "$(MAIN)" "$(CONFIG)"

clean:
	@set -eu; \
	find . -type d -name ".mypy_cache" -prune -exec rm -rf {} +; \
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +; \
	find . -type d -name ".ruff_cache" -prune -exec rm -rf {} +; \
	find . -maxdepth 1 -name "mazegen-*.whl" -delete; \
	find . -maxdepth 1 -name "mazegen-*.tar.gz" -delete; \
	find . -type d -name "build" -prune -exec rm -rf {} +; \
	find . -type d -name "dist" -prune -exec rm -rf {} +; \
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +; \
	find . -type d -name "*.egg-info" -prune -exec rm -rf {} +; \
	find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete

lint:
	@set -eu; \
	if [ ! -f $(PYTHON) ]; then \
		echo "Error: no valid virtualenv found. Run 'make install' first." >&2; \
		exit 1; \
	fi; \
	$(PYTHON) -m flake8 .; \
	$(PYTHON) -m mypy . \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	@set -eu; \
	if [ ! -f $(PYTHON) ]; then \
		echo "Error: no valid virtualenv found. Run 'make install' first." >&2; \
		exit 1; \
	fi; \
	$(PYTHON) -m flake8 .; \
	$(PYTHON) -m mypy . --strict
