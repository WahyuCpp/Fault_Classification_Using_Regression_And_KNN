"""Wavelet and statistical feature extraction for motor fault classification."""
from typing import Dict, Any, Union
import numpy as np
import pywt
from scipy.stats import skew, kurtosis
from scipy.signal import hilbert

def extract_features(
    signal: Union[np.ndarray, list],
    wavelet: str = "bior3.1",
    level: int = 1,
) -> Dict[str, float]:
    """Extract multi-domain features using Discrete Wavelet Transform and Hilbert envelope.

    Extracted feature set per signal axis:
        - Approximation coefficients: mean, std, var, rms, kurtosis, skewness, ZCR, MCR, entropy
        - Detail coefficients: mean, std, var, rms, kurtosis, skewness, entropy
        - Hilbert transform analytic signal: amplitude envelope mean and std

    Robustness enhancements:
        - Handles constant or near-constant signals without divide-by-zero
        - Replaces NaNs / Infs with stable finite values
        - Validates signal length against wavelet filter length

    Args:
        signal: 1D signal vector.
        wavelet: Mother wavelet family ('bior3.1' by default).
        level: Wavelet decomposition level (1 by default).

    Returns:
        Dictionary mapping feature names to scalar float values.
    """
    sig = np.asarray(signal, dtype=np.float64).flatten()
    n = len(sig)

    # Minimum length validation
    if n < 16:
        # Return fallback zeroed feature dict for degenerate signals
        return _fallback_feature_dict(level)

    # Detrend DC offset to stabilize higher-order statistical moments
    sig_mean = np.mean(sig)
    sig_centered = sig - sig_mean

    # Check for near-constant signal
    sig_std = np.std(sig)
    if sig_std < 1e-12:
        return _fallback_feature_dict(level)

    try:
        max_level = pywt.dwt_max_level(n, wavelet)
        actual_level = max(1, min(level, max_level))
        coeffs = pywt.wavedec(sig_centered, wavelet, level=actual_level)
    except Exception:
        # Fallback to Haar wavelet if bior3.1 fails on edge length
        coeffs = pywt.wavedec(sig_centered, "haar", level=1)

    approx_coeff = np.asarray(coeffs[0], dtype=np.float64)
    detail_coeffs = [np.asarray(c, dtype=np.float64) for c in coeffs[1:]]

    def _safe_kurtosis(arr: np.ndarray) -> float:
        if len(arr) < 4 or np.std(arr) < 1e-9:
            return 0.0
        val = float(kurtosis(arr, fisher=True, nan_policy="omit"))
        return 0.0 if np.isnan(val) or np.isinf(val) else val

    def _safe_skew(arr: np.ndarray) -> float:
        if len(arr) < 3 or np.std(arr) < 1e-9:
            return 0.0
        val = float(skew(arr, nan_policy="omit"))
        return 0.0 if np.isnan(val) or np.isinf(val) else val

    def _entropy(arr: np.ndarray) -> float:
        if len(arr) < 4:
            return 0.0
        hist, _ = np.histogram(arr, bins=10, density=True)
        # Avoid log(0) with epsilon
        non_zero_hist = hist[hist > 0]
        return float(-np.sum(non_zero_hist * np.log2(non_zero_hist + 1e-6)))

    # Zero Crossing Rate (ZCR)
    zcr = float(
        np.sum(np.abs(np.diff(np.sign(approx_coeff)))) / (2.0 * max(1, len(approx_coeff) - 1))
    )

    # Mean Crossing Rate (MCR)
    mean_diff = approx_coeff - np.mean(approx_coeff)
    mcr = float(
        np.sum(np.abs(np.diff(np.sign(mean_diff)))) / (2.0 * max(1, len(approx_coeff) - 1))
    )

    features: Dict[str, float] = {
        "mean_approx": float(np.mean(approx_coeff)),
        "std_approx": float(np.std(approx_coeff)),
        "var_approx": float(np.var(approx_coeff)),
        "rms_approx": float(np.sqrt(np.mean(np.square(approx_coeff)))),
        "kurt_approx": _safe_kurtosis(approx_coeff),
        "skew_approx": _safe_skew(approx_coeff),
        "zcr_approx": zcr,
        "mcr_approx": mcr,
        "entropy_approx": _entropy(approx_coeff),
    }

    # Detail coefficients stats
    for i, d_coeff in enumerate(detail_coeffs, 1):
        features[f"mean_d{i}"] = float(np.mean(d_coeff))
        features[f"std_d{i}"] = float(np.std(d_coeff))
        features[f"var_d{i}"] = float(np.var(d_coeff))
        features[f"rms_d{i}"] = float(np.sqrt(np.mean(np.square(d_coeff))))
        features[f"kurt_d{i}"] = _safe_kurtosis(d_coeff)
        features[f"skew_d{i}"] = _safe_skew(d_coeff)
        features[f"entropy_d{i}"] = _entropy(d_coeff)

    # Hilbert Transform envelope stats
    try:
        analytic_signal = hilbert(approx_coeff)
        amplitude_envelope = np.abs(analytic_signal)
        features["hilbert_mean"] = float(np.mean(amplitude_envelope))
        features["hilbert_std"] = float(np.std(amplitude_envelope))
    except Exception:
        features["hilbert_mean"] = 0.0
        features["hilbert_std"] = 0.0

    return features


def extract_axis_features(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    wavelet: str = "bior3.1",
    level: int = 1,
) -> Dict[str, float]:
    """Extract features independently from x, y, and z axes with explicit prefixes."""
    combined = {}
    axes = {"x": x, "y": y, "z": z}

    for axis_name, sig in axes.items():
        feats = extract_features(sig, wavelet=wavelet, level=level)
        for feat_name, val in feats.items():
            combined[f"{axis_name}_{feat_name}"] = val

    return combined


def _fallback_feature_dict(level: int) -> Dict[str, float]:
    """Provide a consistent fallback dictionary with zeroes."""
    keys = [
        "mean_approx", "std_approx", "var_approx", "rms_approx",
        "kurt_approx", "skew_approx", "zcr_approx", "mcr_approx", "entropy_approx"
    ]
    for i in range(1, level + 1):
        keys.extend([
            f"mean_d{i}", f"std_d{i}", f"var_d{i}", f"rms_d{i}",
            f"kurt_d{i}", f"skew_d{i}", f"entropy_d{i}"
        ])
    keys.extend(["hilbert_mean", "hilbert_std"])
    return {k: 0.0 for k in keys}

