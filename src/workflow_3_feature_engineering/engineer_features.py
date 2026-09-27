"""Workflow 3: derive calendar features for a traffic-volume regression task.

Usage example:
cd $(git rev-parse --show-toplevel) && source .venv/bin/activate && python -m src.workflow_3_feature_engineering.engineer_features --work_space $(git rev-parse --show-toplevel) --config_path config/workflow_3_feature_engineering/config.json

Output files:
- output/metro_traffic_volume/feature_engineering/metro_traffic_features.csv
- output/metro_traffic_volume/feature_engineering/feature_dictionary.md
"""

import argparse
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
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
    parser = argparse.ArgumentParser(description="Create model-ready traffic features.")
    parser.add_argument("--work_space", type=str, required=True)
    parser.add_argument(
        "--config_path",
        type=str,
        default="config/workflow_3_feature_engineering/config.json",
    )
    parser.add_argument("--data_path", type=str)
    parser.add_argument("--output_path", type=str)
    return parser.parse_args()


def engineer_features(frame: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    """Add calendar variables while preserving every source observation."""
    dataset_config = config["dataset"]
    feature_config = config["feature_engineering"]
    date_column = dataset_config["date_column"]
    target_column = dataset_config["target_column"]
    missing_by_column = missing_value_counts(frame)
    columns_with_missing = {
        str(column): int(count)
        for column, count in missing_by_column.items()
        if int(count) > 0
    }
    if columns_with_missing:
        raise ValueError(
            "Feature engineering found missing values and will not silently drop or "
            f"impute them: {columns_with_missing}"
        )

    result = frame.copy()
    numeric_columns = feature_config["numeric_columns"]
    for column in numeric_columns:
        if column not in result.columns:
            raise ValueError(f"Required numeric column {column} is missing.")
        values = pd.to_numeric(result[column], errors="coerce")
        if not np.isfinite(values.to_numpy(dtype=float)).all():
            raise ValueError(f"Numeric column {column} contains NaN or infinite values.")
        result[column] = values

    timestamps = pd.to_datetime(result[date_column], errors="coerce")
    invalid_timestamps = int(timestamps.isna().sum())
    if invalid_timestamps:
        raise ValueError(
            f"Cannot engineer calendar features: {invalid_timestamps} invalid {date_column} values."
        )

    result[date_column] = timestamps
    for feature in feature_config["features"]:
        name = feature["name"]
        operation = feature["operation"]
        if operation == "hour":
            result[name] = timestamps.dt.hour
        elif operation == "weekday":
            result[name] = timestamps.dt.dayofweek
        elif operation == "month":
            result[name] = timestamps.dt.month
        elif operation == "is_weekend":
            result[name] = timestamps.dt.dayofweek.isin(
                feature_config["weekend_day_indices"]
            ).astype("int8")
        else:
            raise ValueError(f"Unsupported feature operation {operation!r} for {name}.")
    if target_column not in result.columns:
        raise ValueError(f"Configured target column {target_column} is missing.")
    return result


def write_feature_outputs(
    frame: pd.DataFrame, output_dir: Path, config: Mapping[str, Any]
) -> tuple[Path, Path]:
    """Save the engineered observations and a concise feature dictionary."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_config = config["outputs"]
    data_path = output_dir / output_config["feature_filename"]
    frame.to_csv(data_path, index=False, encoding="utf-8")

    feature_definitions = config["feature_engineering"]["features"]
    date_column = config["dataset"]["date_column"]
    lines = [
        "# Engineered feature dictionary",
        "",
        f"- Input observations: {len(frame):,}",
        "- Rows removed: 0; the raw observations are preserved.",
        f"- Prediction target: `{config['dataset']['target_column']}`.",
        "",
        "| Feature | Definition |",
        "|---|---|",
    ]
    for feature in feature_definitions:
        lines.append(f"| `{feature['name']}` | {feature['description']} |")
    lines.extend(
        [
            "",
            (
                f"The original `{date_column}` column is retained for chronological splitting. "
                "The training workflow uses the derived calendar variables and weather/holiday "
                f"fields, and does not use `{date_column}` as a model predictor."
            ),
            "",
        ]
    )
    dictionary_path = output_dir / output_config["dictionary_filename"]
    dictionary_path.write_text("\n".join(lines), encoding="utf-8")
    return data_path, dictionary_path


def main() -> None:
    """Run the feature-engineering workflow."""
    args = get_args()
    config = load_workflow_config(
        args.work_space,
        args.config_path,
        {"data_path": args.data_path, "output_path": args.output_path},
    )
    data_path = resolve_workspace_path(args.work_space, config["data_path"])
    output_root = resolve_workspace_path(args.work_space, config["output_path"])
    try:
        raw_frame = load_raw_data(data_path, config["dataset"])
        duplicate_rows = int(raw_frame.duplicated().sum())
        if duplicate_rows:
            LOG_WARNING(
                "Feature engineering preserves %s duplicate rows from the raw input.",
                duplicate_rows,
            )
        feature_frame = engineer_features(raw_frame, config)
        csv_path, dictionary_path = write_feature_outputs(
            feature_frame, output_root / config["outputs"]["directory"], config
        )
        LOG_DEBUG(
            "Engineered features: %s",
            ", ".join(feature["name"] for feature in config["feature_engineering"]["features"]),
        )
        LOG_INFO(
            "Created %s feature rows without dropping observations; outputs: %s and %s.",
            len(feature_frame),
            csv_path,
            dictionary_path,
        )
    except Exception as error:
        LOG_ERROR("Feature-engineering workflow failed: %s", error)
        LOG_CRITICAL("Stopping feature-engineering workflow.")
        raise


if __name__ == "__main__":
    main()
