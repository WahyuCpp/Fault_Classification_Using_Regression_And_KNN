"""Column uniforming and standardization module."""
from typing import Optional
import pandas as pd
from datetime import datetime, timedelta

from config.data_cleaning_config import (
    EXPECTED_COLUMNS,
    REQUIRED_MIN_COLUMNS,
    COLUMN_ALIASES,
)
from src.utils.logger import get_logger

logger = get_logger("column_uniforming", "preprocessing.log")

def uniform_columns(
    df: pd.DataFrame,
    default_fault_label: str = "A",
    default_current: float = 0.42,
    default_temperature: float = 43.2,
    default_rpm: Optional[float] = 1450.0,
) -> pd.DataFrame:
    """Standardize column names, types, and ordering.

    Ensures columns adhere strictly to:
    [timestamp, x, y, z, current, temperature, rpm, fault_label]
    or minimum:
    [timestamp, x, y, z, current, temperature, fault_label]

    Args:
        df: Input DataFrame.
        default_fault_label: Class label to assign if missing.
        default_current: Baseline motor current in A if sensor column absent.
        default_temperature: Baseline motor temperature in C if sensor column absent.
        default_rpm: Rotational speed in RPM (or None if excluded).

    Returns:
        DataFrame with standardized column schema and ordering.
    """
    df = df.copy()

    # Rename according to alias dictionary
    rename_map = {}
    for col in df.columns:
        col_str = str(col).strip()
        if col_str in COLUMN_ALIASES:
            rename_map[col] = COLUMN_ALIASES[col_str]
        elif col_str.lower() in COLUMN_ALIASES:
            rename_map[col] = COLUMN_ALIASES[col_str.lower()]

    if rename_map:
        df = df.rename(columns=rename_map)

    # Reconstruct timestamp from 'seconds' or index if timestamp column is missing
    if "timestamp" not in df.columns:
        if "seconds" in df.columns:
            base_time = datetime(2026, 7, 12, 13, 15, 0)
            df["timestamp"] = [
                base_time + timedelta(seconds=float(s)) for s in df["seconds"]
            ]
        else:
            base_time = datetime(2026, 7, 12, 13, 15, 0)
            df["timestamp"] = [
                base_time + timedelta(milliseconds=float(i) * 0.666667)
                for i in range(len(df))
            ]

    # Format timestamp as string ISO format if not already
    try:
        df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S.%f").str[:-3]
    except Exception as e:
        logger.warning("Timestamp string formatting encountered: %s", e)

    # Ensure required numeric sensor columns exist with physically plausible defaults
    if "current" not in df.columns:
        df["current"] = default_current
    if "temperature" not in df.columns:
        df["temperature"] = default_temperature
    if "fault_label" not in df.columns:
        df["fault_label"] = default_fault_label

    # Ensure x, y, z are float64
    for axis in ["x", "y", "z"]:
        if axis in df.columns:
            df[axis] = pd.to_numeric(df[axis], errors="coerce").astype(float)
        else:
            df[axis] = 0.0

    df["current"] = pd.to_numeric(df["current"], errors="coerce").astype(float)
    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce").astype(float)

    # Include RPM if present or default provided
    if "rpm" in df.columns:
        df["rpm"] = pd.to_numeric(df["rpm"], errors="coerce").astype(float)
        ordered_cols = [c for c in EXPECTED_COLUMNS if c in df.columns]
    elif default_rpm is not None:
        df["rpm"] = float(default_rpm)
        ordered_cols = EXPECTED_COLUMNS
    else:
        ordered_cols = REQUIRED_MIN_COLUMNS

    # Retain strictly ordered columns
    return df[ordered_cols].reset_index(drop=True)

