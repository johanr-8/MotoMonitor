from flask import Blueprint, render_template, session
from models.vehicle import count_vehicles_by_user
from models.reminder import count_by_status, get_overdue_reminders, get_upcoming_reminders
from models.service_log import get_total_cost_by_user, get_spend_by_category
from routes.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    vehicle_count = count_vehicles_by_user(user_id)
    status_counts = count_by_status(user_id)
    overdue = get_overdue_reminders(user_id)
    upcoming = get_upcoming_reminders(user_id, limit=5)
    total_cost = get_total_cost_by_user(user_id)
    spend_by_cat = get_spend_by_category(user_id)

    chart_labels = [row["type"] for row in spend_by_cat]
    chart_data = [float(row["total"]) for row in spend_by_cat]

    status_labels = list(status_counts.keys())
    status_data = list(status_counts.values())

    return render_template(
        "dashboard.html",
        vehicle_count=vehicle_count,
        overdue_count=status_counts.get("overdue", 0),
        upcoming_count=status_counts.get("upcoming", 0),
        completed_count=status_counts.get("completed", 0),
        total_cost=total_cost,
        overdue=overdue,
        upcoming=upcoming,
        chart_labels=chart_labels,
        chart_data=chart_data,
        status_labels=status_labels,
        status_data=status_data,
    )
