# Copilot Instructions for Nightjar

## Project Overview

Nightjar is a typing-based dispatching library for Python.

## Code Style

- Use **NumPy docstring style** for all functions and classes
- Follow **ruff** linting rules configured in `pyproject.toml`
- Line length: 79 characters
- Use double quotes for strings

## Python Version

- Target Python 3.9+
- Use `typing_extensions` for backward-compatible type hints

## Project Structure

- Source code is in `src/nightjar/`
- Examples are in `examples/`
- Use relative imports sparingly; prefer absolute imports

## Documentation Guidelines

- Include Parameters, Returns, Raises, and Examples sections in docstrings where applicable
- Keep docstrings concise but informative

## Testing

- Write tests in the `tests/` directory
- Use assertions for test validation
- Generate tests only when user requests them explicitly

## Error Messages

- Store error message in a `msg` variable before raising
- Keep messages as a single sentence without trailing periods
- Avoid using colons or semicolons in messages
- Use f-strings for dynamic values
- Example:
  ```python
  msg = f"expected config to be a Mapping, got {type(config).__name__}"
  raise ValueError(msg)
  ```
