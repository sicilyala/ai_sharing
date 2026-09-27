"""Command-line coverage for workflow 3's file-in/file-out contract."""

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

MODULE = "src.workflow_3_feature_engineering.engineer_features"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _raw_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "holiday": ["None", "None"],
            "temp": ["25.0", "26.0"],
            "rain_1h": ["0.0", "0.0"],
            "snow_1h": ["0.0", "0.0"],
            "clouds_all": ["10", "20"],
            "weather_main": ["Clear", "Clouds"],
            "weather_description": ["clear sky", "few clouds"],
            "date_time": ["2016-01-01 00:00:00", "2016-01-02 23:00:00"],
            "traffic_volume": ["100", "200"],
        }
    )


def _run_cli(workspace: Path, config_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            MODULE,
            "--work_space",
            str(workspace),
            "--config_path",
            str(config_path),
            "--data_path",
            "input",
            "--output_path",
            "results",
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _write_config(path: Path, feature_filename: str = "custom_features.csv") -> None:
    config = {
        "data_path": "ignored-input",
        "output_path": "ignored-output",
        "dataset": {
            "filename": "Metro_Interstate_Traffic_Volume.csv",
            "required_columns": [
                "holiday",
                "temp",
                "rain_1h",
                "snow_1h",
                "clouds_all",
                "weather_main",
                "weather_description",
                "date_time",
                "traffic_volume",
            ],
            "date_column": "date_time",
            "target_column": "traffic_volume",
        },
        "feature_engineering": {
            "numeric_columns": ["temp", "rain_1h", "snow_1h", "clouds_all", "traffic_volume"],
            "weekend_day_indices": [5, 6],
            "features": [
                {"name": "hour", "operation": "hour", "description": "Hour of day."},
                {"name": "weekday", "operation": "weekday", "description": "Day of week."},
                {"name": "month", "operation": "month", "description": "Calendar month."},
                {"name": "is_weekend", "operation": "is_weekend", "description": "Weekend flag."},
            ],
        },
        "outputs": {
            "directory": "feature_engineering",
            "feature_filename": feature_filename,
            "dictionary_filename": "custom_feature_dictionary.md",
        },
    }
    path.write_text(json.dumps(config), encoding="utf-8")


def test_cli_reads_input_and_writes_features_and_dictionary(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    source_path = input_dir / "Metro_Interstate_Traffic_Volume.csv"
    source = _raw_frame()
    source.to_csv(source_path, index=False)
    original_source = source_path.read_bytes()

    config_path = tmp_path / "selected_config.json"
    _write_config(config_path)
    result = _run_cli(tmp_path, config_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert source_path.read_bytes() == original_source

    output_dir = tmp_path / "results" / "feature_engineering"
    features = pd.read_csv(output_dir / "custom_features.csv")
    assert features["hour"].tolist() == [0, 23]
    assert features["weekday"].tolist() == [4, 5]
    assert features["month"].tolist() == [1, 1]
    assert features["is_weekend"].tolist() == [0, 1]
    assert len(features) == len(source)

    dictionary = (output_dir / "custom_feature_dictionary.md").read_text(encoding="utf-8")
    assert "Input observations: 2" in dictionary
    assert "Rows removed: 0" in dictionary
    assert "`is_weekend`" in dictionary


def test_cli_reports_missing_input_columns_without_creating_outputs(
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    source = _raw_frame().drop(columns="weather_description")
    source.to_csv(input_dir / "Metro_Interstate_Traffic_Volume.csv", index=False)

    config_path = tmp_path / "selected_config.json"
    _write_config(config_path)
    result = _run_cli(tmp_path, config_path)

    assert result.returncode != 0
    assert "missing required columns: weather_description" in (result.stdout + result.stderr)
    assert not (tmp_path / "results").exists()
