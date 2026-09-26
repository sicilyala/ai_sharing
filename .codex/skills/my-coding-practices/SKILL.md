---
name: my-coding-practices
description: Apply the coding and logging contract. Use when adding, changing, reviewing, or debugging Python logging, executable Python entry points, reusable utilities, bash entry points that invoke Python, or their tests, especially when code must reuse src/common/logger_setup.py rather than introduce a separate logging stack.
---

# My Coding Practices

Reuse its approved logger implementation and preserve its logging contract.

## Required reading

1. Read `references/coding-practices.md` for coding practice details.
2. Read `${WORKSPACE_ROOT}/src/common/logger_setup.py` before using logging. If this file is missing, stop and ask the user; do not invent logging infrastructure.

## Python workflow

1. For executable modules, provide a one-line modular usage example, implement `get_args()` with `argparse`, parse arguments first in `main()`, and use the standard `if __name__ == "__main__": main()` entry point.
2. Run modules as `python -m src.<module>` from the repository root. Do not add `sys.path` mutations.
3. Put tests under `test/` with the same structure as `src/`; run the narrowest relevant `pytest` command, then the repository's required verification.

## Shell-to-Python CLI contract

- Project Shell and Python entry points accept named options only:
  `--name VALUE` for value-taking options and `--flag` for Boolean switches.
  Do not define positional arguments or positional aliases. This applies
  to all workflow inputs, including paths, configuration, and ports.

- The shell owns the user-facing CLI: declare supported options and
  defaults, parse and consume arguments, and reject unsupported arguments
  or missing required values before environment setup or Python execution.

- The shell determines its workspace internally:
  `WORKSPACE_ROOT="$(git rev-parse --show-toplevel)"`.
  Do not accept or advertise `--work_space` as a shell option.

- Python declares `--work_space` as a required named option. The shell
  supplies it explicitly as `--work_space "$WORKSPACE_ROOT"`.
  Named options must not depend on their order.

- Pass Python arguments using literal option names and quoted, named shell
  variables, for example `--output_path "$OUTPUT_PATH"`. Shell variable
  names are internal implementation details, not additional CLI inputs.

- Never forward raw "$@", "$*", or unparsed user-argument arrays to Python.
  Construct optional argument arrays one supported option at a time from
  parsed, named variables.

- Resolve CLI defaults in the shell. When omission intentionally restores
  saved run settings, implement and document that behavior explicitly.

- Python parses its named options and validates their types and domain
  constraints. The shell must not rely on Python to reject unsupported
  user-facing arguments.

## Logging contract

Use exactly this import pattern in every module that emits application logs:

```python
from src.common.logger_setup import LOG_DEBUG, LOG_ERROR, LOG_INFO, LOG_WARNING, setup_logger

LOGGER = setup_logger(__name__)
```

- Emit messages through `LOG_DEBUG`, `LOG_INFO`, `LOG_WARNING`, `LOG_ERROR`, or `LOG_CRITICAL`, not through `print()` or ad-hoc loggers.
- Keep `setup_logger(__name__)` at module scope so the caller-aware `LOG_*` helpers resolve to a configured logger.
- Configure verbosity with `APP_LOG_LEVEL`; use `APP_LOG_FILE`, `APP_LOG_MAX_BYTES`, and `APP_LOG_BACKUP_COUNT` only through the supplied logger's existing environment contract.
- Do not add duplicate handlers, alter file rotation behavior, or create a second logging abstraction.

## Quality gates

- Check numerical inputs for `NaN` or infinity immediately where relevant.
- Prefer vectorized NumPy/Pandas operations for large data.
