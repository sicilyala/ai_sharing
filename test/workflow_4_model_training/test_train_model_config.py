"""CLI coverage for model-training settings loaded from the selected JSON file."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

MODULE = "src.workflow_4_model_training.train_model"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_cli_uses_selected_split_and_model_settings(tmp_path: Path) -> None:
    input_directory = tmp_path / "features"
    input_directory.mkdir()
    rows = []
    for index in range(12):
        rows.append(
            {
                "holiday": "None",
                "temp": 270.0 + index,
                "rain_1h": 0.0,
                "snow_1h": 0.0,
                "clouds_all": index * 5,
                "weather_main": "Clear" if index % 2 == 0 else "Clouds",
                "weather_description": "clear sky" if index % 2 == 0 else "few clouds",
                "date_time": f"2016-01-{index + 1:02d} 00:00:00",
                "traffic_volume": 100 + index * 10,
                "hour": index % 24,
                "weekday": index % 7,
                "month": 1,
                "is_weekend": int(index % 7 >= 5),
            }
        )
    pd.DataFrame(rows).to_csv(input_directory / "metro_traffic_features.csv", index=False)

    config = json.loads(
        (
            REPOSITORY_ROOT
            / "config/workflow_4_model_training/config.json"
        ).read_text(encoding="utf-8")
    )
    config["data_path"] = str(input_directory)
    config["output_path"] = str(tmp_path / "results")
    config["split"]["test_fraction"] = 0.25
    config["model"]["random_forest"]["n_estimators"] = 5
    config["model"]["random_forest"]["n_jobs"] = 1
    config["figures"]["scatter_filename"] = "custom_scatter.svg"
    config["figures"]["scatter_plot"]["title"] = "Selected Config Scatter"
    config["figures"]["figure"].update(
        {"width": 480, "height": 300, "width_in": 4, "height_in": 2.5}
    )
    config_path = tmp_path / "selected_training.json"
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
    metrics_path = tmp_path / "results" / "model_training" / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert metrics["test_fraction"] == 0.25
    assert metrics["n_test"] == 3
    assert metrics["model_parameters"]["n_estimators"] == 5
    assert (tmp_path / "results" / "model_training" / "model.joblib").is_file()

    node = shutil.which("node")
    assert node is not None, "Node.js is required for workflow 4's figure stage."
    figure_result = subprocess.run(
        [
            node,
            str(REPOSITORY_ROOT / "web/workflow_4_model_training/create_figures.mjs"),
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
    assert figure_result.returncode == 0, figure_result.stdout + figure_result.stderr
    scatter_path = tmp_path / "results" / "model_training" / "custom_scatter.svg"
    scatter_svg = scatter_path.read_text(encoding="utf-8")
    assert 'viewBox="0 0 480 300"' in scatter_svg
    assert "Selected Config Scatter" in scatter_svg
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert str(scatter_path) in metrics["artifacts"]
