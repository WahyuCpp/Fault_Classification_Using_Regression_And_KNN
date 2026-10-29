"""Database initialization script."""
from src.database.connection import get_engine, get_db_status
from src.database.models import Base
from src.database.repository import ReadingRepository
from src.utils.logger import get_logger

logger = get_logger("init_database", "database.log")

def init_database():
    """Create all tables and verify database connection."""
    print("=" * 60)
    print("MONTREAL-VT: Initializing Database Schema")
    print("=" * 60)

    engine, db_type = get_engine()
    print(f"Target Database Type: {db_type}")

    # Create tables
    Base.metadata.create_all(bind=engine)
    print("Schema created: Table 'MONTREAL_VT_reading_data' ready.")

    repo = ReadingRepository()
    count = repo.get_total_count()
    print(f"Current record count: {count}")
    print("=" * 60)
    print("Database initialization completed successfully.")

if __name__ == "__main__":
    init_database()

