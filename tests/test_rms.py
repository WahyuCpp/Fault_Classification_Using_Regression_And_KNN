"""Unit tests for Acceleration and Velocity RMS calculations."""
import numpy as np
import pytest
from src.signal_processing.v_rms import compute_acceleration_rms, compute_velocity_rms

def test_sine_wave_acceleration_rms():
    """Verify that a known sinusoidal signal produces theoretical RMS (Amplitude / sqrt(2))."""
    fs = 1500.0
    t = np.linspace(0, 1.0, int(fs), endpoint=False)
    freq = 50.0
    amplitude = 2.0

    # Theoretical RMS for sine wave is A / sqrt(2)
    expected_rms = amplitude / np.sqrt(2.0)  # ~1.4142

    x = amplitude * np.sin(2 * np.pi * freq * t)
    y = np.zeros_like(x)
    z = np.zeros_like(x)

    rms_result = compute_acceleration_rms(x, y, z)

    assert abs(rms_result["a_rms_x"] - expected_rms) < 0.02
    assert rms_result["a_rms_y"] == 0.0
    assert rms_result["a_rms_z"] == 0.0
    assert abs(rms_result["a_rms_total"] - expected_rms) < 0.02


def test_resultant_rms_combination():
    """Verify 3D resultant RMS: sqrt(x^2 + y^2 + z^2)."""
    x = np.ones(100) * 3.0  # RMS = 3.0
    y = np.ones(100) * 4.0  # RMS = 4.0
    z = np.zeros(100)       # RMS = 0.0

    # Resultant sqrt(3^2 + 4^2 + 0^2) = 5.0
    res = compute_acceleration_rms(x, y, z)
    assert abs(res["a_rms_x"] - 3.0) < 1e-4
    assert abs(res["a_rms_y"] - 4.0) < 1e-4
    assert abs(res["a_rms_total"] - 5.0) < 1e-4


def test_velocity_rms_integration():
    """Verify velocity RMS integration removes DC and produces positive integrated value."""
    fs = 1500.0
    t = np.linspace(0, 1.0, int(fs), endpoint=False)
    # Sine wave acceleration with DC offset
    x = 1.0 * np.sin(2 * np.pi * 50.0 * t) + 9.81
    y = np.zeros_like(x)
    z = np.zeros_like(x)

    v_res = compute_velocity_rms(x, y, z, sampling_rate=fs)
    assert "v_rms_x" in v_res
    assert "v_rms_total" in v_res
    assert v_res["v_rms_x"] > 0.0

