#!/usr/bin/env bash
set -euo pipefail

parse_workflow_arguments() {
  CONFIG_PATH="$DEFAULT_CONFIG_PATH"
  DATA_PATH_OVERRIDE=""
  OUTPUT_PATH_OVERRIDE=""

  while (($# > 0)); do
    case "$1" in
      --config_path)
        if (($# < 2)) || [[ -z "$2" || "$2" == --* ]]; then
          echo "Missing value for --config_path" >&2
          return 2
        fi
        CONFIG_PATH="$2"
        shift 2
        ;;
      --data_path)
        if (($# < 2)) || [[ -z "$2" || "$2" == --* ]]; then
          echo "Missing value for --data_path" >&2
          return 2
        fi
        DATA_PATH_OVERRIDE="$2"
        shift 2
        ;;
      --output_path)
        if (($# < 2)) || [[ -z "$2" || "$2" == --* ]]; then
          echo "Missing value for --output_path" >&2
          return 2
        fi
        OUTPUT_PATH_OVERRIDE="$2"
        shift 2
        ;;
      *)
        echo "Unsupported argument: $1" >&2
        echo "Supported arguments: --config_path VALUE [--data_path VALUE] [--output_path VALUE]" >&2
        return 2
        ;;
    esac
  done
}

prepare_python_environment() {
  WORKSPACE_ROOT="$(git rev-parse --show-toplevel)"
  cd "$WORKSPACE_ROOT"
  source "$WORKSPACE_ROOT/.venv/bin/activate"
  uv sync --frozen
  export PYTHONPATH="$WORKSPACE_ROOT:${PYTHONPATH:-}"
}

run_python_module() {
  local module_name="$1"
  local -a python_args=(
    --work_space "$WORKSPACE_ROOT"
    --config_path "$CONFIG_PATH"
  )
  if [[ -n "$DATA_PATH_OVERRIDE" ]]; then
    python_args+=(--data_path "$DATA_PATH_OVERRIDE")
  fi
  if [[ -n "$OUTPUT_PATH_OVERRIDE" ]]; then
    python_args+=(--output_path "$OUTPUT_PATH_OVERRIDE")
  fi
  python -m "$module_name" "${python_args[@]}"
}

run_figure_stage() {
  local stage="$1"
  local figure_script
  case "$stage" in
    visualization) figure_script="web/workflow_2_visualization/create_figures.mjs" ;;
    model_training) figure_script="web/workflow_4_model_training/create_figures.mjs" ;;
    model_interpretation) figure_script="web/workflow_5_model_interpretation/create_figures.mjs" ;;
    *)
      echo "Unsupported figure workflow: $stage" >&2
      return 2
      ;;
  esac
  local -a figure_args=(
    --work_space "$WORKSPACE_ROOT"
    --config_path "$CONFIG_PATH"
  )
  if [[ -n "$DATA_PATH_OVERRIDE" ]]; then
    figure_args+=(--data_path "$DATA_PATH_OVERRIDE")
  fi
  if [[ -n "$OUTPUT_PATH_OVERRIDE" ]]; then
    figure_args+=(--output_path "$OUTPUT_PATH_OVERRIDE")
  fi
  node "$WORKSPACE_ROOT/$figure_script" "${figure_args[@]}"
}
