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


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
