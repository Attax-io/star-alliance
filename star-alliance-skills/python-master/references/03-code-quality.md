---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Python Code Quality

## Quick Reference

| Tool | Purpose | Command |
|------|---------|---------|
| ruff | Lint + format | `ruff check src && ruff format src` |
| mypy | Type check | `mypy src` |

## Ruff Configuration

Minimal config in pyproject.toml:

```toml
[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP"]
```

For full configuration options, see **[RUFF_CONFIG.md](RUFF_CONFIG.md)**.

## MyPy Configuration

```toml
[tool.mypy]
python_version = "3.10"
disallow_untyped_defs = true
warn_return_any = true
```

For strict settings and overrides, see **[MYPY_CONFIG.md](MYPY_CONFIG.md)**.

## Type Hints Patterns

```python
# Basic
def process(items: list[str]) -> dict[str, int]: ...

# Optional
def fetch(url: str, timeout: int | None = None) -> bytes: ...

# Callable
def apply(func: Callable[[int], str], value: int) -> str: ...

# Generic
T = TypeVar("T")
def first(items: Sequence[T]) -> T | None: ...
```

For protocols and advanced patterns, see **[TYPE_PATTERNS.md](TYPE_PATTERNS.md)**.

## Common Anti-Patterns

```python
# Bad: Mutable default
def process(items: list = []):  # Bug!
    ...

# Good: None default
def process(items: list | None = None):
    items = items or []
    ...
```

```python
# Bad: Bare except
try:
    ...
except:
    pass

# Good: Specific exception
try:
    ...
except ValueError as e:
    logger.error(e)
```

## Pythonic Idioms

```python
# Iteration
for item in items:           # Not: for i in range(len(items))
for i, item in enumerate(items):  # When index needed

# Dictionary access
value = d.get(key, default)  # Not: if key in d: value = d[key]

# Context managers
with open(path) as f:        # Not: f = open(path); try: finally: f.close()

# Comprehensions (simple only)
squares = [x**2 for x in numbers]
```

## Module Organization

```
src/my_library/
├── __init__.py      # Public API exports
├── _internal.py     # Private (underscore prefix)
├── exceptions.py    # Custom exceptions
├── types.py         # Type definitions
└── py.typed         # Type hint marker
```

## Checklist

```
Code Quality:
- [ ] ruff check passes
- [ ] mypy passes (strict mode)
- [ ] Public API has type hints
- [ ] Public API has docstrings
- [ ] No mutable default arguments
- [ ] Specific exception handling
- [ ] py.typed marker present
```

## Learn More

