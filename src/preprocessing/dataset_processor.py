"""Dataset processor: cleans and standardizes a single dataset file."""
from pathlib import Path
from typing import Optional
import pandas as pd

from src.preprocessing.get_class import get_class
from src.preprocessing.missing_value_fix import fix_missing_values
from src.preprocessing.outlier_fix import fix_outliers
from src.preprocessing.duplicate_fix import fix_duplicates
from src.preprocessing.column_uniforming import uniform_columns
from config.main_config import PROCESSED_DATA_DIR
from config.data_cleaning_config import LABEL_TO_CONDITION
from src.utils.logger import get_logger

logger = get_logger("dataset_processor", "preprocessing.log")

def process_dataset_file(
    input_path: str | Path,
    output_path: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None,
) -> pd.DataFrame:
    """Process a single CSV dataset through the full cleaning pipeline.

    Steps:
        1. Load dataset
        2. Determine fault class
        3. Clean missing values
        4. Detect and replace outliers (MAD for vibration)
        5. Remove exact duplicates & aggregate timestamp collisions
        6. Enforce standardized column schema and ordering
        7. Save processed dataset to target path without overwriting input

    Args:
        input_path: Path to the input raw/cleaned CSV.
        output_path: Explicit target path for output CSV.
        output_dir: Base directory for processed data (defaults to data/processed).

    Returns:
        Cleaned and standardized pandas DataFrame.
    """
    in_file = Path(input_path).resolve()
    if not in_file.exists():
        raise FileNotFoundError(f"Input file not found: {in_file}")

    logger.info("Processing dataset file: %s", in_file.name)
    df = pd.read_csv(in_file)

    # 1. Determine fault class
    fault_code = get_class(in_file)

    # 2. Fix missing values
    df = fix_missing_values(df)

    # 3. Fix outliers
    df = fix_outliers(df)

    # 4. Fix duplicates
    df = fix_duplicates(df)

    # 5. Column uniforming
    df = uniform_columns(df, default_fault_label=fault_code)

    # 6. Determine output file path
    if output_path is not None:
        out_file = Path(output_path).resolve()
    else:
        base_proc_dir = Path(output_dir or PROCESSED_DATA_DIR).resolve()
        subfolder_name = LABEL_TO_CONDITION.get(fault_code, "healthy")
        target_subfolder = base_proc_dir / subfolder_name
        target_subfolder.mkdir(parents=True, exist_ok=True)
        # Avoid overwriting original or dropping '_processed' suffix
        stem = in_file.stem
        if not stem.endswith("_processed"):
            stem = f"{stem}_processed"
        out_file = target_subfolder / f"{stem}.csv"

    out_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_file, index=False)
    logger.info("Saved processed dataset to: %s (%d rows)", out_file, len(df))

    return df

