"""Unit tests for rolling element bearing characteristic frequency calculation."""
import pytest
# import numpy as np

from src.signal_processing.bearing_frequency import (
    calculate_rotational_frequency,
    calculate_bearing_frequencies,
    calculate_electrical_frequencies,
)

def test_shaft_rotational_frequency():
    """Verify fr = RPM / 60."""
    fr = calculate_rotational_frequency(1450.0)
    assert fr is not None
    # assert float(calculate_rotational_frequency(1800.0) == 30.0)
    # assert np.abs(calculate_rotational_frequency(1450.0)-24.1667) < 0.01
    assert abs(fr-24.1667) < 0.01
    # return test_shaft_rotational_frequency


def test_bearing_characteristic_frequencies():
    """Verify standard 6205-2RS bearing frequencies at 1450 RPM."""
    # 6205 parameters: Nb=9, Bd=7.94 mm, Pd=39.04 mm, theta=0 deg
    bearing_cfg = {
        "model": "6205-2RS",
        "number_of_rolling_elements": 9,
        "ball_diameter": 7.94,
        "pitch_diameter": 39.04,
        "contact_angle_deg": 0.0,
    }
    rpm = 1450.0  # fr = 24.167 Hz

    res = calculate_bearing_frequencies(rpm, bearing_cfg)

    assert res["status"] == "Calculated (Theoretical)"
    assert abs(res["fr"] - 24.17) < 0.1
    # BPFO ~= 86.5 Hz
    assert abs(res["bpfo"] - 86.53) < 0.2
    # BPFI ~= 130.97 Hz
    assert abs(res["bpfi"] - 130.97) < 0.2
    # BSF ~= 56.78 Hz
    assert abs(res["bsf"] - 56.78) < 0.2
    # FTF ~= 9.61 Hz
    assert abs(res["ftf"] - 9.61) < 0.2


def test_unavailable_bearing_parameters():
    """Verify graceful handling when RPM or parameters are absent."""
    res = calculate_bearing_frequencies(None)
    assert "Unavailable" in res["status"]
    assert res["bpfo"] is None

test_shaft_rotational_frequency()