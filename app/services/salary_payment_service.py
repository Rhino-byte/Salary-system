"""
Service for handling salary payments.
Records salary payments; optional payroll period tags for month close.
"""
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.models.schema import Employee, SalaryPayment, Role
from app.services.payroll_service import get_net_pay_remaining


def record_salary_payment(
    db: Session,
    employee_id: int,
    admin_id: int,
    amount_paid: float = None,
    payment_date: date = None,
    notes: str = None,
    payroll_year: int | None = None,
    payroll_month: int | None = None,
) -> SalaryPayment:
    """
    Record a salary payment for an employee.

    If amount_paid is omitted, uses current net pay remaining (arrears + earned MTD
    minus bills and advances in the current calendar month).
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise ValueError("Employee not found")

    admin = db.query(Employee).filter(Employee.id == admin_id).first()
    if not admin:
        raise ValueError("Admin not found")

    if admin.role != Role.ADMIN:
        raise PermissionError("Only admins can record salary payments")

    if payment_date is None:
        payment_date = date.today()

    if amount_paid is None:
        as_of = payment_date if isinstance(payment_date, date) else date.today()
        amount_paid = max(0.0, get_net_pay_remaining(db, employee_id, as_of))

    salary_payment = SalaryPayment(
        employee_id=employee_id,
        paid_by_id=admin_id,
        amount_paid=amount_paid,
        payment_date=payment_date,
        notes=notes,
        payroll_year=payroll_year,
        payroll_month=payroll_month,
    )

    db.add(salary_payment)
    employee.updated_at = datetime.now()

    try:
        db.flush()
        db.commit()
        db.refresh(salary_payment)
        db.refresh(employee)
        return salary_payment
    except Exception as e:
        db.rollback()
        error_msg = f"Database error recording salary payment: {str(e)}"
        print(error_msg)
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise Exception(f"Failed to save salary payment to database: {str(e)}") from e


def get_employee_salary_payments(db: Session, employee_id: int) -> list:
    return (
        db.query(SalaryPayment)
        .filter(SalaryPayment.employee_id == employee_id)
        .order_by(SalaryPayment.payment_date.desc(), SalaryPayment.created_at.desc())
        .all()
    )


def get_all_salary_payments(db: Session) -> list:
    return (
        db.query(SalaryPayment)
        .order_by(SalaryPayment.payment_date.desc(), SalaryPayment.created_at.desc())
        .all()
    )


def get_salary_payment_by_id(db: Session, payment_id: int) -> SalaryPayment:
    return db.query(SalaryPayment).filter(SalaryPayment.id == payment_id).first()
