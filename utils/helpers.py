# Utility functions
def format_phone_number(phone):
    """Format phone number for display"""
    phone = str(phone).strip()
    if len(phone) == 11 and phone.startswith('0'):
        return f"{phone[:4]} {phone[4:7]} {phone[7:]}"
    return phone

def validate_excel_columns(df):
    """Validate Excel file has required columns"""
    required_columns = ['Ad', 'Soyad', 'Kullanıcı Kodu', 'Telefon Numarası']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Eksik kolonlar: {', '.join(missing_columns)}")

    return True
