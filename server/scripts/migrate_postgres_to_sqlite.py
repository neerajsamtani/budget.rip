"""
One-time migration script: PostgreSQL -> SQLite

Reads all data from a PostgreSQL database and writes it to a SQLite file.
Tables are migrated in dependency order to satisfy foreign key constraints.

Usage:
    # Set PostgreSQL connection details as env vars, then run:
    uv run python scripts/migrate_postgres_to_sqlite.py \
        --pg-host <host> \
        --pg-port 5432 \
        --pg-user <user> \
        --pg-password <password> \
        --pg-dbname <dbname> \
        --sqlite-path budgit.db
"""

import argparse
import sys

import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path so we can import models
sys.path.insert(0, ".")

from models.sql_models import Base

# Tables in dependency order (parents before children)
TABLE_ORDER = [
    "users",
    "categories",
    "payment_methods",
    "tags",
    "bank_accounts",
    "transactions",
    "line_items",
    "events",
    "event_line_items",
    "event_tags",
    "event_hints",
]


def migrate(pg_host, pg_port, pg_user, pg_password, pg_dbname, sqlite_path):
    # Connect to PostgreSQL
    pg_engine = create_engine(
        "postgresql+psycopg2://",
        creator=lambda: psycopg2.connect(
            host=pg_host,
            port=pg_port,
            user=pg_user,
            password=pg_password,
            dbname=pg_dbname,
        ),
    )

    # Connect to SQLite
    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")

    # Create all tables in SQLite
    Base.metadata.create_all(sqlite_engine)

    PgSession = sessionmaker(bind=pg_engine)
    SqliteSession = sessionmaker(bind=sqlite_engine)

    pg_session = PgSession()
    sqlite_session = SqliteSession()

    try:
        for table_name in TABLE_ORDER:
            # Read all rows from PostgreSQL
            result = pg_session.execute(text(f"SELECT * FROM {table_name}"))
            columns = list(result.keys())
            rows = result.fetchall()

            if not rows:
                print(f"  {table_name}: 0 rows (empty)")
                continue

            # Insert into SQLite
            placeholders = ", ".join([f":{col}" for col in columns])
            col_names = ", ".join(columns)
            insert_sql = text(f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})")

            batch = [dict(zip(columns, row)) for row in rows]
            sqlite_session.execute(insert_sql, batch)
            sqlite_session.commit()

            print(f"  {table_name}: {len(rows)} rows migrated")

        print(f"\nMigration complete! SQLite database: {sqlite_path}")

    except Exception as e:
        sqlite_session.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        pg_session.close()
        sqlite_session.close()
        pg_engine.dispose()
        sqlite_engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate data from PostgreSQL to SQLite")
    parser.add_argument("--pg-host", required=True, help="PostgreSQL host")
    parser.add_argument("--pg-port", default="5432", help="PostgreSQL port")
    parser.add_argument("--pg-user", required=True, help="PostgreSQL username")
    parser.add_argument("--pg-password", required=True, help="PostgreSQL password")
    parser.add_argument("--pg-dbname", required=True, help="PostgreSQL database name")
    parser.add_argument("--sqlite-path", default="budgit.db", help="Output SQLite file path")

    args = parser.parse_args()

    print(f"Migrating from PostgreSQL ({args.pg_host}/{args.pg_dbname}) to SQLite ({args.sqlite_path})...")
    migrate(args.pg_host, args.pg_port, args.pg_user, args.pg_password, args.pg_dbname, args.sqlite_path)
