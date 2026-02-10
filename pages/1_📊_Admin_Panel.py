import streamlit as st
import pandas as pd
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
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Dashboard", "📤 CSV Yükle", "📋 Müşteri Listesi", "🎉 Geri Dönenler", "👥 Operatör Yönetimi"])

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
            COUNT(DISTINCT cl.customer_id) as unique_customers,
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
        # Prepare data with success rate
        df_data = []
        for op in operators:
            total_calls = op[1]
            unique_customers = op[2]
            reached = op[3]
            current_customer = op[4] if op[4] else '-'

            # Calculate success rate
            success_rate = f"%{int(reached/total_calls*100)}" if total_calls > 0 else "-"

            df_data.append({
                'Operatör': op[0],
                'Müşteri Sayısı': unique_customers,
                'Toplam Arama': total_calls,
                'Ulaşılan': reached,
                'Başarı Oranı': success_rate,
                'Şu Anki Müşteri': current_customer
            })

        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Henüz operatör yok")

# Tab 2: CSV Upload
with tab2:
    st.subheader("📤 CSV Dosyası Yükle")

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

    # Site selection
    site_selection = st.selectbox(
        "🌐 Site Seçin:",
        ["Truva", "Venus"],
        help="Bu CSV dosyasındaki müşteriler hangi siteye ait?"
    )
    selected_site = site_selection.lower()  # truva or venus

    uploaded_file = st.file_uploader(
        "CSV dosyası seçin (.csv)",
        type=['csv']
    )

    if uploaded_file:
        if st.button("📥 CSV Yükle ve İşle", type="primary"):
            with st.spinner("CSV dosyası işleniyor..."):
                try:
                    upload_id, summary = process_csv_file(uploaded_file, user['id'], selected_site)

                    st.success("✅ CSV dosyası başarıyla işlendi!")

                    # Show detailed metrics
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Toplam Satır", summary['total_rows'])
                    col2.metric("✅ Başarılı", summary['successful'])
                    col3.metric("❌ Başarısız", summary['failed'])

                    # Show import details
                    if summary['successful'] > 0:
                        st.success(f"🎉 {summary['successful']} müşteri başarıyla havuza eklendi!")
                    else:
                        st.warning("⚠️ Hiçbir müşteri havuza eklenmedi. Tüm müşteriler filtrelendi.")

                    # Show skipped statistics
                    st.divider()
                    st.subheader("📊 Filtreleme İstatistikleri")

                    col1, col2, col3 = st.columns(3)
                    col1.metric("🚫 Sıfır Yatırım", summary['skipped_no_deposit'])
                    col2.metric("✅ Aktif Müşteri", summary['skipped_active'])
                    col3.metric("🔄 Duplicate", summary['skipped_duplicate'])

                    # Show reactivations
                    if summary.get('reactivations_detected', 0) > 0:
                        st.divider()
                        st.success(f"🎉 **{summary['reactivations_detected']} müşteri pasiften aktife döndü ve daha önce aranmıştı!**")
                        st.info("Bu müşterileri '🎉 Geri Dönenler' tab'ında görebilirsiniz.")

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

    # Show total counts in database
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM customers")
    total_in_db = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM customers WHERE status = 'pending'")
    pending_in_db = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM customers WHERE status = 'assigned' AND assigned_to IS NOT NULL")
    assigned_in_db = cursor.fetchone()[0]
    conn.close()

    col_info1, col_info2, col_info3, col_info4, col_info5 = st.columns([2, 2, 2, 2, 1])
    col_info1.metric("📊 Toplam Müşteri", total_in_db)
    col_info2.metric("⏳ Havuzda Bekleyen", pending_in_db)
    col_info3.metric("🔄 Şu An Atanmış", assigned_in_db)
    col_info4.metric("🔍 Gösterilen (max)", "500")
    with col_info5:
        st.write("")  # Spacing
        if st.button("🔄", use_container_width=True, help="Yenile"):
            st.rerun()

    st.divider()

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Durum Filtresi:",
            ["Tümü", "⏳ Beklemede", "🔄 Atandı", "✅ Tamamlandı", "❌ Ulaşılamadı"],
            index=0  # Default: Tümü
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
            c.site,
            c.status,
            c.call_attempts,
            c.last_call_status,
            c.created_at,
            c.assigned_to,
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
        st.write(f"**Toplam:** {len(customers)} müşteri (max 500 gösteriliyor)")

        # Convert to DataFrame for better display
        df_data = []
        for customer in customers:
            site_name = customer[5].title() if customer[5] else '-'
            site_emoji = "🎰" if customer[5] == 'truva' else "♠️" if customer[5] == 'venus' else ""

            # Debug: Show assigned_to ID
            assigned_id = customer[10]  # assigned_to (ID)
            assigned_name = customer[11]  # assigned_operator (full_name)

            df_data.append({
                'Ad': customer[1],
                'Soyad': customer[2],
                'Kullanıcı Kodu': customer[3],
                'Telefon': customer[4],
                'Site': f"{site_emoji} {site_name}",
                'Durum': CUSTOMER_STATUS_LABELS.get(customer[6], customer[6]),
                'Deneme': f"{customer[7]}/3",
                'Atanan Op.': assigned_name if assigned_name else ('-' if not assigned_id else f"ID:{assigned_id}"),
                'Oluşturma': customer[9][:10] if customer[9] else '-'
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

# Tab 4: Reactivations (Customers who returned from passive to active)
with tab4:
    st.subheader("🎉 Geri Dönen Müşteriler")
    st.info("""
    **Pasiften Aktife Dönen Müşteriler**

    Bu listede, daha önce 30+ gün yatırım yapmamış (pasif) ancak yeni CSV'de tekrar yatırım yapmaya
    başlamış (aktif) ve operatörlerimiz tarafından aranmış olan müşteriler gösterilir.

    Bu, arama çalışmalarının başarısını ölçmek için kullanılır.
    """)

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        # Get list of uploads for filter
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT eu.id, eu.filename, eu.created_at
            FROM reactivations r
            JOIN excel_uploads eu ON r.excel_upload_id = eu.id
            ORDER BY eu.created_at DESC
        """)
        uploads = cursor.fetchall()
        conn.close()

        upload_options = ["Tümü"] + [f"{u[1]} ({u[2][:10]})" for u in uploads]
        selected_upload = st.selectbox("CSV Yükleme:", upload_options)

    with col2:
        # Operator filter
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT operator_name
            FROM reactivations
            WHERE operator_name IS NOT NULL
            ORDER BY operator_name
        """)
        operators = cursor.fetchall()
        conn.close()

        operator_options = ["Tümü"] + [op[0] for op in operators]
        selected_operator = st.selectbox("Operatör:", operator_options)

    with col3:
        date_range = st.selectbox(
            "Tarih Aralığı:",
            ["Tümü", "Son 7 Gün", "Son 30 Gün", "Son 90 Gün"]
        )

    # Build query
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            r.customer_name || ' ' || r.customer_surname as full_name,
            r.customer_code,
            r.phone_number,
            r.old_last_deposit_date,
            r.new_last_deposit_date,
            r.total_calls,
            r.last_call_status,
            r.last_call_notes,
            r.operator_name,
            r.detected_at,
            eu.filename
        FROM reactivations r
        JOIN excel_uploads eu ON r.excel_upload_id = eu.id
        WHERE 1=1
    """

    params = []

    # Upload filter
    if selected_upload != "Tümü":
        upload_id = uploads[upload_options.index(selected_upload) - 1][0]
        query += " AND r.excel_upload_id = ?"
        params.append(upload_id)

    # Operator filter
    if selected_operator != "Tümü":
        query += " AND r.operator_name = ?"
        params.append(selected_operator)

    # Date filter
    if date_range == "Son 7 Gün":
        query += " AND r.detected_at >= datetime('now', '-7 days')"
    elif date_range == "Son 30 Gün":
        query += " AND r.detected_at >= datetime('now', '-30 days')"
    elif date_range == "Son 90 Gün":
        query += " AND r.detected_at >= datetime('now', '-90 days')"

    query += " ORDER BY r.detected_at DESC"

    cursor.execute(query, params)
    reactivations = cursor.fetchall()
    conn.close()

    # Display results
    if reactivations:
        st.write(f"**Toplam:** {len(reactivations)} geri dönen müşteri")

        # Statistics
        total_calls = sum([r[5] for r in reactivations])
        st.metric("Toplam Arama Yapıldı", total_calls)

        st.divider()

        # Display as expandable cards
        for react in reactivations:
            full_name = react[0]
            customer_code = react[1]
            phone = react[2]
            old_date = react[3][:10] if react[3] else "Bilinmiyor"
            new_date = react[4][:10] if react[4] else "Bilinmiyor"
            total_calls_customer = react[5]
            last_status = react[6]
            last_notes = react[7]
            operator = react[8]
            detected = react[9][:10] if react[9] else "Bilinmiyor"
            upload_file = react[10]

            with st.expander(f"👤 {full_name} ({customer_code}) - {operator}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Telefon:** {phone}")
                    st.write(f"**Eski Yatırım Tarihi:** {old_date}")
                    st.write(f"**Yeni Yatırım Tarihi:** {new_date}")

                with col2:
                    st.write(f"**Toplam Arama:** {total_calls_customer}")
                    st.write(f"**Son Arama Durumu:** {last_status}")
                    st.write(f"**Tespit Tarihi:** {detected}")

                if last_notes:
                    st.write(f"**Son Notlar:**")
                    st.text_area("", last_notes, height=100, disabled=True, key=f"notes_{react[1]}")

                st.caption(f"📁 Yüklendiği Dosya: {upload_file}")

        # Export option
        st.divider()
        df_data = []
        for react in reactivations:
            df_data.append({
                'Ad Soyad': react[0],
                'Kullanıcı Kodu': react[1],
                'Telefon': react[2],
                'Eski Tarih': react[3][:10] if react[3] else '',
                'Yeni Tarih': react[4][:10] if react[4] else '',
                'Toplam Arama': react[5],
                'Son Durum': react[6],
                'Notlar': react[7] if react[7] else '',
                'Operatör': react[8],
                'Tespit': react[9][:10] if react[9] else ''
            })

        df = pd.DataFrame(df_data)
        csv_export = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 CSV Olarak İndir",
            data=csv_export,
            file_name=f"geri_donenler_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    else:
        st.info("Henüz geri dönen müşteri tespit edilmedi. CSV yüklemeye devam edin.")

# Tab 5: Operator Management
with tab5:
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
