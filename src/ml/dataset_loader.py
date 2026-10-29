"""Dataset loading and segmentation module for ML feature generation."""
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

from config.main_config import PROCESSED_DATA_DIR
from config.ml_config import ML_WINDOW_SIZE, ML_OVERLAP
from src.utils.logger import get_logger

logger = get_logger("dataset_loader", "ml.log")

def get_processed_files_by_class(
    base_dir: str | Path = PROCESSED_DATA_DIR,
) -> Dict[str, List[Path]]:
    """Scan processed datasets grouped by condition folder."""
    base_path = Path(base_dir).resolve()
    class_files: Dict[str, List[Path]] = {}

    for folder in base_path.iterdir():
        if folder.is_dir():
            csvs = list(folder.glob("*.csv"))
            if csvs:
                class_files[folder.name] = csvs

    return class_files


def segment_signal_dataframe(
    df: pd.DataFrame,
    window_size: int = ML_WINDOW_SIZE,
    overlap: float = ML_OVERLAP,
) -> List[Tuple[np.ndarray, np.ndarray, np.ndarray, str]]:
    """Segment a dataset into fixed-length windows with overlap.

    Segments do NOT cross file boundaries.

    Args:
        df: Processed DataFrame containing 'x', 'y', 'z', and 'fault_label'.
        window_size: Number of samples per window (e.g., 2048).
        overlap: Fractional overlap between consecutive windows (e.g., 0.5).

    Returns:
        List of tuples: (x_segment, y_segment, z_segment, fault_label).
    """
    total_len = len(df)
    if total_len < window_size:
        # If file has fewer samples than window_size, pad or use entire file
        logger.warning(
            "File length (%d) is smaller than window size (%d). Padding...",
            total_len, window_size
        )
        pad_len = window_size - total_len
        x = np.pad(df["x"].values, (0, pad_len), mode="edge")
        y = np.pad(df["y"].values, (0, pad_len), mode="edge")
        z = np.pad(df["z"].values, (0, pad_len), mode="edge")
        label = str(df["fault_label"].iloc[0])
        return [(x, y, z, label)]

    step = int(window_size * (1.0 - overlap))
    if step <= 0:
        step = window_size

    segments = []
    x_vals = df["x"].to_numpy(dtype=np.float64)
    y_vals = df["y"].to_numpy(dtype=np.float64)
    z_vals = df["z"].to_numpy(dtype=np.float64)
    label = str(df["fault_label"].iloc[0])

    for start in range(0, total_len - window_size + 1, step):
        end = start + window_size
        seg_x = x_vals[start:end]
        seg_y = y_vals[start:end]
        seg_z = z_vals[start:end]
        segments.append((seg_x, seg_y, seg_z, label))

    return segments

