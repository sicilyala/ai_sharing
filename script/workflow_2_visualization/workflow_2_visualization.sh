#!/usr/bin/env bash
set -euo pipefail

# Usage: cd $(git rev-parse --show-toplevel) && script/workflow_2_visualization/workflow_2_visualization.sh [--config_path config/workflow_2_visualization/config.json] [--data_path PATH] [--output_path PATH]
# Outputs: 3 labeled, scalable SVG traffic figures under visualization/

source "$(dirname "${BASH_SOURCE[0]}")/../common.sh"
DEFAULT_CONFIG_PATH="config/workflow_2_visualization/config.json"
parse_workflow_arguments "$@"
prepare_python_environment
run_figure_stage "visualization"