This skill is based on the [Code Quality](https://mcginniscommawill.com/guides/python-library-development/#code-quality-the-foundation) section of the [Guide to Developing High-Quality Python Libraries](https://mcginniscommawill.com/guides/python-library-development/) by [Will McGinnis](https://mcginniscommawill.com/). See these posts for deeper coverage:

- [Linting & Formatting with Ruff](https://mcginniscommawill.com/posts/2025-01-30-linting-formatting-ruff/)
- [Understanding McCabe Complexity](https://mcginniscommawill.com/posts/2025-04-24-understanding-mccabe-complexity/)
- [Adding Type Hints](https://mcginniscommawill.com/posts/2025-04-03-pygeohash-type-hints/)

---

## Reference: RUFF_CONFIG

# Ruff Configuration Reference

## Comprehensive Configuration

```toml
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
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
    "TCH",    # flake8-type-checking
    "PTH",    # flake8-use-pathlib
    "ERA",    # eradicate (commented code)
    "PL",     # pylint
    "RUF",    # ruff-specific
]
ignore = [
    "E501",    # line too long (formatter handles)
    "PLR0913", # too many arguments
    "PLR2004", # magic value comparison
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101", "ARG001", "PLR2004"]
"__init__.py" = ["F401"]  # unused imports OK in __init__

[tool.ruff.lint.isort]
known-first-party = ["my_library"]
force-single-line = true

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

## Rule Categories

| Code | Category | Description |
|------|----------|-------------|
| E, W | pycodestyle | PEP 8 style |
| F | Pyflakes | Logical errors |
| I | isort | Import sorting |
| B | flake8-bugbear | Bug patterns |
| C4 | comprehensions | Simplify comprehensions |
| UP | pyupgrade | Modern syntax |
| S | bandit | Security |
| ARG | unused-arguments | Unused params |
| SIM | simplify | Code simplification |

## Commands

```bash
ruff check src tests           # Lint
ruff check --fix src tests     # Lint + autofix
ruff format src tests          # Format
ruff check --select=I --fix .  # Fix imports only
```

---

## Reference: MYPY_CONFIG

# MyPy Configuration Reference

## Strict Configuration

```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[[tool.mypy.overrides]]
module = "third_party.*"
ignore_missing_imports = true
```

## Gradual Adoption

Start lenient, tighten over time:

```toml
# Phase 1: Basic
[tool.mypy]
python_version = "3.10"
warn_return_any = true

# Phase 2: Require types on new code
disallow_untyped_defs = true
disallow_incomplete_defs = true

# Phase 3: Full strict
strict = true
```

## Common Fixes

```python
# Error: Missing return type
def process(x):  # Add: -> ReturnType
    ...

# Error: Incompatible types
x: str = 123  # Fix: x: int = 123

# Error: Missing type for argument
def func(data):  # Add: data: dict[str, Any]
    ...

# Silence specific line
x = untyped_call()  # type: ignore[no-untyped-call]
```

## Type Stubs

For libraries without type hints:

```bash
# Install stubs
pip install types-requests types-PyYAML

# Or ignore in config
[[tool.mypy.overrides]]
module = "untyped_library.*"
ignore_missing_imports = true
```

---

## Reference: TYPE_PATTERNS

# Type Hint Patterns Reference

## Basic Types

```python
from collections.abc import Sequence, Mapping, Callable, Iterator

# Primitives
x: int = 1
y: str = "hello"
z: bool = True

# Collections
items: list[str] = []
mapping: dict[str, int] = {}
coords: tuple[float, float] = (0.0, 0.0)

# Optional
name: str | None = None
```

## Function Signatures

```python
# Basic
def greet(name: str) -> str:
    return f"Hello, {name}"

# Multiple returns
def parse(s: str) -> tuple[int, str]:
    ...

# Keyword-only after *
def fetch(url: str, *, timeout: int = 30) -> bytes:
    ...

# Callable parameter
def apply(func: Callable[[int], str], value: int) -> str:
    return func(value)
```

## Generics

```python
from typing import TypeVar, Generic

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

def first(items: Sequence[T]) -> T | None:
    return items[0] if items else None

class Cache(Generic[K, V]):
    def __init__(self) -> None:
        self._data: dict[K, V] = {}

    def get(self, key: K) -> V | None:
        return self._data.get(key)

    def set(self, key: K, value: V) -> None:
        self._data[key] = value
```

## Protocols (Structural Typing)

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Encoder(Protocol):
    def encode(self, data: bytes) -> str: ...
    def decode(self, text: str) -> bytes: ...

# Any class with encode/decode methods satisfies Encoder
def process(encoder: Encoder, data: bytes) -> str:
    return encoder.encode(data)
```

## Type Aliases

```python
from typing import TypeAlias

Coordinate: TypeAlias = tuple[float, float]
BoundingBox: TypeAlias = tuple[float, float, float, float]
Handler: TypeAlias = Callable[[str], None]

def process(coord: Coordinate, box: BoundingBox) -> None:
    ...
```

## Overloads

```python
from typing import overload

@overload
def get(key: str) -> str: ...
@overload
def get(key: str, default: str) -> str: ...
@overload
def get(key: str, default: None) -> str | None: ...

def get(key: str, default: str | None = None) -> str | None:
    ...
```

## TypedDict

```python
from typing import TypedDict, Required, NotRequired

class Config(TypedDict):
    name: str                    # Required
    version: str                 # Required
    debug: NotRequired[bool]     # Optional

def load_config() -> Config:
    return {"name": "app", "version": "1.0"}
```
