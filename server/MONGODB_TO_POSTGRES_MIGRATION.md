# MongoDB to PostgreSQL Migration Plan

## Current Status

**Migration Progress**: Phase 5.5 Complete (10 weeks completed)

| Component | Status | Notes |
|-----------|--------|-------|
| **Data Migration** | ✅ COMPLETE | All historical data in PostgreSQL |
| **Dual-Write** | ✅ ACTIVE | All writes go to both databases |
| **Read Operations** | ⏸️ READY | PostgreSQL reads available via feature flag |
| **MongoDB Dependency** | 🔄 OPTIONAL | Can run without MongoDB when `READ_FROM_POSTGRESQL=true` |
| **Frontend** | ⏸️ UNCHANGED | Still using MongoDB ObjectIds |

**What Works Now**:
- All data successfully migrated from MongoDB to PostgreSQL
- Reference data: categories (15), payment methods (14), tags (9)
- Transactions: All raw data from Venmo, Splitwise, Stripe, Cash
- Line items: All line items with proper foreign keys
- Events: All events with line item and tag relationships
- Bank accounts: 18 accounts migrated
- Users: 2 users migrated
- Dual-write: All write operations update both databases
- Read cutover: PostgreSQL reads implemented, controlled by `READ_FROM_POSTGRESQL` flag

**Next Steps** (Phase 6):
1. Enable `READ_FROM_POSTGRESQL=true` in production
2. Monitor for 2+ weeks
3. Remove MongoDB dependencies
4. Update frontend to use PostgreSQL IDs (optional)

---

## Migration Philosophy

**Goal**: Migrate existing MongoDB data structure to PostgreSQL with proper relationships, foreign keys, and transactions. This is a **1:1 structural migration**, not a feature addition project.

**Out of Scope** (for this migration):
- Multi-user support (user_id on everything)
- Category hierarchies
- Automatic deduplication
- New features or business logic changes
- Soft deletes (deleted_at field) - **Phase 7**
- Additional fields (institution_name, last_four, color) - **Phase 7**

**In Scope**:
- Move data from MongoDB to MySQL
- Add foreign key constraints
- Use transactions for data integrity
- Keep existing single-user model
- Use Stripe-style IDs (prefixed strings)
- Use Pydantic for API validation
- Maintain current functionality exactly as-is (hard deletes, existing fields only)

---

## Key Design Decisions

Based on feedback, this migration plan has been simplified:

### 1. Stripe-Style IDs with ULID (Not Auto-Increment)
Format: `{prefix}_{ulid}` (e.g., `evt_01JA8QM9TNWQ3BK42G5YZH3K0P`)

**Why**: Human-readable, type-safe, debuggable, time-sortable (better PostgreSQL performance), matches modern API design

### 2. No user_id Fields (Single User For Now)
All tables remain single-user. We can add `user_id` later when needed without breaking changes.

**Why**: Keeps migration simple, focused on structural improvements

**Authentication**: Since this is a single-user application, authentication will use environment-based credentials rather than a database table. See authentication strategy below.

### 3. No Category Hierarchy
Simple flat list of categories - no parent/child relationships.

**Why**: Not needed for current use case, adds unnecessary complexity

### 4. Pydantic for Validation
SQLAlchemy for ORM + Pydantic for request/response validation.

**Why**: Type safety, automatic validation, better error messages, modern Python best practice

### 5. 1:1 Migration
Current MongoDB structure → MySQL structure with minimal changes to business logic.

**Why**: Reduces risk, keeps migration scope manageable, improvements come from DB features not code changes

### 6. All Line Items Must Have Transactions
**No manual line items** - even manual/cash entries must create a transaction first.

**Why**:
- Maintains referential integrity (transaction_id stays NOT NULL)
- Provides complete audit trail
- Simplifies data model
- Every expense has a source

**Implementation**: Manual entries create a "manual" transaction with source='manual'

### 7. Environment-Based Authentication (Single User)

**Authentication config available in** `migration_examples/utils/auth_config.py`

