"""Raw data inspection and reporting utility."""
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

from src.preprocessing.get_class import get_class
from src.utils.logger import get_logger

logger = get_logger("raw_data_info", "preprocessing.log")

def inspect_raw_data(file_path: str | Path, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """Inspect a raw CSV dataset and compute comprehensive data quality statistics.

    Args:
        file_path: Path to the CSV file.
        df: Optional already loaded DataFrame.

    Returns:
        Dictionary containing inspection metadata and metrics.
    """
    path = Path(file_path)
    if df is None:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        df = pd.read_csv(path)

    fault_code = get_class(path)
    rows, cols = df.shape
    col_names = df.columns.tolist()
    data_types = {col: str(dtype) for col, dtype in df.dtypes.items()}

    # Missing values per column
    missing_counts = df.isnull().sum().to_dict()
    total_missing = sum(missing_counts.values())

    # Duplicate rows count
    duplicate_count = int(df.duplicated().sum())

    # Outliers detection using MAD for numeric vibration/signal columns
    outliers_per_col = {}
    for col in ["x", "y", "z", "current", "temperature", "rpm"]:
        found_col = None
        for c in df.columns:
            if c.lower() == col:
                found_col = c
                break
        if found_col and pd.api.types.is_numeric_dtype(df[found_col]):
            series = df[found_col].dropna()
            if len(series) > 0:
                median = series.median()
                mad = np.median(np.abs(series - median))
                if mad > 1e-9:
                    modified_z_scores = 0.6745 * np.abs(series - median) / mad
                    outliers_per_col[col] = int((modified_z_scores > 3.5).sum())
                else:
                    outliers_per_col[col] = 0

    # Timestamp inspection and approximate sampling rate
    ts_col = None
    for c in df.columns:
        if c.lower() in ["timestamp", "time", "date_time", "datetime"]:
            ts_col = c
            break

    ts_start = None
    ts_end = None
    approx_fs = None

    if ts_col and len(df) > 1:
        try:
            ts_series = pd.to_datetime(df[ts_col].dropna(), errors="coerce")
            valid_ts = ts_series.dropna()
            if len(valid_ts) > 1:
                ts_start = str(valid_ts.iloc[0])
                ts_end = str(valid_ts.iloc[-1])
                diffs = valid_ts.diff().dt.total_seconds().dropna()
                positive_diffs = diffs[diffs > 0]
                if len(positive_diffs) > 0:
                    median_dt = positive_diffs.median()
                    if median_dt > 0:
                        approx_fs = round(1.0 / median_dt, 2)
        except Exception as e:
            logger.warning("Could not parse timestamps in %s: %s", path.name, e)

    # Check for 'seconds' column if timestamp didn't yield sampling rate
    if approx_fs is None:
        for c in df.columns:
            if c.lower() in ["seconds", "sec", "time_sec"]:
                try:
                    s_series = pd.to_numeric(df[c], errors="coerce").dropna()
                    if len(s_series) > 1:
                        diffs = s_series.diff().dropna()
                        positive_diffs = diffs[diffs > 0]
                        if len(positive_diffs) > 0:
                            approx_fs = round(1.0 / positive_diffs.median(), 2)
                except Exception:
                    pass
                break

    report = {
        "file_name": path.name,
        "fault_class": fault_code,
        "shape": (rows, cols),
        "num_rows": rows,
        "num_columns": cols,
        "columns": col_names,
        "data_types": data_types,
        "missing_values": missing_counts,
        "total_missing": total_missing,
        "duplicate_rows": duplicate_count,
        "outliers": outliers_per_col,
        "timestamp_start": ts_start,
        "timestamp_end": ts_end,
        "approx_sampling_rate_hz": approx_fs,
    }

    return report


def print_raw_data_report(report: Dict[str, Any]) -> None:
    """Print formatted inspection report matching project specification."""
    print("=" * 60)
    print(f"File: {report['file_name']}")
    print(f"Class: {report['fault_class']}")
    print(f"Dimensions: {report['shape'][0]} rows x {report['shape'][1]} cols")
    print(f"Sampling Rate: {report['approx_sampling_rate_hz'] or 'Unknown'} Hz")
    if report['timestamp_start']:
        print(f"Timestamp: {report['timestamp_start']} to {report['timestamp_end']}")
    print("\nMissing values:")
    for col, count in report["missing_values"].items():
        print(f"  {col:<15}: {count}")
    print(f"\nDuplicates: {report['duplicate_rows']}")
    print("\nOutliers (MAD):")
    for col, count in report["outliers"].items():
        print(f"  {col:<15}: {count}")
    print("=" * 60)


if __name__ == "__main__":
    import sys
    from config.main_config import CLEANED_DATA_DIR, BASE_DIR

    target_files = list(CLEANED_DATA_DIR.rglob("*.csv"))
    if not target_files:
        raw_dir = BASE_DIR / "data" / "raw"
        target_files = list(raw_dir.rglob("*.csv"))

    if not target_files:
        print("No CSV files found to inspect.")
        sys.exit(0)

    for csv_file in target_files[:5]:
        rep = inspect_raw_data(csv_file)
        print_raw_data_report(rep)

