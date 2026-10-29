"""SQLAlchemy ORM models for MONTREAL-VT sensor readings."""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    DateTime,
    Index,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class SensorReading(Base):
    """Primary continuous-reading table for MONTREAL-VT condition data."""
    __tablename__ = "MONTREAL_VT_reading_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(String(50), nullable=False, default="MOTOR_001", index=True)
    source_file = Column(String(255), nullable=True)
    timestamp = Column(String(32), nullable=False, index=True)
    x = Column(Float, nullable=False, default=0.0)
    y = Column(Float, nullable=False, default=0.0)
    z = Column(Float, nullable=False, default=0.0)
    current = Column(Float, nullable=False, default=0.0)
    temperature = Column(Float, nullable=False, default=0.0)
    rpm = Column(Float, nullable=True)
    fault_label = Column(String(10), nullable=False, default="A", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Composite indexes for querying performance
    __table_args__ = (
        Index("idx_machine_timestamp", "machine_id", "timestamp"),
        Index("idx_fault_timestamp", "fault_label", "timestamp"),
    )

    def to_dict(self):
        """Serialize reading to dictionary."""
        return {
            "id": self.id,
            "machine_id": self.machine_id,
            "source_file": self.source_file,
            "timestamp": self.timestamp,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "current": self.current,
            "temperature": self.temperature,
            "rpm": self.rpm,
            "fault_label": self.fault_label,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

