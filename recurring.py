#Finance Application - Nicole Tressler
# September 2025 - September 2026

"""
recurring.py
Logic for advancing recurring-payment due dates and auto-posting any
payments that have come due as regular expenses.
"""

from datetime import date, datetime, timedelta
import calendar


def _add_month(d: date) -> date:
    month = d.month + 1
    year = d.year + (month - 1) // 12
    month = ((month - 1) % 12) + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)




def _add_year(d: date) -> date:
    try:
        return d.replace(year=d.year + 1)
    except ValueError:
        # Feb 29 on a non-leap year
        return d.replace(month=2, day=28, year=d.year + 1)




def compute_next_date(current: date, frequency: str) -> date:
    frequency = frequency.lower()
    if frequency == "daily":
        return current + timedelta(days=1)
    if frequency == "weekly":
        return current + timedelta(weeks=1)
    if frequency == "monthly":
        return _add_month(current)
    if frequency == "yearly":
        return _add_year(current)
    raise ValueError(f"Unknown frequency: {frequency}")




def process_due_recurring_payments(db, as_of: date = None):
    """
    Checks all active recurring payments; for any whose next_due_date is
    on or before `as_of`, posts an expense and advances the schedule
    (repeating until the due date is in the future, to catch up on any
    payments missed while the app wasn't open).

    Returns the list of expense descriptions that were auto-posted.
    """
    as_of = as_of or date.today()
    posted = []

    for r in db.get_recurring(active_only=True):
        due = datetime.strptime(r["next_due_date"], "%Y-%m-%d").date()
        safety_counter = 0
        while due <= as_of and safety_counter < 500:
            db.add_expense(
                amount=r["amount"],
                category_id=r["category_id"],
                description=f"{r['name']} (recurring)",
                date_str=due.isoformat(),
                source="recurring",
            )
            posted.append(f"{r['name']} — ${r['amount']:.2f} on {due.isoformat()}")
            due = compute_next_date(due, r["frequency"])
            safety_counter += 1
        db.update_recurring_next_date(r["id"], due.isoformat())

    return posted
