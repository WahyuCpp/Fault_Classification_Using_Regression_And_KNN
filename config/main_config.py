"""Main configuration for MONTREAL-VT Motor Condition Monitoring System."""
from pathlib import Path
import os

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Core directories
DATA_DIR = BASE_DIR / "data"
CLEANED_DATA_DIR = DATA_DIR / "cleaned_data"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
READING_DATA_DIR = DATA_DIR / "reading"
TRAINING_DATA_DIR = DATA_DIR / "training"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

# Ensure runtime directories exist
for directory in [
    DATA_DIR,
    CLEANED_DATA_DIR,
    PROCESSED_DATA_DIR,
    READING_DATA_DIR,
    TRAINING_DATA_DIR,
    MODELS_DIR,
    LOGS_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)

# Application runtime mode
# When True, replays CSV without requiring physical ESP32 or sensors
DEMO_MODE = os.getenv("DEMO_MODE", "True").lower() in ("true", "1", "yes")

# Default physical sampling rate (Hz) for accelerometer readings
DEFAULT_SAMPLING_RATE = 1500.0

# Induction Motor Nameplate / Bench Metadata
MACHINE_CONFIG = {
    "machine_id": "MOTOR_001",
    "machine_name": "MONTREAL-VT Induction Motor Test Bench",
    "rated_power_kw": 0.75,
    "rated_voltage_v": 230.0,
    "rated_current_a": 3.2,
    "rated_frequency_hz": 50.0,
    "rated_speed_rpm": 1450.0,
    "number_of_poles": 4,
    "bearing_model": "6205-2RS",
}

