"""Preprocessing package for MONTREAL-VT datasets."""
from src.preprocessing.get_class import get_class, attach_class_label
from src.preprocessing.raw_data_info import inspect_raw_data, print_raw_data_report
from src.preprocessing.missing_value_fix import fix_missing_values
from src.preprocessing.outlier_fix import fix_outliers
from src.preprocessing.duplicate_fix import fix_duplicates
from src.preprocessing.column_uniforming import uniform_columns
from src.preprocessing.dataset_processor import process_dataset_file
from src.preprocessing.preprocessing_pipeline import run_preprocessing_pipeline

__all__ = [
    "get_class",
    "attach_class_label",
    "inspect_raw_data",
    "print_raw_data_report",
    "fix_missing_values",
    "fix_outliers",
    "fix_duplicates",
    "uniform_columns",
    "process_dataset_file",
    "run_preprocessing_pipeline",
]

