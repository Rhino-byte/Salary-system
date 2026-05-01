"""
Payroll: pro-rated monthly gross (calendar days in month), off-day deduction,
current-month bills/advances, and salary_arrears from period close.
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from typing import Any

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models.schema import (
    Advance,
    AdvanceStatus,
    Bill,
    Employee,
    PayrollPeriodClose,
    SalaryPayment,
)
from app.utils.attendance import calculate_off_days_in_range


def _last_day(year: int, month: int) -> date:
    return date(year, month, monthrange(year, month)[1])


def sum_bills_in_calendar_month(
    db: Session, employee_id: int, year: int, month: int
) -> float:
    q = (
        db.query(func.coalesce(func.sum(Bill.amount_billed), 0.0))
        .filter(
            Bill.billed_employee_id == employee_id,
            extract("year", Bill.date) == year,
            extract("month", Bill.date) == month,
        )
        .scalar()
    )
    return float(q or 0)


def sum_approved_advances_in_calendar_month(
    db: Session, employee_id: int, year: int, month: int
) -> float:
    """Approved advances attributed to the month of approval (else creation)."""
    advances = (
        db.query(Advance)
        .filter(
            Advance.employee_id == employee_id,
            Advance.status == AdvanceStatus.APPROVED,
        )
        .all()
    )
    total = 0.0
    for a in advances:
        dt = a.approved_at or a.created_at
        if dt is None:
            continue
        d = dt.date() if isinstance(dt, datetime) else dt
        if d.year == year and d.month == month:
            total += float(a.amount_for_advance or 0)
    return total


def earned_gross_month_to_date(
    db: Session, employee: Employee, as_of: date
) -> dict[str, float | int]:
    """
    Pro-rate base monthly salary by calendar days in the current month (clipped to
    employment start) through ``as_of``, minus approved off days in that window.
    """
    month_start = date(as_of.year, as_of.month, 1)
    month_end = _last_day(as_of.year, as_of.month)
    start = max(month_start, employee.employment_start_date)
    end = min(as_of, date.today(), month_end)
    base = float(employee.salary or 0)
    if start > end:
        return {
            "earned_gross": 0.0,
            "eligible_days": 0,
            "off_days": 0.0,
            "daily_rate": 0.0,
            "off_day_deduction": 0.0,
            "base_monthly": base,
        }

    eligible_days = float((end - start).days + 1)
    off_days = float(
        calculate_off_days_in_range(db, employee.id, start, end)
    )
    worked_part = max(0.0, eligible_days - off_days)
    daily_rate = base / eligible_days if eligible_days > 0 else 0.0
    off_deduction = daily_rate * off_days
    earned = base * (worked_part / eligible_days) if eligible_days > 0 else 0.0

    return {
        "earned_gross": float(earned),
        "eligible_days": int(eligible_days),
        "off_days": off_days,
        "daily_rate": float(daily_rate),
        "off_day_deduction": float(off_deduction),
        "base_monthly": base,
    }


def get_net_pay_remaining(
    db: Session, employee_id: int, as_of: date | None = None
) -> float:
    """Arrears + earned MTD − bills this month − advances this month."""
    if as_of is None:
        as_of = date.today()
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        return 0.0
    parts = earned_gross_month_to_date(db, emp, as_of)
    earned = float(parts["earned_gross"])
    y, m = as_of.year, as_of.month
    bills_m = sum_bills_in_calendar_month(db, employee_id, y, m)
    adv_m = sum_approved_advances_in_calendar_month(db, employee_id, y, m)
    arrears = float(emp.salary_arrears or 0)
    return arrears + earned - bills_m - adv_m


def get_payroll_breakdown(
    db: Session, employee_id: int, as_of: date | None = None
) -> dict[str, Any]:
    if as_of is None:
        as_of = date.today()
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise ValueError(f"Employee {employee_id} not found")
    parts = earned_gross_month_to_date(db, emp, as_of)
    y, m = as_of.year, as_of.month
    bills_m = sum_bills_in_calendar_month(db, employee_id, y, m)
    adv_m = sum_approved_advances_in_calendar_month(db, employee_id, y, m)
    arrears = float(emp.salary_arrears or 0)
    net = arrears + float(parts["earned_gross"]) - bills_m - adv_m
    return {
        "salary_arrears": arrears,
        "earned_gross_month_to_date": parts["earned_gross"],
        "eligible_days": parts["eligible_days"],
        "off_days": parts["off_days"],
        "daily_rate": parts["daily_rate"],
        "off_day_deduction": parts["off_day_deduction"],
        "base_monthly": parts["base_monthly"],
        "bills_this_month": bills_m,
        "advances_this_month": adv_m,
        "remaining_salary": float(net),
    }


def sum_payments_for_period(
    db: Session, employee_id: int, year: int, month: int
) -> float:
    q = (
        db.query(func.coalesce(func.sum(SalaryPayment.amount_paid), 0.0))
        .filter(
            SalaryPayment.employee_id == employee_id,
            SalaryPayment.payroll_year == year,
            SalaryPayment.payroll_month == month,
        )
        .scalar()
    )
    return float(q or 0)


def close_employee_payroll_period(
    db: Session, employee_id: int, year: int, month: int
) -> dict[str, Any]:
    """
    Close a calendar month: roll (net_for_month − payments tagged to that period)
    into salary_arrears. Idempotent per (employee, year, month).
    """
    if (
        db.query(PayrollPeriodClose)
        .filter(
            PayrollPeriodClose.employee_id == employee_id,
            PayrollPeriodClose.year == year,
            PayrollPeriodClose.month == month,
        )
        .first()
    ):
        return {
            "already_closed": True,
            "employee_id": employee_id,
            "year": year,
            "month": month,
        }

    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise ValueError("Employee not found")

    end = _last_day(year, month)
    parts = earned_gross_month_to_date(db, emp, end)
    earned_full = float(parts["earned_gross"])
    bills_m = sum_bills_in_calendar_month(db, employee_id, year, month)
    adv_m = sum_approved_advances_in_calendar_month(db, employee_id, year, month)
    net = earned_full - bills_m - adv_m
    paid_m = sum_payments_for_period(db, employee_id, year, month)
    rolled = net - paid_m

    emp.salary_arrears = float(emp.salary_arrears or 0) + rolled
    db.add(
        PayrollPeriodClose(
            employee_id=employee_id,
            year=year,
            month=month,
            rolled_unpaid=rolled,
        )
    )
    db.commit()
    db.refresh(emp)

    return {
        "already_closed": False,
        "employee_id": employee_id,
        "year": year,
        "month": month,
        "earned_gross_for_month": earned_full,
        "bills_month": bills_m,
        "advances_month": adv_m,
        "net_for_month": net,
        "payments_tagged_to_period": paid_m,
        "rolled_unpaid": rolled,
        "salary_arrears_after": float(emp.salary_arrears or 0),
    }
