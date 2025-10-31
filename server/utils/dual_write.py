"""
Dual-Write Utility for MongoDB to PostgreSQL Migration (Phase 3-5)

This module provides utilities for dual-writing to both MongoDB (primary) and
PostgreSQL (secondary) databases during the migration period.

Strategy:
1. Write to MongoDB first (primary) - if this fails, the operation fails
2. Write to PostgreSQL second (secondary) - if this fails, log error but don't fail
3. Log failures for later reconciliation

Usage:
    from utils.dual_write import dual_write_transaction, dual_write_line_item

    # In your endpoint:
    dual_write_transaction(
        mongo_write_func=lambda: insert(venmo_raw_data_collection, transaction),
        pg_write_func=lambda db: create_pg_transaction(db, transaction),
        operation_name="venmo_transaction"
    )
"""

import logging
from datetime import UTC, datetime
from typing import Any, Callable, Dict, Optional

from sqlalchemy.exc import SQLAlchemyError

from models.database import SessionLocal

# Configure logging
logger = logging.getLogger(__name__)


class DualWriteError(Exception):
    """Custom exception for dual-write failures"""
    pass


def dual_write_operation(
    mongo_write_func: Callable[[], Any],
    pg_write_func: Callable[[Any], Any],
    operation_name: str,
    critical: bool = False
) -> Dict[str, Any]:
    """
    Execute a dual-write operation to both MongoDB and PostgreSQL.

    Args:
        mongo_write_func: Function that performs the MongoDB write (no args)
        pg_write_func: Function that performs the PostgreSQL write (takes db_session)
        operation_name: Name of the operation for logging
        critical: If True, raise exception if PostgreSQL write fails

    Returns:
        Dictionary with success status and any errors:
        {
            'success': bool,
            'mongo_success': bool,
            'pg_success': bool,
            'mongo_error': Optional[str],
            'pg_error': Optional[str],
            'mongo_result': Any,
            'pg_result': Any
        }

    Raises:
        DualWriteError: If MongoDB write fails, or if critical=True and PG fails
    """
    result = {
        'success': False,
        'mongo_success': False,
        'pg_success': False,
        'mongo_error': None,
        'pg_error': None,
        'mongo_result': None,
        'pg_result': None,
    }

    # Step 1: Write to MongoDB (primary)
    try:
        logger.debug(f"DualWrite [{operation_name}]: Writing to MongoDB...")
        mongo_result = mongo_write_func()
        result['mongo_success'] = True
        result['mongo_result'] = mongo_result
        logger.debug(f"DualWrite [{operation_name}]: MongoDB write succeeded")

    except Exception as e:
        # MongoDB write failed - this is critical, fail the operation
        error_msg = f"MongoDB write failed for {operation_name}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        result['mongo_error'] = str(e)
        raise DualWriteError(error_msg) from e

    # Step 2: Write to PostgreSQL (secondary)
    db_session = None
    try:
        logger.debug(f"DualWrite [{operation_name}]: Writing to PostgreSQL...")
        db_session = SessionLocal()

        pg_result = pg_write_func(db_session)

        db_session.commit()
        result['pg_success'] = True
        result['pg_result'] = pg_result
        result['success'] = True
        logger.debug(f"DualWrite [{operation_name}]: PostgreSQL write succeeded")

    except SQLAlchemyError as e:
        # PostgreSQL write failed
        error_msg = f"PostgreSQL write failed for {operation_name}: {str(e)}"

        if db_session:
            db_session.rollback()

        # Log error for reconciliation
        logger.error(error_msg, exc_info=True)
        log_dual_write_failure(operation_name, str(e), result.get('mongo_result'))

        result['pg_error'] = str(e)

        # If critical, raise exception; otherwise just log
        if critical:
            raise DualWriteError(error_msg) from e
        else:
            # PostgreSQL failure is non-critical during migration
            # MongoDB write succeeded, so we return success
            result['success'] = True
            logger.warning(
                f"DualWrite [{operation_name}]: PostgreSQL write failed but continuing "
                "(will be reconciled later)"
            )

    except Exception as e:
        # Unexpected error
        error_msg = f"Unexpected error in PostgreSQL write for {operation_name}: {str(e)}"

        if db_session:
            db_session.rollback()

        logger.error(error_msg, exc_info=True)
        log_dual_write_failure(operation_name, str(e), result.get('mongo_result'))

        result['pg_error'] = str(e)

        if critical:
            raise DualWriteError(error_msg) from e
        else:
            result['success'] = True

    finally:
        if db_session:
            db_session.close()

    return result