Single-user authentication using environment variables:
- `ADMIN_USERNAME` - Username (default: "admin")
- `ADMIN_PASSWORD_HASH` - Bcrypt hash of password

**No users table needed** - MongoDB users collection not migrated. Add auth config to `server/config.py` in Phase 1.

---

## Proposed MySQL Schema

### Design Principles
1. **Stripe-style IDs** - Human-readable prefixes (evt_xxx, li_xxx, cat_xxx, etc.)
2. **Normalized structure** - Eliminate data redundancy
3. **Foreign keys everywhere** - Enforce referential integrity
4. **Timestamps on all tables** - Full audit trail
5. **Immutable source data** - Original transactions never modified
6. **Single user app** - No user_id fields (can add later if multi-user support needed)

---

### ID Generation Strategy

**ID generator available in** `migration_examples/utils/id_generator.py`

Using ULID (Universally Unique Lexicographically Sortable Identifier):
- Format: `{prefix}_{ulid}` (e.g., `evt_01ARZ3NDEKTSV4RRFFQ69G5FAV`)
- Time-sortable (IDs sort by creation time)
- Better PostgreSQL performance (sequential inserts, less index fragmentation)
- Collision-resistant (80 bits of randomness per millisecond)

Copy to `server/utils/id_generator.py` in Phase 1.

---

### SQL Schema Definition

**Complete SQL schema available in** `migration_examples/schema.sql`

The schema includes:
- **Reference Tables**: categories, payment_methods, tags
- **Transaction Tables**: transactions (immutable source), line_items (normalized view)
- **Event Tables**: events (user groupings), event_line_items & event_tags (junctions)
- **Views**: uncategorized_line_items, event_totals, monthly_category_totals

Run in Phase 1:
```bash
mysql -u budgit_user -p budgit < migration_examples/schema.sql
```

---

## Migration Strategy: Incremental Dual-Write

### Phase 0: Pre-Migration Validation & Data Cleanup (Week 1)
**Goal**: Validate MongoDB data quality, fix issues proactively, and prepare for migration

#### Script 1: Comprehensive Data Audit

Create `server/migrations/phase0_data_audit.py` to validate data quality before migration:

**Key Validations:**
- **Line Items**: Check for missing/invalid dates, amounts, descriptions, payment_methods
- **Events**: Verify dates, descriptions, categories exist, line_items are valid references
- **Reference Data**: Ensure categories and payment methods have names
- **Transactions**: Count raw transaction records by source

Create `server/migrations/phase0_data_audit.py` to validate MongoDB data quality. Check for:
- Missing required fields (date, amount, description)
- Invalid data types
- Broken references (categories, payment methods)
- Orphaned records

Run: `python migrations/phase0_data_audit.py`

If issues found, create `phase0_data_cleanup.py` to fix them before proceeding.

Run with confirmation prompt. Re-run audit script after cleanup to verify.

#### Phase 0 Steps

1. **Create MongoDB backup**
   ```bash
   mongodump --db flask_db --out /backup/pre_migration_$(date +%Y%m%d_%H%M%S)
   ```

2. **Run data audit**
   ```bash
   cd server
   python migrations/phase0_data_audit.py
   ```

3. **Fix data issues** (if audit fails)
   ```bash
   # Review errors in audit output
   # Modify phase0_data_cleanup.py as needed for your specific issues
   python migrations/phase0_data_cleanup.py

   # Re-run audit
   python migrations/phase0_data_audit.py
   ```

4. **Repeat until audit passes** - The audit must pass with zero errors before proceeding to Phase 1

**Deliverable**: Clean MongoDB data with zero audit errors, baseline snapshot, documented statistics

---

### Phase 1: Setup PostgreSQL (Week 2)
**Goal**: Get PostgreSQL running alongside MongoDB with no production impact

