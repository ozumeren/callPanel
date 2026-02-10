import sqlite3
import threading
from datetime import datetime, timedelta
from services.database import get_connection, DB_PATH
from utils.config import RECALL_WAITING_DAYS, MAX_CALL_ATTEMPTS, COOLDOWN_DAYS

# Global lock for concurrent access
_db_lock = threading.Lock()

def pull_customer_for_operator(operator_id):
    """
    Atomically pull next available customer from pool
    Thread-safe with explicit locking for SQLite

    PRIORITY LOGIC:
    1. First try to get customers previously handled by this operator (PRIMARY POOL)
    2. If none, get from general PRIMARY pool (is_reserve = 0)
    3. If PRIMARY pool is empty, try RESERVE pool (is_reserve = 1)
       - Reserve: total_deposit < 100k TRY AND inactive 180+ days

    Returns: Customer dict or None
    """
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # STEP 1: Try to get customer previously handled by this operator (PRIMARY POOL ONLY)
            # Only show customers where waiting period has passed OR never called before
            # Note: Customers with call_attempts >= MAX_CALL_ATTEMPTS are included IF cooldown period passed
            cursor.execute("""
                SELECT * FROM customers
                WHERE status = 'pending'
                  AND last_operator_id = ?
                  AND is_reserve = 0
                  AND (assigned_to IS NULL OR assigned_at < datetime('now', '-10 minutes'))
                  AND (available_after IS NULL OR available_after <= datetime('now'))
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            """, (operator_id,))

            customer = cursor.fetchone()

            # STEP 2: If no previous customer, get from general PRIMARY pool
            if not customer:
                cursor.execute("""
                    SELECT * FROM customers
                    WHERE status = 'pending'
                      AND is_reserve = 0
                      AND (assigned_to IS NULL OR assigned_at < datetime('now', '-10 minutes'))
                      AND (available_after IS NULL OR available_after <= datetime('now'))
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                """)
                customer = cursor.fetchone()

            # STEP 3: If PRIMARY pool is empty, try RESERVE pool
            if not customer:
                cursor.execute("""
                    SELECT * FROM customers
                    WHERE status = 'pending'
                      AND is_reserve = 1
                      AND (assigned_to IS NULL OR assigned_at < datetime('now', '-10 minutes'))
                      AND (available_after IS NULL OR available_after <= datetime('now'))
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                """)
                customer = cursor.fetchone()

            if customer:
                # Check if customer completed cooldown period (call_attempts >= 3 and available_after passed)
                reset_attempts = False
                if customer['call_attempts'] >= MAX_CALL_ATTEMPTS:
                    # Customer completed cooldown - reset attempts
                    reset_attempts = True

                # Assign to operator
                if reset_attempts:
                    cursor.execute("""
                        UPDATE customers
                        SET status = 'assigned',
                            assigned_to = ?,
                            assigned_at = ?,
                            call_attempts = 0,
                            updated_at = ?
                        WHERE id = ?
                    """, (operator_id, datetime.now(), datetime.now(), customer['id']))
                else:
                    cursor.execute("""
                        UPDATE customers
                        SET status = 'assigned',
                            assigned_to = ?,
                            assigned_at = ?,
                            updated_at = ?
                        WHERE id = ?
                    """, (operator_id, datetime.now(), datetime.now(), customer['id']))

                conn.commit()

                # Fetch updated customer data
                cursor.execute("SELECT * FROM customers WHERE id = ?", (customer['id'],))
                updated_customer = cursor.fetchone()
                return dict(updated_customer) if updated_customer else dict(customer)

            return None

        finally:
            conn.close()


def return_customer_to_pool(customer_id, call_status, notes, operator_id):
    """
    Process call result and update customer status

    call_status: 'reached', 'no_answer', 'declined', 'busy', 'invalid_phone'
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

            # Determine new status and assigned_to
            if call_status == 'reached':
                new_status = 'completed'
                available_after = None  # Completed customers don't need this
                new_assigned_to = operator_id  # KEEP operator assignment for reached customers
            elif call_status == 'invalid_phone':
                new_status = 'invalid_phone'
                available_after = None  # Don't call until phone updated
                new_assigned_to = None  # Release assignment
            elif new_attempts >= MAX_CALL_ATTEMPTS:
                # After max attempts, enter cooldown period (14 days)
                new_status = 'pending'  # Keep in pool but unavailable
                available_after = datetime.now() + timedelta(days=COOLDOWN_DAYS)
                new_assigned_to = None  # Release assignment
            else:
                new_status = 'pending'
                # Set available_after based on configuration (default: 7 days)
                available_after = datetime.now() + timedelta(days=RECALL_WAITING_DAYS)
                new_assigned_to = None  # Release assignment (back to pool)

            # Update customer (save last_operator_id for continuity)
            cursor.execute("""
                UPDATE customers
                SET status = ?,
                    assigned_to = ?,
                    call_attempts = ?,
                    last_call_status = ?,
                    last_called_at = ?,
                    last_operator_id = ?,
                    available_after = ?,
                    updated_at = ?
                WHERE id = ?
            """, (new_status, new_assigned_to, new_attempts, call_status, datetime.now(), operator_id, available_after, datetime.now(), customer_id))

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
