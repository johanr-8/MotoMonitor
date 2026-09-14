from .db import get_db


def create_order(user_id, product_id, pincode, quantity=1):
    conn = get_db()
    conn.execute(
        "INSERT INTO orders (user_id, product_id, pincode, quantity) VALUES (?, ?, ?, ?)",
        (user_id, product_id, pincode, quantity),
    )
    conn.commit()
    conn.close()


def get_pending_orders_by_product_pincode(product_id, pincode):
    conn = get_db()
    from datetime import datetime, timedelta

    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    orders = conn.execute(
        """SELECT * FROM orders
           WHERE product_id = ? AND pincode = ? AND status = 'pending'
           AND created_at >= ?""",
        (product_id, pincode, week_ago),
    ).fetchall()
    conn.close()
    return orders


def unlock_bulk_orders(product_id, pincode):
    conn = get_db()
    from datetime import datetime, timedelta

    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    conn.execute(
        """UPDATE orders SET status = 'bulk_unlocked'
           WHERE product_id = ? AND pincode = ? AND status = 'pending'
           AND created_at >= ?""",
        (product_id, pincode, week_ago),
    )
    conn.commit()
    conn.close()


def get_all_pending_orders_grouped():
    conn = get_db()
    rows = conn.execute(
        """SELECT o.product_id, o.pincode, p.name as product_name,
                  COUNT(*) as order_count, p.bulk_threshold
           FROM orders o
           JOIN products p ON o.product_id = p.id
           WHERE o.status = 'pending'
           GROUP BY o.product_id, o.pincode
           ORDER BY p.name""",
    ).fetchall()
    conn.close()
    return rows


def get_user_recent_order(user_id, product_id):
    conn = get_db()
    from datetime import datetime, timedelta

    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    order = conn.execute(
        """SELECT * FROM orders
           WHERE user_id = ? AND product_id = ? AND created_at >= ?
           ORDER BY created_at DESC LIMIT 1""",
        (user_id, product_id, week_ago),
    ).fetchone()
    conn.close()
    return order


def get_all_orders_grouped_by_status():
    conn = get_db()
    rows = conn.execute(
        """SELECT o.product_id, o.pincode, p.name as product_name, o.status,
                  COUNT(*) as order_count, p.bulk_threshold
           FROM orders o
           JOIN products p ON o.product_id = p.id
           GROUP BY o.product_id, o.pincode, o.status
           ORDER BY p.name""",
    ).fetchall()
    conn.close()
    return rows


def fulfill_bulk_orders(product_id, pincode):
    conn = get_db()
    conn.execute(
        """UPDATE orders SET status = 'fulfilled'
           WHERE product_id = ? AND pincode = ? AND status = 'bulk_unlocked'""",
        (product_id, pincode),
    )
    conn.commit()
    conn.close()
