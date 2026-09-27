"""Model configuration shared by model training and interpretation."""

from collections.abc import Mapping
from typing import Any

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def build_model(config: Mapping[str, Any]) -> Pipeline:
    """Create a reproducible random-forest regression pipeline."""
    dataset_config = config["dataset"]
    model_config = config["model"]
    if model_config["type"] != "RandomForestRegressor":
        raise ValueError(f"Unsupported model type: {model_config['type']}")
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", "passthrough", dataset_config["numeric_features"]),
            (
                "categorical",
                OneHotEncoder(**model_config["one_hot_encoder"]),
                dataset_config["categorical_features"],
            ),
        ],
        remainder=model_config["remainder"],
    )
    regressor = RandomForestRegressor(**model_config["random_forest"])
    return Pipeline([("preprocessor", preprocessor), ("regressor", regressor)])
