"""Duplicate record and timestamp collision handling."""
from typing import Optional
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("duplicate_fix", "preprocessing.log")

def fix_duplicates(
    df: pd.DataFrame,
    timestamp_col: Optional[str] = None,
    collision_aggregation: str = "median",
) -> pd.DataFrame:
    """Clean duplicate observations and resolve timestamp collisions.

    1. Removes exact duplicate rows, keeping the first occurrence.
    2. Identifies timestamp collisions (same timestamp with different values).
       Aggregates them using the specified method (e.g. median) and logs the event.
       Never replaces entire duplicate rows with a global median.

    Args:
        df: Input DataFrame.
        timestamp_col: Name of timestamp column (autodetected if None).
        collision_aggregation: Aggregation method for collisions ('median', 'mean', 'first').

    Returns:
        Deduplicated DataFrame.
    """
    df = df.copy()

    # Step 1: Remove exact duplicate rows
    initial_len = len(df)
    exact_duplicates = df.duplicated().sum()
    if exact_duplicates > 0:
        df = df.drop_duplicates(keep="first")
        logger.info("Removed %d exact duplicate rows (kept first occurrence).", exact_duplicates)

    # Autodetect timestamp column
    ts_col = timestamp_col
    if not ts_col:
        for col in df.columns:
            if col.lower() in ["timestamp", "time", "datetime"]:
                ts_col = col
                break

    # Step 2: Check for timestamp collisions (same timestamp, different measurements)
    if ts_col and ts_col in df.columns:
        ts_duplicates = df.duplicated(subset=[ts_col]).sum()
        if ts_duplicates > 0:
            logger.warning(
                "Found %d timestamp collisions in '%s'. Aggregating using %s...",
                ts_duplicates, ts_col, collision_aggregation
            )
            # Separate numeric and non-numeric columns
            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            non_numeric_cols = [c for c in df.columns if c not in numeric_cols and c != ts_col]

            # Aggregate numeric columns
            agg_funcs = {col: collision_aggregation for col in numeric_cols}
            for col in non_numeric_cols:
                agg_funcs[col] = "first"

            df = df.groupby(ts_col, as_index=False).agg(agg_funcs)

    return df.reset_index(drop=True)

