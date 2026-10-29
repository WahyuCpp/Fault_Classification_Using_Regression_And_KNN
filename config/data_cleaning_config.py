"""Data cleaning and dataset schema configuration."""
from pathlib import Path
from config.main_config import CLEANED_DATA_DIR, PROCESSED_DATA_DIR

DATA_PATH = str(CLEANED_DATA_DIR)
PROCESSED_PATH = str(PROCESSED_DATA_DIR)

# Condition subfolder-to-code mapping
MOTOR_CONDITION_LABELS = {
    "healthy": "A",
    "outer_bearing_fault": "OB",
    "inner_bearing_fault": "IB",
    "ball_bearing_fault": "BB",
    "unbalance": "UNB",
    "misalignment": "MIS",
}

# Reverse mapping for human readable labels
LABEL_TO_CONDITION = {v: k for k, v in MOTOR_CONDITION_LABELS.items()}

# Expected final columns in order
EXPECTED_COLUMNS = [
    "timestamp",
    "x",
    "y",
    "z",
    "current",
    "temperature",
    "rpm",
    "fault_label",
]

# Minimum required columns when RPM is unavailable
REQUIRED_MIN_COLUMNS = [
    "timestamp",
    "x",
    "y",
    "z",
    "current",
    "temperature",
    "fault_label",
]

# Column alias dictionary for uniforming diverse naming conventions
COLUMN_ALIASES = {
    "time": "timestamp",
    "Time": "timestamp",
    "TIMESTAMP": "timestamp",
    "date_time": "timestamp",
    "datetime": "timestamp",
    "X": "x",
    "acc_x": "x",
    "accel_x": "x",
    "acceleration_x": "x",
    "Y": "y",
    "acc_y": "y",
    "accel_y": "y",
    "acceleration_y": "y",
    "Z": "z",
    "acc_z": "z",
    "accel_z": "z",
    "acceleration_z": "z",
    "Current": "current",
    "current_a": "current",
    "Current_A": "current",
    "i": "current",
    "Temp": "temperature",
    "temp": "temperature",
    "Temperature": "temperature",
    "temperature_c": "temperature",
    "RPM": "rpm",
    "speed": "rpm",
    "speed_rpm": "rpm",
    "label": "fault_label",
    "class": "fault_label",
    "Fault_Label": "fault_label",
}

# Configurable outlier bounds and detection methods
# Using MAD (Median Absolute Deviation) robust z-score as preferred approach for vibration
OUTLIER_CONFIG = {
    "acceleration": {
        "method": "mad",
        "threshold": 4.5,
        "columns": ["x", "y", "z"],
    },
    "current": {
        "method": "engineering_range",
        "min_val": 0.0,
        "max_val": 30.0,
        "columns": ["current"],
    },
    "temperature": {
        "method": "engineering_range",
        "min_val": 0.0,
        "max_val": 130.0,
        "columns": ["temperature"],
    },
    "rpm": {
        "method": "engineering_range",
        "min_val": 0.0,
        "max_val": 4000.0,
        "columns": ["rpm"],
    },
}

