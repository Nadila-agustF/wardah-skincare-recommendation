import streamlit as st
from pathlib import Path

# ===============================
# HELPER FUNCTIONS
# ===============================
# Load CSS
def load_css():
    """Load Globl CSS untuk seluruh aplikasi"""
    css_path = Path(__file__).parent / "style.css"
    if css_path.exists():
        with open(css_path, 'r', encoding='utf-8') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'user_mode' not in st.session_state:
        st.session_state.user_mode = None  # 'guest' or 'admin'
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = "welcome"  

def show_welcome_screen():
    """Welcome page untuk pilih mode"""
    # Hapus JavaScript yang tidak berfungsi dan gunakan Streamlit native
    
    st.markdown("""
    <div class="page-wrapper"></div>            
        <div class="welcome-container">
            <h1 class="welcome-title">
                <span>🌸</span>
                Wardah Skincare Recommender
            </h1>
            <p class="welcome-subtitle">
                Sistem rekomendasi produk skincare Wardah berdasarkan jenis kulit Anda
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="page-wrapper">', unsafe_allow_html=True)
    # Container untuk mode selection
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("""
        <div class="mode-card">
            <div class="mode-icon" align="center">👤</div>
            <h2 class="mode-title" align="center">Mode Pengguna</h2>
            <p style="color: #666; line-height: 1.6;">
                Dapatkan rekomendasi produk Wardah yang sesuai dengan jenis kulit dan kebutuhan Anda
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("👤 **Masuk sebagai Pengguna**", 
                    use_container_width=True, 
                    type="primary",
                    key="guest_btn"):
            st.session_state.user_mode = 'guest'
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class="mode-card">
            <div class="mode-icon" align="center">👑</div>
            <h2 class="mode-title" align="center">Mode Admin</h2>
            <p style="color: #666; line-height: 1.6;">
                Akses dashboard admin untuk melihat statistik dan mengelola sistem
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("👑 **Masuk sebagai Admin**", 
                    use_container_width=True,
                    key="admin_btn"):
            st.session_state.user_mode = 'admin'
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tambahkan informasi footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #888; font-size: 0.9rem;'>"
        "Pilih mode sesuai dengan kebutuhan Anda untuk melanjutkan"
        "</p>", 
        unsafe_allow_html=True
    )
# ===============================
# MAIN APPLICATION
# ===============================
def main():
    # Setup
    st.set_page_config(
        page_title="Wardah Skincare Recommender",
        page_icon="🧴",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    load_css()
    init_session_state()
    
    # ==================== WELCOME SCREEN ====================
    if st.session_state.user_mode is None:
        show_welcome_screen()
        return
    
    # ==================== GUEST MODE ====================
    elif st.session_state.user_mode == 'guest':
        # Import di dalam fungsi untuk menghindari circular import
        try:
            from guest.Home import show_guest_home
            show_guest_home()
        except ImportError as e:
            st.error(f"Modul guest tidak ditemukan: {e}")
            st.info("Kembali ke halaman utama...")
            if st.button("Kembali ke Menu Utama"):
                st.session_state.user_mode = None
                st.session_state.admin_logged_in = False
                st.rerun()
    
    # ==================== ADMIN MODE ====================
    elif st.session_state.user_mode == 'admin':
        if not st.session_state.admin_logged_in:
            from admin.login import show_admin_login_page
            show_admin_login_page()
        else:
            from admin.layout import show_admin_layout
            show_admin_layout() 

if __name__ == "__main__":
    main()