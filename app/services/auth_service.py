"""
Service for role-based permission checks
"""

from app.models.schema import Employee, Role
from sqlalchemy.orm import Session


def check_permission(session: Session, employee_id: int, required_role: Role) -> bool:
    """
    Check if employee has required role
    
    Args:
        session: Database session
        employee_id: ID of employee
        required_role: Required role
    
    Returns:
        True if employee has required role
    """
    employee = session.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        return False
    
    return employee.role == required_role


def can_request_advance(session: Session, employee_id: int) -> bool:
    """Check if employee can request advances (staff and managers)"""
    employee = session.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        return False
    return employee.role in [Role.STAFF, Role.MANAGER]


def can_add_bills(session: Session, employee_id: int) -> bool:
    """Check if employee can add bills (managers and admins)"""
    employee = session.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        return False
    return employee.role in [Role.MANAGER, Role.ADMIN]


def can_approve_advances(session: Session, employee_id: int) -> bool:
    """Check if employee can approve advances (admin only)"""
    return check_permission(session, employee_id, Role.ADMIN)


def can_view_all(session: Session, employee_id: int) -> bool:
    """Check if employee can view all records (admin only)"""
    return check_permission(session, employee_id, Role.ADMIN)

