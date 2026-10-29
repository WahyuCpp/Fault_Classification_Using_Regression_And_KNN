"""Machine learning package for MONTREAL-VT fault classification."""
from src.ml.feature_extraction import extract_features, extract_axis_features
from src.ml.dataset_loader import get_processed_files_by_class, segment_signal_dataframe
from src.ml.preprocess_training import generate_training_features
from src.ml.evaluate_models import evaluate_classifier, print_comparison_table
from src.ml.model_utils import save_model, load_model, get_all_models_metadata
from src.ml.train_logistic_regression import train_logistic_regression
from src.ml.train_decision_tree import train_decision_tree
from src.ml.train_knn import train_knn
from src.ml.predict import FaultPredictor

__all__ = [
    "extract_features",
    "extract_axis_features",
    "get_processed_files_by_class",
    "segment_signal_dataframe",
    "generate_training_features",
    "evaluate_classifier",
    "print_comparison_table",
    "save_model",
    "load_model",
    "get_all_models_metadata",
    "train_logistic_regression",
    "train_decision_tree",
    "train_knn",
    "FaultPredictor",
]

