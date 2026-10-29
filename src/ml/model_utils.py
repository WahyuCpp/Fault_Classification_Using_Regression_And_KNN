"""Model persistence, loading, and metadata management."""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple
import joblib

from config.main_config import MODELS_DIR
from config.ml_config import (
    WAVELET,
    WAVELET_LEVEL,
    ML_WINDOW_SIZE,
    ML_OVERLAP,
)
from config.main_config import DEFAULT_SAMPLING_RATE

METADATA_PATH = MODELS_DIR / "metadata.json"

def save_model(
    model: Any,
    model_name: str,
    feature_names: list,
    classes: list,
    metrics: Dict[str, Any],
    hyperparameters: Dict[str, Any],
) -> Path:
    """Save trained scikit-learn model and update global metadata.json."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    model_file = MODELS_DIR / f"{model_name}.joblib"
    joblib.dump(model, model_file)

    # Load existing metadata or create fresh
    metadata: Dict[str, Any] = {}
    if METADATA_PATH.exists():
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception:
            metadata = {}

    metadata[model_name] = {
        "model_file": model_file.name,
        "model_version": "1.0.0",
        "training_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "feature_names": feature_names,
        "fault_classes": [str(c) for c in classes],
        "wavelet": WAVELET,
        "wavelet_level": WAVELET_LEVEL,
        "segment_size": ML_WINDOW_SIZE,
        "overlap": ML_OVERLAP,
        "sampling_rate_hz": DEFAULT_SAMPLING_RATE,
        "hyperparameters": hyperparameters,
        "evaluation_metrics": metrics,
    }

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return model_file


def load_model(model_name: str) -> Tuple[Any, Dict[str, Any]]:
    """Load a persisted model pipeline and its metadata."""
    model_file = MODELS_DIR / f"{model_name}.joblib"
    if not model_file.exists():
        raise FileNotFoundError(f"Model file not found: {model_file}")

    model = joblib.load(model_file)
    meta = {}
    if METADATA_PATH.exists():
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                full_meta = json.load(f)
                meta = full_meta.get(model_name, {})
        except Exception:
            pass

    return model, meta


def get_all_models_metadata() -> Dict[str, Any]:
    """Return metadata for all available models."""
    if not METADATA_PATH.exists():
        return {}
    try:
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

