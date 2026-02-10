import sqlite3
import os
from datetime import datetime

DB_PATH = 'data/call_panel.db'

def init_database():
    """Initialize database with schema and seed data"""
    os.makedirs('data', exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'operator')),
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            surname TEXT NOT NULL,
            user_code TEXT UNIQUE NOT NULL,
            phone_number TEXT NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'assigned', 'completed', 'unreachable', 'invalid_phone')),
            assigned_to INTEGER,
            assigned_at TIMESTAMP,
            call_attempts INTEGER DEFAULT 0,
            last_call_status TEXT,
            last_called_at TIMESTAMP,
            last_operator_id INTEGER,
            available_after TIMESTAMP,
            priority INTEGER DEFAULT 3,
            excel_upload_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assigned_to) REFERENCES users(id),
            FOREIGN KEY (last_operator_id) REFERENCES users(id),
            FOREIGN KEY (excel_upload_id) REFERENCES excel_uploads(id)
        )
    """)

    # Create call_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS call_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            operator_id INTEGER NOT NULL,
            call_status TEXT NOT NULL CHECK(call_status IN ('reached', 'no_answer', 'declined', 'busy')),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (operator_id) REFERENCES users(id)
        )
    """)

    # Create excel_uploads table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS excel_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            uploaded_by INTEGER NOT NULL,
            total_rows INTEGER,
            successful_imports INTEGER DEFAULT 0,
            failed_imports INTEGER DEFAULT 0,
            error_log TEXT,
            status TEXT DEFAULT 'processing' CHECK(status IN ('processing', 'completed', 'failed')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            FOREIGN KEY (uploaded_by) REFERENCES users(id)
        )
    """)

    # Create reactivations table (customers who went from inactive to active)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reactivations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            excel_upload_id INTEGER NOT NULL,
            customer_code TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            customer_surname TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            old_last_deposit_date TEXT,
            new_last_deposit_date TEXT,
            was_called INTEGER DEFAULT 0,
            total_calls INTEGER DEFAULT 0,
            last_call_status TEXT,
            last_call_notes TEXT,
            operator_id INTEGER,
            operator_name TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (excel_upload_id) REFERENCES excel_uploads(id),
            FOREIGN KEY (operator_id) REFERENCES users(id)
        )
    """)

    # Migration: Add last_operator_id column if it doesn't exist
    cursor.execute("PRAGMA table_info(customers)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'last_operator_id' not in columns:
        cursor.execute("ALTER TABLE customers ADD COLUMN last_operator_id INTEGER REFERENCES users(id)")
        conn.commit()

    # Migration: Add available_after column if it doesn't exist
    cursor.execute("PRAGMA table_info(customers)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'available_after' not in columns:
        cursor.execute("ALTER TABLE customers ADD COLUMN available_after TIMESTAMP")
        conn.commit()

    # Migration: Add last_deposit_date column if it doesn't exist (for CSV imports)
    cursor.execute("PRAGMA table_info(customers)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'last_deposit_date' not in columns:
        cursor.execute("ALTER TABLE customers ADD COLUMN last_deposit_date TEXT")
        conn.commit()

    # Migration: Add site column if it doesn't exist (truva or venus)
    cursor.execute("PRAGMA table_info(customers)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'site' not in columns:
        cursor.execute("ALTER TABLE customers ADD COLUMN site TEXT")
        conn.commit()

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_pooling ON customers(status, priority DESC, created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_user_code ON customers(user_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_assigned_to ON customers(assigned_to)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_last_operator ON customers(last_operator_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_available_after ON customers(available_after)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_logs_customer ON call_logs(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_logs_operator ON call_logs(operator_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_logs_created ON call_logs(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_excel_uploads_user ON excel_uploads(uploaded_by)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reactivations_customer ON reactivations(customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reactivations_upload ON reactivations(excel_upload_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reactivations_operator ON reactivations(operator_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reactivations_detected ON reactivations(detected_at)")

    # Seed admin user if not exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    if cursor.fetchone()[0] == 0:
        from bcrypt import hashpw, gensalt
        password_hash = hashpw('admin123'.encode(), gensalt()).decode()
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, full_name, role)
            VALUES ('admin', 'admin@callpanel.com', ?, 'Sistem Yöneticisi', 'admin')
        """, (password_hash,))

    conn.commit()
    conn.close()

def get_connection():
    """Get SQLite connection with row factory"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
