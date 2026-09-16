from flask import Blueprint, jsonify, session
from models.vehicle import count_vehicles_by_user
from models.reminder import (
    count_by_status,
    get_overdue_reminders,
    get_upcoming_reminders,
    update_overdue_reminders,
)
from models.service_log import get_total_cost_by_user, get_spend_by_category
from models.product import get_all_products
from models.order import get_pending_orders_by_product_pincode, get_user_recent_order
from models.user import get_user_by_id
from services.bulk_unlock import check_and_unlock
from routes.auth import login_required

api_bp = Blueprint("api", __name__)


@api_bp.route("/api/dashboard")
@login_required
def dashboard_data():
    user_id = session["user_id"]
    update_overdue_reminders(user_id)
    vehicle_count = count_vehicles_by_user(user_id)
    status_counts = count_by_status(user_id)
    overdue = get_overdue_reminders(user_id)
    upcoming = get_upcoming_reminders(user_id, limit=5)
    total_cost = get_total_cost_by_user(user_id)
    spend_by_cat = get_spend_by_category(user_id)

    overdue_list = []
    for r in overdue:
        from datetime import date
        today = date.today()
        due = date.fromisoformat(r["due_date"])
        days_overdue = (today - due).days
        if days_overdue <= 7:
            urgency = "Low"
        elif days_overdue <= 30:
            urgency = "Medium"
        elif days_overdue <= 60:
            urgency = "High"
        else:
            urgency = "Critical"
        overdue_list.append({
            "id": r["id"],
            "vehicle_id": r["vehicle_id"],
            "type": r["type"],
            "due_date": r["due_date"],
            "days_overdue": days_overdue,
            "urgency": urgency,
            "notes": r["notes"] or "",
        })

    upcoming_list = []
    for r in upcoming:
        upcoming_list.append({
            "id": r["id"],
            "vehicle_id": r["vehicle_id"],
            "type": r["type"],
            "due_date": r["due_date"],
            "notes": r["notes"] or "",
        })

    return jsonify({
        "vehicle_count": vehicle_count,
        "overdue_count": status_counts.get("overdue", 0),
        "upcoming_count": status_counts.get("upcoming", 0),
        "completed_count": status_counts.get("completed", 0),
        "total_cost": float(total_cost) if total_cost else 0,
        "overdue": overdue_list,
        "upcoming": upcoming_list,
        "chart_labels": [row["type"] for row in spend_by_cat],
        "chart_data": [float(row["total"]) for row in spend_by_cat],
        "status_labels": list(status_counts.keys()),
        "status_data": list(status_counts.values()),
    })


@api_bp.route("/api/marketplace")
@login_required
def marketplace_data():
    products = get_all_products()
    user = get_user_by_id(session["user_id"])
    user_pincode = user["pincode"] if user else ""

    products_list = []
    for p in products:
        pending = get_pending_orders_by_product_pincode(p["id"], user_pincode)
        existing = get_user_recent_order(session["user_id"], p["id"])
        progress = len(pending)
        already_ordered = existing is not None
        products_list.append({
            "id": p["id"],
            "name": p["name"],
            "category": p["category"],
            "retail_price": float(p["retail_price"]),
            "app_price": float(p["app_price"]),
            "image_path": p["image_path"],
            "bulk_threshold": p["bulk_threshold"],
            "progress": progress,
            "already_ordered": already_ordered,
            "savings": float(p["retail_price"]) - float(p["app_price"]),
        })

    return jsonify({
        "products": products_list,
        "user_pincode": user_pincode,
    })


@api_bp.route("/api/marketplace/order", methods=["POST"])
@login_required
def place_order_api():
    from flask import request
    data = request.get_json()
    if not data or "product_id" not in data:
        return jsonify({"error": "product_id required"}), 400

    product_id = data["product_id"]
    from models.product import get_product_by_id
    product = get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    existing = get_user_recent_order(session["user_id"], product["id"])
    if existing:
        return jsonify({"error": "You already have a pending order for this product"}), 409

    user = get_user_by_id(session["user_id"])
    pincode = user["pincode"] if user else ""
    quantity = data.get("quantity", 1)

    from models.order import create_order
    create_order(session["user_id"], product["id"], pincode, quantity)
    unlocked = check_and_unlock(product["id"], pincode, product["bulk_threshold"])

    if unlocked:
        return jsonify({
            "success": True,
            "unlocked": True,
            "message": f"Bulk unlocked! Your order for {product['name']} is confirmed at Rs.{product['app_price']}",
        })
    else:
        pending = get_pending_orders_by_product_pincode(product["id"], pincode)
        needed = product["bulk_threshold"] - len(pending)
        return jsonify({
            "success": True,
            "unlocked": False,
            "message": f"Order placed! {needed} more orders needed in your area to unlock bulk price.",
            "progress": len(pending),
            "needed": needed,
        })
