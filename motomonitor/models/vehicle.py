from .db import get_db


def get_vehicles_by_user(user_id):
    conn = get_db()
    vehicles = conn.execute(
        "SELECT * FROM vehicles WHERE user_id = ? ORDER BY id DESC", (user_id,)
    ).fetchall()
    conn.close()
    return vehicles


def get_vehicle_by_id(vehicle_id, user_id):
    conn = get_db()
    vehicle = conn.execute(
        "SELECT * FROM vehicles WHERE id = ? AND user_id = ?", (vehicle_id, user_id)
    ).fetchone()
    conn.close()
    return vehicle


def create_vehicle(user_id, nickname, make, model, reg_no, purchase_date):
    conn = get_db()
    conn.execute(
        "INSERT INTO vehicles (user_id, nickname, make, model, registration_number, purchase_date) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, nickname, make, model, reg_no, purchase_date),
    )
    conn.commit()
    conn.close()


def update_vehicle(vehicle_id, nickname, make, model, reg_no, purchase_date):
    conn = get_db()
    conn.execute(
        "UPDATE vehicles SET nickname=?, make=?, model=?, registration_number=?, purchase_date=? WHERE id=?",
        (nickname, make, model, reg_no, purchase_date, vehicle_id),
    )
    conn.commit()
    conn.close()


def delete_vehicle(vehicle_id, user_id):
    conn = get_db()
    conn.execute("DELETE FROM vehicles WHERE id = ? AND user_id = ?", (vehicle_id, user_id))
    conn.commit()
    conn.close()


def count_vehicles_by_user(user_id):
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM vehicles WHERE user_id = ?", (user_id,)
    ).fetchone()[0]
    conn.close()
    return count
