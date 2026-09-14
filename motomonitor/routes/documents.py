from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
import uuid
from config import UPLOAD_FOLDER
from models.document import (
    get_documents_by_vehicle,
    get_document_by_id,
    create_document,
    delete_document,
)
from routes.auth import login_required

documents_bp = Blueprint("documents", __name__)

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif", "doc", "docx", "txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@documents_bp.route("/vehicles/<int:vehicle_id>/documents/upload", methods=["POST"])
@login_required
def upload_document(vehicle_id):
    file = request.files.get("file")
    if not file or file.filename == "":
        flash("No file selected", "danger")
        return redirect(url_for("vehicles.vehicle_detail", vehicle_id=vehicle_id))

    if not allowed_file(file.filename):
        flash(f"File type not allowed. Use: {', '.join(sorted(ALLOWED_EXTENSIONS))}", "danger")
        return redirect(url_for("vehicles.vehicle_detail", vehicle_id=vehicle_id))

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    if file_size > MAX_FILE_SIZE:
        flash("File too large. Maximum size is 10MB.", "danger")
        return redirect(url_for("vehicles.vehicle_detail", vehicle_id=vehicle_id))

    original_name = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{original_name}"
    file.save(os.path.join(UPLOAD_FOLDER, unique_name))
    create_document(vehicle_id, unique_name, file.filename)

    flash("Document uploaded!", "success")
    return redirect(url_for("vehicles.vehicle_detail", vehicle_id=vehicle_id))


@documents_bp.route("/documents/<int:doc_id>/delete", methods=["POST"])
@login_required
def delete_document_route(doc_id):
    doc = get_document_by_id(doc_id)
    if not doc or doc["user_id"] != session["user_id"]:
        flash("Document not found", "danger")
        return redirect(url_for("vehicles.list_vehicles"))

    file_path = os.path.join(UPLOAD_FOLDER, doc["filename"])
    if os.path.exists(file_path):
        os.remove(file_path)

    delete_document(doc_id)
    flash("Document deleted", "success")
    return redirect(url_for("vehicles.vehicle_detail", vehicle_id=doc["vehicle_id"]))
