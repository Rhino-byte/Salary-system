"""
Clear (truncate) ALL tables in the database while keeping schema.

Usage:
  python scripts/clear_db.py --yes

Notes:
  - This will TRUNCATE every table in the connected database with
    RESTART IDENTITY CASCADE (PostgreSQL).
  - Requires DATABASE_URL to be configured (same as the app).
"""

import argparse
import sys

from pathlib import Path

# Ensure project root is on sys.path (so `import app.*` works when run as a script)
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config.config import DATABASE_URL  # noqa: E402
from app.models.schema import get_engine  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Truncate all DB tables (keep schema).")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Required confirmation flag. Without this, nothing will be deleted.",
    )
    args = parser.parse_args()

    if not args.yes:
        print("Refusing to run without --yes (safety).")
        return 2

    if not DATABASE_URL or DATABASE_URL == "postgresql://username:password@hostname/database?sslmode=require":
        print("DATABASE_URL is not configured. Aborting.")
        return 2

    engine = get_engine(DATABASE_URL)

    try:
        with engine.begin() as conn:
            # Fetch base tables from the public schema
            rows = conn.exec_driver_sql(
                """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
                """
            ).fetchall()

            tables = [r[0] for r in rows]
            if not tables:
                print("No tables found in public schema; nothing to truncate.")
                return 0

            table_list = ", ".join(f'"{t}"' for t in tables)
            conn.exec_driver_sql(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE;")

        print(f"✅ Truncated {len(tables)} table(s): {', '.join(tables)}")
        return 0
    except Exception as e:
        print(f"❌ Failed to truncate tables: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

