"""Motor thermal condition monitoring module."""
from typing import Dict, Any, List, Union, Optional
import numpy as np

from config.threshold_config import TEMPERATURE_LIMITS

class TemperatureMonitor:
    """Monitors motor casing / winding temperature trends and alarm levels."""

    def __init__(self, limits: Optional[Dict[str, float]] = None):
        self.limits = limits or TEMPERATURE_LIMITS

    def evaluate(
        self,
        temperature_samples: Union[List[float], np.ndarray],
    ) -> Dict[str, Any]:
        """Evaluate latest temperature and rate-of-rise trend against thresholds.

        Args:
            temperature_samples: Buffer of temperature measurements (Celsius).

        Returns:
            Dictionary with latest_temperature, trend_rate, status, is_warning, and messages.
        """
        arr = np.asarray(temperature_samples, dtype=np.float64)
        if len(arr) == 0:
            return {
                "latest_temperature": 0.0,
                "status": "Nominal",
                "is_warning": False,
                "message": "No temperature data available",
            }

        latest = float(arr[-1])
        warning_limit = self.limits.get("warning_limit", 70.0)
        critical_limit = self.limits.get("critical_limit", 85.0)

        # Calculate simple rate of change
        rate_of_rise = 0.0
        if len(arr) >= 10:
            rate_of_rise = float(arr[-1] - arr[-10])

        is_warning = False
        is_critical = False
        status = "Nominal"
        msg = "Casing temperature within normal range"

        if latest >= critical_limit:
            is_warning = True
            is_critical = True
            status = "Critical Overheating"
            msg = f"Critical casing temperature ({latest:.1f} °C >= {critical_limit} °C)"
        elif latest >= warning_limit:
            is_warning = True
            status = "Warning"
            msg = (
                f"Elevated temperature ({latest:.1f} °C >= {warning_limit} °C). "
                "(Prototype threshold; verify against insulation class rating)"
            )

        return {
            "latest_temperature": round(latest, 1),
            "rate_of_rise_deg": round(rate_of_rise, 2),
            "status": status,
            "is_warning": is_warning,
            "is_critical": is_critical,
            "warning_limit": warning_limit,
            "critical_limit": critical_limit,
            "message": msg,
        }

