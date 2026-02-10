from services.database import get_connection
from bcrypt import checkpw, hashpw, gensalt

def authenticate_user(username, password):
    """
    Authenticate user and return user data
    Returns: user dict or None
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM users
        WHERE username = ? AND is_active = 1
    """, (username,))

    user = cursor.fetchone()
    conn.close()

    if user and checkpw(password.encode(), user['password_hash'].encode()):
        return dict(user)

    return None

def create_operator(username, email, password, full_name):
    """Create new operator user"""
    conn = get_connection()
    cursor = conn.cursor()

    password_hash = hashpw(password.encode(), gensalt()).decode()

    cursor.execute("""
        INSERT INTO users (username, email, password_hash, full_name, role)
        VALUES (?, ?, ?, ?, 'operator')
    """, (username, email, password_hash, full_name))

    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return user_id
