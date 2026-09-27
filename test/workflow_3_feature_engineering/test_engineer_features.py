"""Behavioral tests for workflow 3's feature transformation interface."""

from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal

from src.common.workflow_config import load_workflow_config
from src.workflow_3_feature_engineering.engineer_features import engineer_features

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_CONFIG = load_workflow_config(
    WORKSPACE_ROOT,
    "config/workflow_3_feature_engineering/config.json",
)


def test_engineer_features_adds_calendar_values_without_changing_source_rows() -> None:
    """Calendar features use local timestamps and retain input rows in order."""
    source = pd.DataFrame(
        {
            "holiday": ["None", "None", "None"],
            "temp": ["25.0", "26.0", "27.0"],
            "rain_1h": ["0.0", "0.0", "0.2"],
            "snow_1h": ["0.0", "0.0", "0.0"],
            "clouds_all": ["10", "20", "30"],
            "weather_main": ["Clear", "Clouds", "Rain"],
            "weather_description": ["clear sky", "few clouds", "light rain"],
            "date_time": [
                "2016-01-01 00:00:00",
                "2016-01-02 23:00:00",
                "2016-12-31 12:00:00",
            ],
            "traffic_volume": ["100", "200", "300"],
        }
    )
    original = source.copy(deep=True)

    result = engineer_features(source, WORKFLOW_CONFIG)

    assert result["hour"].tolist() == [0, 23, 12]
    assert result["weekday"].tolist() == [4, 5, 5]
    assert result["month"].tolist() == [1, 1, 12]
    assert result["is_weekend"].tolist() == [0, 1, 1]
    assert result["traffic_volume"].tolist() == [100, 200, 300]
    assert len(result) == len(source)
    assert_frame_equal(source, original)
