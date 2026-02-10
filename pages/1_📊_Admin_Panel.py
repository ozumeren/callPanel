import streamlit as st
import pandas as pd
from services.excel_service import process_excel_file
from services.csv_service import process_csv_file
from services.auth_service import create_operator
from services.database import get_connection
from services.pool_service import release_stale_assignments
from utils.constants import CUSTOMER_STATUS_LABELS

st.set_page_config(page_title="Admin Paneli", page_icon="📊", layout="wide")

# Check authentication
if 'user' not in st.session_state:
    st.error("Lütfen giriş yapın")
    st.switch_page("Home.py")

user = st.session_state.user

if user['role'] != 'admin':
    st.error("Bu sayfaya erişim yetkiniz yok")
    st.stop()

# Sidebar
st.sidebar.title(f"👤 {user['full_name']}")
st.sidebar.write(f"**Rol:** Admin")
if st.sidebar.button("🚪 Çıkış Yap"):
    del st.session_state.user
    st.switch_page("Home.py")

st.title("📊 Admin Paneli")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📈 Dashboard", "📤 Dosya Yükle", "📋 Müşteri Listesi", "👥 Operatör Yönetimi"])

# Tab 1: Dashboard
with tab1:
    st.subheader("📊 Genel İstatistikler")

    # Release stale assignments button
    if st.button("🔄 Takılı Müşterileri Serbest Bırak (10dk+ atanmış)"):
        released = release_stale_assignments()
        st.success(f"{released} müşteri havuza geri döndürüldü")

    conn = get_connection()
    cursor = conn.cursor()

    # Customer statistics
    cursor.execute("SELECT COUNT(*) FROM customers")
    total_customers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM customers WHERE status = 'pending'")
    pending_customers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM customers WHERE status = 'completed'")
    completed_customers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM customers WHERE status = 'unreachable'")
    unreachable_customers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM customers WHERE status = 'assigned'")
    assigned_customers = cursor.fetchone()[0]

    # Today's calls
    cursor.execute("SELECT COUNT(*) FROM call_logs WHERE DATE(created_at) = DATE('now')")
    today_calls = cursor.fetchone()[0]

    conn.close()

    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Müşteri", total_customers)
    col2.metric("Havuzda Bekleyen", pending_customers)
    col3.metric("Bugünkü Aramalar", today_calls)

    col1, col2, col3 = st.columns(3)
    col1.metric("Tamamlanan", completed_customers)
    col2.metric("Ulaşılamayan", unreachable_customers)
    col3.metric("Şu An Atanmış", assigned_customers)

    st.divider()

    # Operator performance table
    st.subheader("👥 Operatör Performansı (Bugün)")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            u.full_name,
            COUNT(cl.id) as total_calls,
            SUM(CASE WHEN cl.call_status = 'reached' THEN 1 ELSE 0 END) as reached,
            c.name || ' ' || c.surname as current_customer
        FROM users u
        LEFT JOIN call_logs cl ON u.id = cl.operator_id AND DATE(cl.created_at) = DATE('now')
        LEFT JOIN customers c ON u.id = c.assigned_to AND c.status = 'assigned'
        WHERE u.role = 'operator' AND u.is_active = 1
        GROUP BY u.id
        ORDER BY total_calls DESC
    """)

    operators = cursor.fetchall()
    conn.close()

    if operators:
        df = pd.DataFrame(operators, columns=['Operatör', 'Toplam Arama', 'Ulaşılan', 'Şu Anki Müşteri'])
        df['Şu Anki Müşteri'] = df['Şu Anki Müşteri'].fillna('-')
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Henüz operatör yok")

# Tab 2: File Upload (Excel & CSV)
with tab2:
    st.subheader("📤 Dosya Yükle")

    # File type selector
    upload_type = st.radio(
        "Dosya Türü Seçin:",
        ["📊 Excel (.xlsx, .xls)", "📄 CSV (Pipe-delimited)"],
        horizontal=True
    )

    if upload_type == "📊 Excel (.xlsx, .xls)":
        st.info("""
        **Excel Formatı:**
        - **Ad** (zorunlu)
        - **Soyad** (zorunlu)
        - **Kullanıcı Kodu** (zorunlu, benzersiz)
        - **Telefon Numarası** (zorunlu)
        """)

        uploaded_file = st.file_uploader(
            "Excel dosyası seçin (.xlsx, .xls)",
            type=['xlsx', 'xls'],
            key='excel_uploader'
        )

        if uploaded_file:
            if st.button("📥 Excel Yükle ve İşle", type="primary", key='excel_upload_btn'):
                with st.spinner("Excel dosyası işleniyor..."):
                    try:
                        upload_id, summary = process_excel_file(uploaded_file, user['id'])

                        st.success("✅ Excel dosyası başarıyla işlendi!")

                        col1, col2, col3 = st.columns(3)
                        col1.metric("Toplam Satır", summary['total_rows'])
                        col2.metric("Başarılı", summary['successful'])
                        col3.metric("Başarısız", summary['failed'])

                        if summary['errors']:
                            st.warning("⚠️ Bazı satırlarda hata oluştu:")
                            for error in summary['errors'][:10]:
                                st.write(f"- Satır {error['row']}: {error['error']}")

                            if len(summary['errors']) > 10:
                                st.write(f"... ve {len(summary['errors']) - 10} hata daha")

                    except Exception as e:
                        st.error(f"❌ Hata oluştu: {str(e)}")

    else:  # CSV Upload
        st.info("""
        **CSV Formatı (Pipe-delimited: |)**

        **Gerekli Kolonlar:**
        - FIRST_NAME
        - SURNAME
        - CUSTOMER_CODE (benzersiz)
        - PHONE
        - HAS_DEPOSIT
        - TOTAL_DEPOSIT_AMOUNT
        - LAST_DEPOSIT_TRANSACTION_DATE

        **Otomatik Filtreleme:**
        - ✅ Sadece yatırım yapmış müşteriler (TOTAL_DEPOSIT_AMOUNT > 0)
        - ✅ Sadece pasif müşteriler (30+ gün yatırım yok)
        - ❌ Sıfır yatırımlılar atlanır
        - ❌ Aktif müşteriler atlanır
        - ❌ Duplicate kayıtlar atlanır
        """)

        uploaded_file = st.file_uploader(
            "CSV dosyası seçin (.csv)",
            type=['csv'],
            key='csv_uploader'
        )

        if uploaded_file:
            if st.button("📥 CSV Yükle ve İşle", type="primary", key='csv_upload_btn'):
                with st.spinner("CSV dosyası işleniyor..."):
                    try:
                        upload_id, summary = process_csv_file(uploaded_file, user['id'])

                        st.success("✅ CSV dosyası başarıyla işlendi!")

                        # Show detailed metrics
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Toplam Satır", summary['total_rows'])
                        col2.metric("✅ Başarılı", summary['successful'])
                        col3.metric("❌ Başarısız", summary['failed'])

                        # Show skipped statistics
                        st.divider()
                        st.subheader("📊 Filtreleme İstatistikleri")

                        col1, col2, col3 = st.columns(3)
                        col1.metric("🚫 Sıfır Yatırım", summary['skipped_no_deposit'])
                        col2.metric("✅ Aktif Müşteri", summary['skipped_active'])
                        col3.metric("🔄 Duplicate", summary['skipped_duplicate'])

                        if summary['errors']:
                            st.warning("⚠️ Bazı satırlarda hata oluştu:")
                            for error in summary['errors'][:10]:
                                st.write(f"- Satır {error['row']}: {error.get('error', 'Bilinmeyen hata')}")

                            if len(summary['errors']) > 10:
                                st.write(f"... ve {len(summary['errors']) - 10} hata daha")

                    except Exception as e:
                        st.error(f"❌ Hata oluştu: {str(e)}")

# Tab 3: Customer List View
with tab3:
    st.subheader("📋 Müşteri Listesi")

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Durum Filtresi:",
            ["Tümü", "⏳ Beklemede", "🔄 Atandı", "✅ Tamamlandı", "❌ Ulaşılamadı"]
        )

    with col2:
        search_query = st.text_input("🔍 Ara (Ad, Soyad, Kod, Telefon):", "")

    with col3:
        sort_by = st.selectbox(
            "Sırala:",
            ["En Yeni", "En Eski", "Arama Denemesi (Çok → Az)", "Arama Denemesi (Az → Çok)"]
        )

    # Build query
    conn = get_connection()
    cursor = conn.cursor()

    # Base query
    query = """
        SELECT
            c.id,
            c.name,
            c.surname,
            c.user_code,
            c.phone_number,
            c.status,
            c.call_attempts,
            c.last_call_status,
            c.created_at,
            u.full_name as assigned_operator,
            c.available_after
        FROM customers c
        LEFT JOIN users u ON c.assigned_to = u.id
        WHERE 1=1
    """

    params = []

    # Status filter
    if status_filter != "Tümü":
        status_map = {
            "⏳ Beklemede": "pending",
            "🔄 Atandı": "assigned",
            "✅ Tamamlandı": "completed",
            "❌ Ulaşılamadı": "unreachable"
        }
        query += " AND c.status = ?"
        params.append(status_map[status_filter])

    # Search filter
    if search_query:
        query += """ AND (
            c.name LIKE ? OR
            c.surname LIKE ? OR
            c.user_code LIKE ? OR
            c.phone_number LIKE ?
        )"""
        search_pattern = f"%{search_query}%"
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

    # Sorting
    if sort_by == "En Yeni":
        query += " ORDER BY c.created_at DESC"
    elif sort_by == "En Eski":
        query += " ORDER BY c.created_at ASC"
    elif sort_by == "Arama Denemesi (Çok → Az)":
        query += " ORDER BY c.call_attempts DESC, c.created_at DESC"
    else:  # Az → Çok
        query += " ORDER BY c.call_attempts ASC, c.created_at DESC"

    # Limit results
    query += " LIMIT 500"

    cursor.execute(query, params)
    customers = cursor.fetchall()
    conn.close()

    # Display results
    if customers:
        st.write(f"**Toplam:** {len(customers)} müşteri")

        # Convert to DataFrame for better display
        df_data = []
        for customer in customers:
            df_data.append({
                'Ad': customer[1],
                'Soyad': customer[2],
                'Kullanıcı Kodu': customer[3],
                'Telefon': customer[4],
                'Durum': CUSTOMER_STATUS_LABELS.get(customer[5], customer[5]),
                'Deneme': f"{customer[6]}/3",
                'Atanan Op.': customer[9] if customer[9] else '-',
                'Oluşturma': customer[8][:10] if customer[8] else '-'
            })

        df = pd.DataFrame(df_data)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=400
        )

        # Export option
        st.divider()
        csv_export = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 CSV Olarak İndir",
            data=csv_export,
            file_name=f"musteriler_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("Filtre kriterlerine uygun müşteri bulunamadı.")

# Tab 4: Operator Management
with tab4:
    st.subheader("👥 Yeni Operatör Ekle")

    with st.form("create_operator_form"):
        col1, col2 = st.columns(2)

        with col1:
            new_username = st.text_input("Kullanıcı Adı*")
            new_email = st.text_input("E-posta*")

        with col2:
            new_full_name = st.text_input("Ad Soyad*")
            new_password = st.text_input("Şifre*", type="password")

        submit = st.form_submit_button("➕ Operatör Ekle", type="primary")

        if submit:
            if all([new_username, new_email, new_full_name, new_password]):
                try:
                    user_id = create_operator(new_username, new_email, new_password, new_full_name)
                    st.success(f"✅ Operatör başarıyla oluşturuldu! (ID: {user_id})")
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
            else:
                st.error("Lütfen tüm alanları doldurun")

    st.divider()

    # List existing operators
    st.subheader("📋 Mevcut Operatörler")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username, email, full_name, created_at
        FROM users
        WHERE role = 'operator' AND is_active = 1
        ORDER BY created_at DESC
    """)

    operators = cursor.fetchall()
    conn.close()

    if operators:
        df = pd.DataFrame(operators, columns=['Kullanıcı Adı', 'E-posta', 'Ad Soyad', 'Oluşturma Tarihi'])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Henüz operatör yok")