1. **Install PostgreSQL**
   ```bash
   # macOS
   brew install postgresql@16
   brew services start postgresql@16

   # Create database
   psql postgres
   CREATE DATABASE budgit ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8';
   CREATE USER budgit_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE budgit TO budgit_user;
   \q
   ```

   **Note on Foreign Key Constraints**: PostgreSQL enforces foreign key constraints automatically. All foreign key relationships defined in `schema.sql` will be enforced by the database with better error messages than MySQL.

2. **Add SQLAlchemy to requirements**
   ```python
   # requirements.txt
   SQLAlchemy==2.0.23
   psycopg2-binary==2.9.11  # PostgreSQL adapter
   alembic==1.13.1  # For migrations
   pydantic==2.5.0  # For request/response validation
   python-ulid==2.2.0  # For time-sortable IDs (imports as: from ulid import ULID)
   werkzeug==3.0.1  # For password hashing (if using environment-based auth)
   ```

3. **Create SQLAlchemy models** (see complete models section below - no User model for single-user app)

4. **Initialize Alembic for migrations**
   ```bash
   cd server
   alembic init alembic
   # Edit alembic/env.py to import DATABASE_URL from constants
   ```

5. **Run initial migration**
   ```bash
   alembic revision --autogenerate -m "Initial schema"
   alembic upgrade head
   ```

6. **Test database connection**: Create `test_postgresql_connection.py` that tests engine connection with `SELECT 1`, creates/commits/deletes a test Category to verify models work

**Deliverable**: PostgreSQL running with schema, connection tested, no production code changed

---

### Phase 2: Migrate Reference Data (Week 3)
**Goal**: Migrate reference tables (categories, payment methods, and tags)

#### 2.1 Migrate Categories and Payment Methods

1. **Migrate categories:**
   ```bash
   cd server
   source env/bin/activate
   python migrations/phase2_migrate_categories.py
   ```

2. **Migrate payment methods:**
   ```bash
   python migrations/phase2_migrate_payment_methods.py
   ```

3. **Verify migrations:**
   ```bash
   python migrations/phase2_verify.py
   ```

**Pattern Used:**
- Categories created from `CATEGORIES` constant (15 records)
- Payment methods deduplicated from MongoDB `accounts` collection (18 → 14 records)
- Stripe-style IDs with ULID: `cat_xxx`, `pm_xxx`
- Idempotent scripts (safe to re-run)
- Built-in verification

#### 2.2 Tags - Migrate in Phase 2 or Phase 4

**MongoDB Data:**
- No `tags` collection exists
- Tags stored as string arrays on events: `tags: ["Advika Trip", "Dubai"]`
- 1,119 out of 2,998 events have tags (37%)
- 9 unique tags total: "Advika 2025 Trip", "Advika Shopping", "Advika Trip", "Bois Trip 2025", "Dubai", "Laver Cup", "Moving", "Onsite", "Yosemite"

**Migration Options:**

**Option A: Migrate in Phase 2 (Recommended)**
- Extract unique tags from MongoDB events now
- Create `Tag` records with IDs like `tag_xxx`
- Simpler Phase 4 (just migrate event-tag relationships)

**Option B: Defer to Phase 4**
- Extract tags during event migration
- Create tags and event_tags junction table entries together
- Single migration script for all event-related data

**Recommendation**: **Option A** - Migrate tags in Phase 2 alongside other reference data for consistency.

**Implementation:**
   ```bash
   python migrations/phase2_migrate_tags.py  # Script to create
   ```

5. **Verify data consistency:**
   ```bash
   python migrations/phase2_verify.py
   ```

   This runs automated checks for:
   - Record counts (categories, payment methods, tags)
   - Data integrity (all records migrated)

**Deliverable**: Categories, payment methods, and tags migrated to PostgreSQL with verification.

---

### Phase 3: Migrate Transactions & Line Items (Week 4-5) ✅ COMPLETE
**Goal**: Historical data in PostgreSQL, dual-write for new transactions

**Status**: COMPLETE - All historical data migrated, dual-write operational for all refresh endpoints

