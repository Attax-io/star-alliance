---
name: python-master
description: "The Developer's craft for building production-grade Python libraries and web apps end to end — 14 skills from wdm0006/python-skills merged into one router. Covers project setup (pyproject/uv/ruff/pytest/pre-commit/CI), packaging + PyPI publishing, code quality (ruff/mypy, typing, idioms), testing (pytest, fixtures, mocking, Hypothesis), docs (docstrings, Sphinx), API design + deprecation, CLI building (Click/Typer), performance (cProfile, memray, benchmarks), security audit (Bandit, pip-audit, Semgrep), web-app architecture (FastAPI + SQLAlchemy + Postgres + Stripe + Docker), git hygiene, release management, OSS community, and full library review. Use when starting/modernizing a Python library or service, configuring tooling, writing tests or docs, designing an API or CLI, profiling, auditing security, cutting a release, or reviewing a Python codebase. Triggers: 'set up a python library', 'write pytest tests', 'package for pypi', 'audit python security', 'build a python cli', 'review this python library'."
license: MIT
metadata:
  author: wdm0006/python-skills (merged by Star Alliance)
  version: 1.1.0
type: Skill
---

# Python Master

One member-carried craft that merges the 14 skills of [`wdm0006/python-skills`](https://github.com/wdm0006/python-skills)
into a single router. Each domain is a self-contained reference file under `references/`.
Load only the file(s) the task needs — do not read all 14 up front.

## How to use

1. Match the task to a domain in the table below.
2. Read that one reference file (`references/NN-*.md`) for the full distilled playbook.
3. For setup / release / security automation, run the matching helper in `scripts/`.

## Domain index

| # | Reference | Load when the task is… |
|---|-----------|------------------------|
| 01 | [project-setup](references/01-project-setup.md) | New library scaffold, modernizing to pyproject.toml, uv/ruff/pytest/pre-commit/CI, Makefiles. Includes PYPROJECT / CI / MAKEFILE refs. |
| 02 | [packaging](references/02-packaging.md) | Build backends (setuptools/hatchling), wheels, PyPI + trusted publishing, packaging bugs. |
| 03 | [code-quality](references/03-code-quality.md) | ruff lint/format, mypy typing, Pythonic refactors. Includes RUFF / MYPY / TYPE_PATTERNS refs. |
| 04 | [testing-strategy](references/04-testing-strategy.md) | pytest suites, fixtures, parametrization, mocking, Hypothesis, coverage. Includes FIXTURES / HYPOTHESIS refs. |
| 05 | [documentation](references/05-documentation.md) | Google-style docstrings, Sphinx, API refs, tutorials, ReadTheDocs. |
| 06 | [api-design](references/06-api-design.md) | Designing/reviewing library APIs, evolution, deprecation, breaking changes, error handling. |
| 07 | [cli-development](references/07-cli-development.md) | Click/Typer CLIs, command groups, progress bars, shell completion, CliRunner testing. |
| 08 | [performance](references/08-performance.md) | Profiling (cProfile, PyInstrument), memory (memray, tracemalloc), pytest-benchmark, regression gates. |
| 09 | [security-audit](references/09-security-audit.md) | Bandit, pip-audit, Semgrep, detect-secrets; injection, secrets, weak crypto, insecure deserialization. |
| 10 | [web-app-architecture](references/10-web-app-architecture.md) | Production web app: FastAPI + async SQLAlchemy + Postgres + Stripe + Docker/Terraform. Includes STACK / AUTH / FRONTEND / PAYMENTS / BACKGROUND_JOBS / DEPLOYMENT refs. |
| 11 | [git-hygiene](references/11-git-hygiene.md) | Committed secrets/junk, .gitignore, git rm --cached, history scrubbing, credential rotation. |
| 12 | [release-management](references/12-release-management.md) | Semver, Keep a Changelog, release automation, deprecation comms. |
| 13 | [community](references/13-community.md) | CONTRIBUTING, CODE_OF_CONDUCT, issue/PR templates, contributor recognition, governance. |
| 14 | [library-review](references/14-library-review.md) | End-to-end library health audit across all of the above; prep for a major release or dependency vetting. |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/create_project.py` | Scaffold a new professional Python library (paired with reference 01). |
| `scripts/bump_version.py` | Semver bump for a release (paired with reference 12). |
| `scripts/security_scan.py` | Run the Bandit/pip-audit/Semgrep/detect-secrets sweep (paired with reference 09). |

## Provenance

Merged verbatim (bodies + sub-references concatenated under `## Reference:` headers) from the
14 skills in `wdm0006/python-skills` (MIT). Original skill names preserved inside each reference
file. This router adds the index and load-on-demand discipline; the domain content is upstream's.
