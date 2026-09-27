"""Workflow 4: train and evaluate a chronological traffic-volume model.

Usage example:
cd $(git rev-parse --show-toplevel) && source .venv/bin/activate && python -m src.workflow_4_model_training.train_model --work_space $(git rev-parse --show-toplevel) --config_path config/workflow_4_model_training/config.json

Output files:
- output/metro_traffic_volume/model_training/model.joblib
- output/metro_traffic_volume/model_training/metrics.json
- output/metro_traffic_volume/model_training/test_predictions.csv
"""

import argparse
import json
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.common.logger_setup import (
    LOG_CRITICAL,
    LOG_DEBUG,
    LOG_ERROR,
    LOG_INFO,
    LOG_WARNING,
    setup_logger,
)
from src.common.traffic_data import (
    chronological_split,
    load_feature_data,
    resolve_workspace_path,
)
from src.common.workflow_config import load_workflow_config
from src.workflow_4_model_training.modeling import build_model

LOGGER = setup_logger(__name__)


def get_args() -> argparse.Namespace:
    """Parse the workspace, config, and optional path overrides."""
    parser = argparse.ArgumentParser(description="Train and evaluate a traffic-volume model.")
    parser.add_argument("--work_space", type=str, required=True)
    parser.add_argument(
        "--config_path",
        type=str,
        default="config/workflow_4_model_training/config.json",
    )
    parser.add_argument("--data_path", type=str)
    parser.add_argument("--output_path", type=str)
    return parser.parse_args()


def validate_model_inputs(frame: pd.DataFrame, config: Mapping[str, Any]) -> None:
    """Fail early for non-finite numeric predictors or target values."""
    dataset_config = config["dataset"]
    numeric = frame.loc[:, dataset_config["numeric_features"]].to_numpy(dtype=float)
    target = frame[dataset_config["target_column"]].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError("Numeric model features contain NaN or infinite values.")
    if not np.isfinite(target).all():
        raise ValueError(
            f"The {dataset_config['target_column']} target contains NaN or infinite values."
        )


def train_and_evaluate(
    frame: pd.DataFrame, output_dir: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    """Fit the model and save predictions, metrics, and figures."""
    dataset_config = config["dataset"]
    split_config = config["split"]
    model_config = config["model"]
    output_config = config["outputs"]
    date_column = dataset_config["date_column"]
    target_column = dataset_config["target_column"]
    model_features = dataset_config["model_features"]
    test_fraction = float(split_config["test_fraction"])
    train_frame, test_frame = chronological_split(
        frame, test_fraction, date_column
    )
    validate_model_inputs(frame, config)
    model = build_model(config)
    model.fit(train_frame.loc[:, model_features], train_frame[target_column])
    predicted = model.predict(test_frame.loc[:, model_features])
    observed = test_frame[target_column].to_numpy(dtype=float)
    if not np.isfinite(predicted).all():
        raise ValueError("The model produced NaN or infinite predictions.")

    mae = float(mean_absolute_error(observed, predicted))
    rmse = float(math.sqrt(mean_squared_error(observed, predicted)))
    r_squared = float(r2_score(observed, predicted))
    if not all(math.isfinite(metric) for metric in (mae, rmse, r_squared)):
        raise ValueError("Model evaluation produced a NaN or infinite metric.")
    if r_squared < 0.0:
        LOG_WARNING("Holdout R2 is negative; this model is worse than the test-set mean baseline.")

    output_dir.mkdir(parents=True, exist_ok=True)
    import joblib

    model_path = output_dir / output_config["model_filename"]
    joblib.dump(model, model_path)

    prediction_frame = pd.DataFrame(
        {
            date_column: test_frame[date_column],
            "observed_traffic_volume": observed,
            "predicted_traffic_volume": predicted,
        }
    )
    prediction_frame["absolute_error"] = (
        prediction_frame["observed_traffic_volume"] - prediction_frame["predicted_traffic_volume"]
    ).abs()
    prediction_path = output_dir / output_config["predictions_filename"]
    prediction_frame.to_csv(prediction_path, index=False, encoding="utf-8")

    metrics: dict[str, Any] = {
        "model": model_config["type"],
        "model_parameters": model_config["random_forest"],
        "test_fraction": test_fraction,
        "split_method": (
            f"chronological; latest {test_fraction:.0%} held out; "
            "shared timestamps kept together"
        ),
        "n_train": len(train_frame),
        "n_test": len(test_frame),
        "train_start": train_frame[date_column].min().isoformat(),
        "train_end": train_frame[date_column].max().isoformat(),
        "test_start": test_frame[date_column].min().isoformat(),
        "test_end": test_frame[date_column].max().isoformat(),
        "mae_vehicles_per_hour": mae,
        "rmse_vehicles_per_hour": rmse,
        "r2": r_squared,
        "predictors": list(model_features),
        "target": target_column,
    }
    metrics_path = output_dir / output_config["metrics_filename"]
    metrics["artifacts"] = [
        str(model_path),
        str(prediction_path),
    ]
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return metrics


def main() -> None:
    """Run the model-training and evaluation workflow."""
    args = get_args()
    config = load_workflow_config(
        args.work_space,
        args.config_path,
        {"data_path": args.data_path, "output_path": args.output_path},
    )
    data_path = resolve_workspace_path(args.work_space, config["data_path"])
    output_root = resolve_workspace_path(args.work_space, config["output_path"])
    try:
        frame = load_feature_data(data_path, config["dataset"])
        metrics = train_and_evaluate(
            frame,
            output_root / config["outputs"]["directory"],
            config,
        )
        LOG_DEBUG("Training predictors: %s", ", ".join(config["dataset"]["model_features"]))
        LOG_INFO(
            "Chronological holdout metrics: MAE=%.2f, RMSE=%.2f, R2=%.3f; results saved under %s.",
            metrics["mae_vehicles_per_hour"],
            metrics["rmse_vehicles_per_hour"],
            metrics["r2"],
            output_root / config["outputs"]["directory"],
        )
    except Exception as error:
        LOG_ERROR("Model-training workflow failed: %s", error)
        LOG_CRITICAL("Stopping model-training workflow.")
        raise


if __name__ == "__main__":
    main()
