from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.product import get_all_products, get_product_by_id
from models.order import (
    create_order,
    get_pending_orders_by_product_pincode,
    get_user_recent_order,
)
from models.user import get_user_by_id
from services.bulk_unlock import check_and_unlock
from routes.auth import login_required

marketplace_bp = Blueprint("marketplace", __name__)


@marketplace_bp.route("/marketplace")
@login_required
def marketplace():
    products = get_all_products()
    user = get_user_by_id(session["user_id"])
    user_pincode = user["pincode"] if user else ""

    products_with_progress = []
    for p in products:
        pending = get_pending_orders_by_product_pincode(p["id"], user_pincode)
        existing = get_user_recent_order(session["user_id"], p["id"])
        progress = len(pending)
        already_ordered = existing is not None
        products_with_progress.append(
            {**p, "progress": progress, "already_ordered": already_ordered}
        )

    return render_template(
        "marketplace.html",
        products=products_with_progress,
        user_pincode=user_pincode,
    )


@marketplace_bp.route("/marketplace/order", methods=["POST"])
@login_required
def place_order():
    product_id = request.form.get("product_id", "")
    product = get_product_by_id(int(product_id)) if product_id.isdigit() else None
    if not product:
        flash("Product not found", "danger")
        return redirect(url_for("marketplace.marketplace"))

    existing = get_user_recent_order(session["user_id"], product["id"])
    if existing:
        flash("You already have a pending order for this product", "warning")
        return redirect(url_for("marketplace.marketplace"))

    user = get_user_by_id(session["user_id"])
    pincode = user["pincode"] if user else ""
    quantity = int(request.form.get("quantity", 1))

    create_order(session["user_id"], product["id"], pincode, quantity)
    unlocked = check_and_unlock(product["id"], pincode, product["bulk_threshold"])

    if unlocked:
        flash(
            f"Bulk unlocked! Your order for {product['name']} is confirmed at Rs.{product['app_price']}",
            "success",
        )
    else:
        pending = get_pending_orders_by_product_pincode(product["id"], pincode)
        needed = product["bulk_threshold"] - len(pending)
        flash(
            f"Order placed! {needed} more orders needed in your area to unlock bulk price.",
            "info",
        )

    return redirect(url_for("marketplace.marketplace"))
