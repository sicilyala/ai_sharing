"""Workflow 5: interpret model reliance using held-out permutation importance.

Usage example:
cd $(git rev-parse --show-toplevel) && source .venv/bin/activate && python -m src.workflow_5_model_interpretation.interpret_model --work_space $(git rev-parse --show-toplevel) --config_path config/workflow_5_model_interpretation/config.json

Output files:
- output/metro_traffic_volume/model_interpretation/feature_importance.csv
- output/metro_traffic_volume/model_interpretation/interpretation.md
"""

import argparse
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance

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

LOGGER = setup_logger(__name__)


def get_args() -> argparse.Namespace:
    """Parse the workspace, config, and optional path overrides."""
    parser = argparse.ArgumentParser(description="Explain a trained model's feature reliance.")
    parser.add_argument("--work_space", type=str, required=True)
    parser.add_argument(
        "--config_path",
        type=str,
        default="config/workflow_5_model_interpretation/config.json",
    )
    parser.add_argument("--data_path", type=str)
    parser.add_argument("--output_path", type=str)
    return parser.parse_args()


def create_interpretation(
    frame: pd.DataFrame,
    model_path: Path,
    output_dir: Path,
    config: Mapping[str, Any],
) -> tuple[Path, Path]:
    """Measure input-level permutation importance on the chronological test set."""
    dataset_config = config["dataset"]
    split_config = config["split"]
    interpretation_config = config["interpretation"]
    output_config = config["outputs"]
    date_column = dataset_config["date_column"]
    target_column = dataset_config["target_column"]
    model_features = dataset_config["model_features"]
    test_fraction = float(split_config["test_fraction"])
    if not model_path.is_file():
        raise FileNotFoundError(f"Trained model not found at {model_path}. Run workflow 4 before this workflow.")
    train_frame, test_frame = chronological_split(frame, test_fraction, date_column)
    del train_frame
    model = joblib.load(model_path)
    x_test = test_frame.loc[:, model_features]
    y_test = test_frame[target_column]
    if not np.isfinite(y_test.to_numpy(dtype=float)).all():
        raise ValueError(
            f"The held-out {target_column} target contains NaN or infinite values."
        )

    result = permutation_importance(
        model,
        x_test,
        y_test,
        scoring=interpretation_config["scoring"],
        n_repeats=interpretation_config["n_repeats"],
        random_state=interpretation_config["random_state"],
        n_jobs=interpretation_config["n_jobs"],
    )
    importance = pd.DataFrame(
        {
            "feature": model_features,
            "mean_mae_increase_vehicles_per_hour": result.importances_mean,
            "std_mae_increase_vehicles_per_hour": result.importances_std,
        }
    ).sort_values("mean_mae_increase_vehicles_per_hour", ascending=False)
    if (importance["mean_mae_increase_vehicles_per_hour"] < 0.0).any():
        LOG_WARNING("Some shuffled features reduced MAE; treat small or negative importance values cautiously.")
    if not np.isfinite(
        importance[
            [
                "mean_mae_increase_vehicles_per_hour",
                "std_mae_increase_vehicles_per_hour",
            ]
        ].to_numpy(dtype=float)
    ).all():
        raise ValueError("Permutation importance produced a NaN or infinite result.")

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / output_config["importance_filename"]
    importance.to_csv(csv_path, index=False, encoding="utf-8")

    top = importance.iloc[0]
    interpretation_path = output_dir / output_config["interpretation_filename"]
    top_n = interpretation_config["top_n"]
    interpretation_path.write_text(
        "\n".join(
            [
                "# Model interpretation",
                "",
                (
                    f"The ranking uses permutation importance on the latest {test_fraction:.0%} "
                    f"of observations ({len(test_frame)} held-out rows), as configured for "
                    f"workflow 5. Each input field is shuffled {interpretation_config['n_repeats']} "
                    f"times; the scoring method is {interpretation_config['scoring']}."
                ),
                "",
                f"Held-out period: {test_frame[date_column].min().isoformat()} to {test_frame[date_column].max().isoformat()}.",
                "",
                (
                    f"The largest measured reliance is on `{top['feature']}`: shuffling it "
                    f"increased MAE by {top['mean_mae_increase_vehicles_per_hour']:.2f} "
                    f"{dataset_config['target_unit']} on average."
                ),
                "",
                (
                    "This describes how this fitted model uses its inputs on this held-out period. "
                    "It is not a causal effect or proof that the feature changes traffic volume. "
                    "Correlated predictors can share or mask one another's importance, and the "
                    "single I-94 detector limits how far results generalize."
                ),
                "",
                f"## Top {top_n} input features",
                "",
                f"| Rank | Feature | Mean MAE increase ({dataset_config['target_unit']}) | SD |",
                "|---:|---|---:|---:|",
                *[
                    f"| {rank} | `{row.feature}` | "
                    f"{row.mean_mae_increase_vehicles_per_hour:.2f} | "
                    f"{row.std_mae_increase_vehicles_per_hour:.2f} |"
                    for rank, row in enumerate(importance.head(top_n).itertuples(index=False), start=1)
                ],
                "",
            ]
        ),
        encoding="utf-8",
    )
    return csv_path, interpretation_path


def main() -> None:
    """Run the held-out model-interpretation workflow."""
    args = get_args()
    config = load_workflow_config(
        args.work_space,
        args.config_path,
        {"data_path": args.data_path, "output_path": args.output_path},
    )
    data_path = resolve_workspace_path(args.work_space, config["data_path"])
    output_root = resolve_workspace_path(args.work_space, config["output_path"])
    model_path = (
        output_root
        / config["model_artifact"]["directory"]
        / config["model_artifact"]["filename"]
    )
    try:
        frame = load_feature_data(data_path, config["dataset"])
        paths = create_interpretation(
            frame,
            model_path,
            output_root / config["outputs"]["directory"],
            config,
        )
        LOG_DEBUG("Interpretation covers %s model inputs.", len(config["dataset"]["model_features"]))
        LOG_INFO("Saved model interpretation outputs: %s and %s.", *paths)
    except Exception as error:
        LOG_ERROR("Model-interpretation workflow failed: %s", error)
        LOG_CRITICAL("Stopping model-interpretation workflow.")
        raise


if __name__ == "__main__":
    main()
