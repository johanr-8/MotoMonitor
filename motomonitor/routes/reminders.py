from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from datetime import date
from models.reminder import (
    get_reminders_by_vehicle,
    get_reminder_by_id,
    create_reminder,
    complete_reminder,
    get_overdue_reminders,
    update_overdue_reminders,
)
from models.vehicle import get_vehicles_by_user, get_vehicle_by_id
from routes.auth import login_required

reminders_bp = Blueprint("reminders", __name__)


@reminders_bp.route("/reminders/add", methods=["GET", "POST"])
@login_required
def add_reminder():
    if request.method == "POST":
        vehicle_id = request.form.get("vehicle_id", "")
        rtype = request.form.get("type", "")
        due_date = request.form.get("due_date", "")
        notes = request.form.get("notes", "")

        if not vehicle_id or not rtype or not due_date:
            flash("Vehicle, type, and due date are required", "danger")
            vehicles = get_vehicles_by_user(session["user_id"])
            return render_template("reminder_form.html", vehicles=vehicles)

        vehicle = get_vehicle_by_id(int(vehicle_id), session["user_id"])
        if not vehicle:
            flash("Invalid vehicle", "danger")
            return redirect(url_for("vehicles.list_vehicles"))

        create_reminder(int(vehicle_id), rtype, due_date, notes)
        flash("Reminder added!", "success")
        return redirect(url_for("vehicles.vehicle_detail", vehicle_id=int(vehicle_id)))

    vehicles = get_vehicles_by_user(session["user_id"])
    return render_template("reminder_form.html", vehicles=vehicles)


@reminders_bp.route("/reminders/<int:reminder_id>/complete", methods=["GET", "POST"])
@login_required
def complete_reminder_route(reminder_id):
    reminder = get_reminder_by_id(reminder_id)
    if not reminder or reminder["user_id"] != session["user_id"]:
        flash("Reminder not found", "danger")
        return redirect(url_for("vehicles.list_vehicles"))

    if request.method == "POST":
        cost = request.form.get("cost", 0)
        notes = request.form.get("notes", "")
        try:
            cost = float(cost) if cost else 0
        except ValueError:
            cost = 0
        complete_reminder(reminder_id, cost, notes)
        flash("Reminder completed! Service logged.", "success")
        return redirect(url_for("vehicles.vehicle_detail", vehicle_id=reminder["vehicle_id"]))

    return render_template("complete_reminder.html", reminder=reminder)


@reminders_bp.route("/reminders/overdue")
@login_required
def overdue_reminders():
    update_overdue_reminders(session["user_id"])
    reminders = get_overdue_reminders(session["user_id"])

    today = date.today()
    enriched = []
    for r in reminders:
        due = date.fromisoformat(r["due_date"])
        days_overdue = (today - due).days
        enriched.append({**r, "days_overdue": days_overdue})

    return render_template("overdue.html", reminders=enriched)
