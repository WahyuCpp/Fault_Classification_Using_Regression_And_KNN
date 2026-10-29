"""Training feature extraction pipeline across all processed datasets."""
from pathlib import Path
from typing import Tuple, List, Dict
import pandas as pd
import numpy as np

from config.main_config import PROCESSED_DATA_DIR, TRAINING_DATA_DIR
from config.ml_config import ML_WINDOW_SIZE, ML_OVERLAP, WAVELET, WAVELET_LEVEL
from src.ml.dataset_loader import get_processed_files_by_class, segment_signal_dataframe
from src.ml.feature_extraction import extract_axis_features
from src.utils.logger import get_logger

logger = get_logger("preprocess_training", "ml.log")

def generate_training_features(
    processed_dir: str | Path = PROCESSED_DATA_DIR,
    output_csv: str | Path = TRAINING_DATA_DIR / "training_features.csv",
    window_size: int = ML_WINDOW_SIZE,
    overlap: float = ML_OVERLAP,
    wavelet: str = WAVELET,
    level: int = WAVELET_LEVEL,
) -> pd.DataFrame:
    """Extract segmented wavelet and statistical features from processed files.

    Saves:
        data/training/training_features.csv with metadata columns:
        [source_file, segment_number, fault_label, <feature_columns...>]

    Returns:
        DataFrame of extracted features.
    """
    logger.info("Starting training feature extraction (window=%d, overlap=%.2f)...", window_size, overlap)
    class_files = get_processed_files_by_class(processed_dir)

    all_records: List[Dict[str, Any]] = []
    total_files = sum(len(flist) for flist in class_files.values())

    if total_files == 0:
        raise FileNotFoundError(f"No processed CSV files found in {processed_dir}. Run preprocessing first.")

    for class_folder, files in class_files.items():
        for file_path in files:
            df = pd.read_csv(file_path)
            segments = segment_signal_dataframe(df, window_size=window_size, overlap=overlap)

            for seg_idx, (x_seg, y_seg, z_seg, label) in enumerate(segments):
                features = extract_axis_features(
                    x_seg, y_seg, z_seg, wavelet=wavelet, level=level
                )
                record = {
                    "source_file": file_path.name,
                    "segment_number": seg_idx,
                    "fault_label": label,
                    **features,
                }
                all_records.append(record)

    df_features = pd.DataFrame(all_records)
    out_path = Path(output_csv).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_features.to_csv(out_path, index=False)

    logger.info(
        "Extracted %d feature observations across %d files. Saved to: %s",
        len(df_features), total_files, out_path
    )
    print(f"\n[Feature Extraction Complete] Generated {len(df_features)} observations.")
    print("Class distribution:")
    print(df_features["fault_label"].value_counts().to_string())

    return df_features


if __name__ == "__main__":
    print("=" * 60)
    print("MONTREAL-VT: Preprocessing Training Features")
    print("=" * 60)
    generate_training_features()

