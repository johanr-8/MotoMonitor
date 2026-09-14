SPEC.md is the exact build spec — follow it precisely. info.txt and the other docs are earlier brainstorm notes for context only; some ideas in them were later dropped, so if anything conflicts with SPEC.md, SPEC.md wins.

# MotoMonitor — Build Spec

This is the authoritative spec for what to build. Ignore any older/rejected ideas
mentioned in other files in this folder (React/Next.js frontend, FastAPI,
PostgreSQL, service-center booking, manufacturer recall system, chatbot — these
were discussed and explicitly dropped). Build only what's below.

## Tech Stack (fixed — do not substitute)
- Frontend: HTML5, CSS3, vanilla JavaScript (Chart.js via CDN for the dashboard)
- Backend: Python, Flask
- Database: MySQL
- Notifications: SMTP (email) + SMS (any simple provider/mock — e.g. Twilio test mode, or a stubbed function if no API key is available)
- Tools: Git, VS Code

## Folder Structure
```
motomonitor/
├── app.py                 # Flask entry point, route registration
├── config.py              # DB creds, SMTP/SMS config (use env vars)
├── models/
│   ├── db.py               # DB connection helper
│   ├── user.py
│   ├── vehicle.py
│   ├── reminder.py
│   ├── document.py
│   ├── service_log.py
│   ├── product.py
│   └── order.py
├── routes/
│   ├── auth.py
│   ├── vehicles.py
│   ├── reminders.py
│   ├── documents.py
│   ├── dashboard.py
│   └── marketplace.py
├── services/
│   ├── notifier.py          # email + SMS sending logic
│   ├── reminder_scheduler.py # daily job that checks due dates
│   └── bulk_unlock.py        # marketplace threshold logic
├── templates/                # Jinja2 HTML templates
├── static/
│   ├── css/
│   └── js/
└── requirements.txt
```

## Database Schema (MySQL)

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role ENUM('owner','admin') DEFAULT 'owner',
    pincode VARCHAR(10),
    family_email VARCHAR(150),   -- optional second email for shared alerts
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    nickname VARCHAR(100),        -- e.g. "My CB350"
    make VARCHAR(50),
    model VARCHAR(50),
    registration_number VARCHAR(30),
    purchase_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE reminders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NOT NULL,
    type ENUM('insurance','road_tax','puc','driving_license','rc_renewal',
              'warranty','amc','service') NOT NULL,
    due_date DATE NOT NULL,
    status ENUM('upcoming','due_soon','overdue','completed') DEFAULT 'upcoming',
    last_alert_sent ENUM('none','30day','7day','due_day') DEFAULT 'none',
    notes TEXT,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);

CREATE TABLE documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reminder_id INT NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reminder_id) REFERENCES reminders(id)
);

CREATE TABLE service_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reminder_id INT NOT NULL,
    cost DECIMAL(10,2),
    notes TEXT,
    completed_at DATE,
    FOREIGN KEY (reminder_id) REFERENCES reminders(id)
);

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(50),
    retail_price DECIMAL(10,2) NOT NULL,
    app_price DECIMAL(10,2) NOT NULL,
    image_path VARCHAR(255),
    bulk_threshold INT DEFAULT 5   -- orders needed in window to "unlock" bulk price
);

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    pincode VARCHAR(10),
    quantity INT DEFAULT 1,
    status ENUM('pending','bulk_unlocked','confirmed','cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

## Routes / Pages

| Route | Purpose |
|---|---|
| `/signup`, `/login`, `/logout` | Auth (email + password, session-based) |
| `/dashboard` | Overview: upcoming renewals timeline, spend-by-category chart, overdue count |
| `/vehicles` | List user's vehicles, add/edit/delete |
| `/vehicles/<id>` | Vehicle detail — its reminders, documents, service log |
| `/reminders/add` | Add a reminder (type + due date) for a vehicle |
| `/reminders/<id>/complete` | Mark done → prompts cost + notes → writes to service_log |
| `/reminders/overdue` | Overdue tracker view, sorted by most overdue first |
| `/documents/upload` | Upload a file, linked to a reminder |
| `/marketplace` | Product catalog — shows retail_price, app_price, "you save ₹X", and live bulk progress (e.g. "3/5 needed to unlock in your area") |
| `/marketplace/order` | Place an order (adds to `orders`, pincode-matched) |
| `/admin/bulk-orders` | Admin-only: view aggregated pending orders per product per pincode, mark as procured |

## Core Logic

### Reminder Scheduler (`services/reminder_scheduler.py`)
Run daily (cron or APScheduler inside Flask):
1. For every reminder with `status != completed`:
   - If `due_date - today == 30` and `last_alert_sent == 'none'` → send email, set `last_alert_sent = '30day'`
   - If `due_date - today == 7` and `last_alert_sent in ('none','30day')` → send email + SMS, set `last_alert_sent = '7day'`
   - If `due_date - today == 0` → send email + SMS, set `last_alert_sent = 'due_day'`, `status = 'due_soon'`
   - If `due_date < today` → `status = 'overdue'`
2. Once a week (e.g. Monday), send each user a digest email listing every reminder due in the next 30 days across all their vehicles.

### Bulk Unlock Logic (`services/bulk_unlock.py`)
1. When an order is placed, count `orders` for that `product_id` + `pincode` with `status = 'pending'` created within the last 7 days.
2. If count >= `product.bulk_threshold` → update all matching orders to `status = 'bulk_unlocked'`, notify those users their order is confirmed at app_price.
3. Admin view (`/admin/bulk-orders`) lists pending clusters approaching threshold so "procurement" can be simulated (just a status update, no real supplier integration needed).

### Family Sharing
If `users.family_email` is set, every notification sent to the primary user is CC'd (or BCC'd) to that address too. No separate login needed for the family member — keeps it simple.

## Out of Scope (do not build)
- Service-center accounts, booking, or ratings
- Manufacturer accounts, recalls, or advisories
- Real payment gateway integration (stub the checkout — just record the order)
- Chatbot/FAQ assistant
- React/Next.js, FastAPI, or PostgreSQL — stick to Flask + MySQL + vanilla JS

## MVP Build Order (suggested)
1. Auth + vehicles CRUD
2. Reminders CRUD + overdue tracker (no alerts yet, just DB state)
3. Email/SMS sending (`services/notifier.py`) + scheduler wired in
4. Document upload
5. Dashboard charts
6. Marketplace catalog + order placement
7. Bulk unlock logic + admin view
8. Weekly digest email
