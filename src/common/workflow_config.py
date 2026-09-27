"""Load workflow JSON settings and expose the run-all workflow paths.

Usage example:
cd $(git rev-parse --show-toplevel) && source .venv/bin/activate && python -m src.common.workflow_config --work_space $(git rev-parse --show-toplevel) --config_path config/run_all_workflows/config.json --list_workflow_configs
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

WORKFLOW_NAMES = (
    "workflow_1_data_understanding",
    "workflow_2_visualization",
    "workflow_3_feature_engineering",
    "workflow_4_model_training",
    "workflow_5_model_interpretation",
)


def resolve_config_path(work_space: str | Path, config_path: str | Path) -> Path:
    """Resolve a config file from an absolute path or the workspace root."""
    workspace = Path(work_space).expanduser().resolve()
    candidate = Path(config_path).expanduser()
    if not candidate.is_absolute():
        candidate = workspace / candidate
    return candidate.resolve()


def load_workflow_config(
    work_space: str | Path,
    config_path: str | Path,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Read a workflow JSON object and apply non-None command-line overrides."""
    resolved_path = resolve_config_path(work_space, config_path)
    with resolved_path.open(encoding="utf-8") as config_file:
        config = json.load(config_file)
    if not isinstance(config, dict):
        raise TypeError(f"Workflow config must contain a JSON object: {resolved_path}")
    if overrides:
        config.update({key: value for key, value in overrides.items() if value is not None})
    return config


def load_run_all_workflow_configs(work_space: str | Path, config_path: str | Path) -> dict[str, Path]:
    """Resolve the five workflow config files listed by the run-all JSON file."""
    config = load_workflow_config(work_space, config_path)
    workflow_configs = config.get("workflow_configs")
    if not isinstance(workflow_configs, dict):
        raise TypeError("Run-all config must define a workflow_configs JSON object.")

    resolved: dict[str, Path] = {}
    for workflow_name in WORKFLOW_NAMES:
        path_value = workflow_configs.get(workflow_name)
        if not isinstance(path_value, str) or not path_value.strip():
            raise ValueError(f"Run-all config is missing a non-empty path for {workflow_name}.")
        path = resolve_config_path(work_space, path_value)
        if not path.is_file():
            raise FileNotFoundError(f"Workflow config not found for {workflow_name}: {path}")
        resolved[workflow_name] = path
    return resolved


def resolve_run_all_feature_data_path(
    work_space: str | Path,
    config_path: str | Path,
    output_path_override: str | None = None,
) -> Path:
    """Resolve workflow 3's output directory for a run-all output override."""
    workflow_configs = load_run_all_workflow_configs(work_space, config_path)
    feature_config = load_workflow_config(
        work_space,
        workflow_configs["workflow_3_feature_engineering"],
        {"output_path": output_path_override},
    )
    output_path = feature_config.get("output_path")
    if not isinstance(output_path, str) or not output_path.strip():
        raise TypeError("Workflow 3 config must define a non-empty output_path string.")
    outputs = feature_config.get("outputs")
    if not isinstance(outputs, dict):
        raise TypeError("Workflow 3 config must define an outputs JSON object.")
    output_directory = outputs.get("directory")
    if not isinstance(output_directory, str) or not output_directory.strip():
        raise TypeError("Workflow 3 outputs config must define a non-empty directory string.")
    output_root = Path(output_path).expanduser()
    workspace = Path(work_space).expanduser().resolve()
    if not output_root.is_absolute():
        output_root = workspace / output_root
    return (output_root / output_directory).resolve()


def get_args() -> argparse.Namespace:
    """Parse the config path used by the shell run-all orchestrator."""
    parser = argparse.ArgumentParser(description="Resolve per-workflow JSON config paths.")
    parser.add_argument("--work_space", type=str, required=True)
    parser.add_argument("--config_path", type=str, required=True)
    output_mode = parser.add_mutually_exclusive_group(required=True)
    output_mode.add_argument("--list_workflow_configs", action="store_true")
    output_mode.add_argument("--engineered_data_path", action="store_true")
    parser.add_argument("--output_path", type=str)
    return parser.parse_args()


def main() -> None:
    """Print resolved workflow config paths for the shell orchestrator."""
    args = get_args()
    if args.list_workflow_configs:
        workflow_configs = load_run_all_workflow_configs(args.work_space, args.config_path)
        sys.stdout.write("\n".join(str(path) for path in workflow_configs.values()) + "\n")
    else:
        feature_data_path = resolve_run_all_feature_data_path(args.work_space, args.config_path, args.output_path)
        sys.stdout.write(f"{feature_data_path}\n")


if __name__ == "__main__":
    main()
