DEFAULT_VENV_NAME := .venv
MAIN := a_maze_ing.py
CONFIG ?= config.txt

.PHONY: help detect-venv install run debug clean lint lint-strict

help:
	@echo "Available targets:"
	@echo "  make install      Detect or create a virtualenv and install dependencies"
	@echo "  make run          Run the project"
	@echo "  make debug        Run the project with pdb"
	@echo "  make clean        Remove caches and temporary files"
	@echo "  make lint         Run flake8 and required mypy checks"
	@echo "  make lint-strict  Run flake8 and mypy --strict"
	@echo "  make detect-venv  Show detected virtualenv name"

detect-venv:
	@set -eu; \
	valid_dirs=""; \
	count=0; \
	for cfg in ./*/pyvenv.cfg ./.*/pyvenv.cfg; do \
		[ -f "$$cfg" ] || continue; \
		dir=$$(dirname "$$cfg"); \
		if [ -x "$$dir/bin/python" ] && \
		   [ -x "$$dir/bin/pip" ] && \
		   "$$dir/bin/python" -c "import sys; raise SystemExit(0 if sys.prefix != sys.base_prefix else 1)"; then \
			valid_dirs="$$valid_dirs $$dir"; \
			count=$$((count + 1)); \
		fi; \
	done; \
	if [ "$$count" -eq 1 ]; then \
		set -- $$valid_dirs; \
		printf '%s\n' "$$1"; \
	elif [ "$$count" -eq 0 ]; then \
		exit 0; \
	else \
		echo "Error: multiple valid virtualenvs found:$$valid_dirs" >&2; \
		exit 1; \
	fi
# output
# Prints one detected virtualenv directory, nothing if none, error if multiple

install:
	@set -eu; \
	VENV_DIR="$$( $(MAKE) --no-print-directory detect-venv )"; \
	if [ -z "$$VENV_DIR" ]; then \
		VENV_DIR="$(DEFAULT_VENV_NAME)"; \
		echo "Creating virtual environment in $$VENV_DIR"; \
		python3 -m venv "$$VENV_DIR"; \
	else \
		echo "Using existing virtual environment: $$VENV_DIR"; \
	fi; \
	"$$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel; \
	"$$VENV_DIR/bin/pip" install -r requirements.txt
# output
# Reuses one detected virtualenv or creates DEFAULT_VENV_NAME if none exists

run:
	@set -eu; \
	VENV_DIR="$$( $(MAKE) --no-print-directory detect-venv )"; \
	if [ -z "$$VENV_DIR" ]; then \
		echo "Error: no valid virtualenv found. Run 'make install' first." >&2; \
		exit 1; \
	fi; \
	"$$VENV_DIR/bin/python" "$(MAIN)" "$(CONFIG)"
# output
# Runs a_maze_ing.py with config.txt inside the detected virtualenv

debug:
	@set -eu; \
	VENV_DIR="$$( $(MAKE) --no-print-directory detect-venv )"; \
	if [ -z "$$VENV_DIR" ]; then \
		echo "Error: no valid virtualenv found. Run 'make install' first." >&2; \
		exit 1; \
	fi; \
	"$$VENV_DIR/bin/python" -m pdb "$(MAIN)" "$(CONFIG)"
# output
# Runs the project with Python's built-in debugger

clean:
	rm -rf .mypy_cache .pytest_cache .ruff_cache build dist
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete
# output
# Removes caches and build artifacts without deleting any virtualenv

lint:
	@set -eu; \
	VENV_DIR="$$( $(MAKE) --no-print-directory detect-venv )"; \
	if [ -z "$$VENV_DIR" ]; then \
		echo "Error: no valid virtualenv found. Run 'make install' first." >&2; \
		exit 1; \
	fi; \
	"$$VENV_DIR/bin/python" -m flake8 .; \
	"$$VENV_DIR/bin/python" -m mypy . \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs
# output
# Runs flake8 and required mypy checks in the detected virtualenv

lint-strict:
	@set -eu; \
	VENV_DIR="$$( $(MAKE) --no-print-directory detect-venv )"; \
	if [ -z "$$VENV_DIR" ]; then \
		echo "Error: no valid virtualenv found. Run 'make install' first." >&2; \
		exit 1; \
	fi; \
	"$$VENV_DIR/bin/python" -m flake8 .; \
	"$$VENV_DIR/bin/python" -m mypy . --strict
# output
# Runs flake8 and mypy --strict in the detected virtualenv
