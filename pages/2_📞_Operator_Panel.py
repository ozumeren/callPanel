import streamlit as st
import pandas as pd
from datetime import datetime
from services.pool_service import pull_customer_for_operator, return_customer_to_pool
from services.database import get_connection
from utils.constants import CALL_STATUS_LABELS

st.set_page_config(page_title="Operatör Paneli", page_icon="📞", layout="wide")

# Check authentication
if 'user' not in st.session_state:
    st.error("Lütfen giriş yapın")
    st.switch_page("Home.py")

user = st.session_state.user

if user['role'] != 'operator':
    st.error("Bu sayfaya erişim yetkiniz yok")
    st.stop()

# Sidebar
st.sidebar.title(f"👤 {user['full_name']}")
st.sidebar.write(f"**Rol:** Operatör")
if st.sidebar.button("🚪 Çıkış Yap"):
    del st.session_state.user
    if 'current_customer' in st.session_state:
        del st.session_state.current_customer
    st.switch_page("Home.py")

st.title("📞 Operatör Paneli")

# Create tabs
tab1, tab2 = st.tabs(["🎯 Müşteri Çek", "📖 Telefon Rehberi"])

# ===================================================================
# TAB 1: Customer Pulling (existing functionality)
# ===================================================================
with tab1:
    if 'current_customer' not in st.session_state or st.session_state.current_customer is None:
        # No customer assigned - show pull button
        st.info("Şu anda atanmış müşteri yok. Havuzdan bir müşteri çekin.")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🎯 Müşteri Çek", width="stretch", type="primary"):
                customer = pull_customer_for_operator(user['id'])

                if customer:
                    st.session_state.current_customer = customer
                    st.rerun()
                else:
                    st.warning("Havuzda müşteri yok. Lütfen daha sonra tekrar deneyin.")

        # Show today's statistics
        st.divider()
        st.subheader("📊 Bugünkü İstatistikler")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM call_logs
            WHERE operator_id = ? AND DATE(created_at) = DATE('now')
        """, (user['id'],))
        today_calls = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM call_logs
            WHERE operator_id = ? AND call_status = 'reached' AND DATE(created_at) = DATE('now')
        """, (user['id'],))
        today_reached = cursor.fetchone()[0]

        conn.close()

        col1, col2, col3 = st.columns(3)
        col1.metric("Toplam Arama", today_calls)
        col2.metric("Ulaşılan", today_reached)
        if today_calls > 0:
            col3.metric("Başarı Oranı", f"%{int(today_reached/today_calls*100)}")

    else:
        # Customer assigned - show details and action buttons
        customer = st.session_state.current_customer

        st.success("✅ Müşteri atandı!")

        # Customer card
        st.subheader("👤 Müşteri Bilgileri")

        # Convert to dict for easier access
        customer_dict = dict(customer) if hasattr(customer, 'keys') else customer

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Ad:** {customer['name']}")
            st.write(f"**Soyad:** {customer['surname']}")
            # Show site with emoji
            site_emoji = "🎰" if customer_dict.get('site') == 'truva' else "♠️"
            site_name = customer_dict.get('site', 'bilinmiyor').title()
            st.write(f"**Site:** {site_emoji} {site_name}")
        with col2:
            st.write(f"**Kullanıcı Kodu:** {customer['user_code']}")
            st.write(f"**Telefon Numarası:** `{customer['phone_number']}`")

        # Show how long customer has been inactive
        if customer_dict.get('last_deposit_date'):
            try:
                last_deposit = pd.to_datetime(customer_dict['last_deposit_date'])
                days_inactive = (datetime.now() - last_deposit).days

                # Color code based on inactivity
                if days_inactive > 90:
                    emoji = "🔴"
                elif days_inactive > 60:
                    emoji = "🟠"
                else:
                    emoji = "🟡"

                st.info(f"{emoji} **Pasif Süresi:** {days_inactive} gün (Son yatırım: {customer_dict['last_deposit_date'][:10]})")
            except:
                pass

        if customer['call_attempts'] > 0:
            st.write(f"**Arama Denemesi:** {customer['call_attempts']}/3")

        st.divider()

        # Notes form
        st.subheader("📝 Notlar")
        notes = st.text_area(
            "Bonus teklifleri ve müşteri yanıtlarını buraya yazın...",
            height=150,
            placeholder="Örnek: 100 TL bonus teklif edildi, müşteri kabul etti...",
            key="notes_textarea"
        )

        st.divider()

        # Status selection with confirmation
        st.subheader("📞 Arama Durumu")
        st.write("Arama sonucunu seçin ve 'Gönder' butonuna basın:")

        # Radio button selection
        call_status_options = {
            "✅ Ulaşıldı": "reached",
            "📵 Telefonu Açmadı": "no_answer",
            "🚫 Meşgule Attı": "declined",
            "⏳ Meşgul": "busy",
            "📵 Numara Kullanılmıyor": "invalid_phone"
        }

        selected_status_label = st.radio(
            "Durum Seçin:",
            options=list(call_status_options.keys()),
            index=None,  # No default selection
            horizontal=False,
            key="call_status_radio"
        )

        st.divider()

        # Submit button (only enabled if status is selected)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit_enabled = selected_status_label is not None

            if not submit_enabled:
                st.warning("⚠️ Lütfen önce bir arama durumu seçin")

            if st.button(
                "📤 Gönder ve Kaydet",
                type="primary",
                disabled=not submit_enabled,
                width="stretch",
                key="submit_call_status"
            ):
                # Get the actual status value
                selected_status = call_status_options[selected_status_label]

                # Process the call result
                return_customer_to_pool(customer['id'], selected_status, notes, user['id'])
                st.session_state.current_customer = None

                # Show appropriate message based on status
                if selected_status == 'reached':
                    st.success("✅ Arama kaydedildi! Müşteri tamamlandı olarak işaretlendi.")
                elif selected_status == 'invalid_phone':
                    st.warning("📵 Müşteri 'Numara Geçersiz' olarak işaretlendi. Admin numarayı güncelleyene kadar havuzdan çıkarıldı.")
                else:
                    st.info("📝 Arama kaydedildi! Müşteri tekrar havuza eklendi.")

                st.rerun()

