import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from services.csv_service import process_csv_file
from services.auth_service import create_operator
from services.database import get_connection
from services.pool_service import release_stale_assignments
from utils.constants import CUSTOMER_STATUS_LABELS, CALL_STATUS_LABELS

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
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["📈 Dashboard", "📤 CSV Yükle", "📋 Müşteri Listesi", "🎉 Geri Dönenler", "📵 Geçersiz Numaralar", "👥 Operatör Yönetimi", "🏊 Havuz Yönetimi"])

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

    cursor.execute("SELECT COUNT(*) FROM customers WHERE status = 'invalid_phone'")
    invalid_phone_customers = cursor.fetchone()[0]

    # Reserve pool counts (low value + very old customers)
    cursor.execute("SELECT COUNT(*) FROM customers WHERE status = 'pending' AND is_reserve = 0")
    primary_pool = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM customers WHERE status = 'pending' AND is_reserve = 1")
    reserve_pool = cursor.fetchone()[0]

    # Today's calls
    cursor.execute("SELECT COUNT(*) FROM call_logs WHERE DATE(created_at) = DATE('now')")
    today_calls = cursor.fetchone()[0]

    conn.close()

    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Müşteri", total_customers)
    col2.metric("Havuzda Bekleyen", pending_customers)
    col3.metric("Bugünkü Aramalar", today_calls)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tamamlanan", completed_customers)
    col2.metric("Ulaşılamayan", unreachable_customers)
    col3.metric("Şu An Atanmış", assigned_customers)
    col4.metric("📵 Geçersiz Numara", invalid_phone_customers)

    # Pool tier breakdown
    st.info("**Havuz Dağılımı:** 💎 Birincil (öncelikli müşteriler) | 🔄 Rezerv (düşük yatırım + 180+ gün pasif)")
    col1, col2, col3 = st.columns(3)
    col1.metric("💎 Birincil Havuz", primary_pool)
    col2.metric("🔄 Rezerv Havuz", reserve_pool)
    col3.metric("📊 Havuz Toplam", primary_pool + reserve_pool)

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
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("Henüz operatör yok")

    st.divider()

    # DANGER ZONE: Delete all records
    st.subheader("⚠️ Tehlikeli Bölge")

    with st.expander("🗑️ Tüm Müşteri Kayıtlarını Sil", expanded=False):
        st.error("""
        **DİKKAT:** Bu işlem geri alınamaz!

        Silinecekler:
        - ❌ Tüm müşteri kayıtları
        - ❌ Tüm arama logları
        - ❌ Tüm reaktivasyon kayıtları
        - ❌ Tüm CSV yükleme kayıtları

        Korunacaklar:
        - ✅ Kullanıcı hesapları (Admin & Operatörler)
        """)

        confirm = st.checkbox("⚠️ Evet, TÜM kayıtları silmek istiyorum (bu işlem geri alınamaz)")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "🗑️ TÜM KAYITLARI SİL",
                type="primary",
                disabled=not confirm,
                width="stretch"
            ):
                try:
                    conn = get_connection()
                    cursor = conn.cursor()

                    # Delete in correct order (foreign key constraints)
                    cursor.execute("DELETE FROM call_logs")
                    deleted_logs = cursor.rowcount

                    cursor.execute("DELETE FROM reactivations")
                    deleted_reactivations = cursor.rowcount

                    cursor.execute("DELETE FROM customers")
                    deleted_customers = cursor.rowcount

                    cursor.execute("DELETE FROM excel_uploads")
                    deleted_uploads = cursor.rowcount

                    conn.commit()
                    conn.close()

                    st.success(f"""
                    ✅ Tüm kayıtlar başarıyla silindi!

                    - 🗑️ {deleted_customers} müşteri
                    - 🗑️ {deleted_logs} arama logu
                    - 🗑️ {deleted_reactivations} reaktivasyon kaydı
                    - 🗑️ {deleted_uploads} CSV yükleme kaydı
                    """)

                    st.balloons()

                    # Refresh page after 2 seconds
                    import time
                    time.sleep(2)
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Hata oluştu: {str(e)}")

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
        if st.button("🔄", width="stretch", help="Yenile"):
            st.rerun()

    st.divider()

    # Reset page to 1 when filters change (track filter state)
    if 'customer_list_page' not in st.session_state:
        st.session_state.customer_list_page = 1

    # Filters - Row 1
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status_filter = st.selectbox(
            "Durum Filtresi:",
            ["Tümü", "⏳ Beklemede", "🔄 Atandı", "✅ Tamamlandı", "❌ Ulaşılamadı", "📵 Numara Geçersiz"],
            index=0  # Default: Tümü
        )

    with col2:
        pool_filter = st.selectbox(
            "Havuz Filtresi:",
            ["Tümü", "💎 Birincil", "🔄 Rezerv"],
            index=0  # Default: Tümü
        )

    with col3:
        search_query = st.text_input("🔍 Ara (Ad, Soyad, Kod, Telefon):", "")

    with col4:
        sort_by = st.selectbox(
            "Sırala:",
            ["En Yeni", "En Eski", "Son Arama (Yeni → Eski)", "Son Arama (Eski → Yeni)", "Arama Denemesi (Çok → Az)", "Arama Denemesi (Az → Çok)"]
        )

    # Filters - Row 2: Investment range & date filters
    with st.expander("🔎 Gelişmiş Filtreler (Yatırım & Tarih)", expanded=False):
        col5, col6, col7, col8 = st.columns(4)

        with col5:
            min_deposit = st.number_input(
                "Min. Yatırım (TRY):",
                min_value=0,
                value=0,
                step=1000,
                help="0 = alt sınır yok"
            )

        with col6:
            max_deposit = st.number_input(
                "Max. Yatırım (TRY):",
                min_value=0,
                value=0,
                step=1000,
                help="0 = üst sınır yok"
            )

        with col7:
            deposit_date_start = st.date_input(
                "Son Yatırım Tarihi (Başlangıç):",
                value=None,
                key="dep_date_start",
                help="Bu tarihten itibaren son yatırım yapanlar"
            )

        with col8:
            deposit_date_end = st.date_input(
                "Son Yatırım Tarihi (Bitiş):",
                value=None,
                key="dep_date_end",
                help="Bu tarihe kadar son yatırım yapanlar"
            )

        col9, col10, col11, col12 = st.columns(4)

        with col9:
            login_date_start = st.date_input(
                "Son Giriş Tarihi (Başlangıç):",
                value=None,
                key="login_date_start",
                help="Bu tarihten itibaren platforma giriş yapanlar (LAST_LOGIN_DATE)"
            )

        with col10:
            login_date_end = st.date_input(
                "Son Giriş Tarihi (Bitiş):",
                value=None,
                key="login_date_end",
                help="Bu tarihe kadar son giriş yapanlar (LAST_LOGIN_DATE)"
            )

        with col11:
            last_call_start = st.date_input(
                "Son Arama Tarihi (Başlangıç):",
                value=None,
                key="call_date_start",
                help="Bu tarihten itibaren operatörce arananlar"
            )

        with col12:
            last_call_end = st.date_input(
                "Son Arama Tarihi (Bitiş):",
                value=None,
                key="call_date_end",
                help="Bu tarihe kadar operatörce arananlar"
            )

        col13, col14 = st.columns(4)[:2]

        with col13:
            never_called = st.checkbox("Hiç Aranmayanlar", value=False, help="Sadece hiç arama yapılmamış müşterileri göster")

        with col14:
            site_filter = st.selectbox(
                "Site:",
                ["Tümü", "🎰 Truva", "♠️ Venus"],
                key="site_filter_tab3"
            )

    # Build query
    conn = get_connection()
    cursor = conn.cursor()

    # Base query with last call notes
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
            c.available_after,
            c.last_called_at,
            cl.notes as last_notes,
            c.is_reserve,
            c.last_login_date,
            c.last_deposit_date,
            c.total_deposit_amount
        FROM customers c
        LEFT JOIN users u ON c.assigned_to = u.id
        LEFT JOIN call_logs cl ON cl.id = (
            SELECT MAX(id) FROM call_logs WHERE customer_id = c.id
        )
        WHERE 1=1
    """

    params = []

    # Status filter
    if status_filter != "Tümü":
        status_map = {
            "⏳ Beklemede": "pending",
            "🔄 Atandı": "assigned",
            "✅ Tamamlandı": "completed",
            "❌ Ulaşılamadı": "unreachable",
            "📵 Numara Geçersiz": "invalid_phone"
        }
        query += " AND c.status = ?"
        params.append(status_map[status_filter])

    # Pool filter
    if pool_filter != "Tümü":
        if pool_filter == "💎 Birincil":
            query += " AND c.is_reserve = 0"
        else:  # Rezerv
            query += " AND c.is_reserve = 1"

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

    # Investment amount filter
    if min_deposit > 0:
        query += " AND c.total_deposit_amount >= ?"
        params.append(min_deposit)

    if max_deposit > 0:
        query += " AND c.total_deposit_amount <= ?"
        params.append(max_deposit)

    # Last deposit date filter
    if deposit_date_start:
        query += " AND c.last_deposit_date >= ?"
        params.append(deposit_date_start.strftime('%Y-%m-%d'))

    if deposit_date_end:
        query += " AND c.last_deposit_date <= ?"
        params.append((deposit_date_end + timedelta(days=1)).strftime('%Y-%m-%d'))

    # Last login date filter (from CSV LAST_LOGIN_DATE)
    if login_date_start:
        query += " AND c.last_login_date >= ?"
        params.append(login_date_start.strftime('%Y-%m-%d'))

    if login_date_end:
        query += " AND c.last_login_date <= ?"
        params.append((login_date_end + timedelta(days=1)).strftime('%Y-%m-%d'))

    # Last call date filter (operator calls)
    if never_called:
        query += " AND c.last_called_at IS NULL"
    else:
        if last_call_start:
            query += " AND c.last_called_at >= ?"
            params.append(last_call_start.strftime('%Y-%m-%d'))

        if last_call_end:
            query += " AND c.last_called_at < ?"
            params.append((last_call_end + timedelta(days=1)).strftime('%Y-%m-%d'))

    # Site filter
    if site_filter == "🎰 Truva":
        query += " AND c.site = 'truva'"
    elif site_filter == "♠️ Venus":
        query += " AND c.site = 'venus'"

    # Sorting
    if sort_by == "En Yeni":
        query += " ORDER BY c.created_at DESC"
    elif sort_by == "En Eski":
        query += " ORDER BY c.created_at ASC"
    elif sort_by == "Son Arama (Yeni → Eski)":
        query += " ORDER BY c.last_called_at DESC NULLS LAST"
    elif sort_by == "Son Arama (Eski → Yeni)":
        query += " ORDER BY c.last_called_at ASC NULLS LAST"
    elif sort_by == "Arama Denemesi (Çok → Az)":
        query += " ORDER BY c.call_attempts DESC, c.created_at DESC"
    else:  # Az → Çok
        query += " ORDER BY c.call_attempts ASC, c.created_at DESC"

    # Total count for pagination
    count_query = f"SELECT COUNT(*) FROM ({query}) as q"
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]

    # Pagination
    PAGE_SIZE = 500
    total_pages = max(1, (total_count + PAGE_SIZE - 1) // PAGE_SIZE)

    if 'customer_list_page' not in st.session_state:
        st.session_state.customer_list_page = 1

    # Reset page if filters changed
    page = st.session_state.customer_list_page
    page = max(1, min(page, total_pages))
    st.session_state.customer_list_page = page

    offset = (page - 1) * PAGE_SIZE
    query += f" LIMIT {PAGE_SIZE} OFFSET {offset}"

    cursor.execute(query, params)
    customers = cursor.fetchall()
    conn.close()

    # Display results
    if customers:
        st.write(f"**Toplam:** {total_count} müşteri | Sayfa {page}/{total_pages} ({offset+1}–{min(offset+PAGE_SIZE, total_count)}. kayıt)")

        # Convert to DataFrame for better display
        df_data = []
        for customer in customers:
            site_name = customer[5].title() if customer[5] else '-'
            site_emoji = "🎰" if customer[5] == 'truva' else "♠️" if customer[5] == 'venus' else ""

            assigned_id = customer[10]  # assigned_to (ID)
            assigned_name = customer[11]  # assigned_operator (full_name)
            last_called = customer[13]  # last_called_at
            last_notes = customer[14]  # last_notes
            is_reserve = customer[15]  # is_reserve
            last_login_date = customer[16]  # last_login_date
            last_deposit_date = customer[17]  # last_deposit_date
            total_deposit = customer[18]  # total_deposit_amount

            # Truncate notes for display (first 40 chars)
            notes_display = '-'
            if last_notes:
                notes_display = last_notes[:40] + '...' if len(last_notes) > 40 else last_notes

            # Pool tier display
            pool_tier = "🔄 Rezerv" if is_reserve == 1 else "💎 Birincil"

            df_data.append({
                'Ad': customer[1],
                'Soyad': customer[2],
                'Kullanıcı Kodu': customer[3],
                'Telefon': customer[4],
                'Site': f"{site_emoji} {site_name}",
                'Havuz': pool_tier,
                'Durum': CUSTOMER_STATUS_LABELS.get(customer[6], customer[6]),
                'Yatırım (₺)': float(total_deposit) if total_deposit else 0.0,
                'Son Yatırım': last_deposit_date[:10] if last_deposit_date else '-',
                'Son Giriş': last_login_date[:10] if last_login_date else '-',
                'Deneme': f"{customer[7]}/3",
                'Son Arama': last_called[:16] if last_called else '-',
                'Son Not': notes_display,
                'Atanan Op.': assigned_name if assigned_name else ('-' if not assigned_id else f"ID:{assigned_id}"),
                'Oluşturma': customer[9][:10] if customer[9] else '-'
            })

        df = pd.DataFrame(df_data)
        st.dataframe(
            df,
            width="stretch",
            hide_index=True,
            height=400,
            column_config={
                "Yatırım (₺)": st.column_config.NumberColumn(
                    "Yatırım (₺)",
                    format="%.0f ₺"
                )
            }
        )

        # Pagination controls
        if total_pages > 1:
            pcol1, pcol2, pcol3, pcol4, pcol5 = st.columns([1, 1, 2, 1, 1])
            with pcol1:
                if st.button("⏮ İlk", disabled=(page == 1), key="page_first"):
                    st.session_state.customer_list_page = 1
                    st.rerun()
            with pcol2:
                if st.button("◀ Önceki", disabled=(page == 1), key="page_prev"):
                    st.session_state.customer_list_page = page - 1
                    st.rerun()
            with pcol3:
                st.markdown(f"<div style='text-align:center; padding-top:8px;'>Sayfa <b>{page}</b> / {total_pages}</div>", unsafe_allow_html=True)
            with pcol4:
                if st.button("Sonraki ▶", disabled=(page == total_pages), key="page_next"):
                    st.session_state.customer_list_page = page + 1
                    st.rerun()
            with pcol5:
                if st.button("Son ⏭", disabled=(page == total_pages), key="page_last"):
                    st.session_state.customer_list_page = total_pages
                    st.rerun()

        # Export option
        st.divider()
        csv_export = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 CSV Olarak İndir",
            data=csv_export,
            file_name=f"musteriler_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    # Note details viewer
    st.divider()
    st.subheader("📝 Not Detayları")

    with st.form("view_notes_form"):
        col_note1, col_note2 = st.columns([3, 1])

        with col_note1:
            user_code_notes = st.text_input(
                "Kullanıcı Kodu:",
                placeholder="USR1001",
                help="Notlarını görmek istediğiniz müşterinin kullanıcı kodu"
            )

        with col_note2:
            st.write("")  # Spacing
            view_notes_btn = st.form_submit_button("🔍 Notları Göster", width="stretch")

        if view_notes_btn and user_code_notes:
            conn_notes = get_connection()
            cursor_notes = conn_notes.cursor()

            # Get customer info
            cursor_notes.execute("SELECT id, name, surname FROM customers WHERE user_code = ?", (user_code_notes.strip(),))
            cust = cursor_notes.fetchone()

            if cust:
                st.success(f"👤 **{cust[1]} {cust[2]}** ({user_code_notes})")

                # Get all call logs with notes
                cursor_notes.execute("""
                    SELECT
                        cl.created_at,
                        cl.call_status,
                        cl.notes,
                        u.full_name as operator_name
                    FROM call_logs cl
                    LEFT JOIN users u ON cl.operator_id = u.id
                    WHERE cl.customer_id = ?
                    ORDER BY cl.created_at DESC
                """, (cust[0],))

                call_logs = cursor_notes.fetchall()
                conn_notes.close()

                if call_logs:
                    st.write(f"**Toplam {len(call_logs)} arama kaydı:**")

                    for log in call_logs:
                        log_dict = dict(log)
                        call_time = log_dict['created_at'][:16] if log_dict['created_at'] else '-'
                        status = CALL_STATUS_LABELS.get(log_dict['call_status'], log_dict['call_status'])
                        operator = log_dict['operator_name'] or 'Bilinmiyor'
                        notes = log_dict['notes'] or '(Not yok)'

                        with st.expander(f"🕐 {call_time} - {status} - {operator}"):
                            st.text_area(
                                "Notlar:",
                                value=notes,
                                height=100,
                                disabled=True,
                                key=f"note_{cust[0]}_{call_time}"
                            )
                else:
                    st.info("Bu müşteri için henüz arama kaydı yok.")
            else:
                st.error(f"❌ Kullanıcı kodu '{user_code_notes}' bulunamadı!")

    # Operator assignment tool (available whether customers found or not)
    st.divider()
    st.subheader("🔄 Operatör Değiştir")
    st.info("Bir müşterinin operatörünü değiştirmek veya atamak için kullanın.")

    with st.form("assign_operator_form"):
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            user_code_to_assign = st.text_input(
                "Kullanıcı Kodu:",
                placeholder="USR1001",
                help="Operatör atamak istediğiniz müşterinin kullanıcı kodu"
            )

        with col2:
            # Get all active operators
            conn_op = get_connection()
            cursor_op = conn_op.cursor()
            cursor_op.execute("""
                SELECT id, full_name FROM users
                WHERE role = 'operator' AND is_active = 1
                ORDER BY full_name
            """)
            operators_list = cursor_op.fetchall()
            conn_op.close()

            operator_options = ["(Atamayı Kaldır)"] + [f"{op[1]} (ID:{op[0]})" for op in operators_list]
            selected_operator = st.selectbox(
                "Operatör Seç:",
                operator_options,
                help="Müşteriyi atamak istediğiniz operatör"
            )

        with col3:
            st.write("")  # Spacing
            st.write("")  # Spacing
            submit_assign = st.form_submit_button("✅ Ata", type="primary", width="stretch")

        if submit_assign:
            if user_code_to_assign and user_code_to_assign.strip():
                # Find customer
                conn_assign = get_connection()
                cursor_assign = conn_assign.cursor()

                cursor_assign.execute("SELECT id, name, surname FROM customers WHERE user_code = ?", (user_code_to_assign.strip(),))
                customer_found = cursor_assign.fetchone()

                if customer_found:
                    customer_id = customer_found[0]
                    customer_name = f"{customer_found[1]} {customer_found[2]}"

                    # Determine operator ID
                    if selected_operator == "(Atamayı Kaldır)":
                        new_operator_id = None
                        new_status = 'pending'
                        message = f"✅ {customer_name} ({user_code_to_assign}) için operatör ataması kaldırıldı ve havuza geri eklendi."
                    else:
                        # Extract operator ID from selection
                        operator_id_str = selected_operator.split("ID:")[1].rstrip(")")
                        new_operator_id = int(operator_id_str)
                        new_status = 'assigned'
                        operator_name = selected_operator.split(" (ID:")[0]
                        message = f"✅ {customer_name} ({user_code_to_assign}) → {operator_name} operatörüne atandı."

                    # Update customer
                    cursor_assign.execute("""
                        UPDATE customers
                        SET assigned_to = ?,
                            status = ?,
                            assigned_at = ?,
                            updated_at = ?
                        WHERE id = ?
                    """, (new_operator_id, new_status, datetime.now() if new_operator_id else None, datetime.now(), customer_id))

                    conn_assign.commit()
                    conn_assign.close()

                    st.success(message)
                    st.rerun()
                else:
                    conn_assign.close()
                    st.error(f"❌ Kullanıcı kodu '{user_code_to_assign}' bulunamadı!")
            else:
                st.error("Lütfen bir kullanıcı kodu girin!")

    if not customers:
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

# Tab 5: Invalid Phone Numbers
with tab5:
    st.subheader("📵 Geçersiz Numaralı Müşteriler")
    st.info("""
    **Numara Kullanılmıyor**

    Operatörler tarafından "Numara Kullanılmıyor" olarak işaretlenen müşteriler.
    Numarayı güncelleyip "✅ Numara Güncellendi" butonuna basarak müşteriyi tekrar havuza ekleyebilirsiniz.
    """)

    # Get invalid phone customers
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.id,
            c.name,
            c.surname,
            c.user_code,
            c.phone_number,
            c.site,
            u.full_name as reported_by,
            cl.notes as last_notes,
            cl.created_at as reported_at
        FROM customers c
        LEFT JOIN call_logs cl ON c.id = cl.customer_id AND cl.call_status = 'invalid_phone'
        LEFT JOIN users u ON cl.operator_id = u.id
        WHERE c.status = 'invalid_phone'
        ORDER BY cl.created_at DESC
    """)

    invalid_customers = cursor.fetchall()
    conn.close()

    if invalid_customers:
        st.write(f"**Toplam:** {len(invalid_customers)} müşteri")

        st.divider()

        # Display each invalid customer with edit form
        for idx, cust in enumerate(invalid_customers):
            cust_dict = dict(cust)

            with st.expander(f"📵 {cust_dict['name']} {cust_dict['surname']} - {cust_dict['user_code']}", expanded=True):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Ad Soyad:** {cust_dict['name']} {cust_dict['surname']}")
                    st.write(f"**Kullanıcı Kodu:** {cust_dict['user_code']}")

                    site_name = cust_dict.get('site', 'bilinmiyor').title() if cust_dict.get('site') else 'Bilinmiyor'
                    site_emoji = "🎰" if cust_dict.get('site') == 'truva' else "♠️" if cust_dict.get('site') == 'venus' else ""
                    st.write(f"**Site:** {site_emoji} {site_name}")

                with col2:
                    st.write(f"**Eski Numara:** `{cust_dict['phone_number']}`")
                    if cust_dict.get('reported_by'):
                        st.write(f"**Rapor Eden:** {cust_dict['reported_by']}")
                    if cust_dict.get('reported_at'):
                        st.write(f"**Rapor Tarihi:** {cust_dict['reported_at'][:16]}")

                if cust_dict.get('last_notes'):
                    st.write(f"**Notlar:** {cust_dict['last_notes']}")

                st.divider()

                # Phone number update form
                with st.form(key=f"update_phone_{cust_dict['id']}"):
                    col_input, col_button = st.columns([3, 1])

                    with col_input:
                        new_phone = st.text_input(
                            "Yeni Telefon Numarası:",
                            value=cust_dict['phone_number'],
                            key=f"phone_input_{cust_dict['id']}"
                        )

                    with col_button:
                        st.write("")  # Spacing
                        submit = st.form_submit_button("✅ Numara Güncellendi", type="primary", width="stretch")

                    if submit:
                        if new_phone and new_phone.strip():
                            conn = get_connection()
                            cursor = conn.cursor()

                            # Update phone number and return to pool
                            cursor.execute("""
                                UPDATE customers
                                SET phone_number = ?,
                                    status = 'pending',
                                    call_attempts = 0,
                                    updated_at = ?
                                WHERE id = ?
                            """, (new_phone.strip(), datetime.now(), cust_dict['id']))

                            conn.commit()
                            conn.close()

                            st.success(f"✅ {cust_dict['name']} {cust_dict['surname']} için numara güncellendi ve havuza eklendi!")
                            st.rerun()
                        else:
                            st.error("Lütfen geçerli bir telefon numarası girin!")

    else:
        st.success("✅ Geçersiz numaralı müşteri yok!")

