import logging
from sqlalchemy import event
from sqlmodel import SQLModel, create_engine, Session
from app.models.db import AnalysisResult  # noqa: F401

logger = logging.getLogger(__name__)

sqlite_file_name = "database/database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


@event.listens_for(engine, "connect")
def _enable_wal_mode(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
    except Exception as e:  # pragma: no cover
        logger.warning(f"Could not enable WAL mode: {e}")
    finally:
        cursor.close()


# Columns added after the initial release. SQLModel.metadata.create_all()
# only creates missing TABLES - it never adds columns to an already-existing
# table - so a lightweight startup migration adds them to any pre-existing
# SQLite file. A brand new database already gets these columns via
# create_all() since they're part of the current AnalysisResult definition;
# the ALTER TABLE calls below are then no-ops (skipped because the columns
# already exist).
_ANALYSIS_RESULT_MIGRATIONS = [
    ("needs_review", "BOOLEAN NOT NULL DEFAULT 0"),
    ("review_status", "VARCHAR NOT NULL DEFAULT 'none'"),
    ("human_verdict", "VARCHAR"),
    ("reviewed_at", "DATETIME"),
]


def _migrate_analysis_result_columns():
    table_name = AnalysisResult.__tablename__
    with engine.connect() as conn:
        existing_columns = {
            row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({table_name})")
        }
        for column, ddl in _ANALYSIS_RESULT_MIGRATIONS:
            if column not in existing_columns:
                conn.exec_driver_sql(
                    f"ALTER TABLE {table_name} ADD COLUMN {column} {ddl}"
                )
                logger.info(f"Migration: added column '{column}' to {table_name}")
        conn.commit()


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    _migrate_analysis_result_columns()


def get_session():
    with Session(engine) as session:
        yield session
