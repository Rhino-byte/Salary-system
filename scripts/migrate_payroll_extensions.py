"""
Add salary_arrears, salary_payment payroll period columns, and payroll_period_close table.
"""
import os
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text

from app.config.config import DATABASE_URL
from app.models.schema import Base, PayrollPeriodClose, get_engine


def migrate():
    print("Connecting to database...")
    engine = get_engine(DATABASE_URL)

    with engine.connect() as conn:
        r = conn.execute(
            text(
                """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'employee' AND column_name = 'salary_arrears'
        """
            )
        )
        if not r.fetchone():
            print("Adding employee.salary_arrears ...")
            conn.execute(
                text(
                    "ALTER TABLE employee ADD COLUMN salary_arrears FLOAT DEFAULT 0.0"
                )
            )
            conn.commit()
            print("✓ salary_arrears added")
        else:
            print("✓ salary_arrears already exists")

        for col, ctype in (
            ("payroll_year", "INTEGER"),
            ("payroll_month", "INTEGER"),
        ):
            r = conn.execute(
                text(
                    f"""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'salary_payment' AND column_name = '{col}'
            """
                )
            )
            if not r.fetchone():
                print(f"Adding salary_payment.{col} ...")
                conn.execute(
                    text(
                        f"ALTER TABLE salary_payment ADD COLUMN {col} {ctype} NULL"
                    )
                )
                conn.commit()
                print(f"✓ {col} added")
            else:
                print(f"✓ salary_payment.{col} already exists")

    print("Creating payroll_period_close if missing ...")
    Base.metadata.create_all(engine, tables=[PayrollPeriodClose.__table__])
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
