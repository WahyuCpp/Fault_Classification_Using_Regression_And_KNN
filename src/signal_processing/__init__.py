"""Signal processing package for MONTREAL-VT."""
from src.signal_processing.windowing import get_window, apply_window_function
from src.signal_processing.v_rms import compute_acceleration_rms, compute_velocity_rms
from src.signal_processing.fft_analysis import compute_fft
from src.signal_processing.bearing_frequency import (
    calculate_rotational_frequency,
    calculate_bearing_frequencies,
    calculate_electrical_frequencies,
)
from src.signal_processing.fault_frequency import analyze_fault_frequencies
from src.signal_processing.severity import classify_vibration_severity

__all__ = [
    "get_window",
    "apply_window_function",
    "compute_acceleration_rms",
    "compute_velocity_rms",
    "compute_fft",
    "calculate_rotational_frequency",
    "calculate_bearing_frequencies",
    "calculate_electrical_frequencies",
    "analyze_fault_frequencies",
    "classify_vibration_severity",
]

