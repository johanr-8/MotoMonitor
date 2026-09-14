# MotoMonitor — Agent Context

## Project Overview
Vehicle management web app. Users can sign up, log in, manage their vehicles, track reminders (insurance, tax, PUC, etc.), upload documents, and buy accessories through a marketplace with bulk unlock pricing. Built for absolute beginners to learn web development. ~80% demo-ready for college mini-project submission.

## Tech Stack
- **Frontend:** HTML5, CSS3 (Bootstrap 5.3 CDN), Chart.js (CDN), minimal vanilla JS
- **Backend:** Python 3, Flask (Jinja2 templates)
- **Database:** SQLite (single file — database.db)
- **Auth:** Session-based, passwords hashed with Werkzeug
- **Security:** CSRF protection via Flask-WTF (CSRFProtect)
- **Notifications:** Real SMTP email via smtplib, SMS stubbed (Twilio-ready)
- **Architecture:** Blueprint-based modular Flask (models/, routes/, services/)

## Project Structure
`
motomonitor/
├── app.py                    # Entry point — wires Flask, CSRF, blueprints, DB init
├── config.py                 # DB, upload, SMTP, SMS config (env vars)
├── requirements.txt          # flask, werkzeug, flask-wtf
├── database.db               # Auto-created SQLite file (deleted on fresh run)
├── test_comprehensive.py     # 166 tests covering all features
├── models/
│   ├── db.py                 # SQLite connection, schema creation, product seeding
│   ├── user.py               # get_by_email, get_by_id, create, get_all
│   ├── vehicle.py            # CRUD + count_by_user
│   ├── reminder.py           # CRUD + overdue detection + count_by_status
│   ├── document.py           # CRUD + count
│   ├── service_log.py        # get logs + total cost + spend by category
│   ├── product.py            # get all, get by id
│   └── order.py              # create, pending by product/pincode, grouped, fulfill
├── routes/
│   ├── auth.py               # signup, login, logout + @login_required decorator
│   ├── vehicles.py           # CRUD + vehicle detail (documents, reminders, service log)
│   ├── reminders.py          # add, complete (with cost), overdue page
│   ├── documents.py          # upload (UUID prefix), delete
│   ├── dashboard.py          # summary cards + Chart.js charts
│   ├── marketplace.py        # product catalog + order placement
│   └── admin.py              # bulk order tracker + mark fulfilled (admin-only)
├── services/
│   ├── notifier.py           # Real SMTP email + SMS stub (Twilio-ready structure)
│   ├── reminder_scheduler.py # 30-day / 7-day / due-day / overdue escalation
│   └── bulk_unlock.py        # Threshold-based bulk order unlocking
├── templates/ (12 files)
│   ├── layout.html           # Base — navbar, flash messages, Bootstrap + Chart.js CDN
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html        # Summary cards + 2 Chart.js charts (bar + doughnut)
│   ├── vehicles.html         # Card layout (not table)
│   ├── vehicle_form.html     # Add/edit vehicle
│   ├── vehicle_detail.html   # Docs (with view/download) + reminders + service log
│   ├── reminder_form.html    # Add reminder (with "no vehicles" warning)
│   ├── complete_reminder.html # Cost + notes form
│   ├── overdue.html          # Color-coded urgency table (Low/Medium/High/Critical)
│   ├── marketplace.html      # Product cards + progress bars + order buttons
│   └── admin_bulk_orders.html # Grouped orders + mark fulfilled buttons
└── static/
    ├── css/style.css         # Minimal custom styles
    └── uploads/              # Uploaded document files (UUID-prefixed)
`

