import pandas as pd
import json
from datetime import datetime, timedelta
from services.database import get_connection

def process_csv_file(file, uploaded_by_id):
    """
    Process uploaded CSV file (pipe-delimited) and import inactive customers

    Filtering Logic:
    1. Only customers with deposits (HAS_DEPOSIT > 0 or TOTAL_DEPOSIT_AMOUNT > 0)
    2. Only inactive customers (30+ days since last deposit)
    3. Skip duplicates (CUSTOMER_CODE already exists)

    Expected format: CUSTOMER_ID|OPERATOR_CUSTOM_LABELS|FIRST_NAME|...

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
    skipped_no_deposit = 0
    skipped_active = 0
    skipped_duplicate = 0

    try:
        # Read CSV with pipe delimiter
        df = pd.read_csv(file, sep='|', encoding='utf-8')
        total_rows = len(df)

        # Required columns
        required_columns = [
            'FIRST_NAME', 'SURNAME', 'CUSTOMER_CODE', 'PHONE',
            'HAS_DEPOSIT', 'TOTAL_DEPOSIT_AMOUNT', 'LAST_DEPOSIT_TRANSACTION_DATE'
        ]

        # Check if required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Eksik kolonlar: {', '.join(missing_columns)}")

        # Calculate cutoff date (30 days ago)
        cutoff_date = datetime.now() - timedelta(days=30)

        for idx, row in df.iterrows():
            try:
                # Extract data
                first_name = str(row['FIRST_NAME']).strip() if pd.notna(row['FIRST_NAME']) else ''
                surname = str(row['SURNAME']).strip() if pd.notna(row['SURNAME']) else ''
                customer_code = str(row['CUSTOMER_CODE']).strip() if pd.notna(row['CUSTOMER_CODE']) else ''
                phone = str(row['PHONE']).strip() if pd.notna(row['PHONE']) else ''

                has_deposit = row.get('HAS_DEPOSIT', 0)
                total_deposit = row.get('TOTAL_DEPOSIT_AMOUNT', 0)
                last_deposit_date_str = row.get('LAST_DEPOSIT_TRANSACTION_DATE')

                # Validation: Basic fields
                if not all([first_name, surname, customer_code, phone]):
                    raise ValueError("Eksik alan (ad, soyad, kod veya telefon)")

                # FILTER 1: Must have made at least one deposit
                if has_deposit == 0 or total_deposit == 0:
                    skipped_no_deposit += 1
                    continue  # Skip customers with zero deposits

                # FILTER 2: Must be inactive (30+ days since last deposit)
                if pd.notna(last_deposit_date_str) and last_deposit_date_str:
                    try:
                        # Parse date (format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
                        last_deposit_date = pd.to_datetime(last_deposit_date_str)

                        # Check if customer is active (deposited within 30 days)
                        if last_deposit_date >= cutoff_date:
                            skipped_active += 1
                            continue  # Skip active customers
                    except:
                        # If date parsing fails, treat as inactive
                        pass

                # FILTER 3: Check for duplicates
                cursor.execute("SELECT id FROM customers WHERE user_code = ?", (customer_code,))
                if cursor.fetchone():
                    skipped_duplicate += 1
                    continue  # Skip duplicates

                # All filters passed - insert customer
                cursor.execute("""
                    INSERT INTO customers
                    (name, surname, user_code, phone_number, excel_upload_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (first_name, surname, customer_code, phone, upload_id))

                successful += 1

            except Exception as e:
                failed += 1
                error_log.append({
                    "row": idx + 2,
                    "error": str(e),
                    "customer_code": customer_code if 'customer_code' in locals() else 'N/A'
                })

        # Update upload record with detailed stats
        summary_text = f"Başarılı: {successful}, Başarısız: {failed}, " \
                      f"Atlandı (Sıfır Yatırım): {skipped_no_deposit}, " \
                      f"Atlandı (Aktif): {skipped_active}, " \
                      f"Atlandı (Duplicate): {skipped_duplicate}"

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
            'skipped_no_deposit': skipped_no_deposit,
            'skipped_active': skipped_active,
            'skipped_duplicate': skipped_duplicate,
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
