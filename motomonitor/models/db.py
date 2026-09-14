import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            phone TEXT,
            role TEXT DEFAULT 'owner',
            pincode TEXT,
            family_email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            nickname TEXT,
            make TEXT,
            model TEXT,
            registration_number TEXT,
            purchase_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT DEFAULT 'upcoming',
            last_alert_sent TEXT DEFAULT 'none',
            notes TEXT,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS service_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reminder_id INTEGER NOT NULL,
            cost REAL,
            notes TEXT,
            completed_at TEXT,
            FOREIGN KEY (reminder_id) REFERENCES reminders(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            retail_price REAL NOT NULL,
            app_price REAL NOT NULL,
            image_path TEXT,
            bulk_threshold INTEGER DEFAULT 5
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            pincode TEXT,
            quantity INTEGER DEFAULT 1,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # Seed products if empty
    count = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        products = [
            ("Engine Oil 10W-40", "Lubricants", 650.00, 499.00, "oil.png", 5),
            ("Brake Pads (Front)", "Brakes", 1200.00, 899.00, "brake_pads.png", 5),
            ("Chain Lubricant", "Accessories", 350.00, 249.00, "chain_lube.png", 10),
            ("Air Filter", "Filters", 800.00, 599.00, "air_filter.png", 5),
            ("Spark Plug Set", "Ignition", 450.00, 349.00, "spark_plug.png", 8),
            ("Tyre (Front 100/80-17)", "Tyres", 3500.00, 2799.00, "tyre.png", 3),
            ("Helmet - Full Face", "Safety", 4500.00, 3499.00, "helmet.png", 3),
            ("Riding Gloves", "Safety", 1800.00, 1299.00, "gloves.png", 5),
        ]
        c.executemany(
            "INSERT INTO products (name, category, retail_price, app_price, image_path, bulk_threshold) VALUES (?, ?, ?, ?, ?, ?)",
            products,
        )

    conn.commit()
    conn.close()
