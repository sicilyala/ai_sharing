# AGENTS.md

## Overview

The repo is for AI-assisted research workflow sharing.

## Non-negotiable Working Rules

- Data files are immutable (read-only), such as `*.csv, *.xlsx`, unless the user explicitly approves edits.
- Do **NOT** delete user files. Do **NOT** run destructive commands such as `rm -rf`, `git reset --hard`, or forced checkout, unless the user explicitly approves.
- Do **NOT** stage, commit, push, or pull unless the user explicitly approves.
- Do **NOT** edit or write outside repository except temporary files under `/tmp`.
- Do **NOT** use system-level Python interpreters. Use the project's virtual environment managed by `uv` for all Python work. Activate it with `cd $(git rev-parse --show-toplevel) && source .venv/bin/activate && uv sync --frozen`. Use `uv add <package>` to add necessary dependencies, and use `uv sync` to update the environment.
- New `git worktree` must be created based on the clean `main` branch. Before creating a new worktree, if there are untracked, unstaged, or uncommitted changes in the `main` branch, you must stop and ask me which files to add and commit.

- Use `cd $(git rev-parse --show-toplevel) && script/INIT.sh` for routine verification, run it after any major changes. Do not add any business code to `script/INIT.sh`.
- Use `my-coding-practices` & `TDD` skills when coding.
- Use `bash` for orchestration, `javascript` for web visualization, and `python` for others.
- When adding a new user workflow:
  - Create shell scripts under `script/feature_folder` with descriptive file names.
  - Add concise descriptions of the new workflow in `script/README.md`. The description only needs to include the purpose, input, output, and usage of the workflow, excluding implementation details.
  - Codes in `src`, `web`, and `test` folders and configs in `config` folder, must be structured with the same feature folder name as `script`.

## Repository Map

- Workflows: `script/README.md` describes user workflows.
