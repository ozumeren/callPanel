import streamlit as st
import pandas as pd
from services.excel_service import process_excel_file
from services.auth_service import create_operator
from services.database import get_connection
from services.pool_service import release_stale_assignments

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
tab1, tab2, tab3 = st.tabs(["📈 Dashboard", "📤 Excel Yükle", "👥 Operatör Yönetimi"])

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

# Tab 2: Excel Upload
with tab2:
    st.subheader("📤 Excel Dosyası Yükle")

    st.info("""
    **Excel Formatı:**
    - **Ad** (zorunlu)
    - **Soyad** (zorunlu)
    - **Kullanıcı Kodu** (zorunlu, benzersiz)
    - **Telefon Numarası** (zorunlu)
    """)

    uploaded_file = st.file_uploader(
        "Excel dosyası seçin (.xlsx, .xls)",
        type=['xlsx', 'xls']
    )

    if uploaded_file:
        if st.button("📥 Yükle ve İşle", type="primary"):
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
                        for error in summary['errors'][:10]:  # Show first 10 errors
                            st.write(f"- Satır {error['row']}: {error['error']}")

                        if len(summary['errors']) > 10:
                            st.write(f"... ve {len(summary['errors']) - 10} hata daha")

                except Exception as e:
                    st.error(f"❌ Hata oluştu: {str(e)}")

# Tab 3: Operator Management
with tab3:
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
