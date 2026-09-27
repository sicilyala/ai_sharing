"""Workflow 1: inspect the raw UCI Metro traffic dataset.

Usage example:
cd $(git rev-parse --show-toplevel) && source .venv/bin/activate && python -m src.workflow_1_data_understanding.understand_data --work_space $(git rev-parse --show-toplevel) --config_path config/workflow_1_data_understanding/config.json

Output files:
- output/metro_traffic_volume/data_understanding/data_overview.md
- output/metro_traffic_volume/data_understanding/data_overview.json
"""

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.common.logger_setup import (
    LOG_CRITICAL,
    LOG_DEBUG,
    LOG_ERROR,
    LOG_INFO,
    LOG_WARNING,
    setup_logger,
)
from src.common.traffic_data import (
    load_raw_data,
    missing_value_counts,
    resolve_workspace_path,
)
from src.common.workflow_config import load_workflow_config

LOGGER = setup_logger(__name__)


def get_args() -> argparse.Namespace:
    """Parse the workspace, config, and optional path overrides."""
    parser = argparse.ArgumentParser(description="Summarize the raw Metro traffic dataset.")
    parser.add_argument("--work_space", type=str, required=True)
    parser.add_argument(
        "--config_path",
        type=str,
        default="config/workflow_1_data_understanding/config.json",
    )
    parser.add_argument("--data_path", type=str)
    parser.add_argument("--output_path", type=str)
    return parser.parse_args()


def create_overview(
    frame: pd.DataFrame, output_dir: Path, config: dict[str, Any]
) -> tuple[Path, Path]:
    """Write machine-readable and human-readable dataset summaries."""
    dataset_config = config["dataset"]
    report_config = config["report"]
    target_column = dataset_config["target_column"]
    target_unit = dataset_config["target_unit"]
    date_column = dataset_config["date_column"]
    output_dir.mkdir(parents=True, exist_ok=True)
    missing_values = {str(column): int(count) for column, count in missing_value_counts(frame).items()}
    duplicate_rows = int(frame.duplicated().sum())
    timestamps = pd.to_datetime(frame[date_column], errors="coerce")
    numeric = frame.select_dtypes(include="number")
    numeric_summary = numeric.describe().transpose().round(
        report_config["numeric_round_digits"]
    )
    categorical_columns = [
        column for column in report_config["categorical_columns"] if column in frame.columns
    ]

    overview: dict[str, Any] = {
        "rows": int(frame.shape[0]),
        "columns": int(frame.shape[1]),
        "column_names": [str(column) for column in frame.columns],
        "data_types": {str(column): str(dtype) for column, dtype in frame.dtypes.items()},
        "missing_values": missing_values,
        "duplicated_rows": duplicate_rows,
        date_column + "_min": timestamps.min().isoformat() if timestamps.notna().any() else None,
        date_column + "_max": timestamps.max().isoformat() if timestamps.notna().any() else None,
        "target": target_column,
        "target_summary": {
            str(key): float(value) for key, value in frame[target_column].describe().items()
        },
    }

    output_config = config["outputs"]
    json_path = output_dir / output_config["json_filename"]
    json_path.write_text(json.dumps(overview, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        f"# {report_config['title']}",
        "",
        f"- Rows: {frame.shape[0]:,}",
        f"- Columns: {frame.shape[1]}",
        f"- Time range: {overview[date_column + '_min']} to {overview[date_column + '_max']}",
        f"- Prediction target: `{target_column}` ({target_unit})",
        f"- Exact duplicate rows: {duplicate_rows:,}",
        "",
        "## Column types and missing values",
        "",
        "| Column | Type | Missing |",
        "|---|---|---:|",
    ]
    for column in frame.columns:
        lines.append(f"| `{column}` | `{frame[column].dtype}` | {missing_values[str(column)]:,} |")

    lines.extend(
        [
            "",
            "## Numeric summary",
            "",
            "```text",
            numeric_summary.to_string(),
            "```",
            "",
            "## Categorical value counts",
            "",
        ]
    )
    for column in categorical_columns:
        top_n = report_config["categorical_top_n"]
        counts = frame[column].value_counts(dropna=False).head(top_n)
        lines.append(f"### `{column}` (top {top_n})")
        lines.append("")
        lines.append("| Value | Count |")
        lines.append("|---|---:|")
        for value, count in counts.items():
            lines.append(f"| {value} | {int(count):,} |")
        lines.append("")

    lines.extend(
        [
            "## Interpretation notes",
            "",
            (
                "This step reports missing and duplicate observations without deleting rows. "
                "The dataset is a single-site hourly record, so summaries describe this detector "
                "and period rather than traffic conditions in general."
            ),
            "",
        ]
    )
    markdown_path = output_dir / output_config["markdown_filename"]
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return markdown_path, json_path


def main() -> None:
    """Run the data-understanding workflow."""
    args = get_args()
    workspace = Path(args.work_space).expanduser().resolve()
    config = load_workflow_config(
        args.work_space,
        args.config_path,
        {"data_path": args.data_path, "output_path": args.output_path},
    )
    data_path = resolve_workspace_path(args.work_space, config["data_path"])
    output_root = resolve_workspace_path(args.work_space, config["output_path"])
    try:
        frame = load_raw_data(data_path, config["dataset"])
        markdown_path, json_path = create_overview(
            frame, output_root / config["outputs"]["directory"], config
        )
        duplicate_rows = int(frame.duplicated().sum())
        if duplicate_rows:
            LOG_WARNING("Found %s exact duplicate rows; the raw data was not changed.", duplicate_rows)
        LOG_DEBUG("Workspace resolved to %s", workspace)
        LOG_INFO(
            "Inspected %s rows and %s columns; report saved to %s and %s.",
            len(frame),
            len(frame.columns),
            markdown_path,
            json_path,
        )
    except Exception as error:
        LOG_ERROR("Data-understanding workflow failed: %s", error)
        LOG_CRITICAL("Stopping data-understanding workflow.")
        raise


if __name__ == "__main__":
    main()
