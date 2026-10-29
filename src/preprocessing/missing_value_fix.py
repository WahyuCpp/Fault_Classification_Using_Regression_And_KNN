"""Missing-value cleaning module for signal and time-series data."""
from typing import Optional, List
import pandas as pd
import numpy as np

from src.utils.logger import get_logger

logger = get_logger("missing_value_fix", "preprocessing.log")

DEFAULT_SIGNAL_COLS = ["x", "y", "z", "current", "temperature", "rpm"]

def fix_missing_values(
    df: pd.DataFrame,
    numeric_strategy: str = "median",
    signal_columns: Optional[List[str]] = None,
    sampling_rate: Optional[float] = None,
) -> pd.DataFrame:
    """Clean missing values in dataset according to engineering rules.

    - Numeric signals (x, y, z, current, temp, rpm): filled using column median/mean.
    - Timestamps: never filled with numeric median; reconstructed via sampling rate
      or forward/backward interpolation; invalid records dropped explicitly.

    Args:
        df: Input pandas DataFrame.
        numeric_strategy: 'median', 'mean', or 'ffill'.
        signal_columns: List of signal columns to clean.
        sampling_rate: Sampling frequency (Hz) for timestamp reconstruction if needed.

    Returns:
        Cleaned pandas DataFrame with no NaNs in critical signal columns.
    """
    df = df.copy()
    sig_cols = signal_columns or DEFAULT_SIGNAL_COLS

    # 1. Handle timestamp column
    ts_col = None
    for col in df.columns:
        if col.lower() in ["timestamp", "time", "datetime"]:
            ts_col = col
            break

    if ts_col:
        # Convert to datetime or time if not already
        if not pd.api.types.is_datetime64_any_dtype(df[ts_col]):
            df[ts_col] = pd.to_datetime(df[ts_col], errors="coerce")

        missing_ts = df[ts_col].isna().sum()
        if missing_ts > 0:
            logger.info("Found %d missing timestamps. Attempting reconstruction...", missing_ts)
            # If sampling rate is known, reconstruct missing timestamps linearly
            if sampling_rate and sampling_rate > 0:
                dt_step = pd.to_timedelta(1.0 / sampling_rate, unit="s")
                # Forward fill/interpolate timestamps using index spacing
                df[ts_col] = df[ts_col].interpolate(method="time")
            else:
                # Interpolate linear time where possible
                df[ts_col] = df[ts_col].interpolate(method="linear")

            # Drop any lingering unrecoverable timestamp rows at boundaries
            df = df.dropna(subset=[ts_col])

    # 2. Handle numeric signal columns
    for col in df.columns:
        col_lower = col.lower()
        if col_lower in sig_cols and pd.api.types.is_numeric_dtype(df[col]):
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                if numeric_strategy == "median":
                    fill_value = df[col].median()
                elif numeric_strategy == "mean":
                    fill_value = df[col].mean()
                else:
                    fill_value = df[col].bfill().ffill()

                # If entire column was NaN, fallback to 0.0
                if pd.isna(fill_value):
                    fill_value = 0.0

                df[col] = df[col].fillna(fill_value)
                logger.info("Filled %d missing values in '%s' with %s=%.4f", missing_count, col, numeric_strategy, fill_value)

    return df

