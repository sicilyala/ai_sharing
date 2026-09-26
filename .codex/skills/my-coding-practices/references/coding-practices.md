# Agentic coding practices 

## General 

1. **Visualization**: All plots must have rigorous labeling (units, axes titles), use high DPI (300) and clear font ('Times New Roman', 10pt).
2. **Type Hinting:** Use `mypy` for static type checking in Python.
3. **Test:** Using `pytest` for `Python`, `Vitest` for `Javascript`, and `testthat` for `R`.
   - **All the test files will be located in the `test/` directory with the same structure as their source code in the `src/` directory.**
4. **Linter & Formatter:** Use `ruff` for Python linting and formatting.

## `Python` usage practices

### Common practices
- Before running Python scripts, always remember to activate the virtual environment firstly by running `cd $(git rev-parse --show-toplevel) && source .venv/bin/activate`.
- Use `argparse` for command-line argument parsing. See details in the `Arguments Parsing` section below.
- Do **NOT** write any code like `sys.path.insert(0, str(REPO_ROOT))` in Python scripts.
- If you need to execute Python scripts, you **MUST** follow modularized ways to execute Python scripts. You **MUST** first enter the repository root and activate the Python virtual environment, and then execute the script using `python -m` with the module path. Do **NOT** execute Python scripts directly with `python src/path/to/script.py` to avoid issues with relative imports and environment configurations. Always use the modularized execution approach as described below. For example, to execute the script `src/function/script_name_for_specific_task.py`, you **MUST DO** as follows with one-line shell command:
  ```bash
  cd $(git rev-parse --show-toplevel) && source .venv/bin/activate && python -m src.function.script_name_for_specific_task --< arguments >
  ```
- All executable Python scripts **MUST** have an entrance point as follows:
  ```python
  # the main function as the entry point
  def main():
    ## the main logic pipeline follows here
  
  # entry point
  if __name__ == "__main__":
    main()
  ```
- For executable Python scripts, you **MUST** write down the usage example at the top comment area, demonstrating how to execute the script with necessary arguments. The usage example **MUST** be **one-line shell command** in the modularized execution approach. Also write down the output files if applicable. For example:
  ```python
  """
  Usage example:
  cd $(git rev-parse --show-toplevel) && source .venv/bin/activate && python -m src.submodule.executable_python_script --work_space $(git rev-parse --show-toplevel) --data_path relative/path/to/data --output_path relative/path/to/output --<other_arguments> 

  Output files (if applicable) :
  - relative/path/to/output/file1
  - relative/path/to/output/file2
  """
  ```

### Logger Usage for Python Scripts
- Use the logger defined in `src/common/logger_setup.py` for consistent logging across modules.
- If `src/common/logger_setup.py` is **NOT** found, you **MUST** stop and ask the user for instructions before proceeding. Do **NOT** implement logger without permission. Always use the provided logger for all logging purposes in the project.
- Here's an example of how to use the logger in Python scripts:
  ```python
  from src.common.logger_setup import setup_logger, LOG_INFO, LOG_WARNING, LOG_ERROR, LOG_DEBUG
  logger = setup_logger(__name__)

  LOG_DEBUG("This is a DEBUG message")
  LOG_INFO("This is an INFO message")
  LOG_WARNING("This is a WARNING message")
  LOG_ERROR("This is an ERROR message")
  ```

## `R` usage practices

### Coding rules
- Must wrap the core logic in a `main <- function() { ... }` and call it conditionally (e.g., `if (sys.nframe() == 0L) { main() }`), use `optparse` for CLI arguments interaction.

### R Environment Rules (**MUST** follow)

1) Always run R from the repository root `cd $(git rev-parse --show-toplevel)`, which contains `renv/` and `.Rprofile`.
2) Do NOT use `Rscript --vanilla` for project scripts, because `--vanilla` skips startup files (including the project `.Rprofile`) and will bypass renv.
3) Before running / debugging any R script, verify renv is active by checking that `.libPaths()[1]` contains `$(git rev-parse --show-toplevel)/renv/library/`.
4) For every R command, enable fast renv startup by setting these environment variables (either in `.Renviron` or as command prefixes, and they **MUST** be set **before** `renv/activate.R` runs):
   - `RENV_CONFIG_SANDBOX_ENABLED=false`
   - `RENV_CONFIG_SYNCHRONIZED_CHECK=false`
   - `RENV_PROJECT="$(git rev-parse --show-toplevel)"` (optional but recommended to skip project discovery)
5) For required R package dependencies, do NOT use silent callback-style checks such as `if (requireNamespace("pkg", quietly = TRUE))`. Load the package in the entry script's `suppressPackageStartupMessages({ ... })` block with `library(pkg)`, and keep explicit `pkg::fun()` calls in lower-level functions. If the required package is **NOT** available, the script will fail/stop with a clear error message. Example: for `randtoolbox`, write `library(randtoolbox)` in the entry script, and use `randtoolbox::halton()` / `randtoolbox::sobol()` in helper functions instead of bare `halton()` / `sobol()`.

### Common commands

Run a script (preferred):
- `cd "$(git rev-parse --show-toplevel)" && RENV_CONFIG_SANDBOX_ENABLED=false RENV_CONFIG_SYNCHRONIZED_CHECK=false RENV_PROJECT="$(git rev-parse --show-toplevel)" Rscript src/path/to/script.R [args...]`