**Migration Scripts**:
- `migrations/phase3_migrate_transactions.py` - Migrated historical transactions from raw data collections
- `migrations/phase3_migrate_line_items.py` - Migrated historical line items with foreign key linkage
- `migrations/phase3_verify.py` - Verified data consistency between MongoDB and PostgreSQL
- `migrations/phase3_reconcile.py` - Automated reconciliation of any sync failures

**Dual-Write Implementation**:
- `utils/dual_write.py` - Created with `dual_write_operation()` helper
- All refresh endpoints updated: Venmo, Splitwise, Stripe, Cash
- Strategy: Both MongoDB and PostgreSQL writes must succeed
- **Strong consistency**: Operations fail if either database write fails
- Comprehensive error logging with `DUAL_WRITE_FAILURE:` marker

**Data Migration Results**:
- Transactions: All raw data collections migrated to `transactions` table
- Line Items: All line items migrated with `mongo_id` for ID coexistence
- Foreign Keys: Payment methods and transactions properly linked
- Verification: All counts match between databases

**Deliverable**: ✅ All transactions and line items in PostgreSQL, dual-write operational

---

### Phase 4: Migrate Events with ID Coexistence (Week 6-7) ✅ COMPLETE
**Goal**: Events and relationships in PostgreSQL, API accepts both MongoDB and PostgreSQL IDs during transition

**Status**: COMPLETE - All events migrated, dual-write operational for event operations

**Migration Scripts**:
- `migrations/phase4_migrate_events.py` - Migrated historical events with relationships
- `migrations/phase4_verify.py` - Verified event and tag data consistency

**Implementation Details**:
- Events migrated with `mongo_id` for ID coexistence
- Tags extracted from MongoDB events and migrated to PostgreSQL
- EventLineItem and EventTag junction tables populated
- Event create/delete operations use dual-write pattern

**Dual-Write Implementation**:
- Event creation: `POST /api/events` writes to both databases
- Event deletion: `DELETE /api/events/<id>` writes to both databases
- ID coexistence: Endpoints accept both PostgreSQL and MongoDB IDs

**Frontend compatibility**: No frontend changes needed during Phases 0-5. Frontend continues using MongoDB ObjectIds.

**Deliverable**: ✅ All events in PostgreSQL, dual-write operational for event CRUD

---

### Phase 5: Switch Read Operations (Week 8) ✅ COMPLETE
**Goal**: Read from PostgreSQL, still dual-write to both

**Status**: COMPLETE - All 223 tests passing, including 26 Phase 5 tests

1. ✅ Feature flag `READ_FROM_POSTGRESQL` in `constants.py` (default: false)
2. ✅ All read functions in `dao.py` route to PostgreSQL when flag enabled
3. ✅ ID coexistence via `mongo_id` column supports both PostgreSQL and MongoDB IDs
4. ✅ All collections: line_items, events, transactions, bank_accounts, users

**Next**: Enable `READ_FROM_POSTGRESQL=true` in production, monitor for 2+ weeks before Phase 6

**Deliverable**: All reads from PostgreSQL, writes to both databases

#### Verify Database Sync

Run all verifications:
```bash
python migrations/verify_all.py          # Thorough (5-10 min)
python migrations/verify_all.py --quick  # Quick (1-2 min)
```

Runs Phase 2, 3, 4, and 5.5 verifications. Run weekly during dual-write period and before Phase 6.

Individual phase scripts:
```bash
python migrations/phase2_verify.py
python migrations/phase3_verify.py --thorough
python migrations/phase4_verify.py --thorough
python migrations/phase5_5_verify.py
```

---

### Phase 5.5: Migrate Bank Accounts & Users (Week 8.5) ✅ COMPLETE
**Goal**: Complete MongoDB independence

**Status**: COMPLETE - MongoDB can be fully offline when `READ_FROM_POSTGRESQL=true`

**Implementation**:
- BankAccount and User models in `models/sql_models.py`
- Historical data migrated: 18 bank accounts, 2 users
- Dual-write in `resources/stripe.py` and `resources/auth.py`
- Read functions in `dao.py`
- Migration scripts: `phase5_5_migrate_accounts_users.py`, `phase5_5_verify.py`
- 6 new tests in `test_phase5_read_cutover.py`

