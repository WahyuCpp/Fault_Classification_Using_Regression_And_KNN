"""Motor electrical winding/current monitoring module."""
from typing import Dict, Any, List, Union, Optional
import numpy as np

from config.threshold_config import CURRENT_LIMITS

class CurrentMonitor:
    """Monitors motor line/winding current waveforms, moving RMS, and alarm thresholds."""

    def __init__(self, limits: Optional[Dict[str, float]] = None):
        self.limits = limits or CURRENT_LIMITS

    def evaluate(
        self,
        current_samples: Union[List[float], np.ndarray],
        machine_state: str = "RUNNING",
    ) -> Dict[str, Any]:
        """Compute moving current statistics and warning status based on machine operating state.

        Args:
            current_samples: Buffer of recent current measurements (Amperes).
            machine_state: 'STOPPED', 'STARTING', 'RUNNING', or 'WARNING'.

        Returns:
            Dictionary containing latest_current, moving_rms, state, status, and alert message.
        """
        arr = np.asarray(current_samples, dtype=np.float64)
        if len(arr) == 0:
            return {
                "latest_current": 0.0,
                "moving_rms": 0.0,
                "status": "Nominal",
                "is_warning": False,
                "message": "No current data received",
            }

        latest = float(arr[-1])
        moving_rms = float(np.sqrt(np.mean(np.square(arr))))

        running_limit = self.limits.get("normal_running_warning", 0.5)
        starting_limit = self.limits.get("starting_inrush_max", 5.0)

        is_warning = False
        status = "Nominal"
        msg = "Current within normal limits"

        if machine_state == "STARTING":
            if latest > starting_limit:
                is_warning = True
                status = "Warning"
                msg = f"Starting inrush exceeded allowable threshold ({latest:.2f} A > {starting_limit} A)"
            else:
                status = "Starting Inrush"
                msg = f"Motor inrush transient active ({latest:.2f} A)"
        elif machine_state == "RUNNING":
            if latest > running_limit:
                is_warning = True
                status = "Warning"
                msg = (
                    f"Running current ({latest:.2f} A) exceeded demonstration threshold ({running_limit} A). "
                    "(Note: test/demo threshold; calibrate to motor nameplate)"
                )
        elif machine_state == "STOPPED":
            if latest > self.limits.get("stopped_current_max", 0.1):
                status = "Notice"
                msg = f"Residual current detected while stopped ({latest:.2f} A)"

        return {
            "latest_current": round(latest, 3),
            "moving_rms": round(moving_rms, 3),
            "status": status,
            "is_warning": is_warning,
            "threshold_used": running_limit if machine_state == "RUNNING" else starting_limit,
            "message": msg,
        }

