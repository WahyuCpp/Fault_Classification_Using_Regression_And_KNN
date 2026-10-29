"""Fast Fourier Transform (FFT) continuous spectral analysis."""
from typing import Dict, Any, Union, List, Optional
import numpy as np
from scipy import signal as sp_signal

from src.signal_processing.windowing import apply_window_function, get_window

def compute_fft(
    x: Union[np.ndarray, List[float]],
    y: Union[np.ndarray, List[float]],
    z: Union[np.ndarray, List[float]],
    sampling_rate: float = 1500.0,
    window_size: int = 1024,
    window_func: str = "hann",
    detrend: bool = True,
) -> Dict[str, Any]:
    """Compute one-sided Fast Fourier Transform spectra for 3-axis vibration signals.

    Steps:
        1. Extract the latest contiguous window of size N.
        2. Remove DC component (mean subtraction).
        3. Detrend linear components.
        4. Apply selected mathematical window function (Hann, Hamming, etc.).
        5. Compute real FFT using np.fft.rfft() and frequencies with np.fft.rfftfreq().
        6. Apply one-sided magnitude normalization:
           - DC and Nyquist: |X[k]| / N
           - All other bins: 2 * |X[k]| / N
        7. Compute frequency resolution: delta_f = fs / N, and Nyquist: fs / 2.

    Returns:
        Dictionary containing:
            frequency: List[float]
            magnitude_x: List[float]
            magnitude_y: List[float]
            magnitude_z: List[float]
            sampling_rate: float
            window_size: int
            nyquist_frequency: float
            frequency_resolution: float
    """
    fs = float(sampling_rate) if sampling_rate > 0 else 1500.0
    N = int(window_size)

    # 1. Extract windows
    win_x = get_window(x, N)
    win_y = get_window(y, N)
    win_z = get_window(z, N)

    actual_len = min(len(win_x), len(win_y), len(win_z))
    if actual_len < 16:
        # Insufficient data
        return {
            "frequency": [],
            "magnitude_x": [],
            "magnitude_y": [],
            "magnitude_z": [],
            "sampling_rate": fs,
            "window_size": N,
            "nyquist_frequency": fs / 2.0,
            "frequency_resolution": round(fs / N, 4),
            "status": "Insufficient Data",
        }

    # Slice to actual matching length
    win_x = win_x[-actual_len:]
    win_y = win_y[-actual_len:]
    win_z = win_z[-actual_len:]
    N_eff = actual_len

    # Frequency vector
    freqs = np.fft.rfftfreq(N_eff, d=1.0 / fs)

    def _process_axis(sig: np.ndarray) -> np.ndarray:
        # 2. Remove DC
        sig_no_dc = sig - np.mean(sig)

        # 3. Detrend
        if detrend and len(sig_no_dc) > 4:
            sig_dt = sp_signal.detrend(sig_no_dc, type="linear")
        else:
            sig_dt = sig_no_dc

        # 4. Window function
        sig_win = apply_window_function(sig_dt, window_type=window_func)

        # 5. Real FFT
        fft_complex = np.fft.rfft(sig_win)

        # 6. Correct one-sided magnitude normalization
        # Multiply interior frequencies by 2/N, DC and Nyquist by 1/N
        mag = (2.0 / N_eff) * np.abs(fft_complex)
        if len(mag) > 0:
            mag[0] = mag[0] / 2.0  # DC
            if N_eff % 2 == 0 and len(mag) > 1:
                mag[-1] = mag[-1] / 2.0  # Nyquist
        return mag

    mag_x = _process_axis(win_x)
    mag_y = _process_axis(win_y)
    mag_z = _process_axis(win_z)

    delta_f = fs / float(N_eff)
    nyquist = fs / 2.0

    return {
        "frequency": freqs.tolist(),
        "magnitude_x": mag_x.tolist(),
        "magnitude_y": mag_y.tolist(),
        "magnitude_z": mag_z.tolist(),
        "sampling_rate": fs,
        "window_size": N_eff,
        "nyquist_frequency": round(nyquist, 2),
        "frequency_resolution": round(delta_f, 4),
        "status": "OK",
    }

