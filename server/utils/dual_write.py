"""
Dual-Write Utility for MongoDB to PostgreSQL Migration (Phase 3-5)

Provides utilities for dual-writing to both MongoDB and PostgreSQL during the
migration period. Both writes must succeed or the operation fails, ensuring
strong consistency between databases.
"""

import logging
from datetime import UTC, datetime
from typing import Any, Callable, Dict

from models.database import SessionLocal

logger = logging.getLogger(__name__)


class DualWriteError(Exception):
    """Raised when either MongoDB or PostgreSQL write fails"""

    pass


def dual_write_operation(
    mongo_write_func: Callable[[], Any],
    pg_write_func: Callable[[Any], Any],
    operation_name: str,
) -> Dict[str, Any]:
    """
    Execute dual-write to MongoDB then PostgreSQL.

    Both writes must succeed or DualWriteError is raised. This ensures
    strong consistency between databases during the migration period.

    Returns dict with success status and any errors.
    """
    result = {
        "success": False,
        "mongo_success": False,
        "pg_success": False,
        "mongo_error": None,
        "pg_error": None,
        "mongo_result": None,
        "pg_result": None,
    }

    # Write to MongoDB (primary)
    try:
        logger.debug(f"Writing to MongoDB: {operation_name}")
        mongo_result = mongo_write_func()
        result["mongo_success"] = True
        result["mongo_result"] = mongo_result
    except Exception as e:
        error_msg = f"MongoDB write failed for {operation_name}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        result["mongo_error"] = str(e)
        raise DualWriteError(error_msg) from e

    # Write to PostgreSQL (secondary)
    db_session = None
    try:
        logger.debug(f"Writing to PostgreSQL: {operation_name}")
        db_session = SessionLocal()
        pg_result = pg_write_func(db_session)
        db_session.commit()
        result["pg_success"] = True
        result["pg_result"] = pg_result
        result["success"] = True
    except Exception as e:
        error_msg = f"PostgreSQL write failed for {operation_name}: {str(e)}"
        if db_session:
            db_session.rollback()

        logger.error(error_msg, exc_info=True)
        log_dual_write_failure(operation_name, str(e), result.get("mongo_result"))
        result["pg_error"] = str(e)
        raise DualWriteError(error_msg) from e
    finally:
        if db_session:
            db_session.close()

    return result


def log_dual_write_failure(operation_name: str, error: str, mongo_data: Any):
    """Log dual-write failures for reconciliation script to parse."""
    failure_log = {
        "timestamp": datetime.now(UTC).isoformat(),
        "operation": operation_name,
        "error": error,
        "mongo_data": str(mongo_data),
    }
    logger.error(f"DUAL_WRITE_FAILURE: {failure_log}", extra=failure_log)
