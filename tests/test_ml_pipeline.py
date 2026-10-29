"""Unit tests for the Machine Learning training and inference pipeline."""
import numpy as np
import pandas as pd
import pytest

from src.ml.feature_extraction import extract_features, extract_axis_features
from src.ml.predict import FaultPredictor
from src.ml.train_knn import train_knn

def test_wavelet_feature_extraction_structure():
    """Verify wavelet and statistical feature dict contains expected keys and finite values."""
    sig = np.sin(np.linspace(0, 10, 256))
    features = extract_features(sig, wavelet="bior3.1", level=1)

    expected_keys = [
        "mean_approx", "std_approx", "var_approx", "rms_approx",
        "kurt_approx", "skew_approx", "zcr_approx", "mcr_approx", "entropy_approx",
        "mean_d1", "std_d1", "var_d1", "rms_d1", "kurt_d1", "skew_d1", "entropy_d1",
        "hilbert_mean", "hilbert_std"
    ]
    for key in expected_keys:
        assert key in features
        assert not np.isnan(features[key])
        assert not np.isinf(features[key])


def test_axis_features_naming():
    """Verify independent multi-axis naming with 'x_', 'y_', and 'z_' prefixes."""
    x = np.random.randn(256)
    y = np.random.randn(256)
    z = np.random.randn(256)

    axis_feats = extract_axis_features(x, y, z, wavelet="bior3.1", level=1)
    assert "x_mean_approx" in axis_feats
    assert "y_rms_approx" in axis_feats
    assert "z_hilbert_mean" in axis_feats
    # Total features: 18 features per axis * 3 axes = 54 features
    assert len(axis_feats) == 54


def test_real_time_fault_predictor():
    """Verify real-time prediction pipeline produces valid predicted label and confidence."""
    predictor = FaultPredictor(model_name="knn")
    # Generate 512 samples
    x = np.random.randn(512)
    y = np.random.randn(512)
    z = 9.81 + 0.1 * np.random.randn(512)

    result = predictor.predict_window(x, y, z)
    assert result["status"] == "OK"
    assert "predicted_label" in result
    assert "condition_name" in result
    assert 0.0 <= result["confidence"] <= 1.0

