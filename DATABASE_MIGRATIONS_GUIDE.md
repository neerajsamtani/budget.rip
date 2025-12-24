# Database Migrations Guide for Budget.rip

**Goal:** Master database schema changes with Alembic, including automated migrations in CI/CD and safe rollback strategies.

**Prerequisites:** Complete `DOCKER_GUIDE.md` and `CI_CD_GUIDE.md`.

**Time:** 2-3 hours

---

## Part 1: Understanding Database Migrations (20 min)

### The Problem Without Migrations

```python
# Week 1: Your code
user = {"name": "Alice", "email": "alice@example.com"}

# Week 2: You add a phone field
user = {"name": "Alice", "email": "alice@example.com", "phone": "555-1234"}

# Problem: Existing users in the database don't have the phone field!
# How do you update the schema for millions of existing rows?
```

### What Are Migrations?

**Migrations** are version-controlled, incremental changes to your database schema.

```
Initial Schema (v1)          Add Phone (v2)              Add Address (v3)
┌─────────────────┐         ┌─────────────────┐        ┌─────────────────┐
│ users           │         │ users           │        │ users           │
├─────────────────┤         ├─────────────────┤        ├─────────────────┤
│ id              │  ─────> │ id              │ ────>  │ id              │
│ name            │         │ name            │        │ name            │
│ email           │         │ email           │        │ email           │
└─────────────────┘         │ phone           │        │ phone           │
                            └─────────────────┘        │ address         │
                                                       └─────────────────┘
     migration_001.py           migration_002.py          migration_003.py
```

### Why Alembic?

