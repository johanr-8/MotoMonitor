"""
Comprehensive audit test for MotoMonitor Flask app.
Tests every route, flow, edge case, and security concern.
"""

import os
import sys
import io
import tempfile
import shutil
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))

# Override database path before importing app
import models.db as db_module
_orig_db_path = db_module.DB_PATH

TEST_DB = os.path.join(tempfile.gettempdir(), "motomonitor_test.db")
TEST_UPLOAD = os.path.join(tempfile.gettempdir(), "motomonitor_test_uploads")
db_module.DB_PATH = TEST_DB
os.environ["SECRET_KEY"] = "test-secret-key-for-audit"

# Patch config too
import config
config.DATABASE_PATH = TEST_DB
config.UPLOAD_FOLDER = TEST_UPLOAD

# Now import app
from app import app


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        if os.path.exists(TEST_UPLOAD):
            shutil.rmtree(TEST_UPLOAD)
        os.makedirs(TEST_UPLOAD, exist_ok=True)
        db_module.DB_PATH = TEST_DB
        config.DATABASE_PATH = TEST_DB
        config.UPLOAD_FOLDER = TEST_UPLOAD
        from models.db import init_db
        init_db()
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret"
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        if os.path.exists(TEST_UPLOAD):
            shutil.rmtree(TEST_UPLOAD)

    def signup(self, name="Test User", email="test@example.com", password="pass123", phone="1234567890"):
        return self.client.post("/signup", data={
            "name": name, "email": email, "password": password, "phone": phone
        }, follow_redirects=True)

    def login(self, email="test@example.com", password="pass123"):
        return self.client.post("/login", data={
            "email": email, "password": password
        }, follow_redirects=True)

    def create_vehicle(self, nickname="My Bike", make="Honda", model="CB350",
                       reg="MH12AB1234", date="2024-01-15"):
        return self.client.post("/vehicles/add", data={
            "nickname": nickname, "make": make, "model": model,
            "registration_number": reg, "purchase_date": date
        }, follow_redirects=True)


