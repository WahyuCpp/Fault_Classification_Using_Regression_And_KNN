"""Real-time online inference pipeline for motor condition classification."""
from typing import Dict, Any, List, Optional, Union
import numpy as np
import pandas as pd

from config.data_cleaning_config import LABEL_TO_CONDITION
from config.ml_config import WAVELET, WAVELET_LEVEL
from src.ml.feature_extraction import extract_axis_features
from src.ml.model_utils import load_model, get_all_models_metadata
from src.utils.logger import get_logger

logger = get_logger("predict", "ml.log")

class FaultPredictor:
    """Performs real-time fault classification on live windowed acceleration signals."""

    def __init__(self, model_name: str = "knn"):
        self.model_name = model_name
        self.pipeline = None
        self.metadata = {}
        self.feature_names = []
        self._load_active_model(model_name)

    def _load_active_model(self, model_name: str) -> bool:
        """Attempt to load designated model pipeline."""
        try:
            self.pipeline, self.metadata = load_model(model_name)
            self.feature_names = self.metadata.get("feature_names", [])
            self.model_name = model_name
            logger.info("Loaded ML model: %s", model_name)
            return True
        except Exception as e:
            logger.warning("Could not load model '%s': %s", model_name, e)
            self.pipeline = None
            return False

    def predict_window(
        self,
        x_window: Union[np.ndarray, List[float]],
        y_window: Union[np.ndarray, List[float]],
        z_window: Union[np.ndarray, List[float]],
    ) -> Dict[str, Any]:
        """Perform end-to-end inference on a 3-axis vibration window.

        Steps:
            1. Extract identical wavelet & statistical features across X, Y, Z.
            2. Match feature vector ordering with training-time feature names.
            3. Apply pipeline (StandardScaler + fitted classifier).
            4. Compute predicted class label and class probability distribution.

        Returns:
            Dictionary with predicted_label, condition_name, confidence, probabilities, and model_used.
        """
        if self.pipeline is None:
            # Try reloading in case it was just trained
            if not self._load_active_model(self.model_name):
                return {
                    "status": "Unavailable — model not loaded",
                    "predicted_label": "N/A",
                    "condition_name": "Model Not Loaded",
                    "confidence": 0.0,
                    "probabilities": {},
                    "model_used": self.model_name,
                }

        x = np.asarray(x_window, dtype=np.float64)
        y = np.asarray(y_window, dtype=np.float64)
        z = np.asarray(z_window, dtype=np.float64)

        if len(x) < 16 or len(y) < 16 or len(z) < 16:
            return {
                "status": "Insufficient samples for feature extraction",
                "predicted_label": "N/A",
                "condition_name": "Insufficient Data",
                "confidence": 0.0,
                "probabilities": {},
                "model_used": self.model_name,
            }

        # Step 1: Feature extraction identical to training
        features_dict = extract_axis_features(x, y, z, wavelet=WAVELET, level=WAVELET_LEVEL)

        # Step 2: Assemble feature vector matching training order
        if self.feature_names:
            feature_vector = np.array([
                features_dict.get(fn, 0.0) for fn in self.feature_names
            ]).reshape(1, -1)
        else:
            feature_vector = np.array(list(features_dict.values())).reshape(1, -1)

        # Step 3: Run pipeline
        try:
            pred_class = self.pipeline.predict(feature_vector)[0]
            pred_code = str(pred_class)
            condition_name = LABEL_TO_CONDITION.get(pred_code, pred_code)

            # Extract probabilities if classifier supports predict_proba
            probabilities = {}
            confidence = 1.0

            if hasattr(self.pipeline, "predict_proba"):
                try:
                    probs = self.pipeline.predict_proba(feature_vector)[0]
                    classes = self.pipeline.named_steps["classifier"].classes_
                    for cls_name, prob in zip(classes, probs):
                        str_cls = str(cls_name)
                        probabilities[LABEL_TO_CONDITION.get(str_cls, str_cls)] = round(float(prob), 4)
                    confidence = round(float(np.max(probs)), 4)
                except Exception:
                    pass

            return {
                "status": "OK",
                "predicted_label": pred_code,
                "condition_name": condition_name,
                "confidence": confidence,
                "probabilities": probabilities,
                "model_used": self.model_name,
            }
        except Exception as e:
            logger.error("Inference failed: %s", e)
            return {
                "status": f"Inference Error: {e}",
                "predicted_label": "ERR",
                "condition_name": "Error",
                "confidence": 0.0,
                "probabilities": {},
                "model_used": self.model_name,
            }

