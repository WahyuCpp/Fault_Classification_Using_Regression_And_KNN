"""Real-time monitoring service coordinating ring buffer, DB queue, and DSP."""
import threading
import queue
import time
from collections import deque
from typing import Dict, Any, List, Optional

import numpy as np

from config.signal_processing_config import (
    WINDOW_SIZES,
    DEFAULT_WINDOW_SIZE,
    DEFAULT_FFT_WINDOW,
    DISPLAY_BUFFER_SIZE,
    BEARING_CONFIG,
    ELECTRICAL_CONFIG,
    FAULT_FREQUENCY_CONFIG,
)
from config.database_config import DATABASE_BATCH_SIZE
from src.signal_processing.windowing import get_window
from src.signal_processing.v_rms import compute_acceleration_rms, compute_velocity_rms
from src.signal_processing.fft_analysis import compute_fft
from src.signal_processing.bearing_frequency import (
    calculate_bearing_frequencies,
    calculate_electrical_frequencies,
)
from src.signal_processing.fault_frequency import analyze_fault_frequencies
from src.condition_monitoring.threshold_monitor import MachineStateManager
from src.database.repository import ReadingRepository
from src.ml.predict import FaultPredictor
from src.utils.logger import get_logger

logger = get_logger("monitoring_service", "application.log")

