"""Fault class determination from file path and folder hierarchy."""
from pathlib import Path
from typing import Dict, Optional
import pandas as pd
from config.data_cleaning_config import MOTOR_CONDITION_LABELS

def get_class(file_path: str | Path, label_mapping: Optional[Dict[str, str]] = None) -> str:
    """Determine machine fault class code based on the directory structure.

    Args:
        file_path: Path to the dataset CSV file.
        label_mapping: Mapping of folder/condition names to short class codes.

    Returns:
        Short fault label code (e.g. 'A', 'OB', 'IB', 'BB', 'UNB', 'MIS').
    """
    mapping = label_mapping or MOTOR_CONDITION_LABELS
    path = Path(file_path).resolve()

    # Search through parent folders (from immediate parent upwards)
    for part in reversed(path.parts[:-1]):
        normalized_part = part.lower().strip()
        if normalized_part in mapping:
            return mapping[normalized_part]
        # Check partial/alias matches
        for key, code in mapping.items():
            if key in normalized_part or normalized_part in key:
                return code

    # Fallback to file name if not found in parents
    filename = path.stem.lower()
    for key, code in mapping.items():
        if key in filename:
            return code

    # Default to healthy ('A') if undetermined
    return mapping.get("healthy", "A")


def attach_class_label(df: pd.DataFrame, file_path: str | Path, label_mapping: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """Attach the detected fault label as a column to the dataframe."""
    fault_code = get_class(file_path, label_mapping)
    df = df.copy()
    df["fault_label"] = fault_code
    return df

