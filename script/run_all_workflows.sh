#!/usr/bin/env bash
set -euo pipefail

# Usage: cd $(git rev-parse --show-toplevel) && script/run_all_workflows.sh [--config_path config/run_all_workflows/config.json] [--data_path PATH] [--output_path PATH]
# Outputs: all five workflow deliverables under the selected output directory

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
DEFAULT_CONFIG_PATH="config/run_all_workflows/config.json"
parse_workflow_arguments "$@"
WORKSPACE_ROOT="$(git rev-parse --show-toplevel)"
cd "$WORKSPACE_ROOT"
SCRIPT_DIR="script"

prepare_python_environment
WORKFLOW_CONFIG_PATHS_TEXT="$(python -m src.common.workflow_config \
  --work_space "$WORKSPACE_ROOT" \
  --config_path "$CONFIG_PATH" \
  --list_workflow_configs)"
WORKFLOW_CONFIG_PATHS=()
while IFS= read -r config_path; do
  if [[ -n "$config_path" ]]; then
    WORKFLOW_CONFIG_PATHS+=("$config_path")
  fi
done <<< "$WORKFLOW_CONFIG_PATHS_TEXT"
if ((${#WORKFLOW_CONFIG_PATHS[@]} != 5)); then
  echo "Run-all config must resolve exactly five workflow config files." >&2
  exit 2
fi

run_configured_workflow() {
  local script_path="$1"
  local config_path="$2"
  local data_path_override="${3:-}"
  local -a workflow_args=(--config_path "$config_path")
  if [[ -n "$data_path_override" ]]; then
    workflow_args+=(--data_path "$data_path_override")
  elif [[ -n "$DATA_PATH_OVERRIDE" && "$script_path" != *"workflow_4_model_training"* && "$script_path" != *"workflow_5_model_interpretation"* ]]; then
    workflow_args+=(--data_path "$DATA_PATH_OVERRIDE")
  fi
  if [[ -n "$OUTPUT_PATH_OVERRIDE" ]]; then
    workflow_args+=(--output_path "$OUTPUT_PATH_OVERRIDE")
  fi
  "$script_path" "${workflow_args[@]}"
}

run_configured_workflow \
  "$SCRIPT_DIR/workflow_1_data_understanding/workflow_1_data_understanding.sh" \
  "${WORKFLOW_CONFIG_PATHS[0]}"
run_configured_workflow \
  "$SCRIPT_DIR/workflow_2_visualization/workflow_2_visualization.sh" \
  "${WORKFLOW_CONFIG_PATHS[1]}"
run_configured_workflow \
  "$SCRIPT_DIR/workflow_3_feature_engineering/workflow_3_feature_engineering.sh" \
  "${WORKFLOW_CONFIG_PATHS[2]}"
if [[ -n "$OUTPUT_PATH_OVERRIDE" ]]; then
  WORKFLOW_45_DATA_OVERRIDE="$(python -m src.common.workflow_config \
    --work_space "$WORKSPACE_ROOT" \
    --config_path "$CONFIG_PATH" \
    --engineered_data_path \
    --output_path "$OUTPUT_PATH_OVERRIDE")"
else
  WORKFLOW_45_DATA_OVERRIDE=""
fi
run_configured_workflow \
  "$SCRIPT_DIR/workflow_4_model_training/workflow_4_model_training.sh" \
  "${WORKFLOW_CONFIG_PATHS[3]}" "$WORKFLOW_45_DATA_OVERRIDE"
run_configured_workflow \
  "$SCRIPT_DIR/workflow_5_model_interpretation/workflow_5_model_interpretation.sh" \
  "${WORKFLOW_CONFIG_PATHS[4]}" "$WORKFLOW_45_DATA_OVERRIDE"