## Routes (18 total)
| Route | Method | Blueprint | Purpose |
|-------|--------|-----------|---------|
| / | GET | vehicles | Redirects to dashboard (logged in) or login |
| /signup | GET/POST | auth | User registration |
| /login | GET/POST | auth | User login (session clear + set) |
| /logout | GET | auth | Clear session |
| /dashboard | GET | dashboard | Summary cards + charts |
| /vehicles | GET | vehicles | List user's vehicles (card layout) |
| /vehicles/add | GET/POST | vehicles | Add vehicle form |
| /vehicles/<id> | GET | vehicles | Vehicle detail (docs + reminders + service log) |
| /vehicles/<id>/edit | GET/POST | vehicles | Edit vehicle |
| /vehicles/<id>/delete | POST | vehicles | Delete vehicle + cascade delete docs/files |
| /vehicles/<id>/documents/upload | POST | documents | Upload file (UUID prefix, type/size validation) |
| /documents/<id>/delete | POST | documents | Delete document + file from disk |
| /reminders/add | GET/POST | reminders | Add reminder form |
| /reminders/<id>/complete | GET/POST | reminders | Mark complete (creates service log entry) |
| /reminders/overdue | GET | reminders | Overdue tracker with days_overdue + color-coded urgency |
| /marketplace | GET | marketplace | Product catalog + bulk progress |
| /marketplace/order | POST | marketplace | Place order + auto bulk-unlock check |
| /admin/bulk-orders | GET | admin | Admin-only bulk order tracker |
| /admin/bulk-orders/fulfill | POST | admin | Admin-only mark bulk orders fulfilled |

All POST routes include CSRF tokens (Flask-WTF csrf_token()).

## Database Schema (7 tables)
`sql
users          (id, name, email, password_hash, phone, role, pincode, family_email, created_at)
vehicles       (id, user_id, nickname, make, model, registration_number, purchase_date)
documents      (id, vehicle_id, filename, original_name, uploaded_at)
reminders      (id, vehicle_id, type, due_date, status, last_alert_sent, notes)
service_log    (id, reminder_id, cost, notes, completed_at)
products       (id, name, category, retail_price, app_price, image_path, bulk_threshold)
orders         (id, user_id, product_id, pincode, quantity, status, created_at)
`

**Products are seeded on first run** (8 items: oil, brake pads, chain lube, air filter, spark plugs, tyres, helmet, gloves).

## Reminder Types
insurance, road_tax, puc, driving_license, rc_renewal, warranty, amc, service

## Reminder Status Flow
upcoming -> due_soon (day 0) -> overdue (past due) -> completed

## Overdue Urgency Levels
| Days Overdue | Badge | Color |
|-------------|-------|-------|
| 1-7 | Low | Info (blue) |
| 8-30 | Medium | Warning (yellow) |
| 31-60 | High | Danger (red) |
| 60+ | Critical | Danger (red) |

## Reminder Scheduler Logic (services/reminder_scheduler.py)
- 30 days before due: email alert -> sets last_alert_sent = '30day'
- 7 days before due: email + SMS -> sets last_alert_sent = '7day'
- Due day: email + SMS, status -> due_soon, sets last_alert_sent = 'due_day'
- Past due: status -> overdue
- Sends to user email, user phone, and family_email (if set)

**Note:** Scheduler runs on-demand via check_reminders(). To run daily, wire with APScheduler or system cron.

## Notification System (services/notifier.py)
- **Email:** Real SMTP sending via smtplib + MIMEMultipart. Configurable via env vars (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS). Falls back to console logging when SMTP_USER is empty.
- **SMS:** Stubbed with structured output. Code comments show exact Twilio integration pattern -- drop in TWILIO_SID + TWILIO_TOKEN to activate.
- **Family email CC:** Automatically CC's amily_email if set on user profile.

## CSRF Protection (Flask-WTF)
- CSRFProtect(app) initialized in pp.py
- Every POST form includes: <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
- Protected forms: login, signup, vehicle add/edit, vehicle delete, document upload/delete, reminder add, complete reminder, marketplace order, admin fulfill
- Tests use WTF_CSRF_ENABLED = False for general suite; dedicated TestCSRFProtection class verifies tokens are present and missing tokens return 400

