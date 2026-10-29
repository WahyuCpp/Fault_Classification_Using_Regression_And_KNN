"""Unit tests for the data preprocessing pipeline modules."""
import pandas as pd
import numpy as np
import pytest

from src.preprocessing.get_class import get_class
from src.preprocessing.missing_value_fix import fix_missing_values
from src.preprocessing.outlier_fix import fix_outliers
from src.preprocessing.duplicate_fix import fix_duplicates
from src.preprocessing.column_uniforming import uniform_columns

def test_fault_class_detection():
    """Verify class extraction based on parent folder names."""
    mapping = {"healthy": "A", "outer_bearing_fault": "OB", "unbalance": "UNB"}
    assert get_class("data/cleaned_data/healthy/test_01.csv", mapping) == "A"
    assert get_class("data/cleaned_data/outer_bearing_fault/outer_01.csv", mapping) == "OB"
    assert get_class("data/cleaned_data/unbalance/unb.csv", mapping) == "UNB"


def test_missing_values_imputation():
    """Verify numeric columns are filled with column median and timestamps are not altered by median."""
    df = pd.DataFrame({
        "timestamp": ["2026-07-12 13:15:00.000", "2026-07-12 13:15:00.001", "2026-07-12 13:15:00.002"],
        "x": [1.0, np.nan, 3.0],  # median = 2.0
        "y": [10.0, 20.0, np.nan],  # median = 15.0
        "z": [9.8, 9.8, 9.8],
    })

    cleaned = fix_missing_values(df, numeric_strategy="median")
    assert cleaned["x"].isna().sum() == 0
    assert cleaned["x"].iloc[1] == 2.0
    assert cleaned["y"].iloc[2] == 15.0


def test_duplicate_rows_and_timestamp_collision():
    """Verify exact duplicates are removed and timestamp collisions are aggregated."""
    df = pd.DataFrame({
        "timestamp": ["2026-07-12 13:15:00.000", "2026-07-12 13:15:00.000", "2026-07-12 13:15:00.001"],
        "x": [1.0, 3.0, 2.0],  # Collision at 13:15:00.000 with values 1.0 and 3.0 -> median 2.0
        "y": [0.5, 0.5, 0.5],
        "z": [9.8, 9.8, 9.8],
    })

    deduped = fix_duplicates(df, collision_aggregation="median")
    assert len(deduped) == 2
    assert deduped.loc[deduped["timestamp"] == "2026-07-12 13:15:00.000", "x"].values[0] == 2.0


def test_column_uniforming_order_and_types():
    """Verify uniform ordering [timestamp, x, y, z, current, temperature, rpm, fault_label]."""
    df = pd.DataFrame({
        "Time": ["2026-07-12 13:15:00.000"],
        "X": [0.05],
        "Y": [-0.02],
        "Z": [9.81],
        "Current_A": [0.44],
        "Temp": [45.1],
    })

    uniformed = uniform_columns(df, default_fault_label="OB", default_rpm=1450.0)
    expected_cols = ["timestamp", "x", "y", "z", "current", "temperature", "rpm", "fault_label"]
    assert list(uniformed.columns) == expected_cols
    assert uniformed["fault_label"].iloc[0] == "OB"
    assert uniformed["rpm"].iloc[0] == 1450.0

