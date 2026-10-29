"""Bearing and induction motor characteristic frequency calculator."""
from typing import Dict, Any, Optional
import numpy as np

from config.signal_processing_config import BEARING_CONFIG, ELECTRICAL_CONFIG

def calculate_rotational_frequency(rpm: Optional[float]) -> Optional[float]:
    """Calculate shaft fundamental rotational frequency (1X) from RPM."""
    if rpm is None or rpm <= 0:
        return None
    return float(rpm / 60.0)


def calculate_bearing_frequencies(
    rpm: Optional[float],
    bearing_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Calculate theoretical rolling-element bearing characteristic defect frequencies.

    Formulas:
        f_r = RPM / 60
        BPFO = (Nb / 2) * f_r * (1 - (Bd / Pd) * cos(theta))
        BPFI = (Nb / 2) * f_r * (1 + (Bd / Pd) * cos(theta))
        FTF  = (f_r / 2) * (1 - (Bd / Pd) * cos(theta))
        BSF  = (Pd / (2 * Bd)) * f_r * [1 - ((Bd / Pd) * cos(theta))^2]

    Returns:
        Dictionary with theoretical frequencies and metadata.
    """
    if rpm is None or rpm <= 0:
        return {
            "status": "Unavailable — motor rotational speed (RPM) required",
            "fr": None,
            "bpfo": None,
            "bpfi": None,
            "bsf": None,
            "ftf": None,
            "note": "Theoretical characteristic frequencies require valid RPM.",
        }

    cfg = bearing_params or BEARING_CONFIG
    Nb = cfg.get("number_of_rolling_elements")
    Bd = cfg.get("ball_diameter")
    Pd = cfg.get("pitch_diameter")
    theta_deg = cfg.get("contact_angle_deg", 0.0)

    if not all([Nb, Bd, Pd]) or Pd <= 0 or Bd <= 0:
        return {
            "status": "Unavailable — valid bearing geometry parameters required",
            "fr": round(rpm / 60.0, 2),
            "bpfo": None,
            "bpfi": None,
            "bsf": None,
            "ftf": None,
            "note": "Bearing parameters incomplete.",
        }

    fr = float(rpm / 60.0)
    theta = np.deg2rad(theta_deg)
    gamma = (Bd / Pd) * np.cos(theta)

    bpfo = (Nb / 2.0) * fr * (1.0 - gamma)
    bpfi = (Nb / 2.0) * fr * (1.0 + gamma)
    ftf = (fr / 2.0) * (1.0 - gamma)
    bsf = (Pd / (2.0 * Bd)) * fr * (1.0 - gamma**2)

    return {
        "status": "Calculated (Theoretical)",
        "fr": round(fr, 2),
        "bpfo": round(bpfo, 2),
        "bpfi": round(bpfi, 2),
        "bsf": round(bsf, 2),
        "ftf": round(ftf, 2),
        "harmonics": {
            "1x": round(fr, 2),
            "2x": round(2.0 * fr, 2),
            "3x": round(3.0 * fr, 2),
            "2x_bpfo": round(2.0 * bpfo, 2),
            "2x_bpfi": round(2.0 * bpfi, 2),
        },
        "model": cfg.get("model", "Custom Bearing"),
        "note": "Calculated theoretical characteristic frequencies based on kinematic equations.",
    }


def calculate_electrical_frequencies(
    rpm: Optional[float],
    electrical_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Calculate induction motor electrical frequencies (synchronous speed, slip, pole-pass).

    Formulas:
        Synchronous speed n_sync = 120 * f_supply / poles (RPM)
        Slip s = (n_sync - RPM) / n_sync
        Slip frequency f_slip = s * f_supply
        Pole-pass frequency f_pp = 2 * p * f_slip (where p = poles / 2)

    Returns:
        Dictionary of electrical frequencies or explicit 'Unavailable' status.
    """
    cfg = electrical_params or ELECTRICAL_CONFIG
    supply_freq = cfg.get("supply_frequency")
    poles = cfg.get("number_of_poles")

    if not supply_freq or not poles or poles <= 0:
        return {
            "status": "Unavailable — motor electrical parameters required",
            "pole_pass_frequency": None,
            "slip": None,
            "synchronous_speed_rpm": None,
        }

    if rpm is None or rpm <= 0:
        return {
            "status": "Unavailable — motor rotational speed (RPM) required",
            "pole_pass_frequency": None,
            "slip": None,
            "synchronous_speed_rpm": None,
        }

    pole_pairs = poles / 2.0
    sync_rpm = (120.0 * supply_freq) / poles
    slip = (sync_rpm - rpm) / sync_rpm
    slip_freq = slip * supply_freq
    pole_pass_freq = 2.0 * pole_pairs * slip_freq

    return {
        "status": "Calculated (Theoretical)",
        "supply_frequency": supply_freq,
        "poles": poles,
        "synchronous_speed_rpm": round(sync_rpm, 1),
        "slip": round(slip, 4),
        "slip_frequency": round(slip_freq, 2),
        "pole_pass_frequency": round(pole_pass_freq, 2),
        "note": "Theoretical electrical induction-motor calculations.",
    }

