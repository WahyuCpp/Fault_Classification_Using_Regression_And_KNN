"""Window extraction and FFT windowing function generation."""
from typing import List, Union
import numpy as np
from scipy import signal as sp_signal

from config.signal_processing_config import (
    WINDOW_SIZES,
    DEFAULT_WINDOW_SIZE,
    FFT_WINDOW_FUNCTIONS,
    DEFAULT_FFT_WINDOW,
)

def get_window(
    buffer_data: Union[np.ndarray, List[float]],
    size: int = DEFAULT_WINDOW_SIZE,
) -> np.ndarray:
    """Extract the latest contiguous window of samples from a circular or linear buffer.

    Args:
        buffer_data: Sequential signal array or buffer.
        size: Window length in sample count (must be in WINDOW_SIZES: 256, 512, 1024, 2048).

    Returns:
        1D numpy array of length `min(len(buffer), size)`.
    """
    arr = np.asarray(buffer_data, dtype=np.float64)
    if len(arr) == 0:
        return np.array([], dtype=np.float64)

    if size not in WINDOW_SIZES:
        # Fall back to nearest valid window size
        size = min(WINDOW_SIZES, key=lambda s: abs(s - size))

    if len(arr) <= size:
        return arr.copy()
    return arr[-size:].copy()


def apply_window_function(
    signal_segment: np.ndarray,
    window_type: str = DEFAULT_FFT_WINDOW,
) -> np.ndarray:
    """Apply the specified mathematical window function to a signal segment.

    Supported: 'hann', 'hamming', 'blackman', 'rectangular'.
    """
    n = len(signal_segment)
    if n == 0:
        return signal_segment

    w_type = window_type.lower()
    if w_type == "hann":
        win = np.hanning(n)
    elif w_type == "hamming":
        win = np.hamming(n)
    elif w_type == "blackman":
        win = np.blackman(n)
    elif w_type in ("rectangular", "boxcar", "none"):
        win = np.ones(n)
    else:
        win = np.hanning(n)

    # Coherent gain normalization factor to preserve peak amplitude
    coherent_gain = np.mean(win)
    if coherent_gain > 0:
        win = win / coherent_gain

    return signal_segment * win

