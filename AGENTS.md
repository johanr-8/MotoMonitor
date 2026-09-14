# MotoMonitor — Agent Context

## Project Overview
Vehicle management web app. Users can sign up, log in, manage their vehicles, track reminders (insurance, tax, PUC, etc.), upload documents, and buy accessories through a marketplace with bulk unlock pricing. Built for absolute beginners to learn web development.

## Tech Stack
- **Frontend:** HTML5, CSS3 (Bootstrap 5.3 CDN), Chart.js (CDN), minimal vanilla JS
- **Backend:** Python 3, Flask (Jinja2 templates)
- **Database:** SQLite (single file — `database.db`)
- **Auth:** Session-based, passwords hashed with Werkzeug
- **Architecture:** Blueprint-based modular Flask (models/, routes/, services/)

## Project Structure
```
motomonitor/
├── app.py                    # Entry point — 17 lines, just wires everything together
├── config.py                 # DB, upload, SMTP, SMS config (env vars)
├── requirements.txt          # flask, werkzeug
├── database.db               # Auto-created SQLite file (deleted on fresh run)
├── models/
│   ├── db.py                 # SQLite connection, schema creation, product seeding
│   ├── user.py               # get_by_email, get_by_id, create, get_all
│   ├── vehicle.py            # CRUD + count_by_user
│   ├── reminder.py           # CRUD + overdue detection + count_by_status
│   ├── document.py           # CRUD + count
│   ├── service_log.py        # get logs + total cost + spend by category
│   ├── product.py            # get all, get by id
│   └── order.py              # create, pending by product/pincode, grouped for admin
├── routes/
│   ├── auth.py               # signup, login, logout + @login_required decorator
│   ├── vehicles.py           # CRUD + vehicle detail (documents, reminders, service log)
│   ├── reminders.py          # add, complete (with cost), overdue page
│   ├── documents.py          # upload (UUID prefix), delete
│   ├── dashboard.py          # summary cards + Chart.js charts
│   ├── marketplace.py        # product catalog + order placement
│   └── admin.py              # bulk order tracker (admin-only)
├── services/
│   ├── notifier.py           # Email (SMTP) + SMS stubs, family_email CC
│   ├── reminder_scheduler.py # 30-day / 7-day / due-day / overdue escalation
│   └── bulk_unlock.py        # Threshold-based bulk order unlocking
├── templates/ (12 files)
│   ├── layout.html           # Base — navbar, flash messages, Bootstrap + Chart.js CDN
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html        # Summary cards + 2 Chart.js charts (bar + doughnut)
│   ├── vehicles.html         # Card layout (not table)
│   ├── vehicle_form.html     # Add/edit vehicle
│   ├── vehicle_detail.html   # Docs + reminders + service log sections
│   ├── reminder_form.html    # Add reminder (with "no vehicles" warning)
│   ├── complete_reminder.html # Cost + notes form
│   ├── overdue.html          # Table with days_overdue calculated in route
│   ├── marketplace.html      # Product cards + progress bars + order buttons
│   └── admin_bulk_orders.html # Grouped pending orders table
└── static/
    ├── css/style.css         # Minimal custom styles
    └── uploads/              # Uploaded document files (UUID-prefixed)
```

## Routes (17 total)
| Route | Method | Blueprint | Purpose |
|-------|--------|-----------|---------|
| `/` | GET | vehicles | Redirects to dashboard (logged in) or login |
| `/signup` | GET/POST | auth | User registration |
| `/login` | GET/POST | auth | User login (session clear + set) |
| `/logout` | GET | auth | Clear session |
| `/dashboard` | GET | dashboard | Summary cards + charts |
| `/vehicles` | GET | vehicles | List user's vehicles (card layout) |
| `/vehicles/add` | GET/POST | vehicles | Add vehicle form |
| `/vehicles/<id>` | GET | vehicles | Vehicle detail (docs + reminders + service log) |
| `/vehicles/<id>/edit` | GET/POST | vehicles | Edit vehicle |
| `/vehicles/<id>/delete` | POST | vehicles | Delete vehicle + cascade delete docs/files |
| `/vehicles/<id>/documents/upload` | POST | documents | Upload file (UUID prefix, type/size validation) |
| `/documents/<id>/delete` | POST | documents | Delete document + file from disk |
| `/reminders/add` | GET/POST | reminders | Add reminder form |
| `/reminders/<id>/complete` | GET/POST | reminders | Mark complete (creates service log entry) |
| `/reminders/overdue` | GET | reminders | Overdue tracker with days_overdue |
| `/marketplace` | GET | marketplace | Product catalog + bulk progress |
| `/marketplace/order` | POST | marketplace | Place order + auto bulk-unlock check |
| `/admin/bulk-orders` | GET | admin | Admin-only bulk order tracker |

