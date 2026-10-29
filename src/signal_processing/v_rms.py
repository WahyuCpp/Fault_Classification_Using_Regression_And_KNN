"""Vibration RMS calculation module.

Maintains strict separation between Acceleration RMS and Velocity RMS.
"""
from typing import Dict, Union, List, Optional
import numpy as np
from scipy import signal as sp_signal

def compute_acceleration_rms(
    x: Union[np.ndarray, List[float]],
    y: Union[np.ndarray, List[float]],
    z: Union[np.ndarray, List[float]],
) -> Dict[str, float]:
    """Compute 3-axis and resultant Acceleration RMS directly from acceleration signals.

    Formula:
        a_rms_i = sqrt( (1 / N) * sum(i_n^2) )
        a_rms_total = sqrt( a_rms_x^2 + a_rms_y^2 + a_rms_z^2 )

    Returns:
        Dict containing:
            a_rms_x, a_rms_y, a_rms_z, a_rms_total
    """
    arr_x = np.asarray(x, dtype=np.float64)
    arr_y = np.asarray(y, dtype=np.float64)
    arr_z = np.asarray(z, dtype=np.float64)

    def _rms(arr: np.ndarray) -> float:
        if len(arr) == 0:
            return 0.0
        return float(np.sqrt(np.mean(np.square(arr))))

    a_rms_x = _rms(arr_x)
    a_rms_y = _rms(arr_y)
    a_rms_z = _rms(arr_z)
    a_rms_total = float(np.sqrt(a_rms_x**2 + a_rms_y**2 + a_rms_z**2))

    return {
        "a_rms_x": round(a_rms_x, 4),
        "a_rms_y": round(a_rms_y, 4),
        "a_rms_z": round(a_rms_z, 4),
        "a_rms_total": round(a_rms_total, 4),
    }


def compute_velocity_rms(
    x: Union[np.ndarray, List[float]],
    y: Union[np.ndarray, List[float]],
    z: Union[np.ndarray, List[float]],
    sampling_rate: float = 1500.0,
    hp_cutoff_hz: float = 10.0,
) -> Dict[str, float]:
    """Compute true Velocity RMS by integrating acceleration signals with drift removal.

    Pipeline:
        1. Remove DC offset (mean subtraction)
        2. Detrend linear drift
        3. High-pass filter low-frequency integration drift (Butterworth, order 2)
        4. Time-domain cumulative trapezoidal integration (m/s^2 -> mm/s)
        5. High-pass filter velocity signal again to eliminate residual baseline wander
        6. Compute v_rms_x, v_rms_y, v_rms_z, and v_rms_total

    Returns:
        Dict containing:
            v_rms_x, v_rms_y, v_rms_z, v_rms_total (in mm/s)
    """
    def _integrate_to_velocity(arr: np.ndarray) -> float:
        if len(arr) < 8 or sampling_rate <= 0:
            return 0.0

        # Step 1: Remove DC
        acc = arr - np.mean(arr)

        # Step 2: Detrend
        acc = sp_signal.detrend(acc, type="linear")

        # Step 3: High-pass filter acceleration to suppress DC rumble
        nyquist = 0.5 * sampling_rate
        cutoff = min(hp_cutoff_hz, nyquist * 0.8)
        norm_cutoff = max(0.001, cutoff / nyquist)
        b, a = sp_signal.butter(2, norm_cutoff, btype="highpass")
        acc_filtered = sp_signal.filtfilt(b, a, acc)

        # Step 4: Integrate acceleration to velocity (m/s) -> convert to mm/s (x 1000)
        dt = 1.0 / sampling_rate
        vel = np.cumsum(acc_filtered) * dt * 1000.0

        # Step 5: High-pass velocity to prevent integration baseline wander
        vel_filtered = sp_signal.filtfilt(b, a, vel)

        # Step 6: RMS
        return float(np.sqrt(np.mean(np.square(vel_filtered))))

    arr_x = np.asarray(x, dtype=np.float64)
    arr_y = np.asarray(y, dtype=np.float64)
    arr_z = np.asarray(z, dtype=np.float64)

    v_rms_x = _integrate_to_velocity(arr_x)
    v_rms_y = _integrate_to_velocity(arr_y)
    v_rms_z = _integrate_to_velocity(arr_z)
    v_rms_total = float(np.sqrt(v_rms_x**2 + v_rms_y**2 + v_rms_z**2))

    return {
        "v_rms_x": round(v_rms_x, 4),
        "v_rms_y": round(v_rms_y, 4),
        "v_rms_z": round(v_rms_z, 4),
        "v_rms_total": round(v_rms_total, 4),
    }

