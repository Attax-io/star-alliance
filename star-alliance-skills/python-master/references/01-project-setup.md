---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Python Library Project Setup

## Quick Start

Create a new library with this structure:

```
my-library/
├── src/my_library/
│   ├── __init__.py
│   └── py.typed
├── tests/
├── pyproject.toml
├── Makefile
├── .pre-commit-config.yaml
└── .github/workflows/ci.yml
```

Use `src/` layout to prevent accidental imports of development code.

## Core Configuration

For complete templates, see:
- **[PYPROJECT.md](PYPROJECT.md)** - Full pyproject.toml with all tool configs
- **[CI.md](CI.md)** - GitHub Actions and pre-commit setup
- **[MAKEFILE.md](MAKEFILE.md)** - Makefile automation patterns

## Minimal pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-library"
version = "0.1.0"
description = "What it does"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=7.0", "ruff>=0.1", "mypy>=1.0"]

[tool.setuptools.packages.find]
where = ["src"]
```

## Essential Commands

```bash
# Setup
pip install -e ".[dev]"
pre-commit install

# Daily workflow
ruff check src tests        # Lint
ruff format src tests       # Format
pytest                      # Test
mypy src                    # Type check
```

## Key Decisions

| Choice | Recommendation | Why |
|--------|---------------|-----|
| Layout | `src/` | Catches packaging bugs early |
| Build backend | setuptools | Mature, broad compatibility |
| Linter | ruff | Fast, replaces flake8+isort+black |
| Python range | `>=3.10` | Don't pin exact versions |
| Dependencies | Minimal | Move optional deps to extras |

## Checklist

```
Project Setup:
- [ ] src/ layout with py.typed marker
- [ ] pyproject.toml (not setup.py)
- [ ] Makefile with dev/test/lint/format
- [ ] .pre-commit-config.yaml
- [ ] .github/workflows/ci.yml
- [ ] README.md, LICENSE, CHANGELOG.md
- [ ] .gitignore
```

## Helper Script

Create a new project structure:
```bash
python scripts/create_project.py my-library --author "Name"
```

## Learn More

This skill is based on the [Guide to Developing High-Quality Python Libraries](https://mcginniscommawill.com/guides/python-library-development/) by [Will McGinnis](https://mcginniscommawill.com/). See these posts for deeper coverage:

- [Defining Library Scope](https://mcginniscommawill.com/posts/2025-01-17-defining-library-scope/)
- [Dependency Management](https://mcginniscommawill.com/posts/2025-01-21-dependency-management/)
- [Licensing Your Project](https://mcginniscommawill.com/posts/2025-01-24-licensing-your-project/)
- [pyproject.toml Explained](https://mcginniscommawill.com/posts/2025-01-26-pyproject-toml-explained/)

---

## Reference: PYPROJECT

# Complete pyproject.toml Reference

## Full Template

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my-library"
version = "0.1.0"
description = "A concise description of your library"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "you@example.com"}
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "ruff>=0.1",
    "mypy>=1.0",
    "pre-commit>=3.0",
]
docs = [
    "sphinx>=7.0",
    "sphinx-rtd-theme>=2.0",
]

[project.urls]
Homepage = "https://github.com/username/my-library"
Documentation = "https://my-library.readthedocs.io"
Repository = "https://github.com/username/my-library"
Changelog = "https://github.com/username/my-library/blob/main/CHANGELOG.md"

[tool.setuptools.packages.find]
where = ["src"]

# Ruff configuration
[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["my_library"]

# Pytest configuration
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra -q --cov=my_library --cov-report=term-missing"

# MyPy configuration
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

# Coverage configuration
[tool.coverage.run]
branch = true
source = ["src/my_library"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
```

## Entry Points

For CLI commands:
```toml
[project.scripts]
mycommand = "my_library.cli:main"
```

For plugins:
```toml
[project.entry-points."my_library.plugins"]
default = "my_library.plugins.default:Plugin"
```

## Build Backends

| Backend | Use Case |
|---------|----------|
| setuptools | Default, C extensions, mature |
| hatchling | Modern pure Python, dynamic version |
| flit | Minimal, simple libraries |
| poetry | Already using Poetry ecosystem |

## Dependency Specifiers

```toml
dependencies = [
    "requests>=2.28",           # Minimum version
    "click~=8.0",               # Compatible (>=8.0, <9.0)
    "numpy>=1.20,<2.0",         # Range
    "legacy!=1.2.3",            # Exclude version
]
```

---

## Reference: CI

# CI/CD Configuration Reference

## GitHub Actions CI

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install uv
        uses: astral-sh/setup-uv@v1

      - name: Install dependencies
        run: uv pip install --system -e ".[dev]"

      - name: Lint
        run: ruff check src tests

      - name: Type check
        run: mypy src

      - name: Test
        run: pytest --cov-report=xml

      - name: Upload coverage
        if: matrix.python-version == '3.11'
        uses: codecov/codecov-action@v3
```

## Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: []
```

## Release Workflow

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: ['v*']

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

## .gitignore

```gitignore
__pycache__/
*.py[cod]
*.so
build/
dist/
*.egg-info/
.venv/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/
.idea/
.vscode/
.DS_Store
```

---

## Reference: MAKEFILE

# Makefile Reference

## Standard Makefile

```makefile
.PHONY: help install dev test lint format type-check clean build publish

help:
	@echo "Commands: dev test lint format type-check clean build publish"

dev:
	pip install -e ".[dev,docs]"
	pre-commit install

test:
	pytest

lint:
	ruff check src tests

format:
	ruff format src tests
	ruff check --fix src tests

type-check:
	mypy src

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +

build: clean
	python -m build

publish: build
	twine upload dist/*
```

## With uv (faster)

```makefile
dev:
	uv pip install -e ".[dev,docs]"
	pre-commit install

install:
	uv pip install .
```

## Additional Targets

```makefile
# Documentation
docs:
	cd docs && make html

docs-serve:
	python -m http.server --directory docs/_build/html

# Coverage report
coverage:
	pytest --cov-report=html
	open htmlcov/index.html

# Security scanning
security:
	bandit -r src/
	pip-audit
```