class MonitoringService:
    """Core real-time monitoring coordinator.

    Maintains separation between:
    1. Real-time path: Bounded ring buffer -> DSP -> WebSocket / UI
    2. Historical storage path: Queue -> Asynchronous batch writer -> MySQL
    """

    def __init__(self):
        # Bounded in-memory ring buffers for low-latency oscilloscope plotting
        self.max_buffer_size = DISPLAY_BUFFER_SIZE
        self._lock = threading.RLock()

        self.buf_timestamps = deque(maxlen=self.max_buffer_size)
        self.buf_x = deque(maxlen=self.max_buffer_size)
        self.buf_y = deque(maxlen=self.max_buffer_size)
        self.buf_z = deque(maxlen=self.max_buffer_size)
        self.buf_current = deque(maxlen=self.max_buffer_size)
        self.buf_temp = deque(maxlen=self.max_buffer_size)
        self.buf_rpm = deque(maxlen=self.max_buffer_size)
        self.buf_fault_label = deque(maxlen=self.max_buffer_size)

        # Configurable DSP settings
        self.current_window_size = DEFAULT_WINDOW_SIZE
        self.current_fft_window = DEFAULT_FFT_WINDOW
        self.sampling_rate = 1500.0

        # State machines & predictors
        self.state_manager = MachineStateManager()
        self.predictor = FaultPredictor(model_name="knn")
        self.db_repo = ReadingRepository()

        # Asynchronous DB batch insertion worker
        self.db_queue: queue.Queue = queue.Queue(maxsize=100000)
        self._db_worker_running = True
        self._db_thread = threading.Thread(target=self._db_batch_worker, daemon=True)
        self._db_thread.start()

        # Cached latest processed packet
        self._last_processed_packet: Optional[Dict[str, Any]] = None
        self._last_process_time = 0.0

        logger.info("Initialized MonitoringService (buffer_size=%d)", self.max_buffer_size)

    def set_window_size(self, size: int) -> int:
        """Update active window size (256, 512, 1024, or 2048)."""
        with self._lock:
            if size in WINDOW_SIZES:
                self.current_window_size = size
            else:
                self.current_window_size = min(WINDOW_SIZES, key=lambda s: abs(s - size))
        logger.info("Updated processing window size to: %d samples", self.current_window_size)
        return self.current_window_size

    def set_fft_window_function(self, func_name: str) -> str:
        """Update FFT window function (hann, hamming, blackman, rectangular)."""
        with self._lock:
            self.current_fft_window = func_name.lower()
        return self.current_fft_window

    def set_active_ml_model(self, model_name: str) -> bool:
        """Switch active ML classifier (knn, decision_tree, logistic_regression)."""
        return self.predictor._load_active_model(model_name)

    def ingest_sample(self, sample: Dict[str, Any], fs: Optional[float] = None) -> None:
        """Ingest incoming sample from acquisition source into ring buffer and DB queue."""
        if fs and fs > 0:
            self.sampling_rate = fs

        with self._lock:
            self.buf_timestamps.append(sample.get("timestamp", ""))
            self.buf_x.append(float(sample.get("x", 0.0)))
            self.buf_y.append(float(sample.get("y", 0.0)))
            self.buf_z.append(float(sample.get("z", 0.0)))
            self.buf_current.append(float(sample.get("current", 0.42)))
            self.buf_temp.append(float(sample.get("temperature", 43.2)))
            rpm_val = sample.get("rpm")
            self.buf_rpm.append(float(rpm_val) if rpm_val is not None else 1450.0)
            self.buf_fault_label.append(str(sample.get("fault_label", "A")))

        # Push to asynchronous persistent DB queue
        try:
            self.db_queue.put_nowait(sample)
        except queue.Full:
            logger.warning("DB insertion queue is full. Dropping historical sample.")

    def ingest_batch(self, samples: List[Dict[str, Any]], fs: Optional[float] = None) -> None:
        """Ingest batch of incoming samples."""
        for s in samples:
            self.ingest_sample(s, fs)

    def process_latest(self) -> Dict[str, Any]:
        """Compute full signal-processing, condition monitoring, and ML metrics on latest window."""
        with self._lock:
            x_arr = np.array(self.buf_x)
            y_arr = np.array(self.buf_y)
            z_arr = np.array(self.buf_z)
            curr_arr = list(self.buf_current)
            temp_arr = list(self.buf_temp)
            ts_arr = list(self.buf_timestamps)
            rpm_arr = list(self.buf_rpm)
            fault_arr = list(self.buf_fault_label)
            window_size = self.current_window_size
            fft_win = self.current_fft_window
            fs = self.sampling_rate

        n_samples = len(x_arr)
        if n_samples < 16:
            return {
                "status": "Buffering",
                "sample_count": n_samples,
                "window_size": window_size,
                "sampling_rate": fs,
            }

        # 1. Window extraction
        win_x = get_window(x_arr, window_size)
        win_y = get_window(y_arr, window_size)
        win_z = get_window(z_arr, window_size)

        # 2. Acceleration and Velocity RMS
        acc_rms = compute_acceleration_rms(win_x, win_y, win_z)
        vel_rms = compute_velocity_rms(win_x, win_y, win_z, sampling_rate=fs)

        # 3. FFT Spectral analysis
        fft_data = compute_fft(
            x=win_x,
            y=win_y,
            z=win_z,
            sampling_rate=fs,
            window_size=window_size,
            window_func=fft_win,
        )

        # 4. Rotational, bearing, and electrical frequencies
        latest_rpm = rpm_arr[-1] if rpm_arr else 1450.0
        bearing_freqs = calculate_bearing_frequencies(latest_rpm, BEARING_CONFIG)
        electrical_freqs = calculate_electrical_frequencies(latest_rpm, ELECTRICAL_CONFIG)

        # 5. Fault-frequency matching
        fault_analysis = analyze_fault_frequencies(
            freqs=fft_data.get("frequency", []),
            magnitudes=fft_data.get("magnitude_x", []),
            bearing_info=bearing_freqs,
            electrical_info=electrical_freqs,
            tolerance_percent=FAULT_FREQUENCY_CONFIG.get("frequency_tolerance_percent", 3.0),
        )

        # 6. Condition and machine state monitoring
        condition_eval = self.state_manager.evaluate_condition(
            current_samples=curr_arr[-100:],
            temperature_samples=temp_arr[-100:],
            total_rms=acc_rms["a_rms_total"],
            rpm=latest_rpm,
        )

        # 7. Real-time ML classification
        ml_prediction = self.predictor.predict_window(win_x, win_y, win_z)

        # Construct payload with decimated time-domain signals for smooth web rendering
        # Limit transmitted waveform points to max 512 for responsive client rendering
        display_pts = min(len(win_x), 512)
        step = max(1, len(win_x) // display_pts)

        packet = {
            "timestamp": ts_arr[-1] if ts_arr else "",
            "sampling_rate": fs,
            "window_size": window_size,
            "frequency_resolution": round(fs / window_size, 4),
            "nyquist_frequency": round(fs / 2.0, 2),
            "fft_window_function": fft_win,
            # Live readings
            "latest_readings": {
                "x": round(float(win_x[-1]), 4),
                "y": round(float(win_y[-1]), 4),
                "z": round(float(win_z[-1]), 4),
                "current": round(float(curr_arr[-1]), 3) if curr_arr else 0.0,
                "temperature": round(float(temp_arr[-1]), 1) if temp_arr else 0.0,
                "rpm": round(float(latest_rpm), 1),
                "true_label": fault_arr[-1] if fault_arr else "A",
            },
            # RMS
            "rms": {
                **acc_rms,
                **vel_rms,
            },
            # Time-domain waveform
            "waveform": {
                "timestamps": list(ts_arr[-len(win_x)::step]),
                "x": [round(float(v), 4) for v in win_x[::step]],
                "y": [round(float(v), 4) for v in win_y[::step]],
                "z": [round(float(v), 4) for v in win_z[::step]],
            },
            # Frequency spectrum
            "fft": {
                "frequency": [round(f, 2) for f in fft_data["frequency"]],
                "magnitude_x": [round(m, 5) for m in fft_data["magnitude_x"]],
                "magnitude_y": [round(m, 5) for m in fft_data["magnitude_y"]],
                "magnitude_z": [round(m, 5) for m in fft_data["magnitude_z"]],
            },
            # Diagnostic & Condition Analysis
            "bearing_frequencies": bearing_freqs,
            "electrical_frequencies": electrical_freqs,
            "fault_analysis": fault_analysis,
            "condition": condition_eval,
            "ml_prediction": ml_prediction,
        }

        self._last_processed_packet = packet
        return packet

    def _db_batch_worker(self) -> None:
        """Background thread persisting queued sensor readings in batches to database."""
        batch: List[Dict[str, Any]] = []
        last_flush = time.time()

        while self._db_worker_running:
            try:
                # Wait for items with short timeout
                item = self.db_queue.get(timeout=0.2)
                batch.append(item)
            except queue.Empty:
                pass

            now = time.time()
            # Flush batch if batch size reached or timeout exceeded with data
            if len(batch) >= DATABASE_BATCH_SIZE or (batch and (now - last_flush) > 1.0):
                try:
                    self.db_repo.insert_batch(batch)
                except Exception as e:
                    logger.error("DB batch write error: %s", e)
                batch = []
                last_flush = now

    def shutdown(self) -> None:
        """Cleanly flush remaining DB items and terminate background thread."""
        self._db_worker_running = False
        if self._db_thread.is_alive():
            self._db_thread.join(timeout=1.0)

