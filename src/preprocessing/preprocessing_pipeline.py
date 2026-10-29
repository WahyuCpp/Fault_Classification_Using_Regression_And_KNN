"""Batch preprocessing pipeline for Montreal-VT motor condition datasets."""
from pathlib import Path
from typing import List, Dict
import pandas as pd

from config.main_config import CLEANED_DATA_DIR, PROCESSED_DATA_DIR, BASE_DIR
from config.data_cleaning_config import MOTOR_CONDITION_LABELS
from src.preprocessing.dataset_processor import process_dataset_file
from src.utils.logger import get_logger

logger = get_logger("preprocessing_pipeline", "preprocessing.log")

def run_preprocessing_pipeline(
    input_dir: str | Path = CLEANED_DATA_DIR,
    output_dir: str | Path = PROCESSED_DATA_DIR,
) -> Dict[str, List[Path]]:
    """Scan and process all dataset files into structured processed folders.

    Args:
        input_dir: Directory containing input raw or cleaned CSVs.
        output_dir: Target processed directory.

    Returns:
        Dictionary mapping fault conditions to lists of processed file paths.
    """
    in_dir = Path(input_dir).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Ensure all condition subdirectories exist in both input and output
    for condition_folder in MOTOR_CONDITION_LABELS.keys():
        (in_dir / condition_folder).mkdir(parents=True, exist_ok=True)
        (out_dir / condition_folder).mkdir(parents=True, exist_ok=True)

    csv_files = list(in_dir.rglob("*.csv"))
    logger.info("Found %d CSV files to process in %s", len(csv_files), in_dir)

    results: Dict[str, List[Path]] = {k: [] for k in MOTOR_CONDITION_LABELS.keys()}
    processed_count = 0

    for file_path in csv_files:
        # Skip files that are already inside output_dir or already processed
        if out_dir in file_path.parents or "_processed" in file_path.stem:
            continue

        try:
            df = process_dataset_file(file_path, output_dir=out_dir)
            processed_count += 1
            logger.info("Processed: %s (%d rows)", file_path.name, len(df))
        except Exception as e:
            logger.error("Failed to process %s: %s", file_path, e, exc_info=True)

    # Collect processed files by condition
    for condition_folder in MOTOR_CONDITION_LABELS.keys():
        folder_path = out_dir / condition_folder
        if folder_path.exists():
            results[condition_folder] = list(folder_path.glob("*.csv"))

    print(f"\n[Preprocessing Complete] Successfully processed {processed_count} datasets.")
    for condition, files in results.items():
        print(f"  {condition:<22}: {len(files)} files")

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("MONTREAL-VT: Running Data Preprocessing Pipeline")
    print("=" * 60)
    run_preprocessing_pipeline()

