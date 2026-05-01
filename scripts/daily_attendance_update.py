"""
Daily attendance and salary update script.
This script should be run once per day to update employee attendance counters
and handle monthly salary resets.

Usage:
    python scripts/daily_attendance_update.py

Can be scheduled via:
    - Windows Task Scheduler
    - Linux/Unix cron job
    - Vercel Cron (HTTP): see /api/internal/cron/daily-attendance
"""
import sys
import os
from datetime import date

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.schema import get_engine, get_session
from app.config.config import DATABASE_URL
from app.jobs.daily_attendance import run_daily_attendance_job


def main():
    """Main function to update daily attendance for all employees"""
    print(f"Starting daily attendance update for {date.today()}...")

    engine = get_engine(DATABASE_URL)
    session = get_session(engine)

    try:
        result = run_daily_attendance_job(session, reference_date=date.today())
        if result.get("monthly_reset"):
            mr = result["monthly_reset"]
            if mr and mr.get("attendance_employees_reset", 0) > 0:
                print(
                    f"✓ Reset monthly attendance for {mr['attendance_employees_reset']} employees"
                )
            if mr and mr.get("salary") and mr["salary"].get("reset_count", 0) > 0:
                s = mr["salary"]
                print("✓ Reset monthly salary:")
                print(f"  - Carried forward debts: {s.get('carried_forward', 0)}")
                print(f"  - Reset to zero: {s.get('reset_to_zero', 0)}")

        print(f"\n=== Attendance Recompute Summary ===")
        print(f"Total employees: {result.get('total_employees', 0)}")
        print(f"✓ Recomputed: {result.get('recomputed', 0)}")
        print(f"\nDaily update completed successfully!")

    except Exception as e:
        print(f"ERROR: Failed to update: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        session.rollback()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
