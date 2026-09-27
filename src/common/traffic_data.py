"""Shared traffic-data loading, validation, and chronological splitting."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd


def resolve_workspace_path(work_space: str, path: str) -> Path:
    """Resolve an absolute path or a path relative to the workspace."""
    workspace = Path(work_space).expanduser().resolve()
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = workspace / candidate
    return candidate.resolve()


def load_raw_data(data_path: Path, dataset_config: Mapping[str, Any]) -> pd.DataFrame:
    """Load the immutable UCI CSV from a data directory."""
    if not data_path.is_dir():
        raise NotADirectoryError(f"Data directory does not exist: {data_path}")
    filename = dataset_config.get("filename")
    required_columns = dataset_config.get("required_columns")
    if not isinstance(filename, str) or not filename:
        raise ValueError("Dataset config must define a non-empty filename.")
    if not isinstance(required_columns, list) or not all(
        isinstance(column, str) for column in required_columns
    ):
        raise ValueError("Dataset config must define required_columns as a string list.")
    source = data_path / filename
    if not source.is_file():
        raise FileNotFoundError(
            f"Expected {source}. Download instructions are in script/README.md."
        )
    frame = pd.read_csv(source, keep_default_na=False)
    validate_columns(frame, tuple(required_columns), source)
    return frame


def load_feature_data(data_path: Path, dataset_config: Mapping[str, Any]) -> pd.DataFrame:
    """Load the CSV created by the feature-engineering workflow."""
    if not data_path.is_dir():
        raise NotADirectoryError(f"Feature-data directory does not exist: {data_path}")
    filename = dataset_config.get("filename")
    required_columns = dataset_config.get("required_columns")
    if not isinstance(filename, str) or not filename:
        raise ValueError("Dataset config must define a non-empty filename.")
    if not isinstance(required_columns, list) or not all(
        isinstance(column, str) for column in required_columns
    ):
        raise ValueError("Dataset config must define required_columns as a string list.")
    source = data_path / filename
    if not source.is_file():
        raise FileNotFoundError(
            f"Expected {source}. Run workflow 3 before this workflow."
        )
    frame = pd.read_csv(source, keep_default_na=False)
    validate_columns(frame, tuple(required_columns), source)
    return frame


def validate_columns(frame: pd.DataFrame, required: tuple[str, ...], source: Path) -> None:
    """Raise a clear error when a source file has an incompatible schema."""
    missing = sorted(set(required).difference(frame.columns))
    if missing:
        raise ValueError(f"{source} is missing required columns: {', '.join(missing)}")


def missing_value_counts(frame: pd.DataFrame) -> pd.Series:
    """Count actual missing cells and blank strings, preserving literal "None" values."""
    blank_values = frame.apply(
        lambda column: column.astype("string").str.strip().eq("").fillna(False)
    )
    return (frame.isna() | blank_values).sum()


def chronological_split(
    frame: pd.DataFrame, test_fraction: float, date_column: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return an ordered split with the latest configured fraction held out."""
    if not 0.0 < test_fraction < 1.0:
        raise ValueError("test_fraction must be between 0 and 1.")
    ordered = frame.copy()
    if date_column not in ordered.columns:
        raise ValueError(f"Missing date column {date_column}; cannot split chronologically.")
    ordered[date_column] = pd.to_datetime(ordered[date_column], errors="coerce")
    if ordered[date_column].isna().any():
        raise ValueError(f"{date_column} contains invalid values; cannot split chronologically.")
    ordered = ordered.sort_values(date_column, kind="stable").reset_index(drop=True)
    split_index = int(len(ordered) * (1.0 - test_fraction))
    if split_index < 2 or len(ordered) - split_index < 1:
        raise ValueError("At least three observations are required for a chronological split.")
    split_timestamp = ordered.loc[split_index, date_column]
    train_frame = ordered.loc[ordered[date_column] < split_timestamp].copy()
    test_frame = ordered.loc[ordered[date_column] >= split_timestamp].copy()
    if train_frame.empty or test_frame.empty:
        raise ValueError("The chronological timestamp boundary produced an empty partition.")
    return train_frame.reset_index(drop=True), test_frame.reset_index(drop=True)
