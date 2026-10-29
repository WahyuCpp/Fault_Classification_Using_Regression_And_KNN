"""Unit tests for Fast Fourier Transform (FFT) analysis."""
import numpy as np
import pytest
from src.signal_processing.fft_analysis import compute_fft

def test_fft_known_sine_frequency_peak():
    """Verify that a synthetic 50 Hz sine wave produces a dominant FFT peak at 50 Hz."""
    fs = 1500.0
    N = 1024
    target_freq = 50.0

    t = np.arange(N) / fs
    # Pure sine wave at 50 Hz
    x = 2.5 * np.sin(2 * np.pi * target_freq * t)
    y = np.zeros_like(x)
    z = np.zeros_like(x)

    fft_result = compute_fft(
        x=x,
        y=y,
        z=z,
        sampling_rate=fs,
        window_size=N,
        window_func="hann",
    )

    freqs = np.array(fft_result["frequency"])
    mags = np.array(fft_result["magnitude_x"])

    # Find frequency bin with maximum spectral magnitude
    peak_idx = np.argmax(mags)
    detected_freq = freqs[peak_idx]

    delta_f = fs / N
    assert abs(detected_freq - target_freq) <= delta_f * 1.5, (
        f"Expected peak at {target_freq} Hz, found at {detected_freq} Hz (resolution: {delta_f} Hz)"
    )
    assert fft_result["frequency_resolution"] == round(fs / N, 4)
    assert fft_result["nyquist_frequency"] == round(fs / 2.0, 2)


def test_fft_different_window_sizes():
    """Verify selectable window sizes (256, 512, 1024, 2048) calculate correct frequency resolution."""
    fs = 1500.0
    sig = np.random.randn(3000)

    for n in [256, 512, 1024, 2048]:
        res = compute_fft(sig, sig, sig, sampling_rate=fs, window_size=n)
        assert res["window_size"] == n
        assert abs(res["frequency_resolution"] - (fs / n)) < 1e-3

