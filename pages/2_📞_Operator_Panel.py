import streamlit as st
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

# Main content
if 'current_customer' not in st.session_state or st.session_state.current_customer is None:
    # No customer assigned - show pull button
    st.info("Şu anda atanmış müşteri yok. Havuzdan bir müşteri çekin.")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎯 Müşteri Çek", use_container_width=True, type="primary"):
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

    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Ad:** {customer['name']}")
        st.write(f"**Soyad:** {customer['surname']}")
    with col2:
        st.write(f"**Kullanıcı Kodu:** {customer['user_code']}")
        st.write(f"**Telefon Numarası:** `{customer['phone_number']}`")

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

    # Status buttons
    st.subheader("📞 Arama Durumu")
    st.write("Arama sonucunu seçin:")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("✅ Ulaşıldı", use_container_width=True, type="primary"):
            return_customer_to_pool(customer['id'], 'reached', notes, user['id'])
            st.session_state.current_customer = None
            st.success("Arama kaydedildi! Müşteri tamamlandı olarak işaretlendi.")
            st.rerun()

    with col2:
        if st.button("📵 Telefonu Açmadı", use_container_width=True):
            return_customer_to_pool(customer['id'], 'no_answer', notes, user['id'])
            st.session_state.current_customer = None
            st.info("Arama kaydedildi! Müşteri tekrar havuza eklendi.")
            st.rerun()

    with col3:
        if st.button("🚫 Meşgule Attı", use_container_width=True):
            return_customer_to_pool(customer['id'], 'declined', notes, user['id'])
            st.session_state.current_customer = None
            st.info("Arama kaydedildi! Müşteri tekrar havuza eklendi.")
            st.rerun()

    with col4:
        if st.button("⏳ Meşgul", use_container_width=True):
            return_customer_to_pool(customer['id'], 'busy', notes, user['id'])
            st.session_state.current_customer = None
            st.info("Arama kaydedildi! Müşteri tekrar havuza eklendi.")
            st.rerun()
