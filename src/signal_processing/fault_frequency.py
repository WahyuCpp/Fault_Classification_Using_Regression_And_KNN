"""Rule-based preliminary fault-frequency analysis aid."""
from typing import Dict, Any, List, Optional
import numpy as np
from scipy.signal import find_peaks

from config.signal_processing_config import FAULT_FREQUENCY_CONFIG

def analyze_fault_frequencies(
    freqs: List[float],
    magnitudes: List[float],
    bearing_info: Dict[str, Any],
    electrical_info: Optional[Dict[str, Any]] = None,
    tolerance_percent: float = 3.0,
) -> Dict[str, Any]:
    """Perform rule-based preliminary fault-frequency matching against FFT spectral peaks.

    DISCLAIMER:
        This is an automated preliminary diagnostic aid, NOT a confirmed diagnosis.
        Requires validation with machine operating conditions, physical inspection,
        and machine learning classification results.

    Returns:
        Dictionary containing matched indicators, potential faults table, and disclaimer.
    """
    disclaimer = (
        "Rule-based diagnostic indication only. Requires validation with machine "
        "operating condition and ML/model results."
    )

    if not freqs or not magnitudes or len(freqs) < 16:
        return {
            "status": "Insufficient spectral data",
            "indications": [],
            "potential_faults": [],
            "disclaimer": disclaimer,
        }

    freq_arr = np.asarray(freqs)
    mag_arr = np.asarray(magnitudes)

    # Detect prominent spectral peaks
    if len(mag_arr) > 0 and np.max(mag_arr) > 0:
        prominence = max(0.01, float(np.mean(mag_arr) + 1.5 * np.std(mag_arr)))
        peak_indices, _ = find_peaks(mag_arr, height=prominence, distance=3)
        detected_peaks = [
            (float(freq_arr[idx]), float(mag_arr[idx])) for idx in peak_indices
        ]
    else:
        detected_peaks = []

    # Compile target theoretical frequencies to inspect
    targets = []
    fr = bearing_info.get("fr")
    bpfo = bearing_info.get("bpfo")
    bpfi = bearing_info.get("bpfi")
    bsf = bearing_info.get("bsf")
    ftf = bearing_info.get("ftf")

    if fr is not None:
        targets.append(("1x Shaft Frequency", fr, "Possible rotor unbalance, misalignment, looseness, or synchronous excitation."))
        targets.append(("2x Shaft Harmonic", 2.0 * fr, "Possible misalignment or mechanical/electromagnetic harmonic excitation."))
        targets.append(("3x Shaft Harmonic", 3.0 * fr, "Possible looseness, coupling defect, or harmonic excitation."))

    if bpfo is not None:
        targets.append(("BPFO (Outer Race)", bpfo, "Possible outer-race rolling element bearing defect."))
    if bpfi is not None:
        targets.append(("BPFI (Inner Race)", bpfi, "Possible inner-race rolling element bearing defect."))
    if bsf is not None:
        targets.append(("BSF (Ball Spin)", bsf, "Possible rolling-element (ball/roller) surface defect."))
    if ftf is not None:
        targets.append(("FTF (Cage)", ftf, "Possible bearing retainer/cage defect or roller slip."))

    if electrical_info and electrical_info.get("pole_pass_frequency"):
        f_pp = electrical_info["pole_pass_frequency"]
        targets.append(("Pole-Pass Frequency", f_pp, "Possible rotor bar anomaly or dynamic eccentricity sidebands."))

    indications = []
    potential_faults = []

    for name, expected_f, fault_desc in targets:
        best_match = None
        min_diff = float("inf")

        # Scan detected spectral peaks
        for det_f, det_amp in detected_peaks:
            allowed_tol = expected_f * (tolerance_percent / 100.0)
            diff = abs(det_f - expected_f)
            if diff <= allowed_tol and diff < min_diff:
                min_diff = diff
                best_match = (det_f, det_amp, diff, allowed_tol)

        if best_match is not None:
            det_f, det_amp, diff, tol = best_match
            # Confidence/strength based on amplitude relative to mean spectrum
            mean_mag = float(np.mean(mag_arr)) if len(mag_arr) > 0 else 0.01
            ratio = det_amp / max(1e-6, mean_mag)

            if ratio > 6.0:
                confidence = "High"
                status = "Strong indication"
            elif ratio > 3.0:
                confidence = "Moderate"
                status = "Moderate indication"
            else:
                confidence = "Low"
                status = "Weak/Borderline"

            indications.append({
                "component": name,
                "expected_frequency_hz": round(expected_f, 2),
                "detected_frequency_hz": round(det_f, 2),
                "measured_amplitude": round(det_amp, 4),
                "difference_hz": round(diff, 2),
                "tolerance_hz": round(tol, 2),
                "possible_fault": fault_desc,
                "confidence": confidence,
                "status": status,
            })

            potential_faults.append({
                "fault": name.split("(")[0].strip(),
                "evidence": f"Peak at {round(det_f, 1)} Hz (amp: {round(det_amp, 3)}) near expected {round(expected_f, 1)} Hz",
                "status": confidence,
                "description": fault_desc,
            })

    # If no faults detected, record normal status
    if not potential_faults:
        potential_faults.append({
            "fault": "None Detected",
            "evidence": "No significant spectral peaks within configured tolerance bands",
            "status": "Nominal",
            "description": "Baseline spectral vibration levels within acceptable tolerances.",
        })

    return {
        "status": "Evaluated",
        "tolerance_percent": tolerance_percent,
        "indications": indications,
        "potential_faults": potential_faults,
        "disclaimer": disclaimer,
    }