---

### Phase 6: Remove MongoDB & Update Frontend (Week 9) 🔜 NEXT
**Goal**: PostgreSQL only, MongoDB decommissioned, frontend updated for new IDs

**Current State**:
- All data migrated to PostgreSQL (Phases 2-5.5)
- Dual-write operational for all write operations
- Read operations can use PostgreSQL (via `READ_FROM_POSTGRESQL` flag)
- Default: Still reading from MongoDB (`READ_FROM_POSTGRESQL=false`)

**Prerequisites Before Starting Phase 6**:
- ✅ Enable `READ_FROM_POSTGRESQL=true` in production
- ⏳ Monitor for 2+ weeks with PostgreSQL reads enabled
- ⏳ Ensure all tests pass with `READ_FROM_POSTGRESQL=true`
- ⏳ Verify data consistency via periodic verification scripts

**Phase 6 Steps**:

1. **Enable PostgreSQL reads in production**:
   - Set `READ_FROM_POSTGRESQL=true` in production environment
   - Monitor application performance and error rates
   - Run verification scripts daily

2. **Update frontend to use Stripe-style IDs** (when ready):
   - Create TypeScript types for EventId, LineItemId, etc. with template literal types (`evt_${string}`)
   - Add ID validators
   - Update Event and LineItem interfaces to use typed IDs

3. **Remove dual-write code**:
   - Delete all MongoDB write operations
   - Remove `mongo_db` imports from endpoints
   - Clean up dao.py MongoDB functions

4. **Remove MongoDB dependencies**:
   - Remove pymongo and flask-pymongo from requirements.txt
   - Remove `MONGO_URI` from constants.py
   - Remove PyMongo initialization from application.py

5. **Clean up coexistence fields**:
   - Drop `mongo_id` columns from tables via Alembic migration
   - Remove legacy ID handling from serialization functions

6. **Archive MongoDB data**:
   ```bash
   mongodump --db flask_db --out /backup/mongodb_archive_$(date +%Y%m%d_%H%M%S)
   ```

7. **Shut down MongoDB**:
   ```bash
   brew services stop mongodb-community
   ```

8. **Final verification**:
   - Run SQL queries to verify row counts, foreign key constraints
   - Test all API endpoints
   - Verify application works with MongoDB completely offline

**Deliverable**: PostgreSQL only, MongoDB removed, frontend updated, final verification complete

---

## Technology Stack Changes

### Remove
```python
# requirements.txt
pymongo==4.5.0
flask-pymongo==2.3.0
```

### Add
```python
# requirements.txt
SQLAlchemy==2.0.23
psycopg2-binary==2.9.11  # PostgreSQL adapter
alembic==1.13.1
pydantic==2.5.0     # For request/response validation
python-ulid==2.2.0  # For time-sortable IDs (imports as: from ulid import ULID)
```

### Configuration Changes
```python
# Old: constants.py
MONGO_URI = os.getenv("LIVE_MONGO_URI", "mongodb://localhost:27017/test_db")

# New: constants.py
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://budgit_user:password@localhost:5432/budgit"
)
```

---

## Code Examples

**Complete code examples have been extracted to `server/migration_examples/` directory** to keep this document concise.

See `migration_examples/README.md` for full documentation.

### Quick Reference

**SQLAlchemy Models** (`migration_examples/models/sql_models.py`):
- Category, PaymentMethod, Tag, Transaction, LineItem, Event
- Includes relationships, foreign keys, and computed properties
- Copy to `server/models/sql_models.py` in Phase 1

**Pydantic Schemas** (`migration_examples/schemas/event_schemas.py`):
- EventCreateRequest, EventResponse, LineItemResponse
- Request validation and response serialization
- Copy to `server/schemas/` in Phase 1

**Database Session** (`migration_examples/models/database.py`):
- SQLAlchemy engine and session configuration
- Copy to `server/database.py` in Phase 1

