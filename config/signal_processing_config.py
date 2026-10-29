"""Signal processing configuration: windowing, FFT, and bearing frequencies."""

# Selectable processing window sizes in sample counts (not bits)
WINDOW_SIZES = [256, 512, 1024, 2048]
DEFAULT_WINDOW_SIZE = 1024

# FFT windowing functions
FFT_WINDOW_FUNCTIONS = ["hann", "hamming", "blackman", "rectangular"]
DEFAULT_FFT_WINDOW = "hann"

# Size of the in-memory display ring buffer
DISPLAY_BUFFER_SIZE = 2048

# Bearing geometry configuration (e.g., standard 6205-2RS deep groove ball bearing)
# Nb: number of rolling elements
# Bd: ball diameter (mm)
# Pd: pitch diameter (mm)
# contact_angle_deg: contact angle (degrees, typically 0 for radial ball bearings)
BEARING_CONFIG = {
    "model": "6205-2RS",
    "number_of_rolling_elements": 9,  # Nb
    "ball_diameter": 7.94,            # Bd (mm)
    "pitch_diameter": 39.04,          # Pd (mm)
    "contact_angle_deg": 0.0,         # theta
}

# Motor electrical configuration
ELECTRICAL_CONFIG = {
    "supply_frequency": 50.0,  # Hz (mains supply frequency f_s)
    "number_of_poles": 4,      # 2p = 4 poles -> pole pairs p = 2
}

# Preliminary rule-based fault detection tolerance
FAULT_FREQUENCY_CONFIG = {
    "frequency_tolerance_percent": 3.0,  # 3% tolerance band
    "min_prominence_db": 6.0,            # spectral peak prominence
}

