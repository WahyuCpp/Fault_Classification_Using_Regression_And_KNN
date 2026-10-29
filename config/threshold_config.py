"""Threshold and operating state configuration."""

# Machine operating states
MACHINE_STATES = ["STOPPED", "STARTING", "RUNNING", "WARNING"]

# Duration (seconds) for motor inrush current before switching to running checks
STARTING_DURATION_SECONDS = 3.0

# Current thresholds (Amperes)
# Note: normal_running_warning = 0.5A is a prototype/demonstration default
CURRENT_LIMITS = {
    "stopped_current_max": 0.1,         # Below this, motor considered stopped
    "normal_running_warning": 0.5,      # Test/demo threshold
    "starting_inrush_max": 5.0,         # Maximum allowable starting current
    "critical_running_max": 8.0,        # Critical overcurrent trip
}

# Temperature thresholds (Degrees Celsius)
# Note: 70 C is a prototype/demonstration casing temperature limit
TEMPERATURE_LIMITS = {
    "normal_max": 65.0,
    "warning_limit": 70.0,              # Test/demo warning threshold
    "critical_limit": 85.0,             # Critical shutdown threshold
}

# Vibration Severity thresholds (ISO 10816 / 13373 guidance for Class I/II machines)
# Values represent resultant vibration RMS in m/s^2 (or mm/s if integrated)
# These are configurable guidelines, not universal absolutes
VIBRATION_SEVERITY_LIMITS = {
    "zone_a_good": 1.12,                # Up to 1.12: Good / newly commissioned
    "zone_b_satisfactory": 2.80,        # 1.12 - 2.80: Satisfactory for continuous operation
    "zone_c_unsatisfactory": 4.50,      # 2.80 - 4.50: Unsatisfactory / restricted operation
    "zone_d_unacceptable": 4.50,        # > 4.50: Unacceptable / damage risk
}