**Reusable Templates**:
- `migration_examples/templates/migration_template.py` - Generic migration pattern for reference data
- `migration_examples/templates/verification_template.py` - Generic verification pattern for all phases

**Tests** (`migration_examples/tests/test_models.py`):
- Unit tests demonstrating model usage
- Run with: `pytest migration_examples/tests/ -v`

### Key Patterns for Route Implementation

When updating routes to use SQLAlchemy + Pydantic:

1. **Pydantic Validation**: Use `EventCreateRequest(**request.get_json())` with try/except ValidationError
2. **Database Queries**: `db.query(Event).filter(...).order_by(...).all()`
3. **Foreign Key Lookups**: Look up by name first, then use the ID (`category.id`)
4. **Junction Table Creation**: Create EventLineItem with `generate_id("eli")`
5. **Response Serialization**: `EventResponse.from_orm(event).model_dump()`
6. **Transactions**: Use `with db.begin():` for atomic multi-step operations

**Key Improvements**: Pydantic validation, type hints, DB transactions, enforced FK constraints, cascade deletes, no manual relationship sync

---

## Query Performance Comparison

**MongoDB (Current)**: Requires manual relationship lookups (separate queries + manual dictionary mapping) and aggregation pipelines for joins.

**PostgreSQL (With Indexes)**: Single JOIN queries with automatic relationship loading via SQLAlchemy. Uses `uncategorized_line_items` view for finding unassigned items. Native JSONB support for querying transaction source data.

**Expected Performance**: 2-5x faster for complex queries with JOINs, especially for category/tag filtering and uncategorized item lookups. JSONB queries significantly faster than parsing JSON strings.

---

## Testing Strategy

**Complete unit tests available in** `migration_examples/tests/test_models.py`

### Test Coverage

**Unit Tests** (in-memory SQLite):
- Creating events with line items via junction table
- Foreign key constraint enforcement
- Event total amount calculation (normal and duplicate)
- Relationship loading and traversal

Run tests:
```bash
pytest migration_examples/tests/test_models.py -v
```

### Important: Foreign Key Enforcement

**SQLite (for tests)**: Foreign key constraints must be explicitly enabled via `PRAGMA foreign_keys=ON` when creating the database connection. This is already configured in `migration_examples/tests/test_models.py` using a SQLAlchemy event listener:

