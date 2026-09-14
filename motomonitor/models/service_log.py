from .db import get_db


def get_service_logs_by_vehicle(vehicle_id):
    conn = get_db()
    logs = conn.execute(
        """SELECT s.*, r.type FROM service_log s
           JOIN reminders r ON s.reminder_id = r.id
           WHERE r.vehicle_id = ? ORDER BY s.completed_at DESC""",
        (vehicle_id,),
    ).fetchall()
    conn.close()
    return logs


def get_total_cost_by_user(user_id):
    conn = get_db()
    result = conn.execute(
        """SELECT COALESCE(SUM(s.cost), 0) as total
           FROM service_log s
           JOIN reminders r ON s.reminder_id = r.id
           JOIN vehicles v ON r.vehicle_id = v.id
           WHERE v.user_id = ?""",
        (user_id,),
    ).fetchone()
    conn.close()
    return result["total"]


def get_spend_by_category(user_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT r.type, SUM(s.cost) as total
           FROM service_log s
           JOIN reminders r ON s.reminder_id = r.id
           JOIN vehicles v ON r.vehicle_id = v.id
           WHERE v.user_id = ?
           GROUP BY r.type""",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows
