# server/models/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from constants import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
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