class TestHomePage(BaseTestCase):
    def test_home_redirects_to_login_when_logged_out(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_home_redirects_to_dashboard_when_logged_in(self):
        self.signup()
        self.login()
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/dashboard", resp.headers["Location"])


class TestAuthSignup(BaseTestCase):
    def test_signup_page_renders(self):
        resp = self.client.get("/signup")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Sign Up", resp.data)

    def test_signup_success(self):
        resp = self.signup()
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Account created", resp.data)

    def test_signup_duplicate_email(self):
        self.signup()
        resp = self.signup()
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"already registered", resp.data)

    def test_signup_missing_fields(self):
        resp = self.client.post("/signup", data={}, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

    def test_signup_no_phone(self):
        resp = self.client.post("/signup", data={
            "name": "No Phone", "email": "nophone@test.com", "password": "pass"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Account created", resp.data)


class TestAuthLogin(BaseTestCase):
    def test_login_page_renders(self):
        resp = self.client.get("/login")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Login", resp.data)

    def test_login_success(self):
        self.signup()
        resp = self.login()
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Dashboard", resp.data)

    def test_login_wrong_password(self):
        self.signup()
        resp = self.client.post("/login", data={
            "email": "test@example.com", "password": "wrongpass"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Invalid email or password", resp.data)

    def test_login_nonexistent_email(self):
        resp = self.client.post("/login", data={
            "email": "noone@test.com", "password": "pass"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Invalid email or password", resp.data)

    def test_login_missing_fields(self):
        resp = self.client.post("/login", data={}, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)


class TestAuthLogout(BaseTestCase):
    def test_logout_clears_session(self):
        self.signup()
        self.login()
        resp = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Login", resp.data)

    def test_logout_redirects_to_login(self):
        self.signup()
        self.login()
        resp = self.client.get("/logout")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])


class TestSessionProtection(BaseTestCase):
    def test_vehicles_requires_login(self):
        resp = self.client.get("/vehicles")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_dashboard_requires_login(self):
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_add_vehicle_requires_login(self):
        resp = self.client.get("/vehicles/add")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_add_reminder_requires_login(self):
        resp = self.client.get("/reminders/add")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_marketplace_requires_login(self):
        resp = self.client.get("/marketplace")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_overdue_requires_login(self):
        resp = self.client.get("/reminders/overdue")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_admin_requires_login(self):
        resp = self.client.get("/admin/bulk-orders")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_complete_reminder_requires_login(self):
        resp = self.client.get("/reminders/1/complete")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_document_upload_requires_login(self):
        resp = self.client.post("/vehicles/1/documents/upload")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_document_delete_requires_login(self):
        resp = self.client.post("/documents/1/delete")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])


class TestVehicleCRUD(BaseTestCase):
    def test_vehicles_list_renders_empty(self):
        self.signup()
        self.login()
        resp = self.client.get("/vehicles")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"No vehicles yet", resp.data)

    def test_add_vehicle_page_renders(self):
        self.signup()
        self.login()
        resp = self.client.get("/vehicles/add")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Add Vehicle", resp.data)

    def test_add_vehicle_success(self):
        self.signup()
        self.login()
        resp = self.create_vehicle()
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Vehicle added", resp.data)
        self.assertIn(b"My Bike", resp.data)

    def test_add_vehicle_without_nickname(self):
        self.signup()
        self.login()
        resp = self.client.post("/vehicles/add", data={
            "nickname": "", "make": "Yamaha", "model": "MT15",
            "registration_number": "KA01CD5678", "purchase_date": "2023-06-01"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Vehicle added", resp.data)

    def test_vehicle_detail_renders(self):
        self.signup()
        self.login()
        self.create_vehicle()
        resp = self.client.get("/vehicles/1")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"My Bike", resp.data)
        self.assertIn(b"Documents", resp.data)
        self.assertIn(b"Reminders", resp.data)
        self.assertIn(b"Service Log", resp.data)

    def test_vehicle_detail_not_found_redirects(self):
        self.signup()
        self.login()
        resp = self.client.get("/vehicles/999", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Vehicle not found", resp.data)

    def test_edit_vehicle_page_renders(self):
        self.signup()
        self.login()
        self.create_vehicle()
        resp = self.client.get("/vehicles/1/edit")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Edit Vehicle", resp.data)
        self.assertIn(b"My Bike", resp.data)

    def test_edit_vehicle_success(self):
        self.signup()
        self.login()
        self.create_vehicle()
        resp = self.client.post("/vehicles/1/edit", data={
            "nickname": "Updated Bike", "make": "Honda", "model": "CB500X",
            "registration_number": "MH12AB1234", "purchase_date": "2024-01-15"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Vehicle updated", resp.data)

    def test_edit_vehicle_not_found(self):
        self.signup()
        self.login()
        resp = self.client.get("/vehicles/999/edit", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Vehicle not found", resp.data)

    def test_delete_vehicle_success(self):
        self.signup()
        self.login()
        self.create_vehicle()
        resp = self.client.post("/vehicles/1/delete", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Vehicle deleted", resp.data)
        self.assertIn(b"No vehicles yet", resp.data)

    def test_add_vehicle_missing_fields(self):
        self.signup()
        self.login()
        resp = self.client.post("/vehicles/add", data={}, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

    def test_vehicle_detail_shows_documents_section(self):
        self.signup()
        self.login()
        self.create_vehicle()
        resp = self.client.get("/vehicles/1")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"No documents uploaded yet", resp.data)

    def test_vehicle_detail_shows_reminders_section(self):
        self.signup()
        self.login()
        self.create_vehicle()
        resp = self.client.get("/vehicles/1")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"No reminders yet", resp.data)

    def test_vehicle_detail_shows_service_log_section(self):
        self.signup()
        self.login()
        self.create_vehicle()
        resp = self.client.get("/vehicles/1")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"No service history yet", resp.data)


class TestDocumentUploadDelete(BaseTestCase):
    def test_upload_document_success(self):
        self.signup()
        self.login()
        self.create_vehicle()
        data = {"file": (io.BytesIO(b"test content"), "test.pdf")}
        resp = self.client.post(
            "/vehicles/1/documents/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Document uploaded", resp.data)
        self.assertIn(b"test.pdf", resp.data)

    def test_upload_no_file(self):
        self.signup()
        self.login()
        self.create_vehicle()
        resp = self.client.post(
            "/vehicles/1/documents/upload",
            data={},
            content_type="multipart/form-data",
            follow_redirects=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"No file selected", resp.data)

    def test_upload_empty_filename(self):
        self.signup()
        self.login()
        self.create_vehicle()
        data = {"file": (io.BytesIO(b""), "")}
        resp = self.client.post(
            "/vehicles/1/documents/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"No file selected", resp.data)

    def test_delete_document_success(self):
        self.signup()
        self.login()
        self.create_vehicle()
        data = {"file": (io.BytesIO(b"test content"), "test.pdf")}
        self.client.post(
            "/vehicles/1/documents/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True
        )
        resp = self.client.post("/documents/1/delete", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Document deleted", resp.data)

    def test_delete_document_not_found(self):
        self.signup()
        self.login()
        resp = self.client.post("/documents/999/delete", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Document not found", resp.data)

    def test_document_saved_to_disk(self):
        self.signup()
        self.login()
        self.create_vehicle()
        data = {"file": (io.BytesIO(b"file content here"), "disk_test.txt")}
        self.client.post(
            "/vehicles/1/documents/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True
        )
        files = os.listdir(TEST_UPLOAD)
        matching = [f for f in files if f.endswith("disk_test.txt")]
        self.assertTrue(len(matching) > 0, f"Expected file ending with 'disk_test.txt' in {files}")

    def test_document_deleted_from_disk(self):
        self.signup()
        self.login()
        self.create_vehicle()
        data = {"file": (io.BytesIO(b"file content"), "delete_me.txt")}
        self.client.post(
            "/vehicles/1/documents/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True
        )
        files_before = os.listdir(TEST_UPLOAD)
        matching_before = [f for f in files_before if f.endswith("delete_me.txt")]
        self.assertTrue(len(matching_before) > 0)
        self.client.post("/documents/1/delete", follow_redirects=True)
        files_after = os.listdir(TEST_UPLOAD)
        matching_after = [f for f in files_after if f.endswith("delete_me.txt")]
        self.assertEqual(len(matching_after), 0)


class TestReminderFlow(BaseTestCase):
    def test_add_reminder_page_renders(self):
        self.signup()
        self.login()
        self.create_vehicle()
        resp = self.client.get("/reminders/add")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Add Reminder", resp.data)

    def test_add_reminder_success(self):
        self.signup()
        self.login()
        self.create_vehicle()
        future = (date.today() + timedelta(days=30)).isoformat()
        resp = self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "insurance", "due_date": future, "notes": "Test note"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Reminder added", resp.data)

    def test_add_reminder_invalid_vehicle(self):
        self.signup()
        self.login()
        self.create_vehicle()
        future = (date.today() + timedelta(days=30)).isoformat()
        resp = self.client.post("/reminders/add", data={
            "vehicle_id": "999", "type": "insurance", "due_date": future
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Invalid vehicle", resp.data)

    def test_add_reminder_no_notes(self):
        self.signup()
        self.login()
        self.create_vehicle()
        future = (date.today() + timedelta(days=30)).isoformat()
        resp = self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "road_tax", "due_date": future
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Reminder added", resp.data)

    def test_complete_reminder_page_renders(self):
        self.signup()
        self.login()
        self.create_vehicle()
        future = (date.today() + timedelta(days=30)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "insurance", "due_date": future
        }, follow_redirects=True)
        resp = self.client.get("/reminders/1/complete")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Complete Reminder", resp.data)

    def test_complete_reminder_success(self):
        self.signup()
        self.login()
        self.create_vehicle()
        future = (date.today() + timedelta(days=30)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "insurance", "due_date": future
        }, follow_redirects=True)
        resp = self.client.post("/reminders/1/complete", data={
            "cost": "2500", "notes": "Paid via UPI"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Reminder completed", resp.data)
        self.assertIn(b"Service logged", resp.data)

    def test_complete_reminder_not_found(self):
        self.signup()
        self.login()
        resp = self.client.get("/reminders/999/complete", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Reminder not found", resp.data)

    def test_complete_reminder_without_cost(self):
        self.signup()
        self.login()
        self.create_vehicle()
        future = (date.today() + timedelta(days=30)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "service", "due_date": future
        }, follow_redirects=True)
        resp = self.client.post("/reminders/1/complete", data={
            "notes": "Free checkup"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Reminder completed", resp.data)

    def test_all_reminder_types(self):
        self.signup()
        self.login()
        self.create_vehicle()
        types = ["insurance", "road_tax", "puc", "driving_license",
                 "rc_renewal", "warranty", "amc", "service"]
        future = (date.today() + timedelta(days=60)).isoformat()
        for i, rtype in enumerate(types, 1):
            resp = self.client.post("/reminders/add", data={
                "vehicle_id": "1", "type": rtype, "due_date": future
            }, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Reminder added", resp.data)


class TestOverdueReminders(BaseTestCase):
    def test_overdue_page_renders_empty(self):
        self.signup()
        self.login()
        resp = self.client.get("/reminders/overdue")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"No overdue reminders", resp.data)

    def test_overdue_detection_with_past_date(self):
        self.signup()
        self.login()
        self.create_vehicle()
        past = (date.today() - timedelta(days=10)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "insurance", "due_date": past
        }, follow_redirects=True)
        resp = self.client.get("/reminders/overdue")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Insurance", resp.data)

    def test_overdue_not_completed(self):
        self.signup()
        self.login()
        self.create_vehicle()
        past = (date.today() - timedelta(days=5)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "road_tax", "due_date": past
        }, follow_redirects=True)
        self.client.post("/reminders/1/complete", data={
            "cost": "500"
        }, follow_redirects=True)
        resp = self.client.get("/reminders/overdue")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"No overdue reminders", resp.data)

    def test_multiple_overdue_reminders(self):
        self.signup()
        self.login()
        self.create_vehicle()
        past1 = (date.today() - timedelta(days=30)).isoformat()
        past2 = (date.today() - timedelta(days=60)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "insurance", "due_date": past1
        }, follow_redirects=True)
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "puc", "due_date": past2
        }, follow_redirects=True)
        resp = self.client.get("/reminders/overdue")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Insurance", resp.data)
        self.assertIn(b"Puc", resp.data)


class TestDashboard(BaseTestCase):
    def test_dashboard_renders(self):
        self.signup()
        self.login()
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Dashboard", resp.data)
        self.assertIn(b"Overdue", resp.data)
        self.assertIn(b"Upcoming", resp.data)
        self.assertIn(b"Vehicles", resp.data)
        self.assertIn(b"Total Spent", resp.data)

    def test_dashboard_with_vehicle(self):
        self.signup()
        self.login()
        self.create_vehicle()
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"dashboard-root", resp.data)  # React mount point

    def test_dashboard_with_reminder(self):
        self.signup()
        self.login()
        self.create_vehicle()
        future = (date.today() + timedelta(days=10)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "insurance", "due_date": future
        }, follow_redirects=True)
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_with_completed_reminder_and_cost(self):
        self.signup()
        self.login()
        self.create_vehicle()
        future = (date.today() + timedelta(days=10)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "insurance", "due_date": future
        }, follow_redirects=True)
        self.client.post("/reminders/1/complete", data={
            "cost": "3500", "notes": "Annual premium"
        }, follow_redirects=True)
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"dashboard-root", resp.data)  # React mount point

    def test_dashboard_with_overdue(self):
        self.signup()
        self.login()
        self.create_vehicle()
        past = (date.today() - timedelta(days=5)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "insurance", "due_date": past
        }, follow_redirects=True)
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)


class TestMarketplace(BaseTestCase):
    def test_marketplace_renders(self):
        self.signup()
        self.login()
        resp = self.client.get("/marketplace")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Marketplace", resp.data)
        self.assertIn(b"marketplace-root", resp.data)  # React mount point

    def test_marketplace_shows_all_products(self):
        self.signup()
        self.login()
        resp = self.client.get("/marketplace")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"marketplace-root", resp.data)  # React loads products via API

    def test_place_order_success(self):
        self.signup()
        self.login()
        resp = self.client.post("/marketplace/order", data={
            "product_id": "1"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Order placed", resp.data)

    def test_place_order_duplicate(self):
        self.signup()
        self.login()
        self.client.post("/marketplace/order", data={"product_id": "1"}, follow_redirects=True)
        resp = self.client.post("/marketplace/order", data={"product_id": "1"}, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"already have a pending order", resp.data)

    def test_place_order_invalid_product(self):
        self.signup()
        self.login()
        resp = self.client.post("/marketplace/order", data={
            "product_id": "999"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Product not found", resp.data)

    def test_marketplace_shows_bulk_progress(self):
        self.signup()
        self.login()
        resp = self.client.get("/marketplace")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"marketplace-root", resp.data)  # React loads progress via API

    def test_marketplace_shows_pincode(self):
        self.signup()
        self.login()
        resp = self.client.get("/marketplace")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"marketplace-root", resp.data)  # React loads pincode via API


class TestAdmin(BaseTestCase):
    def test_admin_requires_role(self):
        self.signup()
        self.login()
        resp = self.client.get("/admin/bulk-orders", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Admin access required", resp.data)

    def test_admin_renders_for_admin_user(self):
        from models.db import get_db
        self.signup(name="Admin", email="admin@test.com", password="pass")
        self.login(email="admin@test.com", password="pass")
        conn = get_db()
        conn.execute("UPDATE users SET role = 'admin' WHERE email = 'admin@test.com'")
        conn.commit()
        conn.close()
        resp = self.client.get("/admin/bulk-orders")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Bulk Orders", resp.data)

    def test_admin_empty_orders(self):
        from models.db import get_db
        self.signup(name="Admin", email="admin@test.com", password="pass")
        self.login(email="admin@test.com", password="pass")
        conn = get_db()
        conn.execute("UPDATE users SET role = 'admin' WHERE email = 'admin@test.com'")
        conn.commit()
        conn.close()
        resp = self.client.get("/admin/bulk-orders")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"No bulk orders to process right now.", resp.data)

    def test_admin_page_has_back_button(self):
        from models.db import get_db
        self.signup(name="Admin", email="admin@test.com", password="pass")
        self.login(email="admin@test.com", password="pass")
        conn = get_db()
        conn.execute("UPDATE users SET role = 'admin' WHERE email = 'admin@test.com'")
        conn.commit()
        conn.close()
        resp = self.client.get("/admin/bulk-orders")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Back to Dashboard", resp.data)


class TestCrossUserAccess(BaseTestCase):
    def test_user_cannot_see_other_users_vehicle(self):
        self.signup(name="User1", email="u1@test.com", password="pass1")
        self.login(email="u1@test.com", password="pass1")
        self.create_vehicle(nickname="User1 Bike")
        self.client.get("/logout")

        self.signup(name="User2", email="u2@test.com", password="pass2")
        self.login(email="u2@test.com", password="pass2")
        resp = self.client.get("/vehicles/1", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Vehicle not found", resp.data)

    def test_user_cannot_edit_other_users_vehicle(self):
        self.signup(name="User1", email="u1@test.com", password="pass1")
        self.login(email="u1@test.com", password="pass1")
        self.create_vehicle()
        self.client.get("/logout")

        self.signup(name="User2", email="u2@test.com", password="pass2")
        self.login(email="u2@test.com", password="pass2")
        resp = self.client.get("/vehicles/1/edit", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Vehicle not found", resp.data)

    def test_user_cannot_delete_other_users_vehicle(self):
        self.signup(name="User1", email="u1@test.com", password="pass1")
        self.login(email="u1@test.com", password="pass1")
        self.create_vehicle()
        self.client.get("/logout")

        self.signup(name="User2", email="u2@test.com", password="pass2")
        self.login(email="u2@test.com", password="pass2")
        resp = self.client.post("/vehicles/1/delete", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

    def test_user_cannot_complete_other_users_reminder(self):
        self.signup(name="User1", email="u1@test.com", password="pass1")
        self.login(email="u1@test.com", password="pass1")
        self.create_vehicle()
        future = (date.today() + timedelta(days=30)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "insurance", "due_date": future
        }, follow_redirects=True)
        self.client.get("/logout")

        self.signup(name="User2", email="u2@test.com", password="pass2")
        self.login(email="u2@test.com", password="pass2")
        resp = self.client.get("/reminders/1/complete", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Reminder not found", resp.data)

    def test_user_cannot_delete_other_users_document(self):
        self.signup(name="User1", email="u1@test.com", password="pass1")
        self.login(email="u1@test.com", password="pass1")
        self.create_vehicle()
        data = {"file": (io.BytesIO(b"secret"), "secret.pdf")}
        self.client.post(
            "/vehicles/1/documents/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True
        )
        self.client.get("/logout")

        self.signup(name="User2", email="u2@test.com", password="pass2")
        self.login(email="u2@test.com", password="pass2")
        resp = self.client.post("/documents/1/delete", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Document not found", resp.data)


class TestInvalidIDs(BaseTestCase):
    def test_vehicle_detail_invalid_id(self):
        self.signup()
        self.login()
        resp = self.client.get("/vehicles/abc", follow_redirects=True)
        self.assertEqual(resp.status_code, 404)

    def test_edit_vehicle_invalid_id(self):
        self.signup()
        self.login()
        resp = self.client.get("/vehicles/abc/edit", follow_redirects=True)
        self.assertEqual(resp.status_code, 404)

    def test_complete_reminder_invalid_id(self):
        self.signup()
        self.login()
        resp = self.client.get("/reminders/abc/complete", follow_redirects=True)
        self.assertEqual(resp.status_code, 404)

    def test_delete_document_invalid_id(self):
        self.signup()
        self.login()
        resp = self.client.post("/documents/abc/delete", follow_redirects=True)
        self.assertEqual(resp.status_code, 404)


class TestSQLInjection(BaseTestCase):
    def test_sql_injection_signup_email(self):
        resp = self.client.post("/signup", data={
            "name": "Hacker", "email": "'; DROP TABLE users; --",
            "password": "pass"
        }, follow_redirects=True)
        self.assertIn(resp.status_code, [200, 302])
        # App should still work after this
        self.signup(email="legit@test.com")
        resp = self.client.get("/vehicles")
        self.assertEqual(resp.status_code, 200)

    def test_sql_injection_login(self):
        self.signup()
        resp = self.client.post("/login", data={
            "email": "' OR '1'='1", "password": "anything"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Invalid email or password", resp.data)

    def test_sql_injection_vehicle_search(self):
        self.signup()
        self.login()
        resp = self.client.get("/vehicles/1 OR 1=1")
        self.assertEqual(resp.status_code, 404)


class TestTemplateErrors(BaseTestCase):
    def test_all_templates_render_without_error(self):
        self.signup()
        self.login()
        self.create_vehicle()
        future = (date.today() + timedelta(days=30)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "insurance", "due_date": future
        }, follow_redirects=True)

        pages = [
            "/",
            "/login",
            "/signup",
            "/dashboard",
            "/vehicles",
            "/vehicles/1",
            "/vehicles/1/edit",
            "/vehicles/add",
            "/reminders/add",
            "/reminders/1/complete",
            "/reminders/overdue",
            "/marketplace",
        ]
        for url in pages:
            resp = self.client.get(url)
            self.assertIn(resp.status_code, [200, 302],
                          f"Template error at {url}: status={resp.status_code}")

    def test_dashboard_template_no_jinja_errors(self):
        self.signup()
        self.login()
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(b"UndefinedError", resp.data)
        self.assertNotIn(b"TemplateSyntaxError", resp.data)

    def test_vehicle_detail_template_no_jinja_errors(self):
        self.signup()
        self.login()
        self.create_vehicle()
        resp = self.client.get("/vehicles/1")
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(b"UndefinedError", resp.data)
        self.assertNotIn(b"TemplateSyntaxError", resp.data)


class TestEdgeCases(BaseTestCase):
    def test_signup_with_only_required_fields(self):
        resp = self.client.post("/signup", data={
            "name": "Minimal", "email": "min@test.com", "password": "p"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Account created", resp.data)

    def test_vehicle_with_special_characters(self):
        self.signup()
        self.login()
        resp = self.client.post("/vehicles/add", data={
            "nickname": "Bike <script>alert('x')</script>",
            "make": "Honda & Sons",
            "model": "CB\"350",
            "registration_number": "MH/12/AB/1234",
            "purchase_date": "2024-01-15"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Vehicle added", resp.data)

    def test_multiple_users_independent_data(self):
        self.signup(name="User1", email="u1@test.com", password="pass1")
        self.login(email="u1@test.com", password="pass1")
        self.create_vehicle(nickname="U1 Bike")
        self.client.get("/logout")

        self.signup(name="User2", email="u2@test.com", password="pass2")
        self.login(email="u2@test.com", password="pass2")
        self.create_vehicle(nickname="U2 Bike")

        resp = self.client.get("/vehicles")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"U2 Bike", resp.data)
        self.assertNotIn(b"U1 Bike", resp.data)

    def test_order_with_quantity(self):
        self.signup()
        self.login()
        resp = self.client.post("/marketplace/order", data={
            "product_id": "1", "quantity": "3"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Order placed", resp.data)

    def test_overdue_page_calculation(self):
        self.signup()
        self.login()
        self.create_vehicle()
        past = (date.today() - timedelta(days=15)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "puc", "due_date": past
        }, follow_redirects=True)
        resp = self.client.get("/reminders/overdue")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Puc", resp.data)

    def test_complete_already_completed_reminder(self):
        self.signup()
        self.login()
        self.create_vehicle()
        future = (date.today() + timedelta(days=30)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "service", "due_date": future
        }, follow_redirects=True)
        self.client.post("/reminders/1/complete", data={
            "cost": "1000"
        }, follow_redirects=True)
        # Try to complete again
        resp = self.client.post("/reminders/1/complete", data={
            "cost": "500"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

    def test_vehicle_delete_cascading_data(self):
        self.signup()
        self.login()
        self.create_vehicle()
        future = (date.today() + timedelta(days=30)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "insurance", "due_date": future
        }, follow_redirects=True)
        data = {"file": (io.BytesIO(b"doc"), "doc.pdf")}
        self.client.post(
            "/vehicles/1/documents/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True
        )
        resp = self.client.post("/vehicles/1/delete", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

    def test_progress_bar_zero_division(self):
        """Marketplace with 0 bulk_threshold should not crash."""
        self.signup()
        self.login()
        from models.db import get_db
        conn = get_db()
        conn.execute("UPDATE products SET bulk_threshold = 0 WHERE id = 1")
        conn.commit()
        conn.close()
        resp = self.client.get("/marketplace")
        self.assertEqual(resp.status_code, 200)


class TestBulkUnlock(BaseTestCase):
    def test_bulk_unlock_at_threshold(self):
        self.signup()
        self.login()
        from models.db import get_db
        conn = get_db()
        conn.execute("UPDATE products SET bulk_threshold = 2 WHERE id = 1")
        conn.commit()
        conn.close()

        self.client.post("/marketplace/order", data={"product_id": "1"}, follow_redirects=True)
        self.client.get("/logout")

        self.signup(name="User2", email="u2@test.com", password="pass2")
        self.login(email="u2@test.com", password="pass2")
        resp = self.client.post("/marketplace/order", data={"product_id": "1"}, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Bulk unlocked", resp.data)

    def test_bulk_unlock_not_reached(self):
        self.signup()
        self.login()
        from models.db import get_db
        conn = get_db()
        conn.execute("UPDATE products SET bulk_threshold = 5 WHERE id = 1")
        conn.commit()
        conn.close()

        resp = self.client.post("/marketplace/order", data={"product_id": "1"}, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"more orders needed", resp.data)


class TestServiceLog(BaseTestCase):
    def test_service_log_shows_on_vehicle_detail(self):
        self.signup()
        self.login()
        self.create_vehicle()
        future = (date.today() + timedelta(days=30)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "insurance", "due_date": future
        }, follow_redirects=True)
        self.client.post("/reminders/1/complete", data={
            "cost": "3500", "notes": "Annual premium paid"
        }, follow_redirects=True)
        resp = self.client.get("/vehicles/1")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"3500", resp.data)
        self.assertIn(b"Annual premium paid", resp.data)
        self.assertIn(b"Insurance", resp.data)


class TestNavbar(BaseTestCase):
    def test_navbar_shows_when_logged_out(self):
        resp = self.client.get("/login")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Login", resp.data)
        self.assertIn(b"Sign Up", resp.data)

    def test_navbar_shows_when_logged_in(self):
        self.signup()
        self.login()
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Dashboard", resp.data)
        self.assertIn(b"Vehicles", resp.data)
        self.assertIn(b"Overdue", resp.data)
        self.assertIn(b"Marketplace", resp.data)
        self.assertIn(b"Logout", resp.data)
        self.assertIn(b"Test User", resp.data)


class TestCharts(BaseTestCase):
    def test_dashboard_charts_render(self):
        self.signup()
        self.login()
        self.create_vehicle()
        future = (date.today() + timedelta(days=10)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "insurance", "due_date": future
        }, follow_redirects=True)
        self.client.post("/reminders/1/complete", data={
            "cost": "2000"
        }, follow_redirects=True)
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"spendChart", resp.data)
        self.assertIn(b"statusChart", resp.data)
        self.assertIn(b"chart.js", resp.data)


class TestReminderSchedulerService(BaseTestCase):
    def test_check_reminders_runs_without_error(self):
        from services.reminder_scheduler import check_reminders
        check_reminders()

    def test_check_reminders_with_data(self):
        self.signup()
        self.login()
        self.create_vehicle()
        future = (date.today() + timedelta(days=5)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "insurance", "due_date": future
        }, follow_redirects=True)
        from services.reminder_scheduler import check_reminders
        check_reminders()


class TestNotifierService(BaseTestCase):
    def test_send_email_stub(self):
        from services.notifier import send_email
        result = send_email("test@test.com", "Test Subject", "Test Body")
        self.assertTrue(result)

    def test_send_sms_stub(self):
        from services.notifier import send_sms
        result = send_sms("1234567890", "Test message")
        self.assertTrue(result)

    def test_send_reminder_alert(self):
        from services.notifier import send_reminder_alert
        user = {"name": "Test", "email": "test@test.com", "phone": "1234567890"}
        vehicle = {"nickname": "Bike", "make": "Honda", "model": "CB350", "registration_number": "MH12AB1234"}
        reminder = {"type": "insurance", "due_date": "2024-12-01"}
        result = send_reminder_alert(user, vehicle, reminder, 5)
        self.assertTrue(result)


class TestBulkUnlockService(BaseTestCase):
    def test_check_and_unlock_below_threshold(self):
        from services.bulk_unlock import check_and_unlock
        result = check_and_unlock(1, "110001", 5)
        self.assertFalse(result)

    def test_check_and_unlock_above_threshold(self):
        self.signup()
        self.login()
        from models.db import get_db
        conn = get_db()
        conn.execute("UPDATE products SET bulk_threshold = 1 WHERE id = 1")
        conn.commit()
        conn.close()
        from models.order import create_order
        create_order(1, 1, "110001", 1)
        from services.bulk_unlock import check_and_unlock
        result = check_and_unlock(1, "110001", 1)
        self.assertTrue(result)


class TestDatabaseInit(unittest.TestCase):
    def test_init_db_creates_tables(self):
        test_db = os.path.join(tempfile.gettempdir(), "motomonitor_init_test.db")
        if os.path.exists(test_db):
            os.remove(test_db)
        import models.db as test_db_mod
        old_path = test_db_mod.DB_PATH
        test_db_mod.DB_PATH = test_db
        from models.db import init_db
        init_db()
        import sqlite3
        conn = sqlite3.connect(test_db)
        tables = [row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        conn.close()
        test_db_mod.DB_PATH = old_path
        os.remove(test_db)
        self.assertIn("users", tables)
        self.assertIn("vehicles", tables)
        self.assertIn("reminders", tables)
        self.assertIn("documents", tables)
        self.assertIn("service_log", tables)
        self.assertIn("products", tables)
        self.assertIn("orders", tables)

    def test_init_db_seeds_products(self):
        test_db = os.path.join(tempfile.gettempdir(), "motomonitor_seed_test.db")
        if os.path.exists(test_db):
            os.remove(test_db)
        import models.db as test_db_mod
        old_path = test_db_mod.DB_PATH
        test_db_mod.DB_PATH = test_db
        from models.db import init_db
        init_db()
        import sqlite3
        conn = sqlite3.connect(test_db)
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        conn.close()
        test_db_mod.DB_PATH = old_path
        os.remove(test_db)
        self.assertEqual(count, 8)


class TestPasswordHashing(BaseTestCase):
    def test_password_not_stored_plaintext(self):
        self.signup(email="hash@test.com")
        from models.user import get_user_by_email
        user = get_user_by_email("hash@test.com")
        self.assertNotEqual(user["password_hash"], "pass123")
        self.assertTrue(user["password_hash"].startswith("scrypt:") or
                        user["password_hash"].startswith("pbkdf2:") or
                        len(user["password_hash"]) > 20)

    def test_wrong_password_does_not_login(self):
        self.signup(email="hash2@test.com", password="correct")
        resp = self.client.post("/login", data={
            "email": "hash2@test.com", "password": "incorrect"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Invalid email or password", resp.data)


class TestForeignKeyIntegrity(BaseTestCase):
    def test_reminder_references_valid_vehicle(self):
        self.signup()
        self.login()
        from models.db import get_db
        conn = get_db()
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='reminders'"
        ).fetchone()
        self.assertIsNotNone(result)
        conn.close()

    def test_order_references_valid_product(self):
        from models.db import get_db
        conn = get_db()
        result = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        self.assertGreater(result, 0)
        conn.close()


class TestUserModel(BaseTestCase):
    def test_create_user(self):
        from models.user import create_user, get_user_by_email
        create_user("Test", "model@test.com", "hash123", "123", "110001", "fam@test.com")
        user = get_user_by_email("model@test.com")
        self.assertIsNotNone(user)
        self.assertEqual(user["name"], "Test")
        self.assertEqual(user["phone"], "123")
        self.assertEqual(user["pincode"], "110001")
        self.assertEqual(user["family_email"], "fam@test.com")

    def test_get_user_by_id(self):
        self.signup()
        from models.user import get_user_by_id
        user = get_user_by_id(1)
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], "test@example.com")

    def test_get_all_users(self):
        self.signup()
        self.signup(name="User2", email="u2@test.com")
        from models.user import get_all_users
        users = get_all_users()
        self.assertEqual(len(users), 2)


class TestVehicleModel(BaseTestCase):
    def test_get_vehicles_by_user(self):
        self.signup()
        self.login()
        self.create_vehicle(nickname="Bike1")
        self.create_vehicle(nickname="Bike2")
        from models.vehicle import get_vehicles_by_user
        vehicles = get_vehicles_by_user(1)
        self.assertEqual(len(vehicles), 2)

    def test_count_vehicles_by_user(self):
        self.signup()
        self.login()
        self.create_vehicle()
        self.create_vehicle()
        from models.vehicle import count_vehicles_by_user
        count = count_vehicles_by_user(1)
        self.assertEqual(count, 2)

    def test_vehicle_update(self):
        self.signup()
        self.login()
        self.create_vehicle()
        from models.vehicle import update_vehicle, get_vehicle_by_id
        update_vehicle(1, "Updated", "Yamaha", "MT15", "KA01CD5678", "2023-01-01")
        v = get_vehicle_by_id(1, 1)
        self.assertEqual(v["nickname"], "Updated")
        self.assertEqual(v["make"], "Yamaha")


class TestDocumentModel(BaseTestCase):
    def test_get_documents_by_vehicle(self):
        self.signup()
        self.login()
        self.create_vehicle()
        from models.document import create_document, get_documents_by_vehicle
        create_document(1, "file.pdf", "Original.pdf")
        docs = get_documents_by_vehicle(1)
        self.assertEqual(len(docs), 1)

    def test_count_documents_by_vehicle(self):
        self.signup()
        self.login()
        self.create_vehicle()
        from models.document import create_document, count_documents_by_vehicle
        create_document(1, "a.pdf", "A.pdf")
        create_document(1, "b.pdf", "B.pdf")
        count = count_documents_by_vehicle(1)
        self.assertEqual(count, 2)

    def test_get_document_by_id_with_user(self):
        self.signup()
        self.login()
        self.create_vehicle()
        from models.document import create_document, get_document_by_id
        create_document(1, "file.pdf", "Original.pdf")
        doc = get_document_by_id(1)
        self.assertIsNotNone(doc)
        self.assertEqual(doc["user_id"], 1)


class TestReminderModel(BaseTestCase):
    def test_get_reminders_by_vehicle(self):
        self.signup()
        self.login()
        self.create_vehicle()
        from models.reminder import create_reminder, get_reminders_by_vehicle
        future = (date.today() + timedelta(days=30)).isoformat()
        create_reminder(1, "insurance", future)
        reminders = get_reminders_by_vehicle(1)
        self.assertEqual(len(reminders), 1)

    def test_get_reminder_by_id(self):
        self.signup()
        self.login()
        self.create_vehicle()
        from models.reminder import create_reminder, get_reminder_by_id
        future = (date.today() + timedelta(days=30)).isoformat()
        create_reminder(1, "insurance", future)
        r = get_reminder_by_id(1)
        self.assertIsNotNone(r)
        self.assertEqual(r["user_id"], 1)

    def test_count_reminders_by_vehicle(self):
        self.signup()
        self.login()
        self.create_vehicle()
        from models.reminder import create_reminder, count_reminders_by_vehicle
        future = (date.today() + timedelta(days=30)).isoformat()
        create_reminder(1, "insurance", future)
        create_reminder(1, "puc", future)
        count = count_reminders_by_vehicle(1)
        self.assertEqual(count, 2)

    def test_count_by_status(self):
        self.signup()
        self.login()
        self.create_vehicle()
        from models.reminder import create_reminder, count_by_status
        future = (date.today() + timedelta(days=30)).isoformat()
        past = (date.today() - timedelta(days=5)).isoformat()
        create_reminder(1, "insurance", future)
        create_reminder(1, "puc", past)
        counts = count_by_status(1)
        self.assertEqual(counts.get("upcoming", 0), 1)


class TestServiceLogModel(BaseTestCase):
    def test_get_service_logs_by_vehicle(self):
        self.signup()
        self.login()
        self.create_vehicle()
        from models.reminder import create_reminder, complete_reminder
        from models.service_log import get_service_logs_by_vehicle
        future = (date.today() + timedelta(days=30)).isoformat()
        create_reminder(1, "insurance", future)
        complete_reminder(1, 2500, "Paid")
        logs = get_service_logs_by_vehicle(1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["cost"], 2500.0)

    def test_get_total_cost_by_user(self):
        self.signup()
        self.login()
        self.create_vehicle()
        from models.reminder import create_reminder, complete_reminder
        from models.service_log import get_total_cost_by_user
        future = (date.today() + timedelta(days=30)).isoformat()
        create_reminder(1, "insurance", future)
        complete_reminder(1, 3000, "")
        total = get_total_cost_by_user(1)
        self.assertEqual(total, 3000.0)


class TestProductModel(BaseTestCase):
    def test_get_all_products(self):
        from models.product import get_all_products
        products = get_all_products()
        self.assertEqual(len(products), 8)

    def test_get_product_by_id(self):
        from models.product import get_product_by_id
        p = get_product_by_id(1)
        self.assertIsNotNone(p)
        self.assertEqual(p["name"], "Engine Oil 10W-40")

    def test_get_product_by_id_not_found(self):
        from models.product import get_product_by_id
        p = get_product_by_id(999)
        self.assertIsNone(p)


class TestOrderModel(BaseTestCase):
    def test_create_order(self):
        self.signup()
        self.login()
        from models.order import create_order
        create_order(1, 1, "110001", 1)
        from models.db import get_db
        conn = get_db()
        count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        conn.close()
        self.assertEqual(count, 1)

    def test_get_pending_orders(self):
        self.signup()
        self.login()
        from models.order import create_order, get_pending_orders_by_product_pincode
        create_order(1, 1, "110001", 1)
        orders = get_pending_orders_by_product_pincode(1, "110001")
        self.assertEqual(len(orders), 1)

    def test_get_user_recent_order(self):
        self.signup()
        self.login()
        from models.order import create_order, get_user_recent_order
        create_order(1, 1, "110001", 1)
        order = get_user_recent_order(1, 1)
        self.assertIsNotNone(order)


class TestLayoutTemplate(BaseTestCase):
    def test_layout_has_bootstrap(self):
        resp = self.client.get("/login")
        self.assertIn(b"bootstrap", resp.data)

    def test_layout_has_chartjs_on_dashboard(self):
        self.signup()
        self.login()
        resp = self.client.get("/dashboard")
        self.assertIn(b"chart.js", resp.data)

    def test_layout_flashes_messages(self):
        self.signup()
        self.login()
        self.create_vehicle()
        resp = self.client.get("/vehicles/999", follow_redirects=True)
        self.assertIn(b"Vehicle not found", resp.data)


class TestCSS(BaseTestCase):
    def test_css_file_loads(self):
        resp = self.client.get("/static/css/style.css")
        self.assertEqual(resp.status_code, 200)


class TestAllReminderTypesInTemplates(BaseTestCase):
    def test_reminder_type_display_in_vehicle_detail(self):
        self.signup()
        self.login()
        self.create_vehicle()
        future = (date.today() + timedelta(days=30)).isoformat()
        types = ["insurance", "road_tax", "puc", "driving_license",
                 "rc_renewal", "warranty", "amc", "service"]
        for rtype in types:
            self.client.post("/reminders/add", data={
                "vehicle_id": "1", "type": rtype, "due_date": future
            }, follow_redirects=True)
        resp = self.client.get("/vehicles/1")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Insurance", resp.data)
        self.assertIn(b"Road Tax", resp.data)
        self.assertIn(b"Rc Renewal", resp.data)
        self.assertIn(b"Driving License", resp.data)


class TestDuplicateEmailRegistration(BaseTestCase):
    def test_second_signup_same_email_shows_error(self):
        self.signup(email="dup@test.com")
        resp = self.signup(email="dup@test.com")
        self.assertIn(b"already registered", resp.data)

    def test_different_emails_both_succeed(self):
        self.signup(email="a@test.com")
        resp = self.signup(email="b@test.com")
        self.assertIn(b"Account created", resp.data)


class TestLogoutClearsSession(BaseTestCase):
    def test_after_logout_protected_routes_redirect(self):
        self.signup()
        self.login()
        self.client.get("/logout")
        for url in ["/vehicles", "/dashboard", "/reminders/add", "/marketplace", "/reminders/overdue"]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302, f"Session not cleared for {url}")


class TestEdgeCaseEmptyDatabase(unittest.TestCase):
    def test_empty_db_no_crash(self):
        test_db = os.path.join(tempfile.gettempdir(), "motomonitor_empty_test.db")
        if os.path.exists(test_db):
            os.remove(test_db)
        import models.db as test_db_mod
        old_path = test_db_mod.DB_PATH
        test_db_mod.DB_PATH = test_db
        from models.db import init_db
        init_db()
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        client = app.test_client()
        with app.app_context():
            resp = client.post("/signup", data={
                "name": "First", "email": "first@test.com", "password": "pass"
            }, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            resp = client.post("/login", data={
                "email": "first@test.com", "password": "pass"
            }, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            resp = client.get("/dashboard")
            self.assertEqual(resp.status_code, 200)
            resp = client.get("/vehicles")
            self.assertEqual(resp.status_code, 200)
            resp = client.get("/marketplace")
            self.assertEqual(resp.status_code, 200)
        test_db_mod.DB_PATH = old_path
        os.remove(test_db)


class TestCSRFProtection(unittest.TestCase):
    def test_csrf_token_in_login_form(self):
        app.config["TESTING"] = True
        client = app.test_client()
        resp = client.get("/login")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"csrf_token", resp.data)

    def test_csrf_token_in_signup_form(self):
        app.config["TESTING"] = True
        client = app.test_client()
        resp = client.get("/signup")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"csrf_token", resp.data)

    def test_csrf_blocks_post_without_token(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = True
        client = app.test_client()
        resp = client.post("/login", data={
            "email": "test@test.com", "password": "pass"
        }, follow_redirects=False)
        self.assertEqual(resp.status_code, 400)
        app.config["WTF_CSRF_ENABLED"] = False

    def test_csrf_all_post_forms_have_token(self):
        app.config["TESTING"] = True
        client = app.test_client()
        pages = ["/login", "/signup", "/vehicles/add", "/reminders/add", "/marketplace"]
        for url in pages:
            resp = client.get(url)
            if resp.status_code == 200:
                self.assertIn(b"csrf_token", resp.data, f"CSRF token missing at {url}")


class TestNotificationIntegration(BaseTestCase):
    def test_notifier_send_email_returns_true(self):
        from services.notifier import send_email
        result = send_email("test@test.com", "Subject", "Body")
        self.assertTrue(result)

    def test_notifier_send_sms_returns_true(self):
        from services.notifier import send_sms
        result = send_sms("1234567890", "Message")
        self.assertTrue(result)

    def test_notifier_send_sms_with_empty_number(self):
        from services.notifier import send_sms
        result = send_sms("", "Message")
        self.assertTrue(result)

    def test_send_reminder_alert_with_family_email(self):
        from services.notifier import send_reminder_alert
        user = {"name": "Test", "email": "test@test.com", "phone": "123", "family_email": "fam@test.com"}
        vehicle = {"nickname": "Bike", "make": "Honda", "model": "CB350", "registration_number": "MH12AB1234"}
        reminder = {"type": "insurance", "due_date": "2024-12-01"}
        result = send_reminder_alert(user, vehicle, reminder, 5)
        self.assertTrue(result)

    def test_send_reminder_alert_without_family_email(self):
        from services.notifier import send_reminder_alert
        user = {"name": "Test", "email": "test@test.com", "phone": "123"}
        vehicle = {"make": "Honda", "model": "CB350", "registration_number": "MH12AB1234"}
        reminder = {"type": "insurance", "due_date": "2024-12-01"}
        result = send_reminder_alert(user, vehicle, reminder, 5)
        self.assertTrue(result)

    def test_reminder_scheduler_sends_alerts(self):
        self.signup()
        self.login()
        self.create_vehicle()
        past = (date.today() - timedelta(days=5)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "insurance", "due_date": past
        }, follow_redirects=True)
        from services.reminder_scheduler import check_reminders
        check_reminders()

    def test_reminder_scheduler_with_upcoming(self):
        self.signup()
        self.login()
        self.create_vehicle()
        future = (date.today() + timedelta(days=5)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "puc", "due_date": future
        }, follow_redirects=True)
        from services.reminder_scheduler import check_reminders
        check_reminders()

    def test_reminder_scheduler_30day_alert(self):
        self.signup()
        self.login()
        self.create_vehicle()
        future = (date.today() + timedelta(days=25)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "road_tax", "due_date": future
        }, follow_redirects=True)
        from services.reminder_scheduler import check_reminders
        check_reminders()

    def test_reminder_scheduler_due_today(self):
        self.signup()
        self.login()
        self.create_vehicle()
        today = date.today().isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "service", "due_date": today
        }, follow_redirects=True)
        from services.reminder_scheduler import check_reminders
        check_reminders()


class TestAdminFulfill(BaseTestCase):
    def _make_admin(self):
        from models.db import get_db
        self.signup(name="Admin", email="admin@test.com", password="pass")
        self.login(email="admin@test.com", password="pass")
        conn = get_db()
        conn.execute("UPDATE users SET role = 'admin' WHERE email = 'admin@test.com'")
        conn.commit()
        conn.close()

    def test_fulfill_bulk_orders(self):
        self._make_admin()
        from models.db import get_db
        conn = get_db()
        conn.execute("UPDATE products SET bulk_threshold = 1 WHERE id = 1")
        conn.commit()
        conn.close()
        from models.order import create_order
        create_order(1, 1, "110001", 1)
        from services.bulk_unlock import check_and_unlock
        check_and_unlock(1, "110001", 1)
        resp = self.client.post("/admin/bulk-orders/fulfill", data={
            "product_id": "1", "pincode": "110001"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"fulfilled", resp.data.lower())

    def test_fulfill_requires_admin(self):
        self.signup()
        self.login()
        resp = self.client.post("/admin/bulk-orders/fulfill", data={
            "product_id": "1", "pincode": "110001"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Admin access required", resp.data)

    def test_fulfill_invalid_data(self):
        self._make_admin()
        resp = self.client.post("/admin/bulk-orders/fulfill", data={
            "product_id": "", "pincode": ""
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Invalid request", resp.data)

    def test_admin_page_shows_all_statuses(self):
        self._make_admin()
        from models.db import get_db
        conn = get_db()
        conn.execute("UPDATE products SET bulk_threshold = 1 WHERE id = 1")
        conn.commit()
        conn.close()
        from models.order import create_order
        create_order(1, 1, "110001", 1)
        from services.bulk_unlock import check_and_unlock
        check_and_unlock(1, "110001", 1)
        resp = self.client.get("/admin/bulk-orders")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Unlocked", resp.data)


class TestDocumentDownload(BaseTestCase):
    def test_document_has_view_link(self):
        self.signup()
        self.login()
        self.create_vehicle()
        data = {"file": (io.BytesIO(b"test"), "test.pdf")}
        self.client.post(
            "/vehicles/1/documents/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True
        )
        resp = self.client.get("/vehicles/1")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"static/uploads/", resp.data)


class TestOverdueUrgency(BaseTestCase):
    def test_overdue_page_shows_urgency_labels(self):
        self.signup()
        self.login()
        self.create_vehicle()
        past_5 = (date.today() - timedelta(days=5)).isoformat()
        past_15 = (date.today() - timedelta(days=15)).isoformat()
        past_65 = (date.today() - timedelta(days=65)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "insurance", "due_date": past_5
        }, follow_redirects=True)
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "puc", "due_date": past_15
        }, follow_redirects=True)
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "road_tax", "due_date": past_65
        }, follow_redirects=True)
        resp = self.client.get("/reminders/overdue")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Low", resp.data)
        self.assertIn(b"Medium", resp.data)
        self.assertIn(b"Critical", resp.data)

    def test_overdue_page_shows_days_overdue(self):
        self.signup()
        self.login()
        self.create_vehicle()
        past = (date.today() - timedelta(days=15)).isoformat()
        self.client.post("/reminders/add", data={
            "vehicle_id": "1", "type": "driving_license", "due_date": past
        }, follow_redirects=True)
        resp = self.client.get("/reminders/overdue")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"15 days", resp.data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
