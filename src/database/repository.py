"""Database repository for sensor readings persistence and querying."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import pandas as pd
from sqlalchemy import desc, func, delete

from src.database.connection import get_session, get_engine
from src.database.models import SensorReading, Base
from config.database_config import DATABASE_BATCH_SIZE
from src.utils.logger import get_logger

logger = get_logger("database_repo", "database.log")

class ReadingRepository:
    """Repository handling CRUD operations on MONTREAL_VT_reading_data."""

    def __init__(self):
        # Ensure schema tables exist on active engine
        engine, _ = get_engine()
        Base.metadata.create_all(bind=engine)

    def insert_batch(self, readings: List[Dict[str, Any]]) -> int:
        """Batch insert sensor readings into database.

        Args:
            readings: List of reading dictionaries.

        Returns:
            Number of inserted records.
        """
        if not readings:
            return 0

        session = get_session()
        try:
            # Efficient bulk insert using SQLAlchemy Core
            session.bulk_insert_mappings(SensorReading, readings)
            session.commit()
            return len(readings)
        except Exception as e:
            session.rollback()
            logger.error("Failed to insert batch of %d records: %s", len(readings), e)
            raise e
        finally:
            session.close()

    def get_latest_readings(
        self,
        limit: int = 100,
        machine_id: Optional[str] = None,
        fault_label: Optional[str] = None,
        source_file: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve newest records with optional filtering."""
        session = get_session()
        try:
            query = session.query(SensorReading)

            if machine_id:
                query = query.filter(SensorReading.machine_id == machine_id)
            if fault_label:
                query = query.filter(SensorReading.fault_label == fault_label)
            if source_file:
                query = query.filter(SensorReading.source_file == source_file)
            if start_time:
                query = query.filter(SensorReading.timestamp >= start_time)
            if end_time:
                query = query.filter(SensorReading.timestamp <= end_time)

            readings = (
                query.order_by(desc(SensorReading.id))
                .limit(limit)
                .all()
            )
            return [r.to_dict() for r in readings]
        finally:
            session.close()

    def get_total_count(self) -> int:
        """Count total stored readings."""
        session = get_session()
        try:
            return session.query(func.count(SensorReading.id)).scalar() or 0
        finally:
            session.close()

    def get_distinct_metadata(self) -> Dict[str, List[str]]:
        """Return distinct machines, classes, and source files for filtering UI."""
        session = get_session()
        try:
            machines = [
                m[0] for m in session.query(SensorReading.machine_id).distinct().all() if m[0]
            ]
            faults = [
                f[0] for f in session.query(SensorReading.fault_label).distinct().all() if f[0]
            ]
            files = [
                sf[0] for sf in session.query(SensorReading.source_file).distinct().all() if sf[0]
            ]
            return {
                "machines": sorted(machines),
                "fault_labels": sorted(faults),
                "source_files": sorted(files),
            }
        finally:
            session.close()

    def export_to_csv(
        self,
        target_path: str | Path,
        machine_id: Optional[str] = None,
        fault_label: Optional[str] = None,
        limit: int = 10000,
    ) -> Path:
        """Export stored records to a CSV file."""
        records = self.get_latest_readings(
            limit=limit, machine_id=machine_id, fault_label=fault_label
        )
        # Reverse to chronological order for export
        records.reverse()
        df = pd.DataFrame(records)
        out_path = Path(target_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)
        logger.info("Exported %d records to %s", len(df), out_path)
        return out_path

    def delete_historical_data(self, confirm: bool = False) -> int:
        """Delete historical records with required explicit confirmation.

        Never runs on application exit; requires manual user invocation.
        """
        if not confirm:
            raise PermissionError("Explicit confirmation required to delete historical data.")

        session = get_session()
        try:
            deleted_count = session.query(SensorReading).delete()
            session.commit()
            logger.warning("USER ACTION: Deleted %d historical records from database.", deleted_count)
            return deleted_count
        except Exception as e:
            session.rollback()
            logger.error("Failed to delete historical records: %s", e)
            raise e
        finally:
            session.close()