## Database Schema (7 tables)
```sql
users          (id, name, email, password_hash, phone, role, pincode, family_email, created_at)
vehicles       (id, user_id, nickname, make, model, registration_number, purchase_date)
documents      (id, vehicle_id, filename, original_name, uploaded_at)
reminders      (id, vehicle_id, type, due_date, status, last_alert_sent, notes)
service_log    (id, reminder_id, cost, notes, completed_at)
products       (id, name, category, retail_price, app_price, image_path, bulk_threshold)
orders         (id, user_id, product_id, pincode, quantity, status, created_at)
```

**Products are seeded on first run** (8 items: oil, brake pads, chain lube, air filter, spark plugs, tyres, helmet, gloves).

## Reminder Types
insurance, road_tax, puc, driving_license, rc_renewal, warranty, amc, service

## Reminder Status Flow
`upcoming` → `due_soon` (day 0) → `overdue` (past due) → `completed`

## Reminder Scheduler Logic (services/reminder_scheduler.py)
- Runs daily (needs cron or APScheduler — not wired yet)
- 30 days before due: email alert → sets `last_alert_sent = '30day'`
- 7 days before due: email + SMS → sets `last_alert_sent = '7day'`
- Due day: email + SMS, status → `due_soon`, sets `last_alert_sent = 'due_day'`
- Past due: status → `overdue`
- Sends to user email, user phone, and family_email (if set)

## Bulk Unlock Logic (services/bulk_unlock.py)
1. User places order → stored with `status = 'pending'`, linked to pincode
2. `check_and_unlock()` counts pending orders for same product + pincode in last 7 days
3. If count >= `product.bulk_threshold` → all matching orders → `status = 'bulk_unlocked'`
4. User sees "Bulk unlocked! Confirmed at app_price"

## Config (via environment variables)
| Var | Default | Purpose |
|-----|---------|---------|
| `SECRET_KEY` | `change-this-to-something-secret` | Flask session signing |
| `SMTP_HOST` | `smtp.gmail.com` | Email server |
| `SMTP_PORT` | `587` | Email port |
| `SMTP_USER` | `""` | Email username |
| `SMTP_PASS` | `""` | Email password |
| `SMS_API_KEY` | `""` | SMS provider key |

## How to Run
```
cd motomonitor
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Testing
```bash
# Smoke test (all 40 tests):
Remove-Item database.db -Force -ErrorAction SilentlyContinue
python test_full.py
```
The test file (`test_full.py`) exercises:
- Auth flow (signup, login, logout, duplicate email, missing fields)
- Dashboard rendering
- Vehicle CRUD (add, list, edit, delete, invalid ID)
- Document upload (valid, disallowed type, duplicate filename, delete)
- Reminder add, complete, overdue detection
- Marketplace (view, place order, duplicate order prevention)
- Admin access control (non-admin blocked)
- Session protection on all protected routes
- Cross-user data isolation

## Bug Fixes Applied (this session)
1. **ZeroDivisionError** in marketplace — guarded against `bulk_threshold = 0`
2. **`sqlite3.Row` `.get()` crash** in notifier — changed to `[]` access
3. **`KeyError` on missing form fields** — all routes use `.get()` + validation
4. **Stale `count_by_status()`** — now calls `update_overdue_reminders()` first
5. **Vehicle delete orphans** — cascading delete of docs + files
6. **Filename collision on uploads** — UUID prefix prevents overwrites
7. **No file type validation** — allowlist + 10MB size limit
8. **Broken days-overdue display** — calculated in route, passed to template
9. **`login_required` was a function** — converted to `@login_required` decorator
10. **No session reset after login** — `session.clear()` prevents session fixation
11. **Confusing admin logic** — simplified to single check + early return
12. **Empty vehicle list in reminder form** — shows "Add a vehicle first" message

## What's NOT Built
- CSRF protection (needs Flask-WTF)
- Real email sending (stubbed, needs SMTP credentials)
- Real SMS sending (stubbed, needs Twilio or similar)
- Cron/scheduler integration (logic exists, needs APScheduler or system cron)
- REST API (only HTML pages, no JSON endpoints)
- ORM (raw SQL throughout)
- Database migrations (schema created on startup)
- Automated testing framework (test file exists but not pytest)
- Docker / CI/CD
- Role-based access beyond admin/owner

## Future Ideas (discussed, not built)
- **Document parsing** — upload PDF (insurance, RC), extract dates with `pypdf`, auto-create reminders
- **Real notifications** — wire SMTP + Twilio to `notifier.py`
- **Scheduler** — APScheduler or cron to run `reminder_scheduler.py` daily
- **CSRF** — add Flask-WTF for form tokens
- **REST API** — JSON endpoints for mobile app integration
