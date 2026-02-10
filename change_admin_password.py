#!/usr/bin/env python3
"""
Script to change admin username and password
Usage: python change_admin_password.py
"""

import sqlite3
from bcrypt import hashpw, gensalt

# Database path
DB_PATH = 'data/call_panel.db'

# NEW credentials (change these)
NEW_USERNAME = 'admin'  # Change this to your desired username
NEW_PASSWORD = 'admin123'  # Change this to your desired password

def change_admin_credentials():
    """Update admin username and password"""

    # Hash the new password
    password_hash = hashpw(NEW_PASSWORD.encode(), gensalt()).decode()

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Find current admin
        cursor.execute("SELECT id, username FROM users WHERE role = 'admin' LIMIT 1")
        admin = cursor.fetchone()

        if not admin:
            print("❌ Admin user not found!")
            return

        admin_id = admin[0]
        old_username = admin[1]

        print(f"Current admin username: {old_username}")
        print(f"New admin username: {NEW_USERNAME}")
        print(f"New admin password: {NEW_PASSWORD}")
        print()

        # Update credentials
        cursor.execute("""
            UPDATE users
            SET username = ?,
                password_hash = ?
            WHERE id = ?
        """, (NEW_USERNAME, password_hash, admin_id))

        conn.commit()

        print("✅ Admin credentials updated successfully!")
        print()
        print("You can now login with:")
        print(f"  Username: {NEW_USERNAME}")
        print(f"  Password: {NEW_PASSWORD}")

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()

    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 50)
    print("Admin Credentials Changer")
    print("=" * 50)
    print()

    response = input("Are you sure you want to change admin credentials? (yes/no): ")

    if response.lower() == 'yes':
        change_admin_credentials()
    else:
        print("Operation cancelled.")
