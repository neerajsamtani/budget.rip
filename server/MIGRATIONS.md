# Database Migrations

This document covers how to create, test, and deploy database migrations for Budgit.

## Overview

Budgit uses [Alembic](https://alembic.sqlalchemy.org/) for PostgreSQL schema migrations. Migrations are version-controlled Python scripts that modify the database schema.

## Local Development

### Common Commands

```bash
cd server

# Check current migration version
uv run alembic current

# View migration history
uv run alembic history

# Create a new migration (auto-generates from model changes)
uv run alembic revision --autogenerate -m "Add user preferences table"

# Apply all pending migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# Rollback to a specific revision
uv run alembic downgrade abc123
```

### Creating Migrations

1. **Modify your SQLAlchemy models** in `models/sql_models.py`

2. **Generate the migration:**
   ```bash
   uv run alembic revision --autogenerate -m "Description of change"
   ```

3. **Review the generated migration** in `alembic/versions/`. Alembic auto-detection isn't perfect—always verify:
   - Column types are correct
   - Nullable settings are intentional
   - No unintended changes were picked up

4. **Test locally:**
   ```bash
   uv run alembic upgrade head
   uv run alembic downgrade -1
   uv run alembic upgrade head
   ```

## Production Migrations

### Running Migrations via GitHub Actions

Production migrations are run manually via GitHub Actions workflow dispatch. This provides:
- **Visibility**: See exactly what will run before applying
- **Safety**: Requires explicit confirmation
- **Audit trail**: All runs are logged in GitHub Actions

#### Steps to Run Production Migrations

1. Go to **Actions** → **Run Database Migrations** in GitHub

2. Click **Run workflow**

3. Configure the run:
   | Option | Description |
   |--------|-------------|
   | `environment` | Target environment (production) |
   | `dry_run` | Set to `true` to preview without applying |
   | `confirm` | Type `migrate` to confirm (required when dry_run is false) |

4. **Always do a dry run first** to see pending migrations

5. If the dry run looks correct, re-run with:
   - `dry_run`: `false`
   - `confirm`: `migrate`

#### Required GitHub Secrets

The workflow requires these secrets configured in GitHub (Settings → Secrets → Actions):

| Secret | Description |
|--------|-------------|
| `DATABASE_HOST` | PostgreSQL host |
| `DATABASE_PORT` | PostgreSQL port (usually 5432) |
| `DATABASE_USERNAME` | Database user |
| `DATABASE_PASSWORD` | Database password |
| `DATABASE_NAME` | Database name |

#### Environment Protection (Recommended)

For additional safety, configure environment protection rules in GitHub:

1. Go to **Settings** → **Environments** → **production**
2. Enable **Required reviewers** and add yourself
3. Now migrations will require approval before running

## Writing Safe Migrations

### Backward-Compatible Migrations

Write migrations that work with both old and new code. This allows safe deployments:

```
1. Deploy migration (schema supports both old and new code)
2. Deploy new code
3. (Optional) Deploy cleanup migration later
```

### Examples

#### ✅ Safe: Adding a nullable column
```python
def upgrade():
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))

def downgrade():
    op.drop_column('users', 'phone')
```

#### ✅ Safe: Adding a column with default
```python
def upgrade():
    op.add_column('users', sa.Column('is_active', sa.Boolean(),
                                      nullable=False, server_default='true'))

def downgrade():
    op.drop_column('users', 'is_active')
```

#### ⚠️ Dangerous: Renaming a column (breaks old code)
```python
# DON'T do this in one migration!
def upgrade():
    op.alter_column('users', 'name', new_column_name='full_name')
```

#### ✅ Safe: Renaming a column (3-phase approach)
```python
# Migration 1: Add new column
def upgrade():
    op.add_column('users', sa.Column('full_name', sa.String()))
    op.execute("UPDATE users SET full_name = name")

# Deploy code that writes to both columns, reads from full_name

# Migration 2 (later): Drop old column
def upgrade():
    op.drop_column('users', 'name')
```

#### ⚠️ Dangerous: Dropping a column (data loss)
```python
# Make sure no code references this column before dropping!
def upgrade():
    op.drop_column('users', 'legacy_field')
```

### Migration Checklist

Before deploying a migration:

- [ ] Tested locally with `upgrade` and `downgrade`
- [ ] Reviewed auto-generated SQL for correctness
- [ ] Migration is backward-compatible (or coordinated with code deploy)
- [ ] No sensitive data in migration file
- [ ] Ran `make test` to ensure tests pass
- [ ] Did a dry run in GitHub Actions

## Troubleshooting

### "Target database is not up to date"

Your local database is behind. Run:
```bash
uv run alembic upgrade head
```

### "Can't locate revision"

The migration history is inconsistent. Check:
```bash
uv run alembic history
uv run alembic current
```

### Migration failed mid-way

If a migration fails partway through:
1. Check the error message
2. Manually fix the database state if needed
3. Either fix the migration and retry, or mark it as complete:
   ```bash
   uv run alembic stamp <revision>
   ```

### Conflicts between developers

If two developers create migrations simultaneously:
1. Pull latest changes
2. Check for multiple heads: `uv run alembic heads`
3. Create a merge migration: `uv run alembic merge heads -m "Merge migrations"`