## Bulk Unlock Logic (services/bulk_unlock.py)
1. User places order -> stored with status = 'pending', linked to pincode
2. check_and_unlock() counts pending orders for same product + pincode in last 7 days
3. If count >= product.bulk_threshold -> all matching orders -> status = 'bulk_unlocked'
4. User sees "Bulk unlocked! Confirmed at app_price"
5. Admin can mark fulfilled -> status changes to 'fulfilled'

**Order status flow:** pending -> ulk_unlocked -> ulfilled

## Admin Panel (routes/admin.py)
- GET /admin/bulk-orders -- Shows grouped orders by product/pincode with status badges
- POST /admin/bulk-orders/fulfill -- Marks bulk_unlocked orders as fulfilled
- Admin-only access: checks user.role == 'admin', non-admins redirected with flash message

## Document Upload Flow
- UUID-prefixed filenames prevent collisions ({uuid4hex}_{original_name})
- Allowed types: pdf, png, jpg, jpeg, gif, doc, docx, txt
- 10MB size limit
- View/download links on vehicle detail page (<a href="{{ url_for('static', filename='uploads/' + doc.filename) }}" target="_blank">)
- Delete removes both DB record and file from disk

## Config (via environment variables)
| Var | Default | Purpose |
|-----|---------|---------|
| SECRET_KEY | change-this-to-something-secret | Flask session signing |
| SMTP_HOST | smtp.gmail.com | Email server |
| SMTP_PORT | 587 | Email port |
| SMTP_USER | "" | Email username (empty = stub mode) |
| SMTP_PASS | "" | Email password |
| SMS_API_KEY | "" | SMS provider key (reserved for Twilio) |

## How to Run
`
cd motomonitor
pip install -r requirements.txt
python app.py
`
Open http://127.0.0.1:5000

## Testing
`ash
# Smoke test (166 tests):
Remove-Item database.db -Force -ErrorAction SilentlyContinue
python test_comprehensive.py
`

### Test Classes (166 tests total)
| Class | Tests | What it covers |
|-------|-------|----------------|
| TestHomePage | 2 | Root redirect logic |
| TestAuthSignup | 5 | Signup flow, validation, duplicate email |
| TestAuthLogin | 5 | Login flow, wrong password, missing fields |
| TestAuthLogout | 2 | Session clearing, redirect |
| TestSessionProtection | 9 | All protected routes require login |
| TestVehicleCRUD | 13 | Add, list, edit, delete, detail, missing fields |
| TestDocumentUploadDelete | 8 | Upload, delete, disk persistence, UUID naming |
| TestReminderFlow | 8 | Add, complete, all reminder types |
| TestOverdueReminders | 3 | Overdue detection, completed not shown, multiple |
| TestDashboard | 5 | Rendering, cards, charts, cost data |
| TestMarketplace | 7 | Products, order, duplicate prevention, progress bar |
| TestAdmin | 4 | Role enforcement, empty orders, back button |
| TestCrossUserAccess | 5 | Data isolation between users |
| TestInvalidIDs | 4 | 404 for non-numeric route params |
| TestSQLInjection | 3 | SQL injection in signup, login, vehicle routes |
| TestTemplateErrors | 3 | All templates render without Jinja errors |
| TestEdgeCases | 7 | Special chars, zero threshold, already completed |
| TestBulkUnlock | 2 | Threshold reached/not reached |
| TestServiceLog | 1 | Service log shows on vehicle detail |
| TestNavbar | 2 | Navbar content for logged in/out |
| TestCharts | 1 | Chart.js rendering on dashboard |
| TestReminderSchedulerService | 2 | check_reminders runs without error |
| TestNotifierService | 3 | Email/SMS stubs, reminder alert |
| TestBulkUnlockService | 2 | check_and_unlock below/above threshold |
| TestDatabaseInit | 2 | Tables created, products seeded |
| TestPasswordHashing | 2 | Password not plaintext, wrong password rejected |
| TestForeignKeyIntegrity | 2 | Tables and products exist |
| TestUserModel | 3 | CRUD operations on user model |
| TestVehicleModel | 3 | CRUD operations on vehicle model |
| TestDocumentModel | 3 | CRUD operations on document model |
| TestReminderModel | 4 | CRUD operations on reminder model |
| TestServiceLogModel | 2 | Service log queries |
| TestProductModel | 3 | Product queries |
| TestOrderModel | 3 | Order creation and queries |
| TestLayoutTemplate | 3 | Bootstrap, Chart.js, flash messages |
| TestCSS | 1 | CSS file loads |
| TestAllReminderTypesInTemplates | 1 | All 8 types display correctly |
| TestDuplicateEmailRegistration | 2 | Duplicate prevention |
| TestLogoutClearsSession | 1 | All protected routes redirect after logout |
| TestEdgeCaseEmptyDatabase | 1 | Fresh DB with no data |
| TestCSRFProtection | 4 | Tokens present, missing token returns 400 |
| TestNotificationIntegration | 7 | Real SMTP stub, SMS, family_email, scheduler |
| TestAdminFulfill | 4 | Fulfill orders, admin enforcement, invalid data |
| TestDocumentDownload | 1 | View links in vehicle detail |
| TestOverdueUrgency | 2 | Urgency labels, days overdue display |

