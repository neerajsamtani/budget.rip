# Plan 022: Add user_id to Tag model for per-user tag isolation

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4183f93..HEAD -- server/models/sql_models.py server/resources/tags.py`
> If either changed, compare before proceeding.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: MED
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `4183f93`, 2026-06-10

## Why this matters

The `Tag` model has no `user_id` column. `GET /api/tags` returns all tags from
all users. While the app is currently single-user in practice, the schema has
`user_id` on most other entities (`Category`, `EventHint`) as preparation for
multi-user support. Tags are the odd one out. This plan adds the column for
consistency, following the same pattern as `Category`.

Note: this is an architectural preparation step, not a fix for an active security
breach. It involves a database migration that touches the live `tags` table.

## Current state

**Tag model** (`server/models/sql_models.py:109-119`):
```python
class Tag(Base):
    __tablename__ = "tags"
    id = Column(String(255), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    ...
```

No `user_id` column. The `unique=True` on `name` means tags are global and
shared across users.

**Category model** (`server/models/sql_models.py:69-86`) — the pattern to follow:
```python
class Category(Base):
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_category_name"),)
```

**Tags endpoint** (`server/resources/tags.py:11-20`):
```python
def get_all_tags_api():
    with SessionLocal.begin() as db:
        tags = db.query(Tag).order_by(Tag.name).all()
```

No user filtering.

## Commands you will need

| Purpose     | Command                                                         | Expected on success |
|-------------|-----------------------------------------------------------------|---------------------|
| Migration   | `cd server && uv run alembic upgrade head`                      | exit 0 |
| Tests       | `cd server && uv run python -m pytest tests/test_tags.py -v`    | all pass |
| All tests   | `cd server && uv run python -m pytest -v`                       | all pass |
| Lint        | `cd server && make lint`                                        | exit 0 |

## Scope

**In scope**:
- `server/models/sql_models.py` — `Tag` model
- `server/resources/tags.py` — add user filtering
- `server/alembic/` — new migration (generated via alembic autogenerate)
- `server/tests/test_tags.py` — update/add tests

**Out of scope**:
- `EventTag` junction table — no user_id needed there (events already have user-scoped categories).
- Client tag-related code — the API response shape does not change.

## Git workflow

- Branch: `advisor/022-add-tags-user-id`
- Commit message style: `Add user_id to Tag model for per-user isolation (#NNN)`

## Steps

### Step 1: Update the Tag model

In `server/models/sql_models.py`, add `user_id` to `Tag`:

```python
class Tag(Base):
    __tablename__ = "tags"
    id = Column(String(255), primary_key=True)
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    ...
    user = relationship("User")
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_tag_name"),)
```

Remove the global `unique=True` from `name` (replaced by the `(user_id, name)` unique constraint).

### Step 2: Generate the Alembic migration

```bash
cd server && uv run alembic revision --autogenerate -m "add user_id to tags"
```

Read the generated migration file. Verify it:
- Adds `user_id` column (nullable initially for backfill)
- Adds the foreign key to `users`
- Adds the unique constraint `uq_user_tag_name`
- Drops the old `unique=True` on `name`

If the app has existing tag data (production), the migration must backfill
`user_id` before making it NOT NULL. Add a data migration step:

```python
# In the upgrade() function, before making user_id NOT NULL:
# Get the first (only) user's ID and assign it to all tags
op.execute("UPDATE tags SET user_id = (SELECT id FROM users LIMIT 1) WHERE user_id IS NULL")
```

Then alter the column to NOT NULL.

### Step 3: Apply the migration (test DB only)

The test suite uses SQLite in-memory and recreates tables from scratch — migration
is not applied to tests. Running `pytest` will use the updated model directly.

**Verify**: `cd server && uv run python -m pytest tests/test_tags.py -v` → all pass.

### Step 4: Update the tags endpoint to filter by user

In `server/resources/tags.py`, import `get_current_user` and filter by user:

```python
from flask_jwt_extended import get_current_user, jwt_required

@tags_blueprint.route("/api/tags", methods=["GET"])
@jwt_required()
def get_all_tags_api():
    user = get_current_user()
    with SessionLocal.begin() as db:
        tags = db.query(Tag).filter(Tag.user_id == user["id"]).order_by(Tag.name).all()
        tags_list = [{"id": tag.id, "name": tag.name} for tag in tags]
        return jsonify({"data": tags_list}), 200
```

Also update any endpoint that creates tags to include `user_id = user["id"]`.
Find tag creation: `grep -rn "Tag(" server/resources/` and `grep -rn "Tag(" server/utils/`.

### Step 5: Run all tests

**Verify**: `cd server && uv run python -m pytest -v` → all pass.

### Step 6: Lint

**Verify**: `cd server && make lint` → exit 0.

## Done criteria

- [ ] `Tag` model has `user_id` FK column and `(user_id, name)` unique constraint
- [ ] Alembic migration exists and is valid
- [ ] Tags endpoint filters by `current_user["id"]`
- [ ] Tag creation includes `user_id`
- [ ] `cd server && uv run python -m pytest -v` exits 0
- [ ] `plans/README.md` status row updated to DONE

## STOP conditions

- Tag creation happens in many places with complex flows — map all creation sites
  with `grep -rn "Tag(" server/` before adding `user_id` to ensure none are missed.
- The migration file looks wrong (wrong column type, missing FK) — do not run it;
  edit the migration manually or regenerate.

## Maintenance notes

- After this change, `EventTag` entries are indirectly user-scoped (via `Event.category.user_id`).
  No changes to `EventTag` are needed.
- When multi-user support is added (plan 023), this change is already in place.
