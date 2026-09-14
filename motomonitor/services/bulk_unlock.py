"""Bulk unlock logic.

When enough pending orders exist for a product in a pincode within 7 days,
all those orders are unlocked at the app price.
"""

from datetime import datetime, timedelta
from models.db import get_db


def check_and_unlock(product_id, pincode, threshold):
    """Check if bulk threshold is met. If yes, unlock orders. Returns True if unlocked."""
    conn = get_db()
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    count = conn.execute(
        """SELECT COUNT(*) FROM orders
           WHERE product_id = ? AND pincode = ? AND status = 'pending'
           AND created_at >= ?""",
        (product_id, pincode, week_ago),
    ).fetchone()[0]

    if count >= threshold:
        conn.execute(
            """UPDATE orders SET status = 'bulk_unlocked'
               WHERE product_id = ? AND pincode = ? AND status = 'pending'
               AND created_at >= ?""",
            (product_id, pincode, week_ago),
        )
        conn.commit()
        conn.close()
        return True

    conn.close()
    return False