Quick renv check (**MUST** pass):
- `cd "$(git rev-parse --show-toplevel)" && RENV_CONFIG_SANDBOX_ENABLED=false RENV_CONFIG_SYNCHRONIZED_CHECK=false RENV_PROJECT="$(git rev-parse --show-toplevel)" Rscript -e 'cat(.libPaths()[1], "\n")'`

Startup diagnostics (one-off, to locate renv autoload slowness):
- `cd "$(git rev-parse --show-toplevel)" && RENV_STARTUP_DIAGNOSTICS=TRUE RENV_CONFIG_SANDBOX_ENABLED=false RENV_CONFIG_SYNCHRONIZED_CHECK=false RENV_PROJECT="$(git rev-parse --show-toplevel)" Rscript -e 'cat(.libPaths()[1], "\n")'`

If you MUST use --vanilla (only when unavoidable):
Explicitly activate renv first (do **NOT** assume `.Rprofile` will run) by using command: `cd "$(git rev-parse --show-toplevel)" && RENV_CONFIG_SANDBOX_ENABLED=false RENV_CONFIG_SYNCHRONIZED_CHECK=false RENV_PROJECT="$(git rev-parse --show-toplevel)" Rscript --vanilla -e 'source("renv/activate.R"); renv::load(); cat(.libPaths()[1], "\n")'`. Then run the intended work in the same style (ensure renv is active).

If autoload still hangs (last resort, avoids autoloader but keeps renv)
Disable autoloader via env var and manually activate renv:
- `cd "$(git rev-parse --show-toplevel)" && RENV_CONFIG_AUTOLOADER_ENABLED=false RENV_CONFIG_SANDBOX_ENABLED=false RENV_CONFIG_SYNCHRONIZED_CHECK=false RENV_PROJECT="$(git rev-parse --show-toplevel)" Rscript -e 'source("renv/activate.R"); renv::load(); cat(.libPaths()[1], "\n")'`

## `bash` usage practices
- Use `bash` for scripting and orchestration of Python/R scripts.
- Include error handling in `bash` scripts to ensure that any failure is properly logged and does **NOT** cause cascading failures without clear diagnostics.
- Use `set -euo pipefail` at the beginning of `bash` scripts.
- Include the following commands to set up environment variables and workspace configuration as a standard header:
  ```bash
  #!/bin/bash
  set -euo pipefail

  # ----- workspace and environment configuration -----
  WORKSPACE_ROOT="$(git rev-parse --show-toplevel)"

  source "$WORKSPACE_ROOT/.venv/bin/activate"
  export PYTHONPATH="$WORKSPACE_ROOT:${PYTHONPATH:-}"
  # ----- workspace and environment configuration-----
  ```
- Include a clear usage example at the top area of `bash` scripts, demonstrating how to execute the script with necessary arguments and what the expected output would be.
- Make sure to give `+x` permission to `bash` scripts.
- Execute `bash` scripts from the repository root to ensure that all relative paths and environment configurations work correctly. For example, to execute the script `script/run_task_name.sh`, you will run: `cd $(git rev-parse --show-toplevel) && script/run_task_name.sh --<arguments>`

## Arguments Parsing
- Use `argparse` for CLI argument parsing in Python scripts.
- Use `optparse` for CLI argument parsing in R scripts.
- For Shell-to-Python workflows, follow the "## Shell-to-Python CLI contract" in `../SKILL.md`.
- In Python, declare `--work_space` as a required named option supplied by the shell. Its value should be the root directory of the current repository. Resolve relative paths against this workspace.
- Take `"--data_path"` as a required argument to specify the input data directory. Use the relative path from the workspace root.
- Take `"--output_path"` as a required argument to specify the deliverables output directory. Use the relative path from the workspace root.
- Define all the arguments in the `get_args()` function.
- Call `get_args()` first to retrieve the parsed arguments in the `main` function.

Example template are as follows:
```python
import argparse  
def get_args():
    """获取命令行参数"""
    parser = argparse.ArgumentParser(description="The training script for crash severity prediction model.")

    parser.add_argument("--work_space", type=str, required=True)
    parser.add_argument("--data_path", type=str, required=True)
    parser.add_argument("--output_path", type=str, required=True)

    return parser.parse_args()

def main():
    # 1. Parse Arguments
    args = get_args()
    # the main logic follows

# Entry point
if __name__ == "__main__":
    main()
```

```R
# arguments parsing function
get_args <- function() {
  option_list <- list(
    make_option(
      c("-w", "--work_space"),
      type = "character",
      default = NULL,
      help = "Project root directory [required]"
    ),
    make_option(
      c("-d", "--data_path"),
      type = "character",
      default = NULL,
      help = "Data directory [required]"
    ),
    make_option(
      c("-o", "--output_path"),
      type = "character",
      default = NULL,
      help = "Output directory for model files [default: work_space/output/econometrics]"
    )
  )

  opt_parser <- OptionParser(
    usage = "%prog [options]",
    option_list = option_list,
    description = "Econometrics Analysis for Traffic Accident Data"
  )
  opt <- parse_args(opt_parser)
  opt
}

# Main function
main <- function() {
    # 1. Parse Arguments
    opt <- get_args()
    # the main logic follows
}

# Entry point
if (sys.nframe() == 0L) {
    main()
}
```

## Naming Conventions for Tests
- 测试文件命名规则
  - 文件名必须以 `test_` 开头
  - 例如：`test_econometrics_data.py`

- 测试函数命名规则
  - 测试函数必须以 `test_` 开头
  - 例如：`test_base_year_splines()`

- 测试类命名规则
  - 测试类必须以 `Test` 开头
  - 例如：`class TestTemporalSplines`
