CONFIG ?= config.txt
VENV_NAME := .venv

.PHONY: install run debug clean lint lint-strict
install:
	python3 -m venv $(VENV_NAME)
	source $(VENV_NAME)/bin/activate
	pip install -r requirements.txt

run:
	python3 a_maze_ing.py $(CONFIG)

debug:
	python3 -m pdb a_maze_ing.py $(CONFIG)

clean:
	rm -r __pycache__/ .mypy_cache/ .pytest_cache/ .ruff_cache/ *.pyc *.pyo build/ dist/ *.egg-info/

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict
