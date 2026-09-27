"""CLI coverage for independent workflow 5 split and importance settings."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import joblib
import pandas as pd

from src.workflow_4_model_training.modeling import build_model

MODULE = "src.workflow_5_model_interpretation.interpret_model"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _feature_frame() -> pd.DataFrame:
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
    return pd.DataFrame(rows)


def test_cli_uses_its_own_split_and_importance_settings(tmp_path: Path) -> None:
    input_directory = tmp_path / "features"
    input_directory.mkdir()
    frame = _feature_frame()
    frame.to_csv(input_directory / "metro_traffic_features.csv", index=False)

    training_config = json.loads(
        (REPOSITORY_ROOT / "config/workflow_4_model_training/config.json").read_text(
            encoding="utf-8"
        )
    )
    training_config["model"]["random_forest"]["n_estimators"] = 5
    training_config["model"]["random_forest"]["n_jobs"] = 1
    model = build_model(training_config)
    model.fit(
        frame.loc[:, training_config["dataset"]["model_features"]],
        frame[training_config["dataset"]["target_column"]],
    )
    output_root = tmp_path / "results"
    model_path = (
        output_root
        / training_config["outputs"]["directory"]
        / training_config["outputs"]["model_filename"]
    )
    model_path.parent.mkdir(parents=True)
    joblib.dump(model, model_path)

    config = json.loads(
        (REPOSITORY_ROOT / "config/workflow_5_model_interpretation/config.json").read_text(
            encoding="utf-8"
        )
    )
    config["data_path"] = str(input_directory)
    config["output_path"] = str(output_root)
    config["split"]["test_fraction"] = 0.5
    config["interpretation"]["n_repeats"] = 2
    config["interpretation"]["top_n"] = 5
    config["outputs"]["figure_filename"] = "custom_importance.svg"
    config["figures"]["importance_plot"]["title"] = "Selected Config Importance"
    config["figures"]["figure"].update(
        {"width": 480, "height": 300, "width_in": 4, "height_in": 2.5}
    )
    config_path = tmp_path / "selected_interpretation.json"
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
    report_path = output_root / "model_interpretation" / "interpretation.md"
    report = report_path.read_text(encoding="utf-8")
    assert "latest 50% of observations (6 held-out rows)" in report
    assert "shuffled 2 times" in report
    assert "Top 5 input features" in report

    node = shutil.which("node")
    assert node is not None, "Node.js is required for workflow 5's figure stage."
    figure_result = subprocess.run(
        [
            node,
            str(REPOSITORY_ROOT / "web/workflow_5_model_interpretation/create_figures.mjs"),
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
    figure_path = output_root / "model_interpretation" / "custom_importance.svg"
    figure_svg = figure_path.read_text(encoding="utf-8")
    assert 'viewBox="0 0 480 300"' in figure_svg
    assert "Selected Config Importance" in figure_svg
