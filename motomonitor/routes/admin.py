from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from models.order import get_all_pending_orders_grouped, fulfill_bulk_orders
from models.user import get_user_by_id
from routes.auth import login_required

admin_bp = Blueprint("admin", __name__)


def _is_admin():
    user = get_user_by_id(session["user_id"])
    return user and user["role"] == "admin"


@admin_bp.route("/admin/bulk-orders")
@login_required
def bulk_orders():
    if not _is_admin():
        flash("Admin access required", "danger")
        return redirect(url_for("dashboard.dashboard"))

    grouped = get_all_pending_orders_grouped()
    return render_template("admin_bulk_orders.html", grouped=grouped)


@admin_bp.route("/admin/bulk-orders/fulfill", methods=["POST"])
@login_required
def fulfill_order():
    if not _is_admin():
        flash("Admin access required", "danger")
        return redirect(url_for("dashboard.dashboard"))

    product_id = request.form.get("product_id", "")
    pincode = request.form.get("pincode", "")

    if product_id and pincode and product_id.isdigit():
        fulfill_bulk_orders(int(product_id), pincode)
        flash("Orders marked as fulfilled!", "success")
    else:
        flash("Invalid request", "danger")

    return redirect(url_for("admin.bulk_orders"))