def log_dual_write_failure(
    operation_name: str,
    error: str,
    mongo_data: Any
):
    """
    Log dual-write failures for later reconciliation.

    This creates a log entry that can be parsed by the reconciliation script.

    Args:
        operation_name: Name of the operation that failed
        error: Error message
        mongo_data: Data that was written to MongoDB
    """
    failure_log = {
        'timestamp': datetime.now(UTC).isoformat(),
        'operation': operation_name,
        'error': error,
        'mongo_data': str(mongo_data),  # Convert to string for safety
    }

    # Log in structured format for easy parsing
    logger.error(
        f"DUAL_WRITE_FAILURE: {failure_log}",
        extra=failure_log
    )


# Convenience functions for common operations

def dual_write_transaction(
    mongo_write_func: Callable[[], Any],
    transaction_data: Dict[str, Any],
    source: str,
    critical: bool = False
) -> Dict[str, Any]:
    """
    Dual-write a transaction to both MongoDB and PostgreSQL.

    Args:
        mongo_write_func: Function to write to MongoDB
        transaction_data: Transaction data dict
        source: Transaction source (venmo, splitwise, stripe, cash)
        critical: If True, raise exception if PostgreSQL write fails

    Returns:
        Dual-write result dictionary
    """
    from models.sql_models import Transaction
    from utils.id_generator import generate_id

    def pg_write(db_session):
        # Create PostgreSQL transaction
        from datetime import datetime, UTC

        # Generate transaction ID
        txn_id = generate_id('txn')

        # Extract or create transaction date
        if 'date_created' in transaction_data:
            # Venmo format
            txn_date = datetime.fromtimestamp(
                float(transaction_data['date_created']), UTC
            )
        elif 'created' in transaction_data:
            # Stripe format
            txn_date = datetime.fromtimestamp(
                float(transaction_data['created']), UTC
            )
        elif 'date' in transaction_data:
            # Splitwise/Cash format
            if isinstance(transaction_data['date'], (int, float)):
                txn_date = datetime.fromtimestamp(
                    float(transaction_data['date']), UTC
                )
            else:
                # ISO string
                from helpers import iso_8601_to_posix
                posix = iso_8601_to_posix(transaction_data['date'])
                txn_date = datetime.fromtimestamp(posix, UTC)
        else:
            txn_date = datetime.now(UTC)

        # Get source_id (MongoDB _id)
        source_id = str(transaction_data.get('_id', transaction_data.get('id', '')))

        # Create transaction
        transaction = Transaction(
            id=txn_id,
            source=source,
            source_id=source_id,
            source_data=transaction_data,
            transaction_date=txn_date,
        )

        db_session.add(transaction)
        db_session.flush()

        return transaction

    return dual_write_operation(
        mongo_write_func,
        pg_write,
        f"{source}_transaction",
        critical
    )


def dual_write_line_item(
    mongo_write_func: Callable[[], Any],
    line_item_obj: Any,  # LineItem object
    transaction_id: str,
    payment_method_name: str,
    critical: bool = False
) -> Dict[str, Any]:
    """
    Dual-write a line item to both MongoDB and PostgreSQL.

    Args:
        mongo_write_func: Function to write to MongoDB
        line_item_obj: LineItem object with data
        transaction_id: PostgreSQL transaction ID to link to
        payment_method_name: Payment method name to look up
        critical: If True, raise exception if PostgreSQL write fails

    Returns:
        Dual-write result dictionary
    """
    from decimal import Decimal
    from datetime import datetime, UTC
    from models.sql_models import LineItem, PaymentMethod
    from utils.id_generator import generate_id

    def pg_write(db_session):
        # Look up payment method
        payment_method = db_session.query(PaymentMethod).filter_by(
            name=payment_method_name
        ).first()

        if not payment_method:
            # Create Unknown payment method if needed
            payment_method = db_session.query(PaymentMethod).filter_by(
                name='Unknown'
            ).first()

            if not payment_method:
                payment_method = PaymentMethod(
                    id=generate_id('pm'),
                    name='Unknown',
                    type='cash',
                    is_active=True
                )
                db_session.add(payment_method)
                db_session.flush()

        # Create LineItem
        line_item = LineItem(
            id=generate_id('li'),
            transaction_id=transaction_id,
            mongo_id=str(line_item_obj.id),
            date=datetime.fromtimestamp(float(line_item_obj.date), UTC),
            amount=Decimal(str(line_item_obj.amount)),
            description=line_item_obj.description,
            payment_method_id=payment_method.id,
            notes=getattr(line_item_obj, 'notes', None),
        )

        db_session.add(line_item)
        db_session.flush()

        return line_item

    return dual_write_operation(
        mongo_write_func,
        pg_write,
        f"line_item_{line_item_obj.id}",
        critical
    )
