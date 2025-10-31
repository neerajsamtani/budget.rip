# Phase 3 Implementation Summary

## Overview

Phase 3 of the MongoDB to PostgreSQL migration has been implemented. This phase focuses on migrating transactions and line items from MongoDB to PostgreSQL, implementing dual-write capabilities, and providing tools for verification and reconciliation.

## Implemented Components

### 1. Migration Scripts

#### `phase3_migrate_transactions.py`
Migrates raw transaction data from MongoDB collections to PostgreSQL:
- **Sources**: venmo_raw_data, splitwise_raw_data, stripe_raw_transaction_data, cash_raw_data
- **Features**:
  - Extracts transaction dates based on source type
  - Stores original MongoDB _id in `source_id` field
  - Preserves complete transaction data in `source_data` JSONB column
  - Idempotent (safe to re-run)
  - Built-in verification
  - Outputs transaction mapping file for line items migration

**Usage**:
```bash
cd server
python migrations/phase3_migrate_transactions.py
```

#### `phase3_migrate_line_items.py`
Migrates line items from MongoDB to PostgreSQL:
- **Features**:
  - Links line items to transactions via `transaction_id` foreign key
  - Stores original MongoDB _id in `mongo_id` column for ID coexistence
  - Looks up payment methods by name
  - Creates manual transactions for orphaned line items
  - Handles missing payment methods by creating "Unknown" payment method
  - Idempotent (safe to re-run)
  - Built-in verification

**Prerequisites**:
- Run `phase3_migrate_transactions.py` first
- Payment methods must be migrated (Phase 2)

**Usage**:
```bash
cd server
python migrations/phase3_migrate_line_items.py
```

### 2. Dual-Write Utility (`utils/dual_write.py`)

A robust dual-write utility for the migration period (Phases 3-5):

**Features**:
- Writes to MongoDB first (primary)
- Then writes to PostgreSQL (secondary)
- Non-blocking: PostgreSQL failures don't fail the operation
- Comprehensive error logging for reconciliation
- Supports critical mode for important operations

**Functions**:
- `dual_write_operation()`: Generic dual-write for any operation
- `dual_write_transaction()`: Convenience function for transactions
- `dual_write_line_item()`: Convenience function for line items
- `log_dual_write_failure()`: Structured logging for reconciliation

**Example Usage**:
```python
from utils.dual_write import dual_write_operation

result = dual_write_operation(
    mongo_write_func=lambda: insert(collection, data),
    pg_write_func=lambda db: create_pg_record(db, data),
    operation_name="venmo_transaction",
    critical=False
)

if not result['pg_success']:
    # PostgreSQL write failed but MongoDB succeeded
    # Will be reconciled later
    pass
```

### 3. Verification Script (`phase3_verify.py`)

Comprehensive verification tool to ensure data consistency:

**Checks Performed**:
1. ✓ Transaction count verification (per source and total)
2. ✓ Line item count verification
3. ✓ Transaction spot checks (random sampling)
4. ✓ Line item spot checks (field-level validation)
5. ✓ Foreign key integrity
6. ✓ mongo_id uniqueness
7. ✓ Transaction date reasonableness

**Usage**:
```bash
cd server
python migrations/phase3_verify.py
```

**Output**:
- Detailed check results with ✓/✗ indicators
- Summary of passed/failed/warning checks
- Exit code 0 on success, 1 on failure (suitable for CI/CD)

**Recommended Schedule**:
- After initial migration
- Periodically during dual-write period (e.g., hourly cron)
- Before switching reads to PostgreSQL (Phase 5)

### 4. Reconciliation Script (`phase3_reconcile.py`)

Automated reconciliation for dual-write failures:

**Features**:
- Finds records in MongoDB missing from PostgreSQL
- Syncs missing records to PostgreSQL
- Creates manual transactions for orphaned line items
- Dry-run mode for safety
- Detailed statistics and logging

**Usage**:
```bash
# Dry run (see what would be synced)
cd server
python migrations/phase3_reconcile.py --dry-run

# Actual reconciliation
python migrations/phase3_reconcile.py
```

**Recommended Schedule**:
- Run hourly as cron job during dual-write period (Phases 3-5)
- Run before verification checks
- Run before Phase 5 (switching reads to PostgreSQL)

**Cron Example**:
```bash
# Run every hour
0 * * * * cd /path/to/server && python migrations/phase3_reconcile.py >> /var/log/reconcile.log 2>&1
```

### 5. Unit Tests (`tests/test_phase3_migration.py`)

Comprehensive test suite covering:

**Test Classes**:
1. `TestDualWriteUtility`: Tests dual-write functions
   - Successful dual-write
   - MongoDB failure handling
   - PostgreSQL failure (critical and non-critical)

2. `TestTransactionMigration`: Tests transaction migration logic
   - Date extraction for all sources (Venmo, Splitwise, Stripe, Cash)
   - Transaction creation
   - Unique constraint enforcement

3. `TestLineItemMigration`: Tests line item migration
   - Line item creation
   - Foreign key constraints
   - Cascade delete behavior

4. `TestMigrationIntegration`: End-to-end tests
   - Complete Venmo migration flow
   - Orphaned line item handling

5. `TestPaymentMethodLookup`: Payment method tests
   - Lookup by name
   - Unknown payment method creation

**Run Tests**:
```bash
cd server
pytest tests/test_phase3_migration.py -v
```

## Data Model

### Transaction Table Schema
```sql
CREATE TABLE transactions (
    id VARCHAR(255) PRIMARY KEY,           -- txn_xxx
    source ENUM(...) NOT NULL,              -- venmo, splitwise, stripe, cash, manual
    source_id VARCHAR(255) NOT NULL,        -- MongoDB _id
    source_data JSONB NOT NULL,             -- Original transaction data
    transaction_date TIMESTAMP NOT NULL,
    imported_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source, source_id)
);
```

