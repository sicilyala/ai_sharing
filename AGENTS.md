# AGENTS.md

## Overview

The repo is for AI-assisted research workflow sharing. 

## Non-negotiable Working Rules

- Data files are immutable (read-only), such as `*.csv, *.xlsx`, unless the user explicitly approves edits.
- Do **NOT** delete user files. Do **NOT** run destructive commands such as `rm -rf`, `git reset --hard`, or forced checkout, unless the user explicitly approves.
- Do **NOT** stage, commit, push, or pull unless the user explicitly approves.
- Do **NOT** edit or write outside repository except temporary files under `/tmp`.
- Do **NOT** use system-level Python interpreters. Use the project's virtual environment managed by `uv` for all Python work. Activate it with `cd $(git rev-parse --show-toplevel) && source .venv/bin/activate && uv sync --frozen`.
- New `git worktree` must be created based on the clean `main` branch. Before creating a new worktree, if there are untracked, unstaged, or uncommitted changes in the `main` branch, you must stop and ask me which files to add and commit.

## What You Should Do

- Use `cd $(git rev-parse --show-toplevel) && script/INIT.sh` for routine verification only. Do not add any business code to `script/INIT.sh`.
- Use `uv add <package>` to add necessary dependencies, and use `uv sync` to update the environment.
- Use `my-coding-practices` skills when coding.
- When adding a new user workflow:
  - Create shell scripts under `script/feature_folder` with descriptive file names.
  - Add concise descriptions of the new workflow in `script/README.md`, and follows the existing format.
  - Codes in `src`, `frontend`, and `test` folders and configs in `config` folder, must be structured with the same feature folder name as `script`.
- Use `bash` for orchestration, `python` for data processing, and `javascript` for visualization.

## Repository Map

- Workflows: `script/README.md` describes user workflows.
