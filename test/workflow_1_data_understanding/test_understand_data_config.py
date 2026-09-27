"""CLI coverage for workflow 1's selected JSON config and output settings."""

import json
import subprocess
import sys
from pathlib import Path

MODULE = "src.workflow_1_data_understanding.understand_data"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_cli_uses_selected_dataset_and_report_config(tmp_path: Path) -> None:
    input_directory = tmp_path / "input"
    input_directory.mkdir()
    (input_directory / "custom.csv").write_text(
        "observed_at,outcome,group\n"
        "2016-01-01 00:00:00,10,alpha\n"
        "2016-01-01 01:00:00,20,beta\n",
        encoding="utf-8",
    )
    config = {
        "data_path": "input",
        "output_path": "results",
        "dataset": {
            "filename": "custom.csv",
            "date_column": "observed_at",
            "target_column": "outcome",
            "target_unit": "cars per hour",
            "required_columns": ["observed_at", "outcome", "group"],
        },
        "report": {
            "title": "Selected dataset overview",
            "categorical_columns": ["group"],
            "numeric_round_digits": 1,
            "categorical_top_n": 1,
        },
        "outputs": {
            "directory": "summary",
            "markdown_filename": "custom.md",
            "json_filename": "custom.json",
        },
    }
    config_path = tmp_path / "selected-data-understanding.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            MODULE,
            "--work_space",
            str(tmp_path),
            "--config_path",
            str(config_path),
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    output_directory = tmp_path / "results" / "summary"
    overview = json.loads((output_directory / "custom.json").read_text(encoding="utf-8"))
    assert overview["target"] == "outcome"
    assert overview["rows"] == 2
    report = (output_directory / "custom.md").read_text(encoding="utf-8")
    assert "`group` (top 1)" in report
    assert "# Selected dataset overview" in report
    assert "(cars per hour)" in report