```python
@sqlalchemy.event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

**PostgreSQL (for production)**: Foreign key constraints are enforced by default. No special configuration needed. The schema in `migration_examples/schema.sql` already defines all foreign key constraints with `ON DELETE CASCADE` or `ON DELETE RESTRICT` as appropriate. PostgreSQL provides superior error messages for constraint violations compared to other databases.

**Integration Tests** (during dual-write period):
- Data consistency checks between MongoDB and PostgreSQL
- Count verification across all entities
- Spot checks comparing field values via `mongo_id`
- Use `migration_examples/templates/verification_template.py` for automated checks

---

## Rollback Plan

If migration fails at any phase:

### During Phases 0-5 (Dual-Write Period)

1. **Set feature flag to read from MongoDB**
   ```bash
   export READ_FROM_POSTGRESQL=false
   ```

2. **Stop dual-writes to PostgreSQL (optional)**
   ```python
   # Comment out PostgreSQL write code in affected endpoints
   # Keep MongoDB writes active
   ```

3. **MongoDB is still primary** - no data loss
   - All user-facing operations continue with MongoDB
   - PostgreSQL data can be dropped and re-migrated
   - Frontend unaffected due to ID coexistence pattern

4. **Analyze what went wrong**
   - Check migration logs: `server/logs/migration.log`
   - Verify data consistency with verification scripts
   - Review performance metrics from monitoring
   - Check mongo_id coexistence fields for inconsistencies

5. **Fix issues and retry**
   - Drop MySQL tables: `DROP DATABASE budgit; CREATE DATABASE budgit;`
   - Re-run failed migration phase
   - Verify with phase-specific verification script

### After Phase 6 (MongoDB Removed)

**WARNING**: After Phase 6, MongoDB is shut down. Rollback requires:

1. **Restore MongoDB from backup**
   ```bash
   mongorestore /backup/pre_migration_YYYYMMDD_HHMMSS/
   ```

2. **Reverse migrate new PostgreSQL data to MongoDB**
   ```python
   # Migrate any data created in PostgreSQL after Phase 6 back to MongoDB
   # This is complex and should be avoided by thorough testing before Phase 6
   ```

3. **Update frontend** - Revert frontend changes if deployed

4. **High risk** - Avoid needing to rollback after Phase 6 through:
   - Extensive testing in Phases 0-5
   - Gradual rollout with monitoring
   - User acceptance testing before Phase 6

**Best Practice**: Run Phases 0-5 in production for at least 2 weeks before Phase 6 to ensure stability.

---

## Benefits Summary

| Aspect | MongoDB (Current) | PostgreSQL (Proposed) |
|--------|------------------|----------------------|
| **Referential Integrity** | Manual | Automatic (FK) ✅ |
| **Transactions** | Requires replica set | Built-in ACID ✅ |
| **Schema Validation** | Application code | Database + Pydantic ✅ |
| **Query Performance** | Aggregation pipelines | JOINs with indexes ✅ |
| **Data Consistency** | Manual sync | Foreign keys ✅ |
| **Type Safety** | Weak | Strong (DECIMAL + Pydantic) ✅ |
| **Relationships** | Manual | Declarative (ORM) ✅ |
| **Cascading Deletes** | Manual | Automatic (ON DELETE) ✅ |
| **Debugging** | Harder | Easier (SQL logs) ✅ |
| **Tooling** | Limited | Extensive (pgAdmin, DBeaver, etc.) ✅ |
| **ID Format** | ObjectId/Custom | Stripe-style prefixed ✅ |
| **JSON Support** | Native BSON | Native JSONB with indexing ✅ |
| **Timezone Support** | Basic | TIMESTAMP WITH TIME ZONE ✅ |

---

## Timeline

| Phase | Duration | Status | Description |
|-------|----------|--------|-------------|
| 0. Pre-Migration Validation | 1 week | ✅ COMPLETE | Data audit, quality checks, baseline metrics |
| 1. Setup PostgreSQL | 1 week | ✅ COMPLETE | Install, create schema, add ID generator, test connection |
| 2. Migrate Reference Data | 1 week | ✅ COMPLETE | Categories, payment methods, tags with verification |
| 3. Migrate Transactions & Line Items | 2 weeks | ✅ COMPLETE | Historical data + mongo_id coexistence + dual-write for all refresh endpoints |
| 4. Migrate Events & ID Coexistence | 2 weeks | ✅ COMPLETE | Events + tags + dual-write for event create/delete |
| 5. Switch Reads | 2 weeks | ✅ COMPLETE | PostgreSQL read operations with feature flag, still dual-write |
| 5.5. Migrate Bank Accounts & Users | 3 days | ✅ COMPLETE | Complete MongoDB independence capability |
| 6. Remove MongoDB & Update Frontend | 1 week | 🔜 NEXT | Enable PG reads in production, monitor, remove MongoDB |
| **Migration Total** | **10 weeks** | **Phase 5.5 Complete** | Safe, incremental, with comprehensive safeguards |
| **7. Enhancements** | TBD | FUTURE | Soft deletes, additional fields, optimizations (see Phase 7 below) |

**Current State (as of migration-5 branch)**:
- ✅ All historical data migrated to PostgreSQL
- ✅ Dual-write operational for all write operations
- ✅ PostgreSQL read operations implemented (feature flag: `READ_FROM_POSTGRESQL`)
- ⏸️ Default: Still reading from MongoDB (`READ_FROM_POSTGRESQL=false`)
- 🎯 Next: Enable `READ_FROM_POSTGRESQL=true`, monitor, then remove MongoDB

**Critical Success Factors**:
- ✅ Phase 0 validation passed before proceeding
- ✅ Each phase includes data verification scripts
- ✅ ID coexistence pattern maintains frontend compatibility during transition
- ✅ Dual-write period (Phases 3-5.5) allows safe rollback
- ✅ Monitoring tracks query performance and errors
- ⏳ Run in production with `READ_FROM_POSTGRESQL=true` for 2+ weeks before Phase 6

---

## Phase 7: Post-Migration Enhancements

After the migration is complete and MySQL is the sole database, these enhancements can be added as separate features:

### 1. Soft Deletes
**What**: Add `deleted_at` timestamp to events table for recoverable deletion
```sql
ALTER TABLE events ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE events ADD INDEX idx_deleted (deleted_at);
```

**Why**:
- Recover from accidental deletions
- Maintain audit trail of deleted events
- Allows "undelete" functionality

**Implementation**:
- Update DELETE endpoints to set `deleted_at` instead of removing records
- Filter queries to exclude `WHERE deleted_at IS NULL`
- Add admin endpoint to permanently purge old soft-deleted records

---

### 2. Additional Payment Method Fields
**What**: Add institution details to payment methods
```sql
ALTER TABLE payment_methods ADD COLUMN institution_name VARCHAR(255) NULL;
ALTER TABLE payment_methods ADD COLUMN last_four VARCHAR(4) NULL;
```

**Why**:
- Better display in UI (show "Chase ...1234" instead of just "Chase Sapphire")
- Easier to distinguish multiple cards from same bank
- Matches how Stripe and Plaid display payment methods

---

### 3. Tag Colors
**What**: Add visual color coding to tags
```sql
ALTER TABLE tags ADD COLUMN color VARCHAR(7) NULL COMMENT 'Hex color code like #FF5733';
```

**Why**:
- Visual categorization in UI
- Better UX for quickly identifying tag types
- Common feature in tagging systems

---

### 4. Additional Optimizations to Consider

**Database Views** (already in migration schema):
- `uncategorized_line_items` - Pre-computed view of unassigned line items
- `event_totals` - Pre-computed event amounts
- `monthly_category_totals` - Pre-aggregated spending by month/category

**Indexes** (add if needed based on query patterns):
```sql
-- For date range queries
ALTER TABLE line_items ADD INDEX idx_date_amount (date, amount);

