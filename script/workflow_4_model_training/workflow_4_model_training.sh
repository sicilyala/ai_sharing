#!/usr/bin/env bash
set -euo pipefail

# Usage: cd $(git rev-parse --show-toplevel) && script/workflow_4_model_training/workflow_4_model_training.sh [--config_path config/workflow_4_model_training/config.json] [--data_path PATH] [--output_path PATH]
# Outputs: model, chronological holdout metrics, predictions, and evaluation figures

source "$(dirname "${BASH_SOURCE[0]}")/../common.sh"
DEFAULT_CONFIG_PATH="config/workflow_4_model_training/config.json"
parse_workflow_arguments "$@"
prepare_python_environment
run_python_module "src.workflow_4_model_training.train_model"
run_figure_stage "model_training"
