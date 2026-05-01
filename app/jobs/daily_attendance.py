"""
Daily attendance batch: monthly resets on the 1st + full recompute of days worked.
Used by scripts/daily_attendance_update.py and the Vercel Cron HTTP handler.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.services.attendance_service import reset_monthly_attendance_for_new_month
from app.services.salary_service import reset_monthly_salary_for_new_month
from app.utils.attendance import recompute_all_employees_attendance


def run_daily_attendance_job(db: Session, reference_date: date | None = None) -> dict[str, Any]:
    """
    Run the same logic as scripts/daily_attendance_update.py main body.

    Args:
        db: SQLAlchemy session (caller manages lifecycle).
        reference_date: Run as-of this date (defaults to today).

    Returns:
        Dict with recompute stats and optional monthly reset details.
    """
    if reference_date is None:
        reference_date = date.today()

    out: dict[str, Any] = {"reference_date": reference_date.isoformat()}

    if reference_date.day == 1:
        attendance_reset_count = reset_monthly_attendance_for_new_month(
            db, target_date=reference_date
        )
        salary_stats = reset_monthly_salary_for_new_month(
            db, target_date=reference_date
        )
        out["monthly_reset"] = {
            "attendance_employees_reset": attendance_reset_count,
            "salary": salary_stats,
        }
    else:
        out["monthly_reset"] = None

    stats = recompute_all_employees_attendance(db, reference_date=reference_date)
    out.update(stats)
    return out
