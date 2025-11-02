"""
Dual-Write Utility for MongoDB to PostgreSQL Migration (Phase 3-5)

Provides utilities for dual-writing to both MongoDB (primary) and PostgreSQL
(secondary) during the migration period. MongoDB write failures cause the
operation to fail, PostgreSQL failures are logged for reconciliation.
"""

import logging
from datetime import UTC, datetime
from typing import Any, Callable, Dict

from sqlalchemy.exc import SQLAlchemyError

from models.database import SessionLocal

logger = logging.getLogger(__name__)


class DualWriteError(Exception):
    """Raised when MongoDB write fails or critical PostgreSQL write fails"""

    pass


def dual_write_operation(
    mongo_write_func: Callable[[], Any],
    pg_write_func: Callable[[Any], Any],
    operation_name: str,
    critical: bool = False,
) -> Dict[str, Any]:
    """
    Execute dual-write to MongoDB (primary) then PostgreSQL (secondary).

    MongoDB failure raises DualWriteError. PostgreSQL failure is logged
    for reconciliation unless critical=True.

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

        if critical:
            raise DualWriteError(error_msg) from e

        # Non-critical: MongoDB succeeded, PG will be reconciled
        result["success"] = True
        logger.warning(
            f"PostgreSQL write failed for {operation_name} but continuing "
            "(will be reconciled later)"
        )
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
