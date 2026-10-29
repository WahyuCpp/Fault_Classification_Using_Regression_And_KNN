"""CSV dataset replay data source for simulated real-time monitoring."""
import time
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np

from src.acquisition.base_source import DataSource
from config.main_config import DEFAULT_SAMPLING_RATE, MACHINE_CONFIG
from src.utils.logger import get_logger

logger = get_logger("csv_replay", "acquisition.log")

class CSVReplaySource(DataSource):
    """Replays previously recorded CSV datasets to emulate continuous sensor streams."""

    def __init__(
        self,
        csv_file_path: str | Path,
        sampling_rate: Optional[float] = None,
        playback_speed: float = 1.0,
        loop: bool = True,
        machine_id: Optional[str] = None,
    ):
        self.file_path = Path(csv_file_path).resolve()
        if not self.file_path.exists():
            raise FileNotFoundError(f"Replay file not found: {self.file_path}")

        self.machine_id = machine_id or MACHINE_CONFIG["machine_id"]
        self.loop = loop
        self.playback_speed = max(0.1, playback_speed)
        self.is_max_speed = False

        # Load CSV once into memory buffer
        self._df = pd.read_csv(self.file_path)
        self._total_rows = len(self._df)
        self._current_idx = 0

        # Physical sampling rate (remains independent of playback speed for accurate FFT)
        self.sampling_rate = sampling_rate or self._detect_sampling_rate()
        self._expected_interval_sec = 1.0 / self.sampling_rate

        # Acquisition control
        self.is_running = False
        self.is_paused = False
        self._lock = threading.RLock()

        # Sampling integrity tracking
        self.samples_emitted = 0
        self.dropped_samples = 0
        self.late_samples = 0
        self._last_emission_time: Optional[float] = None

        logger.info(
            "Initialized CSVReplaySource: %s (%d rows, fs=%.1f Hz, speed=%.1fx, loop=%s)",
            self.file_path.name,
            self._total_rows,
            self.sampling_rate,
            self.playback_speed,
            self.loop,
        )

    def _detect_sampling_rate(self) -> float:
        """Infer sampling rate from timestamp or seconds columns, or return default."""
        for col in ["seconds", "sec"]:
            if col in self._df.columns:
                diffs = self._df[col].diff().dropna()
                pos = diffs[diffs > 0]
                if len(pos) > 0:
                    dt = pos.median()
                    if dt > 0:
                        return float(round(1.0 / dt, 1))

        if "timestamp" in self._df.columns and len(self._df) > 1:
            try:
                ts = pd.to_datetime(self._df["timestamp"].iloc[:100], errors="coerce")
                diffs = ts.diff().dt.total_seconds().dropna()
                pos = diffs[diffs > 0]
                if len(pos) > 0:
                    dt = pos.median()
                    if dt > 0:
                        return float(round(1.0 / dt, 1))
            except Exception:
                pass

        return DEFAULT_SAMPLING_RATE

    def set_speed(self, speed: float | str) -> None:
        """Set playback speed multiplier (0.5, 1.0, 2.0, or 'max')."""
        with self._lock:
            if isinstance(speed, str) and speed.lower() == "max":
                self.is_max_speed = True
                self.playback_speed = 100.0
            else:
                self.is_max_speed = False
                self.playback_speed = float(speed)
        logger.info("Replay speed updated: %.1fx (max=%s)", self.playback_speed, self.is_max_speed)

    def set_loop(self, loop: bool) -> None:
        """Configure whether replay loops when reaching end of file."""
        with self._lock:
            self.loop = loop

    def start(self) -> None:
        with self._lock:
            self.is_running = True
            self.is_paused = False
            self._last_emission_time = time.perf_counter()

    def pause(self) -> None:
        with self._lock:
            self.is_paused = True

    def resume(self) -> None:
        with self._lock:
            self.is_paused = False
            self._last_emission_time = time.perf_counter()

    def stop(self) -> None:
        with self._lock:
            self.is_running = False
            self.is_paused = False

    def reset(self) -> None:
        with self._lock:
            self._current_idx = 0
            self.samples_emitted = 0
            self.dropped_samples = 0
            self.late_samples = 0
            self._last_emission_time = time.perf_counter()

    def read_sample(self) -> Optional[Dict[str, Any]]:
        """Read the next sequential sample with timing integrity checks."""
        with self._lock:
            if not self.is_running or self.is_paused:
                return None

            if self._current_idx >= self._total_rows:
                if self.loop:
                    self._current_idx = 0
                    logger.debug("Replay reached EOF. Looping to beginning.")
                else:
                    self.is_running = False
                    logger.info("Replay reached EOF. Stopping.")
                    return None

            row = self._df.iloc[self._current_idx]
            self._current_idx += 1

            # Integrity metrics
            now = time.perf_counter()
            if self._last_emission_time is not None and not self.is_max_speed:
                actual_interval = now - self._last_emission_time
                target_interval = self._expected_interval_sec / self.playback_speed
                if actual_interval > target_interval * 1.5:
                    self.late_samples += 1
            self._last_emission_time = now
            self.samples_emitted += 1

            sample = {
                "source_file": self.file_path.name,
                "machine_id": self.machine_id,
                "timestamp": str(row.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))),
                "x": float(row.get("x", 0.0)),
                "y": float(row.get("y", 0.0)),
                "z": float(row.get("z", 0.0)),
                "current": float(row.get("current", 0.42)),
                "temperature": float(row.get("temperature", 43.2)),
                "rpm": float(row["rpm"]) if "rpm" in row and pd.notna(row["rpm"]) else None,
                "fault_label": str(row.get("fault_label", "A")),
            }
            return sample

    def read_batch(self, max_samples: int = 100) -> List[Dict[str, Any]]:
        """Read a batch of available samples."""
        batch = []
        for _ in range(max_samples):
            sample = self.read_sample()
            if sample is None:
                break
            batch.append(sample)
        return batch

    def get_sampling_rate(self) -> float:
        return self.sampling_rate

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            progress_pct = round((self._current_idx / max(1, self._total_rows)) * 100.0, 1)
            return {
                "source_type": "CSVReplaySource",
                "file_name": self.file_path.name,
                "is_running": self.is_running,
                "is_paused": self.is_paused,
                "loop": self.loop,
                "playback_speed": self.playback_speed,
                "is_max_speed": self.is_max_speed,
                "current_index": self._current_idx,
                "total_rows": self._total_rows,
                "progress_percent": progress_pct,
                "sampling_rate_hz": self.sampling_rate,
                "samples_emitted": self.samples_emitted,
                "late_samples": self.late_samples,
                "dropped_samples": self.dropped_samples,
                "data_quality_percent": round(
                    max(0.0, 100.0 - (self.late_samples / max(1, self.samples_emitted) * 100.0)), 1
                ),
            }

