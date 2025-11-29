"""
Service for handling bills
Managers and Admins can add/update bills for staff and managers
"""

from sqlalchemy.orm import Session
from app.models.schema import Employee, Bill, Role
from datetime import datetime


def add_bill(
    session: Session,
    recorded_by_id: int,
    employee_id: int,
    amount: float,
    date: datetime = None,
    reason: str = None,
) -> Bill:
    """
    Manager or Admin can add a bill for a staff member or manager
    
    Args:
        session: Database session
        recorded_by_id: ID of manager or admin recording the bill
        employee_id: ID of employee (staff or manager) the bill is for
        amount: Bill amount
        date: Date of bill (defaults to now)
        reason: Optional reason for bill
        pin: Optional unique pin, if not provided will be auto-generated
    
    Returns:
        BillAdvance object
    """
    # Verify person recording exists and has appropriate role
    recorder = session.query(Employee).filter(Employee.id == recorded_by_id).first()
    if not recorder:
        raise ValueError("Person recording bill not found")
    
    if recorder.role not in [Role.MANAGER, Role.ADMIN]:
        raise PermissionError("Only managers and admins can add bills")
    
    # Verify employee exists and is staff or manager (not admin)
    employee = session.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise ValueError("Employee not found")
    
    if employee.role not in [Role.STAFF, Role.MANAGER]:
        raise PermissionError("Bills can only be added for staff and managers")
    
    # Managers cannot add bills for themselves
    if recorder.role == Role.MANAGER and recorded_by_id == employee_id:
        raise PermissionError("Managers cannot add bills for themselves")
    
    # Use current date if not provided
    if not date:
        date = datetime.utcnow()
    
    # Create bill record
    bill = Bill(
        employee_id=employee_id,
        billed_employee_id=employee_id,
        amount_billed=amount,
        date=date,
        reason=reason,
        recorded_by_id=recorded_by_id,
    )
    
    session.add(bill)
    session.commit()
    session.refresh(bill)
    
    return bill


def update_bill(
    session: Session,
    bill_id: int,
    employee_id: int,
    amount: float = None,
    date: datetime = None,
    reason: str = None
) -> Bill:
    """
    Manager or Admin can update a bill they recorded
    
    Args:
        session: Database session
        bill_id: ID of bill to update
        employee_id: ID of manager/admin updating (must be the one who recorded it)
        amount: New amount (optional)
        date: New date (optional)
        reason: New reason (optional)
    
    Returns:
        Updated BillAdvance object
    """
    # Verify employee exists and has appropriate role
    employee = session.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise ValueError("Employee not found")
    
    if employee.role not in [Role.MANAGER, Role.ADMIN]:
        raise PermissionError("Only managers and admins can update bills")
    
    # Get bill
    bill = session.query(Bill).filter(Bill.id == bill_id).first()
    
    if not bill:
        raise ValueError("Bill not found")
    
    # Verify employee recorded this bill (or admin can update any bill)
    if employee.role != Role.ADMIN and bill.recorded_by_id != employee_id:
        raise PermissionError("You can only update bills you recorded")
    
    # Update fields
    if amount is not None:
        bill.amount_billed = amount
    if date is not None:
        bill.date = date
    if reason is not None:
        bill.reason = reason
    
    session.commit()
    session.refresh(bill)
    
    return bill


def get_employee_bills(session: Session, employee_id: int) -> list:
    """Get all bills for a specific employee (staff or manager)"""
    return (
        session.query(Bill)
        .filter(Bill.billed_employee_id == employee_id)
        .order_by(Bill.date.desc())
        .all()
    )


def get_staff_bills(session: Session, staff_employee_id: int) -> list:
    """Get all bills for a specific staff member (deprecated, use get_employee_bills)"""
    return get_employee_bills(session, staff_employee_id)


def get_all_bills(session: Session) -> list:
    """Get all bills (for admin)"""
    return session.query(Bill).order_by(Bill.date.desc()).all()


def get_recorded_bills(session: Session, employee_id: int) -> list:
    """Get all bills recorded by a specific manager or admin"""
    return (
        session.query(Bill)
        .filter(Bill.recorded_by_id == employee_id)
        .order_by(Bill.date.desc())
        .all()
    )


def get_manager_bills(session: Session, manager_id: int) -> list:
    """Get all bills recorded by a specific manager (deprecated, use get_recorded_bills)"""
    return get_recorded_bills(session, manager_id)