### LineItem Table Schema
```sql
CREATE TABLE line_items (
    id VARCHAR(255) PRIMARY KEY,           -- li_xxx
    transaction_id VARCHAR(255) NOT NULL,   -- FK to transactions
    mongo_id VARCHAR(24),                   -- Original MongoDB _id (for ID coexistence)
    date TIMESTAMP NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    description TEXT NOT NULL,
    payment_method_id VARCHAR(255) NOT NULL, -- FK to payment_methods
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
    FOREIGN KEY (payment_method_id) REFERENCES payment_methods(id) ON DELETE RESTRICT
);
```

## Migration Workflow

### Initial Migration (One-Time)

1. **Backup MongoDB**:
   ```bash
   mongodump --db flask_db --out /backup/pre_phase3_$(date +%Y%m%d_%H%M%S)
   ```

2. **Run Phase 2 (if not done)**:
   Ensure categories, payment methods, and tags are migrated.

3. **Migrate Transactions**:
   ```bash
   python migrations/phase3_migrate_transactions.py
   ```
   This creates `phase3_transaction_mapping.json` for line items.

4. **Migrate Line Items**:
   ```bash
   python migrations/phase3_migrate_line_items.py
   ```

5. **Verify Migration**:
   ```bash
   python migrations/phase3_verify.py
   ```
   All checks should pass before proceeding.

### Dual-Write Period (Ongoing)

**Note**: The refresh endpoint updates (Venmo, Splitwise, Stripe, Cash) should be implemented to use the dual-write utility. This ensures new data is written to both databases.

**Example Dual-Write Integration** (to be implemented):
```python
# In resources/venmo.py
from utils.dual_write import dual_write_transaction

def refresh_venmo():
    # ... existing code to get transactions ...

    for transaction in all_transactions:
        dual_write_transaction(
            mongo_write_func=lambda: bulk_upsert(venmo_raw_data_collection, [transaction]),
            transaction_data=transaction,
            source='venmo',
            critical=False
        )
```

### Reconciliation (Automated)

Set up cron job:
```bash
0 * * * * cd /path/to/server && python migrations/phase3_reconcile.py >> /var/log/phase3_reconcile.log 2>&1
```

### Verification (Periodic)

Run verification daily or before major changes:
```bash
python migrations/phase3_verify.py
```

## Files Created

```
server/
├── migrations/
│   ├── phase3_migrate_transactions.py     # Transaction migration script
│   ├── phase3_migrate_line_items.py       # Line item migration script
│   ├── phase3_verify.py                   # Verification script
│   ├── phase3_reconcile.py                # Reconciliation script
│   ├── phase3_transaction_mapping.json    # Generated: mongo_id -> txn_id mapping
│   └── PHASE3_IMPLEMENTATION.md           # This file
├── utils/
│   └── dual_write.py                       # Dual-write utility
└── tests/
    └── test_phase3_migration.py            # Unit tests
```

## Key Design Decisions

### 1. Transaction-First Approach
All line items must have a transaction. Orphaned line items get manual transactions created automatically.

**Why**: Maintains referential integrity and provides complete audit trail.

### 2. JSONB for Source Data
Original transaction data stored in `source_data` JSONB column.

**Why**:
- Complete audit trail
- Can query original data if needed
- No data loss during migration

### 3. mongo_id for ID Coexistence
Original MongoDB `_id` stored in `mongo_id` column on line_items.

**Why**:
- Allows API endpoints to accept both ID formats during transition
- Enables verification between databases
- Supports gradual frontend migration

### 4. Non-Blocking Dual-Write
PostgreSQL write failures don't fail the operation.

**Why**:
- MongoDB remains source of truth during migration
- No user-facing impact from PostgreSQL issues
- Reconciliation handles eventual consistency

### 5. Idempotent Scripts
All migration scripts can be safely re-run.

**Why**:
- Safe to retry on failures
- Easy to test
- Reduces risk during migration

## Next Steps (Phase 4)

After Phase 3 is complete and verified:

1. **Update Refresh Endpoints**:
   - Integrate dual-write utility into Venmo/Splitwise/Stripe/Cash refresh functions
   - Test dual-write with live API calls

2. **Monitor Dual-Write Period**:
   - Review reconciliation logs
   - Monitor PostgreSQL write success rate
   - Verify data consistency regularly

3. **Phase 4 Preparation**:
   - Migrate events and tags
   - Implement ID coexistence for events
   - Update event CRUD endpoints to dual-write

## Troubleshooting

### Migration Fails
1. Check MongoDB connection: `MONGO_URI` in `.env`
2. Check PostgreSQL connection: `DATABASE_URL` in `.env`
3. Verify Phase 2 completed (payment methods exist)
4. Check logs for specific errors

### Verification Fails
1. Run reconciliation: `python migrations/phase3_reconcile.py`
2. Check for schema changes
3. Verify foreign key relationships
4. Review error logs

### Dual-Write Failures
1. Check `DUAL_WRITE_FAILURE` entries in logs
2. Run reconciliation script
3. Verify PostgreSQL connection and schema
4. Check for constraint violations

## Success Criteria

Phase 3 is considered complete when:

- ✅ All transactions migrated (counts match)
- ✅ All line items migrated (counts match)
- ✅ Verification script passes all checks
- ✅ Foreign key integrity verified
- ✅ Spot checks show matching data
- ✅ Dual-write utility tested
- ✅ Reconciliation script tested
- ✅ Unit tests written and passing

## Support

For issues or questions:
1. Check verification output for specific errors
2. Review reconciliation logs
3. Check PostgreSQL logs for constraint violations
4. Review MongoDB data for inconsistencies