Alembic is a migration tool for SQLAlchemy (which you're already using).

**Key features:**
- **Auto-generate**: Compares your models to the database and creates migrations
- **Version control**: Each migration has a unique ID and tracks dependencies
- **Upgrade/Downgrade**: Can move forward or backward through versions
- **Branching**: Supports multiple migration paths (advanced)

---

## Part 2: Understanding Your Existing Setup (30 min)

You already have Alembic configured! Let's understand it.

### Exercise 1: Explore Your Migrations

```bash
cd server

# View current database version
alembic current

# View migration history
alembic history

# View pending migrations (not yet applied)
alembic history --verbose
```

**Your migrations directory:**
```
server/
├── alembic/
│   ├── env.py                    # Alembic configuration
│   ├── script.py.mako           # Template for new migrations
│   └── versions/                # All migration files
│       ├── e8f383ab67fa_initial_postgresql_schema.py
│       ├── 9a34125f75b2_add_bank_accounts_and_users_tables.py
│       └── fb7a20ffd5fe_add_currency_and_balance_fields.py
└── alembic.ini                   # Alembic settings
```

### Exercise 2: Anatomy of a Migration

Open `server/alembic/versions/fb7a20ffd5fe_add_currency_and_balance_fields_to_bank_.py`:

```python
# Metadata
revision = "fb7a20ffd5fe"         # Unique ID for this migration
down_revision = "89d79c1aa775"    # Previous migration (creates a chain)

def upgrade() -> None:
    """Apply the migration (moving forward)"""
    op.add_column("bank_accounts", sa.Column("currency", sa.String(3)))
    op.add_column("bank_accounts", sa.Column("latest_balance", sa.DECIMAL(12, 2)))

def downgrade() -> None:
    """Revert the migration (moving backward)"""
    op.drop_column("bank_accounts", "latest_balance")
    op.drop_column("bank_accounts", "currency")
```

**Key concepts:**
- **revision**: This migration's ID
- **down_revision**: Parent migration (forms a linked list)
- **upgrade()**: SQL to apply changes
- **downgrade()**: SQL to undo changes

**Check your understanding:**
- What happens if you run `alembic upgrade head`?
- What happens if you run `alembic downgrade -1`?
- Why is the order of `drop_column` reversed in downgrade?

<details>
<summary>Answers</summary>

- Applies all pending migrations up to the latest
- Reverts the most recent migration
- Columns must be dropped in reverse order to avoid dependency issues
</details>

---

## Part 3: Creating Migrations (45 min)

### Auto-Generate vs Manual Migrations

| Method | When to Use |
|--------|-------------|
| **Auto-generate** | Adding/removing/modifying columns, tables, indexes |
| **Manual** | Data migrations, complex schema changes, custom SQL |

### Exercise 3: Auto-Generate a Migration

Let's add a new field to track when users last logged in.

**1. Update your SQLAlchemy model:**

```python
# server/models/sql_models.py
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(100))
    last_login = Column(TIMESTAMP(timezone=True), nullable=True)  # NEW FIELD
```

**2. Generate the migration:**

```bash
cd server
alembic revision --autogenerate -m "Add last_login to users"
```

**3. Review the generated migration:**

```bash
# Alembic created: versions/abc123_add_last_login_to_users.py
cat alembic/versions/*_add_last_login_to_users.py
```

You should see:
```python
def upgrade() -> None:
    op.add_column('users', sa.Column('last_login', sa.TIMESTAMP(timezone=True), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'last_login')
```

**4. Apply the migration:**

```bash
alembic upgrade head
```

**5. Verify in database:**

```bash
# Connect to your local PostgreSQL
docker compose exec postgres psql -U budgit_user -d budgit

# In psql:
\d users
# Should show last_login column

\q
```

### Exercise 4: Manual Migration (Data Migration)

Sometimes you need to migrate data, not just schema. Let's say you want to set a default value for existing users.

**Create a manual migration:**

```bash
alembic revision -m "Set default last_login for existing users"
```

**Edit the generated migration:**

```python
def upgrade() -> None:
    """Set last_login to account creation date for existing users."""
    from sqlalchemy import text

    # Use raw SQL for data migrations
    op.execute(text("""
        UPDATE users
        SET last_login = created_at
        WHERE last_login IS NULL
    """))

def downgrade() -> None:
    """No downgrade needed for data migration."""
    # Setting last_login back to NULL would lose data
    # Document that this migration is not reversible
    pass
```

**Apply it:**

```bash
alembic upgrade head
```

---

## Part 4: Testing Migrations Locally (30 min)

Before deploying, always test migrations.

### Exercise 5: Full Migration Test Cycle

**1. Create a fresh test database:**

```bash
# Start with a clean database
docker compose down -v
docker compose up -d postgres

# Wait for postgres to be ready
sleep 5
```

**2. Apply all migrations from scratch:**

```bash
cd server
alembic upgrade head
```

**3. Verify the schema:**

```bash
docker compose exec postgres psql -U budgit_user -d budgit -c "\dt"
# Should list all tables

docker compose exec postgres psql -U budgit_user -d budgit -c "\d users"
# Should show all columns including last_login
```

**4. Test rollback (downgrade):**

```bash
# Downgrade one migration
alembic downgrade -1

# Check the database
docker compose exec postgres psql -U budgit_user -d budgit -c "\d users"
# last_login column should be gone

# Upgrade back
alembic upgrade head
```

**5. Test with actual data:**

```bash
# Insert test data
docker compose exec postgres psql -U budgit_user -d budgit -c "
INSERT INTO users (name, email, created_at)
VALUES ('Test User', 'test@example.com', NOW());
"

# Run migration
alembic upgrade head

# Verify data is intact
docker compose exec postgres psql -U budgit_user -d budgit -c "SELECT * FROM users;"
```

---

## Part 5: Migrations in CI/CD (60 min)

Now let's automate migrations before deployment.

### The Challenge

```
Old approach:
1. Deploy new code
2. Code tries to use new column
3. Column doesn't exist yet → 💥 Error
4. Manually SSH and run migrations
5. Restart app

Problem: Downtime + manual steps
```

### The Solution: Run Migrations Before Deployment

```
New approach:
1. Run migrations (add new column)
2. Deploy new code
3. Code finds the column → ✅ Works
4. Zero manual intervention
```

### Exercise 6: Add Migration Step to CI/CD

**Update `.github/workflows/ci-cd.yml`:**

```yaml
jobs:
  # ... existing test jobs ...

  # New job: Run migrations in CI to verify they work
  test-migrations:
    runs-on: ubuntu-latest
    needs: [test-backend]

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: budgit_user
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: budgit_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v4

    - name: Install uv
      uses: astral-sh/setup-uv@v3

    - name: Set up Python
      run: uv python install 3.12

    - name: Install dependencies
      run: cd server && uv sync

    - name: Test migrations (upgrade)
      run: cd server && uv run alembic upgrade head
      env:
        DATABASE_URL: postgresql://budgit_user:test_password@localhost:5432/budgit_test

    - name: Test migrations (downgrade)
      run: cd server && uv run alembic downgrade -1
      env:
        DATABASE_URL: postgresql://budgit_user:test_password@localhost:5432/budgit_test

    - name: Test migrations (re-upgrade)
      run: cd server && uv run alembic upgrade head
      env:
        DATABASE_URL: postgresql://budgit_user:test_password@localhost:5432/budgit_test

  deploy:
    needs: [build-and-push, test-migrations]  # Wait for migration tests
    # ... rest of deploy job ...
```

This ensures migrations are tested before deployment!

### Exercise 7: Run Migrations on VPS Before Deploy

**Update the deploy job:**

```yaml
deploy:
  runs-on: ubuntu-latest
  needs: [build-and-push, test-migrations]

  steps:
  - name: Run database migrations
    uses: appleboy/ssh-action@v1.0.0
    with:
      host: ${{ secrets.VPS_HOST }}
      username: ${{ secrets.VPS_USER }}
      key: ${{ secrets.SSH_PRIVATE_KEY }}
      script: |
        cd /home/deploy/budget.rip/server

        # Backup current migration state
        docker compose exec -T backend alembic current > /tmp/migration_backup.txt || echo "none" > /tmp/migration_backup.txt

        # Run migrations
        docker compose exec -T backend alembic upgrade head

        # Check if migrations succeeded
        if [ $? -ne 0 ]; then
          echo "Migration failed!"
          exit 1
        fi

  - name: Deploy application
    uses: appleboy/ssh-action@v1.0.0
    with:
      host: ${{ secrets.VPS_HOST }}
      username: ${{ secrets.VPS_USER }}
      key: ${{ secrets.SSH_PRIVATE_KEY }}
      script: |
        cd /home/deploy/budget.rip
        docker compose pull
        docker compose up -d --remove-orphans
```

**Important:** Migrations run BEFORE deploying new code.

---

## Part 6: Migration Rollback Strategies (45 min)

What happens if a migration or deployment fails?

### Strategy 1: Automatic Rollback on Migration Failure

**Update deploy workflow with rollback:**

```yaml
- name: Run migrations with rollback on failure
  uses: appleboy/ssh-action@v1.0.0
  with:
    host: ${{ secrets.VPS_HOST }}
    username: ${{ secrets.VPS_USER }}
    key: ${{ secrets.SSH_PRIVATE_KEY }}
    script: |
      cd /home/deploy/budget.rip/server

      # Get current migration version
      CURRENT_VERSION=$(docker compose exec -T backend alembic current 2>/dev/null | grep -oP '[a-f0-9]+' | head -1)
      echo "Current migration: $CURRENT_VERSION"

      # Try to upgrade
      if docker compose exec -T backend alembic upgrade head; then
        echo "Migrations succeeded"
      else
        echo "Migration failed! Rolling back..."
        if [ ! -z "$CURRENT_VERSION" ]; then
          docker compose exec -T backend alembic downgrade $CURRENT_VERSION
        fi
        exit 1
      fi
```

### Strategy 2: Rollback on Deployment Failure

```yaml
- name: Deploy with health check and rollback
  uses: appleboy/ssh-action@v1.0.0
  with:
    script: |
      cd /home/deploy/budget.rip

      # Store current image tags
      docker compose images > /tmp/old_images.txt

      # Deploy new version
      docker compose pull
      docker compose up -d

      # Wait for services to start
      sleep 10

      # Health check
      if curl -f http://localhost:4242/api/; then
        echo "Deployment successful"
      else
        echo "Health check failed! Rolling back..."

        # Rollback migrations
        cd server
        docker compose exec -T backend alembic downgrade -1

        # Rollback containers
        cd ..
        docker compose down
        # Use old images (stored in /tmp/old_images.txt)
        docker compose up -d

        exit 1
      fi
```

### Strategy 3: Blue-Green Deployments (Advanced)

For zero-downtime deployments:

1. Keep old version running (blue)
2. Start new version (green)
3. Run migrations (safe because old version still works)
4. Switch traffic to green
5. If issues, switch back to blue

This is complex and requires orchestration tools like Docker Swarm or Kubernetes.

---

## Part 7: Common Migration Patterns (30 min)

### Pattern 1: Adding a Non-Nullable Column

**Problem:** Can't add `NOT NULL` column to table with existing rows.

**Solution:** Three-step migration:

```python
# Migration 1: Add column as nullable
def upgrade():
    op.add_column('users', sa.Column('username', sa.String(50), nullable=True))

# Migration 2: Populate data
def upgrade():
    from sqlalchemy import text
    op.execute(text("UPDATE users SET username = email WHERE username IS NULL"))

# Migration 3: Make non-nullable
def upgrade():
    op.alter_column('users', 'username', nullable=False)
```

### Pattern 2: Renaming a Column

**Problem:** Renaming breaks old code that's still deployed.

**Solution:** Multi-step deployment:

```python
# Step 1: Add new column
def upgrade():
    op.add_column('users', sa.Column('full_name', sa.String(100)))
    # Copy data
    op.execute(text("UPDATE users SET full_name = name"))

# Deploy code that writes to both columns

# Step 2: Drop old column
def upgrade():
    op.drop_column('users', 'name')
```

### Pattern 3: Dropping a Table

**Problem:** Accidentally dropping a table with data.

**Solution:** Archive before dropping:

```python
def upgrade():
    # Create archive table
    op.rename_table('old_table', 'old_table_archived_20250120')

    # Add archive timestamp
    op.execute(text("""
        ALTER TABLE old_table_archived_20250120
        ADD COLUMN archived_at TIMESTAMP DEFAULT NOW()
    """))

def downgrade():
    # Can restore from archive if needed
    op.rename_table('old_table_archived_20250120', 'old_table')
    op.drop_column('old_table', 'archived_at')
```

### Pattern 4: Complex Data Migration

**Example:** Split full_name into first_name and last_name:

```python
def upgrade():
    # Add new columns
    op.add_column('users', sa.Column('first_name', sa.String(50)))
    op.add_column('users', sa.Column('last_name', sa.String(50)))

    # Migrate data with Python logic
    from sqlalchemy.orm import Session
    from models.sql_models import User

    bind = op.get_bind()
    session = Session(bind=bind)

    users = session.query(User).all()
    for user in users:
        if user.full_name:
            parts = user.full_name.split(' ', 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''

    session.commit()

    # Drop old column
    op.drop_column('users', 'full_name')
```

---

## Part 8: Zero-Downtime Migrations (20 min)

### The Problem

Traditional migrations cause downtime:

```
1. Take app offline
2. Run migrations
3. Deploy new code
4. Bring app online
```

For PlanetScale and other production databases, you want zero downtime.

### Backward-Compatible Migrations

**Rule:** New migrations must work with old code.

**Examples:**

✅ **Safe:**
- Adding a nullable column
- Adding a new table
- Adding an index
- Adding a column with a default value

❌ **Unsafe (causes downtime):**
- Dropping a column (old code tries to use it)
- Renaming a column
- Changing column type (might break old code)
- Making a column non-nullable

### Multi-Phase Migration Strategy

For unsafe changes, use multiple deployments:

**Phase 1: Add new, keep old**
```python
# Migration: Add new column
op.add_column('users', sa.Column('email_verified', sa.Boolean(), default=False))

# Deploy: Code writes to both old and new columns
```

**Phase 2: Switch reads**
```python
# Deploy: Code reads from new column, still writes to both
```

**Phase 3: Remove old**
```python
# Migration: Drop old column
op.drop_column('users', 'is_verified')

# Deploy: Code only uses new column
```

---

## Part 9: Troubleshooting (15 min)

### Issue 1: "Target database is not up to date"

```bash
# Problem: Alembic thinks database is at a different version

# Solution: Stamp the database with current version
alembic stamp head

# Or if you know the version:
alembic stamp abc123def456
```

### Issue 2: Migration conflict

```bash
# Problem: Two developers created migrations with same down_revision

# Solution: Merge the migration branches
alembic merge -m "merge branches" revision1 revision2
```

### Issue 3: Failed migration left database in bad state

```bash
# Check current state
alembic current

# Manually fix the database
psql $DATABASE_URL
# ... run SQL to fix ...

# Stamp as if migration succeeded
alembic stamp revision_id
```

### Issue 4: Need to skip a migration

```bash
# If a migration is problematic, you can skip it
alembic upgrade abc123  # Upgrade to specific version
alembic stamp def456    # Mark next version as current (without running)
```

---

## Part 10: Verification Checklist

By now, you should be able to:

- [ ] Explain what database migrations are and why they matter
- [ ] Understand Alembic's revision chain
- [ ] Create migrations using auto-generate
- [ ] Create manual data migrations
- [ ] Test migrations locally (upgrade and downgrade)
- [ ] Run migrations in CI/CD before deployment
- [ ] Implement automatic rollback on migration failure
- [ ] Handle rollback on deployment failure
- [ ] Apply common migration patterns (add column, rename, drop table)
- [ ] Plan zero-downtime migration strategies
- [ ] Troubleshoot failed migrations

---

## Final Exercise: Complete Migration Pipeline

**Objective:** Add a new feature with database changes and deploy it safely.

**Scenario:** Add a "premium user" feature.

**1. Create the migration:**

```bash
cd server
```

Edit `models/sql_models.py`:
```python
class User(Base):
    # ... existing columns ...
    is_premium = Column(Boolean, default=False, nullable=False)
    premium_since = Column(TIMESTAMP(timezone=True), nullable=True)
```

Generate migration:
```bash
alembic revision --autogenerate -m "Add premium user fields"
```

**2. Test locally:**

```bash
# Apply migration
alembic upgrade head

# Verify
docker compose exec postgres psql -U budgit_user -d budgit -c "\d users"

# Test rollback
alembic downgrade -1
alembic upgrade head
```

**3. Update CI/CD:**

The `test-migrations` job will automatically test this when you push.

**4. Deploy:**

```bash
git add .
git commit -m "Add premium user feature"
git push origin main

# Watch GitHub Actions:
# - Tests pass
# - Migrations tested
# - Images built
# - Migrations run on VPS
# - New code deployed
```

**5. Verify on VPS:**

```bash
ssh deploy@your-vps
cd /home/deploy/budget.rip
docker compose exec backend alembic current
# Should show your new migration

docker compose exec postgres psql -U budgit_user -d budgit -c "\d users"
# Should show is_premium and premium_since columns
```

**Success criteria:**
- ✅ Migration created and committed
- ✅ CI tests pass (including migration tests)
- ✅ Migration runs automatically on VPS before deploy
- ✅ Application works with new schema
- ✅ No downtime during deployment

---

## Best Practices Summary

1. **Always test migrations locally first**
2. **Never edit an applied migration** - create a new one
3. **Make migrations reversible** - implement downgrade()
4. **Keep migrations small** - one logical change per migration
5. **Run migrations before deploying code**
6. **Use transactions** - migrations should be atomic
7. **Test with production-like data** - edge cases matter
8. **Document complex migrations** - explain the "why"
9. **Plan for rollback** - have a backup strategy
10. **Monitor migration duration** - long migrations block deploys

---

## Next Steps

### Advanced Topics

1. **Branching migrations** - Multiple parallel migration paths
2. **Tenant-specific migrations** - Multi-tenant applications
3. **Large table migrations** - Handling millions of rows
4. **Online schema changes** - Tools like pt-online-schema-change
5. **Blue-green database deployments** - Separate DB per environment

### Recommended Reading

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Django Migrations (comparison)](https://docs.djangoproject.com/en/stable/topics/migrations/)
- [Liquibase (alternative tool)](https://www.liquibase.org/)
- [Zero-Downtime Deployments](https://www.braintreepayments.com/blog/safe-database-migrations/)

Congratulations! You now have automated, safe database migrations in your CI/CD pipeline.
