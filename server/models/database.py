# server/models/database.py
import sqlite3

from sqlalchemy import create_engine
from sqlalchemy import event as sa_event
from sqlalchemy.orm import sessionmaker

from constants import DATABASE_NAME, TESTING

if TESTING:
    # Tests use a shared in-memory database
    def _get_connection():
        return sqlite3.connect("file::memory:?cache=shared", uri=True, check_same_thread=False)

    engine = create_engine(
        "sqlite://",
        creator=_get_connection,
        echo=False,
    )
else:
    # Production uses a file-based SQLite database
    db_path = DATABASE_NAME or "budgit.db"

    engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        connect_args={"check_same_thread": False},
    )


# Enable foreign keys and performance pragmas for all SQLite connections
@sa_event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency for Flask routes.

    Usage in Flask routes:
        db = next(get_db())
        try:
            # ... use db
            db.commit()
        except:
            db.rollback()
            raise
        finally:
            db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
