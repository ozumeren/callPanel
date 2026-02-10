import sqlite3
import threading
from datetime import datetime, timedelta
from services.database import get_connection, DB_PATH
from utils.config import RECALL_WAITING_DAYS, MAX_CALL_ATTEMPTS

# Global lock for concurrent access
_db_lock = threading.Lock()

def pull_customer_for_operator(operator_id):
    """
    Atomically pull next available customer from pool
    Thread-safe with explicit locking for SQLite

    PRIORITY LOGIC:
    1. First try to get customers previously handled by this operator
    2. If none, get from general pool (FIFO with priority)

    Returns: Customer dict or None
    """
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # STEP 1: Try to get customer previously handled by this operator
            # Only show customers where waiting period has passed OR never called before
            cursor.execute("""
                SELECT * FROM customers
                WHERE status = 'pending'
                  AND call_attempts < ?
                  AND last_operator_id = ?
                  AND (assigned_to IS NULL OR assigned_at < datetime('now', '-10 minutes'))
                  AND (available_after IS NULL OR available_after <= datetime('now'))
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            """, (MAX_CALL_ATTEMPTS, operator_id))

            customer = cursor.fetchone()

            # STEP 2: If no previous customer, get from general pool
            if not customer:
                cursor.execute("""
                    SELECT * FROM customers
                    WHERE status = 'pending'
                      AND call_attempts < ?
                      AND (assigned_to IS NULL OR assigned_at < datetime('now', '-10 minutes'))
                      AND (available_after IS NULL OR available_after <= datetime('now'))
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                """, (MAX_CALL_ATTEMPTS,))
                customer = cursor.fetchone()

            if customer:
                # Assign to operator
                cursor.execute("""
                    UPDATE customers
                    SET status = 'assigned',
                        assigned_to = ?,
                        assigned_at = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (operator_id, datetime.now(), datetime.now(), customer['id']))

                conn.commit()
                return dict(customer)

            return None

        finally:
            conn.close()


def return_customer_to_pool(customer_id, call_status, notes, operator_id):
    """
    Process call result and update customer status

    call_status: 'reached', 'no_answer', 'declined', 'busy'
    """
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            # Insert call log
            cursor.execute("""
                INSERT INTO call_logs (customer_id, operator_id, call_status, notes)
                VALUES (?, ?, ?, ?)
            """, (customer_id, operator_id, call_status, notes))

            # Get current customer info
            cursor.execute("SELECT call_attempts FROM customers WHERE id = ?", (customer_id,))
            current_attempts = cursor.fetchone()[0]
            new_attempts = current_attempts + 1

            # Determine new status
            if call_status == 'reached':
                new_status = 'completed'
                available_after = None  # Completed customers don't need this
            elif new_attempts >= MAX_CALL_ATTEMPTS:
                new_status = 'unreachable'
                available_after = None  # Unreachable customers won't be called again
            else:
                new_status = 'pending'
                # Set available_after based on configuration (default: 7 days)
                available_after = datetime.now() + timedelta(days=RECALL_WAITING_DAYS)

            # Update customer (save last_operator_id for continuity)
            cursor.execute("""
                UPDATE customers
                SET status = ?,
                    assigned_to = NULL,
                    call_attempts = ?,
                    last_call_status = ?,
                    last_called_at = ?,
                    last_operator_id = ?,
                    available_after = ?,
                    updated_at = ?
                WHERE id = ?
            """, (new_status, new_attempts, call_status, datetime.now(), operator_id, available_after, datetime.now(), customer_id))

            conn.commit()

        finally:
            conn.close()


def release_stale_assignments():
    """
    Release customers assigned for >10 minutes without update
    Run periodically or on-demand
    """
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE customers
                SET status = 'pending',
                    assigned_to = NULL,
                    updated_at = ?
                WHERE status = 'assigned'
                  AND assigned_at < datetime('now', '-10 minutes')
            """, (datetime.now(),))

            conn.commit()
            released_count = cursor.rowcount
            return released_count

        finally:
            conn.close()
