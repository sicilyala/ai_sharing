"""Behavioral tests for loading workflow settings from JSON files."""

import json
from pathlib import Path

import pytest

from src.common.workflow_config import (
    WORKFLOW_NAMES,
    load_run_all_workflow_configs,
    load_workflow_config,
    resolve_run_all_feature_data_path,
)


def test_load_workflow_config_resolves_relative_path_and_applies_cli_overrides(
    tmp_path: Path,
) -> None:
    config_directory = tmp_path / "config" / "workflow"
    config_directory.mkdir(parents=True)
    config_path = config_directory / "settings.json"
    config_path.write_text(
        json.dumps({"data_path": "configured-input", "output_path": "configured-output"}),
        encoding="utf-8",
    )

    config = load_workflow_config(
        tmp_path,
        "config/workflow/settings.json",
        {"data_path": "cli-input", "output_path": None},
    )

    assert config["data_path"] == "cli-input"
    assert config["output_path"] == "configured-output"


def test_load_workflow_config_rejects_non_object_json(tmp_path: Path) -> None:
    (tmp_path / "settings.json").write_text("[]", encoding="utf-8")

    with pytest.raises(TypeError, match="JSON object"):
        load_workflow_config(tmp_path, "settings.json")


def test_run_all_config_resolves_each_workflow_file(tmp_path: Path) -> None:
    config_paths = {}
    for workflow_name in WORKFLOW_NAMES:
        config_path = tmp_path / "config" / workflow_name / "config.json"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("{}", encoding="utf-8")
        config_paths[workflow_name] = config_path.relative_to(tmp_path).as_posix()
    run_all_path = tmp_path / "run_all.json"
    run_all_path.write_text(
        json.dumps({"workflow_configs": config_paths}), encoding="utf-8"
    )

    resolved = load_run_all_workflow_configs(tmp_path, "run_all.json")

    assert list(resolved) == list(WORKFLOW_NAMES)
    assert resolved["workflow_5_model_interpretation"] == (
        tmp_path / "config/workflow_5_model_interpretation/config.json"
    )


def test_run_all_output_override_uses_workflow_3_output_directory(
    tmp_path: Path,
) -> None:
    config_paths = {}
    for workflow_name in WORKFLOW_NAMES:
        config_path = tmp_path / "config" / workflow_name / "config.json"
        config_path.parent.mkdir(parents=True)
        config = {}
        if workflow_name == "workflow_3_feature_engineering":
            config = {
                "output_path": "configured-output",
                "outputs": {"directory": "engineered"},
            }
        config_path.write_text(json.dumps(config), encoding="utf-8")
        config_paths[workflow_name] = config_path.relative_to(tmp_path).as_posix()
    run_all_path = tmp_path / "run_all.json"
    run_all_path.write_text(
        json.dumps({"workflow_configs": config_paths}), encoding="utf-8"
    )

    feature_data_path = resolve_run_all_feature_data_path(
        tmp_path, "run_all.json", "custom-output"
    )

    assert feature_data_path == (tmp_path / "custom-output" / "engineered")