# Tab 6: Operator Management
with tab6:
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
        SELECT id, username, email, full_name, created_at
        FROM users
        WHERE role = 'operator' AND is_active = 1
        ORDER BY created_at DESC
    """)

    operators = cursor.fetchall()
    conn.close()

    if operators:
        # Display operators with delete option
        for op in operators:
            op_dict = dict(op)
            with st.expander(f"👤 {op_dict['full_name']} (@{op_dict['username']})", expanded=False):
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.write(f"**Kullanıcı Adı:** {op_dict['username']}")
                    st.write(f"**E-posta:** {op_dict['email']}")

                with col2:
                    st.write(f"**Ad Soyad:** {op_dict['full_name']}")
                    st.write(f"**Oluşturma:** {op_dict['created_at'][:10]}")

                with col3:
                    st.write("")  # Spacing
                    if st.button("🗑️ Sil", key=f"delete_op_{op_dict['id']}", type="secondary"):
                        # Soft delete: Set is_active = 0
                        conn_del = get_connection()
                        cursor_del = conn_del.cursor()

                        # Release assigned customers
                        cursor_del.execute("""
                            UPDATE customers
                            SET assigned_to = NULL,
                                status = 'pending',
                                updated_at = ?
                            WHERE assigned_to = ?
                        """, (datetime.now(), op_dict['id']))

                        # Deactivate operator
                        cursor_del.execute("""
                            UPDATE users
                            SET is_active = 0
                            WHERE id = ?
                        """, (op_dict['id'],))

                        conn_del.commit()
                        released_count = cursor_del.rowcount
                        conn_del.close()

                        st.success(f"✅ Operatör '{op_dict['full_name']}' silindi. {released_count} müşteri havuza geri eklendi.")
                        st.rerun()
    else:
        st.info("Henüz operatör yok")

# Tab 7: Pool Management
with tab7:
    st.subheader("🏊 Havuz Yönetimi")
    st.info("Bu sekme üzerinden havuzdaki müşterileri operatörlere atabilir veya operatöre atanmış müşterileri havuza geri alabilirsiniz.")

    pool_subtab1, pool_subtab2 = st.tabs(["➕ Havuzdan Personele Ekle", "➖ Personelden Havuza Al"])

    # ── Sub-tab 1: Pool → Operator ──────────────────────────────────────────
    with pool_subtab1:
        st.write("Havuzdaki (bekleyen) bir müşteriyi seçip doğrudan bir operatöre atayın.")

        # Get active operators
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, full_name FROM users
            WHERE role = 'operator' AND is_active = 1
            ORDER BY full_name
        """)
        ops_pool = cursor.fetchall()
        conn.close()

        if not ops_pool:
            st.warning("⚠️ Aktif operatör bulunamadı. Önce operatör ekleyin.")
        else:
            ops_pool_dict = {op['full_name']: op['id'] for op in ops_pool}

            # Controls
            ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([2, 2, 2, 1])
            with ctrl1:
                selected_op_for_pool = st.selectbox(
                    "Atanacak Operatör:",
                    list(ops_pool_dict.keys()),
                    key="pool_to_op_select"
                )
            with ctrl2:
                pool_type_f = st.selectbox(
                    "Havuz Tipi:",
                    ["Tümü", "💎 Birincil", "🔄 Rezerv"],
                    key="pool_type_f"
                )
            with ctrl3:
                pool_search_f = st.text_input("🔍 Ara (Ad, Soyad, Kod):", "", key="pool_search_f")
            with ctrl4:
                st.write("")
                if st.button("🔄 Yenile", key="refresh_pool_list"):
                    st.rerun()

            # Build pool query
            conn = get_connection()
            cursor = conn.cursor()

            pq = """
                SELECT c.id, c.name, c.surname, c.user_code, c.phone_number,
                       c.site, c.total_deposit_amount, c.last_deposit_date,
                       c.is_reserve, c.call_attempts, c.last_called_at
                FROM customers c
                WHERE c.status = 'pending'
                  AND (c.available_after IS NULL OR c.available_after <= datetime('now'))
            """
            pp = []

            if pool_type_f == "💎 Birincil":
                pq += " AND c.is_reserve = 0"
            elif pool_type_f == "🔄 Rezerv":
                pq += " AND c.is_reserve = 1"

            if pool_search_f:
                pq += " AND (c.name LIKE ? OR c.surname LIKE ? OR c.user_code LIKE ?)"
                sp = f"%{pool_search_f}%"
                pp.extend([sp, sp, sp])

            pq += " ORDER BY c.is_reserve ASC, c.priority DESC, c.created_at ASC LIMIT 100"

            cursor.execute(pq, pp)
            pool_custs = cursor.fetchall()
            conn.close()

            st.write(f"**Havuzda {len(pool_custs)} müşteri** (max 100 gösteriliyor)")

            if pool_custs:
                # Header row
                hc1, hc2, hc3, hc4, hc5, hc6 = st.columns([2, 1, 1, 1, 1, 1])
                hc1.markdown("**Ad Soyad / Kod**")
                hc2.markdown("**Havuz**")
                hc3.markdown("**Yatırım**")
                hc4.markdown("**Son Yatırım**")
                hc5.markdown("**Deneme**")
                hc6.markdown("**İşlem**")
                st.divider()

                for cust in pool_custs:
                    cust_dict = dict(cust)
                    pool_tier = "🔄 Rezerv" if cust_dict['is_reserve'] else "💎 Birincil"
                    site_emoji = "🎰" if cust_dict.get('site') == 'truva' else "♠️" if cust_dict.get('site') == 'venus' else ""
                    deposit_str = f"{cust_dict['total_deposit_amount']:,.0f} ₺" if cust_dict.get('total_deposit_amount') else "-"
                    dep_date = cust_dict['last_deposit_date'][:10] if cust_dict.get('last_deposit_date') else "-"

                    rc1, rc2, rc3, rc4, rc5, rc6 = st.columns([2, 1, 1, 1, 1, 1])
                    with rc1:
                        st.write(f"**{cust_dict['name']} {cust_dict['surname']}**")
                        st.caption(f"{cust_dict['user_code']} {site_emoji} | {cust_dict['phone_number']}")
                    with rc2:
                        st.write(pool_tier)
                    with rc3:
                        st.write(deposit_str)
                    with rc4:
                        st.write(dep_date)
                    with rc5:
                        st.write(f"{cust_dict['call_attempts']}/3")
                    with rc6:
                        if st.button("➕ Ata", key=f"assign_pool_{cust_dict['id']}", type="primary"):
                            op_id = ops_pool_dict[selected_op_for_pool]
                            conn_a = get_connection()
                            cursor_a = conn_a.cursor()
                            cursor_a.execute("""
                                UPDATE customers
                                SET assigned_to = ?,
                                    status = 'assigned',
                                    assigned_at = ?,
                                    updated_at = ?
                                WHERE id = ?
                            """, (op_id, datetime.now(), datetime.now(), cust_dict['id']))
                            conn_a.commit()
                            conn_a.close()
                            st.success(f"✅ {cust_dict['name']} {cust_dict['surname']} → {selected_op_for_pool}")
                            st.rerun()

                    st.divider()
            else:
                st.info("Havuzda uygun müşteri bulunamadı.")

    # ── Sub-tab 2: Operator → Pool ──────────────────────────────────────────
    with pool_subtab2:
        st.write("Bir operatöre atanmış müşterileri havuza geri alın.")

        # Get active operators for filter
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT u.id, u.full_name
            FROM users u
            JOIN customers c ON c.assigned_to = u.id
            WHERE c.status = 'assigned' AND u.is_active = 1
            ORDER BY u.full_name
        """)
        ops_assigned = cursor.fetchall()
        conn.close()

        op_filter_opts = ["Tüm Operatörler"] + [op['full_name'] for op in ops_assigned]

        ac1, ac2 = st.columns([2, 1])
        with ac1:
            selected_op_filter2 = st.selectbox(
                "Operatöre Göre Filtrele:",
                op_filter_opts,
                key="assigned_op_filter2"
            )
        with ac2:
            st.write("")
            if st.button("🔄 Yenile", key="refresh_assigned_list"):
                st.rerun()

        # Build assigned customers query
        conn = get_connection()
        cursor = conn.cursor()

        aq = """
            SELECT c.id, c.name, c.surname, c.user_code, c.phone_number,
                   c.site, c.total_deposit_amount, c.last_deposit_date,
                   c.assigned_at, u.full_name as operator_name, u.id as operator_id
            FROM customers c
            LEFT JOIN users u ON c.assigned_to = u.id
            WHERE c.status = 'assigned'
        """
        ap = []

        if selected_op_filter2 != "Tüm Operatörler":
            aq += " AND u.full_name = ?"
            ap.append(selected_op_filter2)

        aq += " ORDER BY u.full_name ASC, c.assigned_at DESC LIMIT 200"

        cursor.execute(aq, ap)
        assigned_custs = cursor.fetchall()
        conn.close()

        st.write(f"**{len(assigned_custs)} müşteri operatöre atanmış**")

        if assigned_custs:
            # Header row
            ah1, ah2, ah3, ah4, ah5, ah6 = st.columns([2, 1, 1, 1, 1, 1])
            ah1.markdown("**Ad Soyad / Kod**")
            ah2.markdown("**Operatör**")
            ah3.markdown("**Yatırım**")
            ah4.markdown("**Son Yatırım**")
            ah5.markdown("**Atanma**")
            ah6.markdown("**İşlem**")
            st.divider()

            for cust in assigned_custs:
                cust_dict = dict(cust)
                site_emoji = "🎰" if cust_dict.get('site') == 'truva' else "♠️" if cust_dict.get('site') == 'venus' else ""
                deposit_str = f"{cust_dict['total_deposit_amount']:,.0f} ₺" if cust_dict.get('total_deposit_amount') else "-"
                dep_date = cust_dict['last_deposit_date'][:10] if cust_dict.get('last_deposit_date') else "-"
                assigned_at_str = cust_dict['assigned_at'][:16] if cust_dict.get('assigned_at') else "-"

                ar1, ar2, ar3, ar4, ar5, ar6 = st.columns([2, 1, 1, 1, 1, 1])
                with ar1:
                    st.write(f"**{cust_dict['name']} {cust_dict['surname']}**")
                    st.caption(f"{cust_dict['user_code']} {site_emoji} | {cust_dict['phone_number']}")
                with ar2:
                    st.write(cust_dict.get('operator_name') or '-')
                with ar3:
                    st.write(deposit_str)
                with ar4:
                    st.write(dep_date)
                with ar5:
                    st.write(assigned_at_str)
                with ar6:
                    if st.button("➖ Havuza Al", key=f"release_pool_{cust_dict['id']}"):
                        conn_r = get_connection()
                        cursor_r = conn_r.cursor()
                        cursor_r.execute("""
                            UPDATE customers
                            SET assigned_to = NULL,
                                status = 'pending',
                                assigned_at = NULL,
                                updated_at = ?
                            WHERE id = ?
                        """, (datetime.now(), cust_dict['id']))
                        conn_r.commit()
                        conn_r.close()
                        st.success(f"✅ {cust_dict['name']} {cust_dict['surname']} havuza geri alındı.")
                        st.rerun()

                st.divider()
        else:
            st.info("Operatöre atanmış müşteri bulunamadı.")
