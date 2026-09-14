from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.vehicle import (
    get_vehicles_by_user,
    get_vehicle_by_id,
    create_vehicle,
    update_vehicle,
    delete_vehicle,
)
from models.document import get_documents_by_vehicle, get_document_by_id, delete_document as delete_document_record
from models.reminder import get_reminders_by_vehicle, update_overdue_reminders
from models.service_log import get_service_logs_by_vehicle
from routes.auth import login_required
import os
from config import UPLOAD_FOLDER

vehicles_bp = Blueprint("vehicles", __name__)


@vehicles_bp.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard"))
    return redirect(url_for("auth.login"))


@vehicles_bp.route("/vehicles")
@login_required
def list_vehicles():
    vehicles = get_vehicles_by_user(session["user_id"])
    return render_template("vehicles.html", vehicles=vehicles)


@vehicles_bp.route("/vehicles/<int:vehicle_id>")
@login_required
def vehicle_detail(vehicle_id):
    vehicle = get_vehicle_by_id(vehicle_id, session["user_id"])
    if not vehicle:
        flash("Vehicle not found", "danger")
        return redirect(url_for("vehicles.list_vehicles"))

    documents = get_documents_by_vehicle(vehicle_id)
    update_overdue_reminders(session["user_id"])
    reminders = get_reminders_by_vehicle(vehicle_id)
    service_logs = get_service_logs_by_vehicle(vehicle_id)

    return render_template(
        "vehicle_detail.html",
        vehicle=vehicle,
        documents=documents,
        reminders=reminders,
        service_logs=service_logs,
    )


@vehicles_bp.route("/vehicles/add", methods=["GET", "POST"])
@login_required
def add_vehicle():
    if request.method == "POST":
        nickname = request.form.get("nickname", "").strip()
        make = request.form.get("make", "").strip()
        model = request.form.get("model", "").strip()
        reg_no = request.form.get("registration_number", "").strip()
        purchase_date = request.form.get("purchase_date", "")

        if not make or not model or not reg_no or not purchase_date:
            flash("Make, model, registration number, and purchase date are required", "danger")
            return render_template("vehicle_form.html")

        create_vehicle(session["user_id"], nickname, make, model, reg_no, purchase_date)
        flash("Vehicle added!", "success")
        return redirect(url_for("vehicles.list_vehicles"))

    return render_template("vehicle_form.html")


@vehicles_bp.route("/vehicles/<int:vehicle_id>/edit", methods=["GET", "POST"])
@login_required
def edit_vehicle(vehicle_id):
    vehicle = get_vehicle_by_id(vehicle_id, session["user_id"])
    if not vehicle:
        flash("Vehicle not found", "danger")
        return redirect(url_for("vehicles.list_vehicles"))

    if request.method == "POST":
        nickname = request.form.get("nickname", "").strip()
        make = request.form.get("make", "").strip()
        model = request.form.get("model", "").strip()
        reg_no = request.form.get("registration_number", "").strip()
        purchase_date = request.form.get("purchase_date", "")

        if not make or not model or not reg_no or not purchase_date:
            flash("Make, model, registration number, and purchase date are required", "danger")
            return render_template("vehicle_form.html", vehicle=vehicle)

        update_vehicle(vehicle_id, nickname, make, model, reg_no, purchase_date)
        flash("Vehicle updated!", "success")
        return redirect(url_for("vehicles.list_vehicles"))

    return render_template("vehicle_form.html", vehicle=vehicle)


@vehicles_bp.route("/vehicles/<int:vehicle_id>/delete", methods=["POST"])
@login_required
def delete_vehicle_route(vehicle_id):
    vehicle = get_vehicle_by_id(vehicle_id, session["user_id"])
    if not vehicle:
        flash("Vehicle not found", "danger")
        return redirect(url_for("vehicles.list_vehicles"))

    documents = get_documents_by_vehicle(vehicle_id)
    for doc in documents:
        file_path = os.path.join(UPLOAD_FOLDER, doc["filename"])
        if os.path.exists(file_path):
            os.remove(file_path)
        delete_document_record(doc["id"])

    delete_vehicle(vehicle_id, session["user_id"])
    flash("Vehicle deleted", "success")
    return redirect(url_for("vehicles.list_vehicles"))
