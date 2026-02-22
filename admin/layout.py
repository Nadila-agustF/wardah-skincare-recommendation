import streamlit as st
from admin.login import log_admin_logout

def show_admin_layout():
    st.markdown("""
    <style>
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div {
            background: linear-gradient(
                180deg,
                #1e6fa3 0%,
                #2b8cc4 50%,
                #3fa9dd 100%
            ) !important;
        }

        /* ===== SIDEBAR HEADER (Home page / Menu) ===== */
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            background: rgba(255, 255, 255, 0.15); /* transparan */
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            margin-bottom: 1.5rem;
            padding: 14px 18px;
            border-radius: 14px;
            font-size: 1.5rem;
            color: #ffffff !important;
            font-weight: 700;
            text-align: center;
            }

        /* ===== TEKS UMUM DI SIDEBAR ===== */
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span {
            color: white !important;
            font-size: 1rem;
        }
        /* Hilangkan border default */
        section[data-testid="stSidebar"] {
            border-right: 1px solid #e9ecef;
        }

        /* Rapihin header */
        section[data-testid="stSidebar"] .st-emotion-cache-10trblm {
            margin-bottom: 1.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

    if not st.session_state.get("admin_logged_in", True):
        st.error("⚠️ Harap login sebagai admin")
        return

    # ===== SIDEBAR NAVIGATION =====
    with st.sidebar:
        st.header("🧭 Home Page")
        
        # Navigation akan menggunakan CSS di atas
        
        page = st.radio(
            "",
            ["🏠 Dashboard", "📋 User History", "👤 Tambah Admin","📴 Logout"],
            key="guest_nav",
            label_visibility="collapsed"
        )

    # ===== CONTENT =====
    if page == "🏠 Dashboard":
        try:
            from admin.dashboard import show_admin_dashboard
            show_admin_dashboard()
        except ImportError as e:
            st.error(f"Modul dashboard tidak ditemukan: {e}")
            st.warning("Silakan periksa apakah file dashboard.py ada dan dapat diimpor.")

    elif page == "📋 User History":
        try:
            from admin.history import show_user_history_page
            show_user_history_page()
        except ImportError as e:
            st.error(f"Modul history tidak ditemukan: {e}")

    elif page == "👤 Tambah Admin":
        try:
            from admin.add_admin import show_add_admin_page
            show_add_admin_page()
        except ImportError as e:
            st.error(f"Modul tambah admin tidak ditemukan: {e}")
            st.warning("Silakan periksa apakah file add_admin.py ada dan dapat diimpor.")
    
    elif page == "📴 Logout":
        if "activity_id" in st.session_state:
            log_admin_logout(st.session_state.activity_id)
            
        st.session_state.user_mode = 'admin'
        st.session_state.admin_logged_in = False 
        st.rerun()


    
