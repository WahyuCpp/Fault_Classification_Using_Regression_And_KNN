"""Operating state machine and integrated multi-parameter threshold evaluation."""
import time
from typing import Dict, Any, Optional

from config.threshold_config import (
    MACHINE_STATES,
    STARTING_DURATION_SECONDS,
    CURRENT_LIMITS,
    TEMPERATURE_LIMITS,
    VIBRATION_SEVERITY_LIMITS,
)
from src.condition_monitoring.current_monitor import CurrentMonitor
from src.condition_monitoring.temperature_monitor import TemperatureMonitor
from src.signal_processing.severity import classify_vibration_severity

class MachineStateManager:
    """Tracks machine operational state (STOPPED, STARTING, RUNNING, WARNING)

    and orchestrates condition monitoring thresholds.
    """

    def __init__(
        self,
        starting_duration_sec: float = STARTING_DURATION_SECONDS,
        current_limits: Optional[Dict[str, float]] = None,
        temp_limits: Optional[Dict[str, float]] = None,
    ):
        self.starting_duration_sec = starting_duration_sec
        self.current_monitor = CurrentMonitor(current_limits)
        self.temp_monitor = TemperatureMonitor(temp_limits)

        self.current_state = "RUNNING"
        self._state_transition_time = time.time()
        self._previous_current = 0.0

    def update_state(self, current: float, rpm: Optional[float] = None) -> str:
        """Infer machine state transition based on current, speed, and elapsed time."""
        now = time.time()
        stopped_limit = CURRENT_LIMITS.get("stopped_current_max", 0.1)

        if current < stopped_limit and (rpm is None or rpm < 50.0):
            if self.current_state != "STOPPED":
                self.current_state = "STOPPED"
                self._state_transition_time = now
        elif self.current_state == "STOPPED" and current >= stopped_limit:
            # Motor just started
            self.current_state = "STARTING"
            self._state_transition_time = now
        elif self.current_state == "STARTING":
            # Transition from STARTING to RUNNING after starting inrush duration
            if (now - self._state_transition_time) >= self.starting_duration_sec:
                self.current_state = "RUNNING"
                self._state_transition_time = now

        self._previous_current = current
        return self.current_state

    def evaluate_condition(
        self,
        current_samples: list,
        temperature_samples: list,
        total_rms: float,
        rpm: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Perform unified condition evaluation across electrical, thermal, and mechanical parameters."""
        latest_curr = float(current_samples[-1]) if current_samples else 0.0
        state = self.update_state(latest_curr, rpm)

        current_eval = self.current_monitor.evaluate(current_samples, machine_state=state)
        temp_eval = self.temp_monitor.evaluate(temperature_samples)
        vib_eval = classify_vibration_severity(total_rms)

        # Determine overall alarm status
        active_warnings = []
        if current_eval["is_warning"]:
            active_warnings.append(f"Current: {current_eval['message']}")
        if temp_eval["is_warning"]:
            active_warnings.append(f"Temperature: {temp_eval['message']}")
        if vib_eval["severity"] in ("Unsatisfactory", "Unacceptable"):
            active_warnings.append(f"Vibration: {vib_eval['description']}")

        if active_warnings and state == "RUNNING":
            overall_state = "WARNING"
        else:
            overall_state = state

        return {
            "machine_state": overall_state,
            "current_eval": current_eval,
            "temperature_eval": temp_eval,
            "vibration_eval": vib_eval,
            "active_warnings": active_warnings,
            "is_alarm_active": len(active_warnings) > 0,
        }

