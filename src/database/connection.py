"""Database connection management with resilient failover support."""
from typing import Optional, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from config.database_config import (
    DATABASE_URL,
    SQLITE_FALLBACK_URL,
    ENABLE_FALLBACK,
    DB_NAME,
    DB_HOST,
    DB_PORT,
    DB_USER,
    DB_PASSWORD,
)
from src.utils.logger import get_logger

logger = get_logger("database", "database.log")

import socket

_engine: Optional[Engine] = None
_SessionFactory: Optional[sessionmaker] = None
_active_db_type: str = "Unknown"
_is_connected: bool = False

def is_mysql_reachable(host: str = DB_HOST, port: int = DB_PORT, timeout: float = 0.3) -> bool:
    """Fast probe to determine if MySQL port is open and accepting TCP connections."""
    try:
        # Use IPv4 loopback if localhost
        target_host = "127.0.0.1" if host in ("localhost", "127.0.0.1") else host
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((target_host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def create_mysql_database_if_needed():
    """Attempt to create the MONTREAL_VT database if it does not already exist."""
    admin_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/"
    try:
        temp_engine = create_engine(admin_url, pool_pre_ping=True, connect_args={"connect_timeout": 1})
        with temp_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`"))
            conn.commit()
        temp_engine.dispose()
        logger.info("Ensured database '%s' exists on MySQL server.", DB_NAME)
    except Exception as e:
        logger.debug("Could not verify/create MySQL database: %s", e)


def get_engine() -> Tuple[Engine, str]:
    """Get or create the SQLAlchemy engine with graceful MySQL-to-SQLite fallback.

    Returns:
        Tuple of (Engine, db_type_description)
    """
    global _engine, _SessionFactory, _active_db_type, _is_connected

    if _engine is not None:
        return _engine, _active_db_type

    # Fast probe: if MySQL port is not open, switch to SQLite fallback immediately
    if not is_mysql_reachable():
        if ENABLE_FALLBACK:
            logger.info("MySQL service offline at %s:%d. Using local SQLite fallback: %s", DB_HOST, DB_PORT, SQLITE_FALLBACK_URL)
            _engine = create_engine(
                SQLITE_FALLBACK_URL,
                connect_args={"check_same_thread": False},
            )
            _active_db_type = "SQLite (Fallback - MySQL offline)"
            _is_connected = True
            _SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
            return _engine, _active_db_type

    # Attempt MySQL connection if port is open
    try:
        create_mysql_database_if_needed()
        mysql_engine = create_engine(
            DATABASE_URL,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 2},
        )
        with mysql_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _engine = mysql_engine
        _active_db_type = "MySQL"
        _is_connected = True
        logger.info("Successfully connected to MySQL database: %s", DB_NAME)
    except Exception as e:
        logger.warning(
            "MySQL connection failed (%s). Error: %s",
            DATABASE_URL.split("@")[-1],
            e,
        )
        if ENABLE_FALLBACK:
            logger.info("Falling back to local SQLite database at: %s", SQLITE_FALLBACK_URL)
            _engine = create_engine(
                SQLITE_FALLBACK_URL,
                connect_args={"check_same_thread": False},
            )
            _active_db_type = "SQLite (Fallback - MySQL offline)"
            _is_connected = True
        else:
            _active_db_type = "Disconnected"
            _is_connected = False
            raise ConnectionError(f"Could not connect to MySQL database: {e}") from e

    _SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine, _active_db_type


def get_session() -> Session:
    """Provide a new SQLAlchemy session."""
    if _SessionFactory is None:
        get_engine()
    session_factory = _SessionFactory
    if session_factory is None:
        raise RuntimeError("Database session factory was not initialized.")
    return session_factory()


def get_db_status() -> dict:
    """Return database health and type information."""
    global _active_db_type, _is_connected
    if _engine is None:
        try:
            get_engine()
        except Exception:
            pass

    return {
        "connected": _is_connected,
        "db_type": _active_db_type,
        "is_mysql": "MySQL" in _active_db_type and "Fallback" not in _active_db_type,
    }
