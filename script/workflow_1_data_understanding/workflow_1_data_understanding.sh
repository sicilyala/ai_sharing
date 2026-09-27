#!/usr/bin/env bash
set -euo pipefail

# Usage: cd $(git rev-parse --show-toplevel) && script/workflow_1_data_understanding/workflow_1_data_understanding.sh [--config_path config/workflow_1_data_understanding/config.json] [--data_path PATH] [--output_path PATH]
# Outputs: data_understanding/data_overview.md and data_overview.json

source "$(dirname "${BASH_SOURCE[0]}")/../common.sh"
DEFAULT_CONFIG_PATH="config/workflow_1_data_understanding/config.json"
parse_workflow_arguments "$@"
prepare_python_environment
run_python_module "src.workflow_1_data_understanding.understand_data"
