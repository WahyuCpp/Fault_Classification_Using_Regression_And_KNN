"""CSV simulation replay service coordinating background sample delivery."""
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.acquisition.csv_replay_source import CSVReplaySource
from src.services.monitoring_service import MonitoringService
from config.main_config import CLEANED_DATA_DIR, PROCESSED_DATA_DIR
from src.utils.logger import get_logger

logger = get_logger("replay_service", "acquisition.log")

class ReplayService:
    """Manages continuous dataset playback thread feeding into the MonitoringService."""

    def __init__(self, monitoring_service: MonitoringService):
        self.monitoring_service = monitoring_service
        self.source: Optional[CSVReplaySource] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()
        self.active_file_path: Optional[Path] = None

        # Autoselect initial default dataset if available
        self._select_default_dataset()

    def _select_default_dataset(self) -> None:
        """Pick an initial dataset file from processed or cleaned folders."""
        candidates = list(PROCESSED_DATA_DIR.rglob("*.csv")) or list(CLEANED_DATA_DIR.rglob("*.csv"))
        if candidates:
            # Prefer outer bearing fault or unbalance for interesting initial vibration
            preferred = [f for f in candidates if "outer" in f.name or "unbalance" in f.name]
            chosen = preferred[0] if preferred else candidates[0]
            self.load_dataset(chosen)

    def load_dataset(
        self,
        file_path: str | Path,
        playback_speed: float = 1.0,
        loop: bool = True,
    ) -> bool:
        """Load a CSV dataset for simulated replay."""
        with self._lock:
            self.stop()
            path = Path(file_path).resolve()
            if not path.exists():
                logger.error("Replay dataset file not found: %s", path)
                return False

            self.active_file_path = path
            self.source = CSVReplaySource(
                csv_file_path=path,
                playback_speed=playback_speed,
                loop=loop,
            )
            # Update monitoring service physical sampling rate to match dataset
            self.monitoring_service.sampling_rate = self.source.get_sampling_rate()
            logger.info("Loaded replay dataset: %s", path.name)
            return True

    def start(self) -> bool:
        """Start replay streaming thread."""
        with self._lock:
            if self.source is None:
                logger.warning("No dataset loaded to start replay.")
                return False

            if self._thread and self._thread.is_alive():
                self.source.resume()
                return True

            self._stop_event.clear()
            self.source.start()
            self._thread = threading.Thread(target=self._run_replay_loop, daemon=True)
            self._thread.start()
            logger.info("Started replay loop thread.")
            return True

    def pause(self) -> None:
        with self._lock:
            if self.source:
                self.source.pause()

    def resume(self) -> None:
        with self._lock:
            if self.source:
                self.source.resume()

    def stop(self) -> None:
        with self._lock:
            self._stop_event.set()
            if self.source:
                self.source.stop()
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=1.0)
            self._thread = None

    def reset(self) -> None:
        with self._lock:
            if self.source:
                self.source.reset()

    def set_speed(self, speed: float | str) -> None:
        with self._lock:
            if self.source:
                self.source.set_speed(speed)

    def set_loop(self, loop: bool) -> None:
        with self._lock:
            if self.source:
                self.source.set_loop(loop)

    def _run_replay_loop(self) -> None:
        """Replay thread loop delivering batches of samples at simulated real-time rate."""
        batch_size = 50  # Samples per emission slice

        while not self._stop_event.is_set():
            if self.source is None or not self.source.is_running or self.source.is_paused:
                time.sleep(0.05)
                continue

            # Read batch of samples
            samples = self.source.read_batch(max_samples=batch_size)
            if not samples:
                if not self.source.loop:
                    break
                time.sleep(0.02)
                continue

            # Ingest into monitoring service
            self.monitoring_service.ingest_batch(samples, fs=self.source.get_sampling_rate())

            # Sleep to match physical sampling rate and playback speed
            if not self.source.is_max_speed:
                fs = self.source.get_sampling_rate()
                nominal_delay = (len(samples) / fs) / self.source.playback_speed
                # Sleep briefly
                if nominal_delay > 0.001:
                    time.sleep(nominal_delay)

    def get_status(self) -> Dict[str, Any]:
        """Return combined status of replay source and active dataset."""
        with self._lock:
            if self.source is None:
                return {
                    "is_loaded": False,
                    "is_running": False,
                    "is_paused": False,
                    "file_name": "None",
                    "progress_percent": 0.0,
                }
            status = self.source.get_status()
            status["is_loaded"] = True
            return status

