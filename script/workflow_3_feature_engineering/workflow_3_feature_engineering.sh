#!/usr/bin/env bash
set -euo pipefail

# Usage: cd $(git rev-parse --show-toplevel) && script/workflow_3_feature_engineering/workflow_3_feature_engineering.sh [--config_path config/workflow_3_feature_engineering/config.json] [--data_path PATH] [--output_path PATH]
# Outputs: feature_engineering/metro_traffic_features.csv and feature_dictionary.md

source "$(dirname "${BASH_SOURCE[0]}")/../common.sh"
DEFAULT_CONFIG_PATH="config/workflow_3_feature_engineering/config.json"
parse_workflow_arguments "$@"
prepare_python_environment
run_python_module "src.workflow_3_feature_engineering.engineer_features"