# ===================================================================
# TAB 2: Phone Directory (NEW FEATURE)
# ===================================================================
with tab2:
    st.subheader("📖 Telefon Rehberim")
    st.write("Ulaştığınız müşterilerin listesi. Gerektiğinde buradan numarasını alıp tekrar arayabilirsiniz.")

    # Search box
    search = st.text_input("🔍 Ara (Ad, Soyad, Telefon)", placeholder="Ahmet, 0532...")

    # Get successfully reached customers
    conn = get_connection()
    cursor = conn.cursor()

    # Get all reached customers with their last call details
    query = """
        SELECT
            c.id,
            c.name,
            c.surname,
            c.user_code,
            c.phone_number,
            c.site,
            cl.notes,
            cl.created_at as last_call_date,
            COUNT(DISTINCT cl2.id) as total_calls
        FROM customers c
        INNER JOIN call_logs cl ON c.id = cl.customer_id
        LEFT JOIN call_logs cl2 ON c.id = cl2.customer_id AND cl2.operator_id = ?
        WHERE c.id IN (
            SELECT DISTINCT customer_id
            FROM call_logs
            WHERE operator_id = ? AND call_status = 'reached'
        )
        AND cl.id = (
            SELECT MAX(id)
            FROM call_logs
            WHERE customer_id = c.id AND operator_id = ?
        )
        AND cl.operator_id = ?
        GROUP BY c.id
        ORDER BY cl.created_at DESC
    """

    cursor.execute(query, (user['id'], user['id'], user['id'], user['id']))
    contacts = cursor.fetchall()
    conn.close()

    if contacts:
        # Filter by search
        if search:
            search_lower = search.lower()
            filtered_contacts = [
                c for c in contacts
                if search_lower in c['name'].lower()
                or search_lower in c['surname'].lower()
                or search_lower in c['phone_number']
                or search_lower in c['user_code'].lower()
            ]
        else:
            filtered_contacts = contacts

        if filtered_contacts:
            st.write(f"**Toplam {len(filtered_contacts)} kişi** (ulaştığınız müşteriler)")
            st.divider()

            # Display each contact
            for contact in filtered_contacts:
                # Show site with emoji in title
                contact_dict = dict(contact)
                site_emoji = "🎰" if contact_dict.get('site') == 'truva' else "♠️"
                site_name = contact_dict.get('site', 'bilinmiyor').title()

                with st.expander(f"👤 {contact['name']} {contact['surname']} - {site_emoji} {site_name} - {contact['phone_number']}", expanded=False):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Ad Soyad:** {contact['name']} {contact['surname']}")
                        st.write(f"**Kullanıcı Kodu:** {contact['user_code']}")
                        st.write(f"**Site:** {site_emoji} {site_name}")

                    with col2:
                        st.write(f"**Telefon:** `{contact['phone_number']}`")
                        st.write(f"**Toplam Arama:** {contact['total_calls']} kez")

                    # Last call date
                    from datetime import datetime
                    last_call = datetime.fromisoformat(contact['last_call_date'])
                    st.write(f"**Son Arama:** {last_call.strftime('%d/%m/%Y %H:%M')}")

                    # Notes from last call
                    if contact['notes']:
                        st.write("**Son Görüşme Notları:**")
                        st.info(contact['notes'])
                    else:
                        st.write("**Son Görüşme Notları:** _Not girilmemiş_")

        else:
            st.warning(f"'{search}' araması için sonuç bulunamadı.")
    else:
        st.info("📭 Henüz ulaştığınız müşteri yok. Müşterilere ulaştıkça burada görünecekler.")
        st.write("💡 **İpucu:** 'Müşteri Çek' sekmesinden müşteri çekin ve '✅ Ulaşıldı' butonuna basın.")
