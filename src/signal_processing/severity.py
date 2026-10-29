"""Vibration severity classification module based on ISO 10816/13373 guidelines."""
from typing import Dict, Any, Optional
from config.threshold_config import VIBRATION_SEVERITY_LIMITS

def classify_vibration_severity(
    total_rms: float,
    thresholds: Optional[Dict[str, float]] = None,
    machine_description: str = "Medium Induction Motor (rigidly mounted)",
) -> Dict[str, Any]:
    """Classify overall vibration severity into standardized ISO zones.

    Zones:
        Zone A: Good (newly commissioned machines)
        Zone B: Satisfactory (unrestricted long-term operation)
        Zone C: Unsatisfactory (restricted operation until maintenance)
        Zone D: Unacceptable (danger of catastrophic damage)

    Returns:
        Dictionary with zone, severity level, color indicator, and disclaimer.
    """
    cfg = thresholds or VIBRATION_SEVERITY_LIMITS
    zone_a = cfg.get("zone_a_good", 1.12)
    zone_b = cfg.get("zone_b_satisfactory", 2.80)
    zone_c = cfg.get("zone_c_unsatisfactory", 4.50)

    val = float(total_rms)

    if val <= zone_a:
        zone = "Zone A"
        severity = "Good"
        color = "#28a745"  # Green
        description = "Vibration of newly commissioned machines in optimal balance."
    elif val <= zone_b:
        zone = "Zone B"
        severity = "Satisfactory"
        color = "#17a2b8"  # Teal/Blue
        description = "Vibration normally considered acceptable for unrestricted long-term operation."
    elif val <= zone_c:
        zone = "Zone C"
        severity = "Unsatisfactory"
        color = "#ffc107"  # Yellow
        description = "Vibration unsatisfactory for continuous operation; investigate at next maintenance."
    else:
        zone = "Zone D"
        severity = "Unacceptable"
        color = "#dc3545"  # Red
        description = "Vibration severity dangerous; machine requires immediate corrective action."

    return {
        "rms_value": round(val, 4),
        "zone": zone,
        "severity": severity,
        "color": color,
        "description": description,
        "machine_type": machine_description,
        "thresholds_used": {
            "good_limit": zone_a,
            "satisfactory_limit": zone_b,
            "unsatisfactory_limit": zone_c,
        },
        "disclaimer": (
            "ISO 10816 / 13373 guidance limits depend on machine foundation, power rating, "
            "and mounting. Thresholds are configurable engineering recommendations."
        ),
    }

