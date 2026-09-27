"""CLI coverage for workflow 2's JSON-driven JavaScript figure generator."""

import json
import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIGURE_SCRIPT = REPOSITORY_ROOT / "web/workflow_2_visualization/create_figures.mjs"
DEFAULT_CONFIG = REPOSITORY_ROOT / "config/workflow_2_visualization/config.json"


def test_figure_generator_uses_selected_config(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is required to run workflow 2's figure generator.")

    input_directory = tmp_path / "input"
    input_directory.mkdir()
    rows = ["timestamp,volume,condition"]
    first_day = datetime(2016, 1, 4, tzinfo=UTC)
    for day in range(7):
        for hour in range(24):
            timestamp = first_day + timedelta(days=day, hours=hour)
            condition = "Clear" if day % 2 == 0 else "Rain"
            rows.append(f"{timestamp:%Y-%m-%d %H:%M:%S},{100 + day * 10 + hour},{condition}")
    (input_directory / "custom-traffic.csv").write_text(
        "\n".join(rows) + "\n", encoding="utf-8"
    )

    config = json.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    config["data_path"] = "input"
    config["output_path"] = "results"
    config["dataset"].update(
        {
            "filename": "custom-traffic.csv",
            "date_column": "timestamp",
            "target_column": "volume",
            "weather_column": "condition",
        }
    )
    config["visualization"]["output_directory"] = "charts"
    config["visualization"]["hour_plot"].update(
        {"title": "Configured Hourly Volume", "output_filename": "hourly.svg", "bottom": 240}
    )
    config["visualization"]["weekday_plot"].update(
        {"output_filename": "weekday.svg", "bottom": 240}
    )
    config["visualization"]["weather_plot"].update(
        {"output_filename": "weather.svg", "top": 40, "bottom_padding": 30}
    )
    config["visualization"]["figure"].update(
        {"width": 480, "height": 300, "width_in": 4, "height_in": 2.5}
    )
    config_path = tmp_path / "selected-visualization.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    result = subprocess.run(
        [
            node,
            str(FIGURE_SCRIPT),
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
    hourly_path = tmp_path / "results" / "charts" / "hourly.svg"
    hourly_svg = hourly_path.read_text(encoding="utf-8")
    assert 'viewBox="0 0 480 300"' in hourly_svg
    assert "Configured Hourly Volume" in hourly_svg
    assert (tmp_path / "results" / "charts" / "weekday.svg").is_file()
    assert (tmp_path / "results" / "charts" / "weather.svg").is_file()
