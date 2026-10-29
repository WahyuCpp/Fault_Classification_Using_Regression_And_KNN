"""Abstract base data source interface for sensor acquisition."""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

class DataSource(ABC):
    """Abstract generic data source interface.

    Allows interchangeable data acquisition from CSV simulation,
    ESP32-S3 serial, MQTT broker, or TCP socket without modifying downstream logic.
    """

    @abstractmethod
    def start(self) -> None:
        """Start data acquisition."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop data acquisition."""
        pass

    @abstractmethod
    def pause(self) -> None:
        """Pause data acquisition."""
        pass

    @abstractmethod
    def resume(self) -> None:
        """Resume paused data acquisition."""
        pass

    @abstractmethod
    def read_sample(self) -> Optional[Dict[str, Any]]:
        """Read a single continuous sensor measurement."""
        pass

    @abstractmethod
    def read_batch(self, max_samples: int = 100) -> List[Dict[str, Any]]:
        """Read a batch of newly arrived sensor measurements."""
        pass

    @abstractmethod
    def get_sampling_rate(self) -> float:
        """Return the physical signal sampling frequency (Hz) for FFT/DSP."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Return acquisition health, sampling integrity, and progress metadata."""
        pass

