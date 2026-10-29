"""Database configuration for MONTREAL-VT system."""
import os
from pathlib import Path
from dotenv import load_dotenv
from config.main_config import BASE_DIR, DATA_DIR

# Load environment variables from .env if present
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

DB_HOST = str(os.getenv("DB_HOST"))
DB_PORT = int (os.getenv("DB_PORT","3306"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# MySQL Connection URI using PyMySQL
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Batch size for high-frequency sensor readings persistence
DATABASE_BATCH_SIZE = int(os.getenv("DATABASE_BATCH_SIZE", "500"))

# Resilient SQLite fallback when MySQL server is unreachable or offline
ENABLE_FALLBACK = True
SQLITE_FALLBACK_URL = f"sqlite:///{DATA_DIR / 'MONTREAL_VT_fallback.db'}"