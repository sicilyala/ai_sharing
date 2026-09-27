#!/usr/bin/env bash
set -euo pipefail

# Usage: cd $(git rev-parse --show-toplevel) && script/workflow_5_model_interpretation/workflow_5_model_interpretation.sh [--config_path config/workflow_5_model_interpretation/config.json] [--data_path PATH] [--output_path PATH]
# Outputs: held-out permutation-importance table, figure, and interpretation.md

source "$(dirname "${BASH_SOURCE[0]}")/../common.sh"
DEFAULT_CONFIG_PATH="config/workflow_5_model_interpretation/config.json"
parse_workflow_arguments "$@"
prepare_python_environment
run_python_module "src.workflow_5_model_interpretation.interpret_model"
run_figure_stage "model_interpretation"
