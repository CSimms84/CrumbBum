PY ?= python3
PKG = crumbbum

.PHONY: help install dev-install test lint format type clean

help:
	@echo "Targets: install, dev-install, test, lint, format, type, clean"

install:
	$(PY) -m pip install .

dev-install:
	$(PY) -m pip install -e .[dev]

test:
	PYTHONPATH=src $(PY) -m pytest -q

lint:
	ruff check .

format:
	ruff format .

type:
	mypy src

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache

