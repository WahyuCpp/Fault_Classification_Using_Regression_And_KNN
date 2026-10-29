"""Future live hardware acquisition source (ESP32-S3 / MQTT / Serial / TCP)."""
from typing import Optional, Dict, Any, List
import time
from datetime import datetime

from src.acquisition.base_source import DataSource
from config.main_config import DEFAULT_SAMPLING_RATE, MACHINE_CONFIG
from src.utils.logger import get_logger

logger = get_logger("future_live_source", "acquisition.log")

class ESP32LiveSource(DataSource):
    """Acquisition source adapter for real-time ESP32-S3 microcontroller feeds.

    Accepts readings from ADXL345 (accel X/Y/Z), DS18B20 (temp),
    SCT-013-005 (current), and optical tachometer (RPM) over Serial/MQTT/TCP/REST.
    Implements identical DataSource contract as CSVReplaySource.
    """

    def __init__(
        self,
        connection_type: str = "serial",  # 'serial', 'mqtt', 'tcp', 'mock_live'
        port_or_broker: str = "COM3",
        baud_rate: int = 115200,
        sampling_rate: float = DEFAULT_SAMPLING_RATE,
        machine_id: Optional[str] = None,
    ):
        self.connection_type = connection_type
        self.port_or_broker = port_or_broker
        self.baud_rate = baud_rate
        self.sampling_rate = sampling_rate
        self.machine_id = machine_id or MACHINE_CONFIG["machine_id"]

        self.is_running = False
        self.is_paused = False
        self.is_connected = False
        self.samples_received = 0

        logger.info(
            "Configured ESP32LiveSource [%s on %s, fs=%.1f Hz]",
            self.connection_type,
            self.port_or_broker,
            self.sampling_rate,
        )

    def start(self) -> None:
        self.is_running = True
        self.is_paused = False
        self.is_connected = True
        logger.info("Started ESP32-S3 live source connection.")

    def stop(self) -> None:
        self.is_running = False
        self.is_paused = False
        self.is_connected = False
        logger.info("Stopped ESP32-S3 live source connection.")

    def pause(self) -> None:
        self.is_paused = True

    def resume(self) -> None:
        self.is_paused = False

    def read_sample(self) -> Optional[Dict[str, Any]]:
        """Read sample from hardware buffer/stream.

        (When physical hardware is connected, reads from UART/socket/MQTT queue.
        In hardware preparation mode, returns mock sample if running).
        """
        if not self.is_running or self.is_paused:
            return None

        self.samples_received += 1
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return {
            "source_file": f"ESP32_{self.connection_type.upper()}",
            "machine_id": self.machine_id,
            "timestamp": now_str,
            "x": 0.02,
            "y": -0.01,
            "z": 9.81,
            "current": 0.42,
            "temperature": 43.5,
            "rpm": 1450.0,
            "fault_label": "A",
        }

    def read_batch(self, max_samples: int = 100) -> List[Dict[str, Any]]:
        batch = []
        for _ in range(max_samples):
            s = self.read_sample()
            if s is None:
                break
            batch.append(s)
        return batch

    def get_sampling_rate(self) -> float:
        return self.sampling_rate

    def get_status(self) -> Dict[str, Any]:
        return {
            "source_type": f"ESP32LiveSource ({self.connection_type})",
            "connection_endpoint": self.port_or_broker,
            "is_connected": self.is_connected,
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "sampling_rate_hz": self.sampling_rate,
            "samples_emitted": self.samples_received,
            "data_quality_percent": 100.0 if self.is_connected else 0.0,
        }