## Bug Fixes Applied
### Original 12
1. **ZeroDivisionError** in marketplace -- guarded against ulk_threshold = 0
2. **sqlite3.Row .get() crash** in notifier -- changed to [] access
3. **KeyError on missing form fields** -- all routes use .get() + validation
4. **Stale count_by_status()** -- now calls update_overdue_reminders() first
5. **Vehicle delete orphans** -- cascading delete of docs + files
6. **Filename collision on uploads** -- UUID prefix prevents overwrites
7. **No file type validation** -- allowlist + 10MB size limit
8. **Broken days-overdue display** -- calculated in route, passed to template
9. **login_required was a function** -- converted to @login_required decorator
10. **No session reset after login** -- session.clear() prevents session fixation
11. **Confusing admin logic** -- simplified to single check + early return
12. **Empty vehicle list in reminder form** -- shows "Add a vehicle first" message

### This session
13. **KeyError on amily_email** in notifier -- changed to .get() for optional fields
14. **check_and_unlock test failure** -- test was not creating an order before checking threshold
15. **UUID-prefixed filenames vs test assertions** -- tests now check for filename suffix instead of exact match
16. **MIMEMultipart for emails** -- upgraded from plain MIMEText for proper email formatting

## What's NOT Built
- Real SMS sending (stubbed, Twilio integration point ready)
- Cron/scheduler integration (logic exists, needs APScheduler or system cron)
- REST API (only HTML pages, no JSON endpoints)
- ORM (raw SQL throughout)
- Database migrations (schema created on startup)
- Automated testing framework (test file exists but not pytest)
- Docker / CI/CD
- Role-based access beyond admin/owner

## What IS Built (this session)
- CSRF protection via Flask-WTF on all POST forms
- Real SMTP email notifications via smtplib (MIMEMultipart)
- Color-coded overdue urgency (Low/Medium/High/Critical)
- Document download/view links on vehicle detail page
- Admin mark-fulfilled action for bulk orders
- 166 tests (was 146) with CSRF, notifications, admin fulfill, downloads, urgency

## Future Ideas (discussed, not built)
- **Document parsing** -- upload PDF (insurance, RC), extract dates with pypdf, auto-create reminders
- **Twilio SMS** -- drop in TWILIO_SID + TWILIO_TOKEN env vars, uncomment integration in 
otifier.py
- **Scheduler** -- APScheduler or cron to run eminder_scheduler.py daily
- **REST API** -- JSON endpoints for mobile app integration
- **Payment integration** -- complete marketplace flow with actual payment processing
