"""
Utility functions for calculating employee attendance and days worked.
"""
from datetime import date, datetime
from typing import List
from sqlalchemy.orm import Session
from app.models.schema import Employee, OffDay, OffDayStatus


def calculate_off_days_in_range(
    db: Session,
    employee_id: int,
    start_date: date,
    end_date: date
) -> float:
    """
    Calculate total off days (in days) for an employee within a date range.
    Only counts APPROVED off days.
    Half days count as 0.5, full days count as 1.0.
    Only counts days that actually fall within the specified range.
    
    Args:
        db: Database session
        employee_id: Employee ID
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
    
    Returns:
        Total off days as float (handles half days)
    """
    from datetime import timedelta
    
    # Get all approved off days for this employee that might overlap with the range
    # An off day request spans from off_day.date to off_day.date + day_count - 1
    # We need to find off days where the range overlaps with our target range
    off_days = db.query(OffDay).filter(
        OffDay.employee_id == employee_id,
        OffDay.status == OffDayStatus.APPROVED
    ).all()
    
    total_off_days = 0.0
    for off_day in off_days:
        # Calculate the end date of this off day request
        off_day_start = off_day.date
        off_day_end = off_day_start + timedelta(days=off_day.day_count - 1)
        
        # Check if this off day request overlaps with our target range
        # Overlap exists if: off_day_start <= end_date AND off_day_end >= start_date
        if off_day_start <= end_date and off_day_end >= start_date:
            # Calculate the overlapping range
            overlap_start = max(off_day_start, start_date)
            overlap_end = min(off_day_end, end_date)
            
            # Count days in the overlap (inclusive)
            overlap_days = (overlap_end - overlap_start).days + 1
            
            # Calculate days for this off day request
            # If it's a half day, count as 0.5 per day, otherwise 1.0 per day
            day_value = 0.5 if off_day.off_type == "half" else 1.0
            total_off_days += day_value * overlap_days
    
    return total_off_days


def calculate_days_worked_this_month(
    db: Session,
    employee: Employee,
    reference_date: date = None
) -> int:
    """
    Calculate days worked in the current month (from 1st to today).
    Every day is considered a working day.
    Subtracts approved off days.
    
    Args:
        db: Database session
        employee: Employee object
        reference_date: Date to calculate from (defaults to today)
    
    Returns:
        Number of days worked this month (integer, rounded)
    """
    if reference_date is None:
        reference_date = date.today()
    
    # Month starts at 1st
    month_start = date(reference_date.year, reference_date.month, 1)
    
    # If employee started after month start, use employment start date
    start_date = max(month_start, employee.employment_start_date)
    
    # End date is today (or reference_date)
    end_date = min(reference_date, date.today())
    
    # Calculate total calendar days in the period
    if start_date > end_date:
        return 0
    
    # Calculate days difference (inclusive)
    total_days = (end_date - start_date).days + 1
    
    # Subtract approved off days
    off_days = calculate_off_days_in_range(db, employee.id, start_date, end_date)
    
    # Round to integer (days worked)
    days_worked = int(round(total_days - off_days))
    
    return max(0, days_worked)  # Ensure non-negative


def calculate_total_days_worked(
    db: Session,
    employee: Employee,
    reference_date: date = None
) -> int:
    """
    Calculate total days worked since employment start date.
    Every day is considered a working day.
    Subtracts all approved off days.
    
    Args:
        db: Database session
        employee: Employee object
        reference_date: Date to calculate up to (defaults to today)
    
    Returns:
        Total number of days worked (integer, rounded)
    """
    if reference_date is None:
        reference_date = date.today()
    
    # Start from employment start date
    start_date = employee.employment_start_date
    
    # End date is today (or reference_date)
    end_date = min(reference_date, date.today())
    
    # Calculate total calendar days in the period
    if start_date > end_date:
        return 0
    
    # Calculate days difference (inclusive)
    total_days = (end_date - start_date).days + 1
    
    # Subtract all approved off days
    off_days = calculate_off_days_in_range(db, employee.id, start_date, end_date)
    
    # Round to integer (days worked)
    days_worked = int(round(total_days - off_days))
    
    return max(0, days_worked)  # Ensure non-negative


def update_employee_attendance(
    db: Session,
    employee: Employee,
    reference_date: date = None
) -> Employee:
    """
    Update the days_worked_this_month and total_days_worked fields for an employee.
    
    Args:
        db: Database session
        employee: Employee object
        reference_date: Date to calculate from (defaults to today)
    
    Returns:
        Updated employee object
    """
    employee.days_worked_this_month = calculate_days_worked_this_month(
        db, employee, reference_date
    )
    employee.total_days_worked = calculate_total_days_worked(
        db, employee, reference_date
    )
    db.commit()
    db.refresh(employee)
    return employee
