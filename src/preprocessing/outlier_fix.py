"""Outlier detection and cleaning for vibration and operating signals."""
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np

from config.data_cleaning_config import OUTLIER_CONFIG
from src.utils.logger import get_logger

logger = get_logger("outlier_fix", "preprocessing.log")

def fix_outliers(
    df: pd.DataFrame,
    config: Optional[Dict[str, Any]] = None,
    replacement_strategy: str = "median",
) -> pd.DataFrame:
    """Detect and clean signal outliers using robust statistics and engineering bounds.

    - Vibration signals (x, y, z): MAD (Median Absolute Deviation) robust z-score.
    - Physical signals (current, temperature, rpm): physical engineering plausibility limits.
    - Outliers are replaced by local/global median without deleting the row.

    Args:
        df: Input DataFrame.
        config: Optional configuration dictionary.
        replacement_strategy: 'median' or 'clip'.

    Returns:
        DataFrame with outliers replaced by median values.
    """
    df = df.copy()
    cfg = config or OUTLIER_CONFIG

    # Map column names in df to categories
    for category, settings in cfg.items():
        cols = settings.get("columns", [])
        method = settings.get("method", "mad")

        for col_name in cols:
            target_col = None
            for c in df.columns:
                if c.lower() == col_name.lower():
                    target_col = c
                    break

            if not target_col or not pd.api.types.is_numeric_dtype(df[target_col]):
                continue

            series = df[target_col].copy()
            col_median = series.median()
            outlier_mask = pd.Series(False, index=df.index)

            if method == "mad":
                threshold = settings.get("threshold", 4.5)
                mad = np.median(np.abs(series - col_median))
                if mad > 1e-9:
                    modified_z_scores = 0.6745 * np.abs(series - col_median) / mad
                    outlier_mask = modified_z_scores > threshold

            elif method == "iqr":
                k = settings.get("k", 3.0)
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                if iqr > 1e-9:
                    outlier_mask = (series < (q1 - k * iqr)) | (series > (q3 + k * iqr))

            elif method == "engineering_range":
                min_val = settings.get("min_val", -np.inf)
                max_val = settings.get("max_val", np.inf)
                outlier_mask = (series < min_val) | (series > max_val)

            outlier_count = int(outlier_mask.sum())
            if outlier_count > 0:
                logger.info(
                    "Detected %d outliers in '%s' (%s, method=%s). Replacing with %s...",
                    outlier_count, target_col, category, method, replacement_strategy
                )
                if replacement_strategy == "median":
                    # Replace outliers with median
                    df.loc[outlier_mask, target_col] = col_median
                elif replacement_strategy == "clip":
                    min_val = settings.get("min_val", col_median - 3 * (series.std() or 1))
                    max_val = settings.get("max_val", col_median + 3 * (series.std() or 1))
                    df[target_col] = df[target_col].clip(lower=min_val, upper=max_val)

    return df

