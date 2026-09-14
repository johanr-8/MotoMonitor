from datetime import date
from .db import get_db


def get_reminders_by_vehicle(vehicle_id):
    conn = get_db()
    reminders = conn.execute(
        "SELECT * FROM reminders WHERE vehicle_id = ? ORDER BY due_date ASC", (vehicle_id,)
    ).fetchall()
    conn.close()
    return reminders


def get_reminder_by_id(reminder_id):
    conn = get_db()
    reminder = conn.execute(
        """SELECT r.*, v.user_id FROM reminders r
           JOIN vehicles v ON r.vehicle_id = v.id WHERE r.id = ?""",
        (reminder_id,),
    ).fetchone()
    conn.close()
    return reminder


def create_reminder(vehicle_id, rtype, due_date, notes=""):
    conn = get_db()
    conn.execute(
        "INSERT INTO reminders (vehicle_id, type, due_date, notes) VALUES (?, ?, ?, ?)",
        (vehicle_id, rtype, due_date, notes),
    )
    conn.commit()
    conn.close()


def complete_reminder(reminder_id, cost, notes):
    conn = get_db()
    today_str = date.today().isoformat()
    conn.execute(
        "UPDATE reminders SET status = 'completed', notes = ? WHERE id = ?",
        (notes, reminder_id),
    )
    conn.execute(
        "INSERT INTO service_log (reminder_id, cost, notes, completed_at) VALUES (?, ?, ?, ?)",
        (reminder_id, cost, notes, today_str),
    )
    conn.commit()
    conn.close()


def update_overdue_reminders(user_id):
    conn = get_db()
    today_str = date.today().isoformat()
    conn.execute(
        """UPDATE reminders SET status = 'overdue'
           WHERE id IN (
               SELECT r.id FROM reminders r
               JOIN vehicles v ON r.vehicle_id = v.id
               WHERE v.user_id = ? AND r.due_date < ? AND r.status != 'completed' AND r.status != 'overdue'
           )""",
        (user_id, today_str),
    )
    conn.commit()
    conn.close()


def get_overdue_reminders(user_id):
    conn = get_db()
    today_str = date.today().isoformat()
    update_overdue_reminders(user_id)
    reminders = conn.execute(
        """SELECT r.*, v.nickname, v.registration_number
           FROM reminders r JOIN vehicles v ON r.vehicle_id = v.id
           WHERE v.user_id = ? AND r.status = 'overdue'
           ORDER BY r.due_date ASC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return reminders


def get_upcoming_reminders(user_id, limit=5):
    conn = get_db()
    today_str = date.today().isoformat()
    reminders = conn.execute(
        """SELECT r.*, v.nickname, v.registration_number
           FROM reminders r JOIN vehicles v ON r.vehicle_id = v.id
           WHERE v.user_id = ? AND r.due_date >= ? AND r.status = 'upcoming'
           ORDER BY r.due_date ASC LIMIT ?""",
        (user_id, today_str, limit),
    ).fetchall()
    conn.close()
    return reminders


def count_by_status(user_id):
    update_overdue_reminders(user_id)
    conn = get_db()
    result = conn.execute(
        """SELECT r.status, COUNT(*) as cnt
           FROM reminders r JOIN vehicles v ON r.vehicle_id = v.id
           WHERE v.user_id = ? GROUP BY r.status""",
        (user_id,),
    ).fetchall()
    conn.close()
    return {row["status"]: row["cnt"] for row in result}


def count_reminders_by_vehicle(vehicle_id):
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM reminders WHERE vehicle_id = ?", (vehicle_id,)
    ).fetchone()[0]
    conn.close()
    return count