-- For payment method reporting
ALTER TABLE line_items ADD INDEX idx_payment_date (payment_method_id, date);
```

**Read Replicas** (if needed for scaling):
- Set up MySQL read replica for reporting queries
- Keep writes on primary instance
- Route analytics queries to replica

---

### 5. Future Feature Additions (Out of Scope)

These are **not** part of the 1:1 migration and should be separate projects:

- **Multi-user support**: Add `user_id` to all tables, add row-level security
- **Category hierarchies**: Parent/child category relationships
- **Automatic deduplication**: ML-based duplicate transaction detection
- **Budgeting features**: Budget table, spending limits, alerts
- **Recurring transactions**: Template-based transaction creation
- **Split transactions**: Single line item split across multiple categories
- **Multi-currency**: Currency fields and conversion rates
- **Receipt attachments**: File uploads linked to events
- **Collaborative features**: Shared events, comments, approvals

---

## Next Steps

1. **Review this plan** - Discuss and adjust timeline
2. **Set up local MySQL** - Get familiar with MySQL
3. **Create SQL schema** - Run the DDL statements
4. **Write migration scripts** - Start with users table
5. **Implement dual-write** - Auth endpoints first
6. **Test thoroughly** - Data consistency checks
7. **Execute phase by phase** - Incremental rollout

---

## Questions to Answer

1. **Hosting**: Where will PostgreSQL run in production? (Supabase, AWS RDS, DigitalOcean, Render?)
2. **Backups**: What's the backup strategy? (Automated daily backups via hosting provider?)
3. **Monitoring**: How will we monitor PostgreSQL? (Built-in pgAdmin, CloudWatch, DataDog?)
4. **Scaling**: What's the read/write pattern? (Need read replicas?)
5. **Dev/Staging**: Do we need separate PostgreSQL instances for dev/staging?
