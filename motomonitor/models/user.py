from .db import get_db


def get_user_by_email(email):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def create_user(name, email, password_hash, phone="", pincode="", family_email=""):
    conn = get_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash, phone, pincode, family_email) VALUES (?, ?, ?, ?, ?, ?)",
        (name, email, password_hash, phone, pincode, family_email),
    )
    conn.commit()
    conn.close()


def get_all_users():
    conn = get_db()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return users
