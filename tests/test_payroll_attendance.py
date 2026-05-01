"""
Unit tests: off-day overlap and payroll helpers (in-memory SQLite).
"""
import datetime as dt
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.schema import (
    Base,
    Employee,
    Role,
    OffDay,
    OffDayStatus,
    PayrollPeriodClose,
)
from app.utils.attendance import calculate_off_days_in_range, calculate_days_worked_this_month
from app.services.payroll_service import earned_gross_month_to_date, close_employee_payroll_period


def _memory_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


class OffDayOverlapTests(unittest.TestCase):
    def test_half_day_counts_fraction(self):
        db = _memory_session()
        emp = Employee(
            first_name="A",
            last_name="B",
            role=Role.STAFF,
            salary=30000.0,
            phone_no="0700000001",
            employment_start_date=dt.date(2026, 1, 1),
        )
        db.add(emp)
        db.commit()
        db.refresh(emp)

        db.add(
            OffDay(
                employee_id=emp.id,
                date=dt.date(2026, 5, 10),
                day_count=1,
                off_type="half",
                status=OffDayStatus.APPROVED,
            )
        )
        db.commit()

        off = calculate_off_days_in_range(
            db, emp.id, dt.date(2026, 5, 1), dt.date(2026, 5, 31)
        )
        self.assertAlmostEqual(off, 0.5, places=5)

        with patch("app.utils.attendance.date") as md:
            md.today.return_value = dt.date(2026, 5, 31)
            md.side_effect = lambda *a, **kw: dt.date(*a, **kw)
            days = calculate_days_worked_this_month(
                db, emp, reference_date=dt.date(2026, 5, 31)
            )
        self.assertGreater(days, 0)

    def test_spanning_months_only_counts_overlap(self):
        db = _memory_session()
        emp = Employee(
            first_name="C",
            last_name="D",
            role=Role.STAFF,
            salary=30000.0,
            phone_no="0700000002",
            employment_start_date=dt.date(2026, 1, 1),
        )
        db.add(emp)
        db.commit()
        db.refresh(emp)

        db.add(
            OffDay(
                employee_id=emp.id,
                date=dt.date(2026, 5, 30),
                day_count=3,
                off_type="full",
                status=OffDayStatus.APPROVED,
            )
        )
        db.commit()

        may_off = calculate_off_days_in_range(
            db, emp.id, dt.date(2026, 5, 1), dt.date(2026, 5, 31)
        )
        self.assertEqual(may_off, 2.0)
        june_off = calculate_off_days_in_range(
            db, emp.id, dt.date(2026, 6, 1), dt.date(2026, 6, 30)
        )
        self.assertEqual(june_off, 1.0)


class PayrollEarnedTests(unittest.TestCase):
    @patch("app.services.payroll_service.date")
    def test_earned_reduced_by_full_off_days(self, mock_date):
        mock_date.today.return_value = dt.date(2026, 5, 31)
        mock_date.side_effect = lambda *a, **kw: dt.date(*a, **kw)

        db = _memory_session()
        emp = Employee(
            first_name="E",
            last_name="F",
            role=Role.STAFF,
            salary=31000.0,
            phone_no="0700000003",
            employment_start_date=dt.date(2026, 5, 1),
        )
        db.add(emp)
        db.commit()
        db.refresh(emp)

        db.add(
            OffDay(
                employee_id=emp.id,
                date=dt.date(2026, 5, 5),
                day_count=2,
                off_type="full",
                status=OffDayStatus.APPROVED,
            )
        )
        db.commit()

        parts = earned_gross_month_to_date(db, emp, dt.date(2026, 5, 31))
        self.assertGreater(parts["off_days"], 0)
        self.assertLess(parts["earned_gross"], float(emp.salary))


class ClosePeriodTests(unittest.TestCase):
    def test_second_close_is_noop(self):
        db = _memory_session()
        emp = Employee(
            first_name="G",
            last_name="H",
            role=Role.STAFF,
            salary=30000.0,
            phone_no="0700000004",
            employment_start_date=dt.date(2026, 4, 1),
            salary_arrears=0.0,
        )
        db.add(emp)
        db.commit()
        db.refresh(emp)

        db.add(
            PayrollPeriodClose(
                employee_id=emp.id, year=2026, month=4, rolled_unpaid=0.0
            )
        )
        db.commit()

        r = close_employee_payroll_period(db, emp.id, 2026, 4)
        self.assertTrue(r.get("already_closed"))


if __name__ == "__main__":
    unittest.main()
