"""Check due dates and send notifications.

Run this daily (via cron, APScheduler, or a manual trigger).
"""

from datetime import date, timedelta
from models.db import get_db
from models.user import get_user_by_id
from services.notifier import send_reminder_alert


def check_reminders():
    """Scan all non-completed reminders and act based on due date proximity."""
    conn = get_db()
    today = date.today()

    reminders = conn.execute(
        """SELECT r.*, v.user_id, v.nickname, v.make, v.model, v.registration_number
           FROM reminders r
           JOIN vehicles v ON r.vehicle_id = v.id
           WHERE r.status != 'completed'"""
    ).fetchall()
    conn.close()

    for r in reminders:
        due = date.fromisoformat(r["due_date"])
        days_left = (due - today).days
        user = get_user_by_id(r["user_id"])

        if not user:
            continue

        vehicle = {
            "nickname": r["nickname"],
            "make": r["make"],
            "model": r["model"],
            "registration_number": r["registration_number"],
        }

        if days_left < 0:
            # Overdue
            _update_status(r["id"], "overdue")
            if r["last_alert_sent"] != "overdue":
                send_reminder_alert(user, vehicle, r, days_left)
                _update_last_alert(r["id"], "overdue")

        elif days_left == 0:
            # Due today
            _update_status(r["id"], "due_soon")
            if r["last_alert_sent"] not in ("due_day", "overdue"):
                send_reminder_alert(user, vehicle, r, days_left)
                _update_last_alert(r["id"], "due_day")

        elif days_left <= 7:
            # Due soon (7 days)
            if r["last_alert_sent"] in ("none", "30day"):
                send_reminder_alert(user, vehicle, r, days_left)
                _update_last_alert(r["id"], "7day")

        elif days_left <= 30:
            # 30-day warning
            if r["last_alert_sent"] == "none":
                send_reminder_alert(user, vehicle, r, days_left)
                _update_last_alert(r["id"], "30day")


def _update_status(reminder_id, status):
    conn = get_db()
    conn.execute("UPDATE reminders SET status = ? WHERE id = ?", (status, reminder_id))
    conn.commit()
    conn.close()


def _update_last_alert(reminder_id, alert_level):
    conn = get_db()
    conn.execute(
        "UPDATE reminders SET last_alert_sent = ? WHERE id = ?", (alert_level, reminder_id)
    )
    conn.commit()
    conn.close()
