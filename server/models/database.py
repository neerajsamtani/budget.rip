# server/models/database.py
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from constants import DATABASE_HOST, DATABASE_NAME, DATABASE_PASSWORD, DATABASE_PORT, DATABASE_SSL_MODE, DATABASE_USERNAME

# Configure engine based on database type
if DATABASE_HOST == "sqlite":
    # SQLite configuration using a shared in-memory database
    # Use a creator function to avoid SQLite creating physical files
    import sqlite3

    def get_shared_memory_connection():
        return sqlite3.connect("file::memory:?cache=shared", uri=True, check_same_thread=False)

    engine = create_engine(
        "sqlite://",
        creator=get_shared_memory_connection,
        echo=False,
    )

    # Enable foreign key constraints for SQLite (required for CASCADE deletes)
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL configuration using psycopg2 directly for connection
    # This avoids URL encoding issues with special characters in credentials
    import psycopg2

    engine = create_engine(
        "postgresql+psycopg2://",
        creator=lambda: psycopg2.connect(
            host=DATABASE_HOST,
            port=DATABASE_PORT,
            user=DATABASE_USERNAME,
            password=DATABASE_PASSWORD,
            dbname=DATABASE_NAME,
            sslmode=DATABASE_SSL_MODE,
        ),
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,  # Recycle connections after 1 hour
        echo=False,  # Set to True for SQL debugging
    )

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
