import pandas as pd
import json
from datetime import datetime
from services.database import get_connection
from utils.helpers import validate_excel_columns

def process_excel_file(file, uploaded_by_id):
    """
    Process uploaded Excel file and import customers

    Expected columns: Ad, Soyad, Kullanıcı Kodu, Telefon Numarası
    Returns: upload_id, summary dict
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Create upload record
    cursor.execute("""
        INSERT INTO excel_uploads (filename, uploaded_by, status)
        VALUES (?, ?, 'processing')
    """, (file.name, uploaded_by_id))
    upload_id = cursor.lastrowid
    conn.commit()

    error_log = []
    successful = 0
    failed = 0

    try:
        # Read Excel
        df = pd.read_excel(file)
        total_rows = len(df)

        # Validate columns
        validate_excel_columns(df)

        for idx, row in df.iterrows():
            try:
                name = str(row['Ad']).strip()
                surname = str(row['Soyad']).strip()
                user_code = str(row['Kullanıcı Kodu']).strip()
                phone_number = str(row['Telefon Numarası']).strip()

                # Validate
                if not all([name, surname, user_code, phone_number]) or name == 'nan' or surname == 'nan':
                    raise ValueError("Eksik alan")

                # Check duplicate
                cursor.execute("SELECT id FROM customers WHERE user_code = ?", (user_code,))
                if cursor.fetchone():
                    raise ValueError(f"Kullanıcı kodu zaten var: {user_code}")

                # Insert customer
                cursor.execute("""
                    INSERT INTO customers
                    (name, surname, user_code, phone_number, excel_upload_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, surname, user_code, phone_number, upload_id))

                successful += 1

            except Exception as e:
                failed += 1
                error_log.append({"row": idx + 2, "error": str(e)})

        # Update upload record
        cursor.execute("""
            UPDATE excel_uploads
            SET total_rows = ?,
                successful_imports = ?,
                failed_imports = ?,
                error_log = ?,
                status = 'completed',
                processed_at = ?
            WHERE id = ?
        """, (total_rows, successful, failed, json.dumps(error_log), datetime.now(), upload_id))

        conn.commit()

        return upload_id, {
            'total_rows': total_rows,
            'successful': successful,
            'failed': failed,
            'errors': error_log
        }

    except Exception as e:
        cursor.execute("""
            UPDATE excel_uploads
            SET status = 'failed',
                error_log = ?
            WHERE id = ?
        """, (json.dumps([{"error": str(e)}]), upload_id))
        conn.commit()
        raise

    finally:
        conn.close()
