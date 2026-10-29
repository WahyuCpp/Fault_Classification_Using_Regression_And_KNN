"""Machine learning pipeline and model hyperparameter configuration."""
from config.main_config import MODELS_DIR

# Window segmentation parameters for ML feature extraction
ML_WINDOW_SIZE = 2048
ML_OVERLAP = 0.5

# Discrete Wavelet Transform settings
WAVELET = "bior3.1"
WAVELET_LEVEL = 1

# Train/Test evaluation settings
TEST_SIZE = 0.2
RANDOM_STATE = 42

# Default hyperparameters for required classifiers
HYPERPARAMETERS = {
    "logistic_regression": {
        "max_iter": 1000,
        "solver": "lbfgs",
        "random_state": RANDOM_STATE,
    },
    "decision_tree": {
        "max_depth": 10,
        "min_samples_split": 5,
        "min_samples_leaf": 2,
        "criterion": "gini",
        "random_state": RANDOM_STATE,
    },
    "knn": {
        "n_neighbors": 5,
        "weights": "distance",
        "metric": "minkowski",
    },
}

