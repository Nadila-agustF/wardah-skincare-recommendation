# admin/login.py
import streamlit as st
import hashlib
import time
from datetime import datetime

import hashlib
from utils.db import DatabaseConnection
from utils.generator_id import generate_id

def authenticate_admin(username, password):
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    db = DatabaseConnection()
    conn = db.connect()
    if conn is None:
        return None

    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT id, username, email, role
        FROM admin
        WHERE username = %s AND password = %s
        LIMIT 1
    """
    cursor.execute(query, (username, password_hash))
    admin = cursor.fetchone()

    cursor.close()
    conn.close()

    return admin  # None kalau tidak ketemu

def log_admin_login(admin_id, admin_role):
    db = DatabaseConnection()
    conn = db.connect()
    cursor = conn.cursor()  
    activity_id = generate_id(cursor, "admin_activity", "id", "ACT")

    query = """
    INSERT INTO admin_activity
    (id, admin_id, login_time, status)
    VALUES (%s, %s, %s, %s)
    """

    cursor.execute(query, (
        activity_id,
        admin_id,
        datetime.now(),
        "Online"
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return activity_id

def log_admin_logout(activity_id):
    db = DatabaseConnection()
    conn = db.connect()     
    cursor = conn.cursor()

    query = """
        UPDATE admin_activity
        set logout_time=%s, 
        status=%s
        WHERE id=%s
    """

    cursor.execute(query, (
        datetime.now(),
        "Offline",
        activity_id
    ))

    conn.commit()
    cursor.close()
    conn.close()

def show_admin_login_page():
    """Display admin login page"""
    
    # Admin credentials (In production, store in database or secrets)
    ADMIN_CREDENTIALS = {
        "admin": {
            "password_hash": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",  # sha256("admin")
            "name": "Super Admin"
        },
        "wardah": {
            "password_hash": "15e2b0d3c33891ebb0f1ef609ec419420c20e320ce94c65fbc8c3312448eb225",  # sha256("wardah123")
            "name": "Wardah Admin"
        }
    }
    
    # Session state initialization
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0
    if 'last_attempt_time' not in st.session_state:
        st.session_state.last_attempt_time = 0
    
    # Check if user is temporarily locked out
    current_time = time.time()
    lockout_time = 300  # 5 minutes lockout
    if st.session_state.login_attempts >= 5:
        time_since_last = current_time - st.session_state.last_attempt_time
        if time_since_last < lockout_time:
            remaining = int((lockout_time - time_since_last) / 60)
            st.error(f"⏳ Terlalu banyak percobaan gagal. Silakan coba lagi dalam {remaining} menit.")
            return
    
    # Login form
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div class="login-card">
                <h3 style="text-align: center; color: #1e40af;">Administrator Access</h3>
                <p style="text-align: center; color: #6b7280;">
                    Masukkan kredensial admin untuk mengakses dashboard
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            username = st.text_input(
                "👤 **Username**",
                placeholder="Masukkan username admin",
                key="admin_username_input"
            )
            
            password = st.text_input(
                "🔒 **Password**",
                type="password",
                placeholder="Masukkan password",
                key="admin_password_input"
            )
            
            # Remember me option
            remember_me = st.checkbox("Ingat saya", value=False)
            
            # Login button
            login_col1, login_col2, login_col3 = st.columns([1, 2, 1])
            with login_col2:
                login_clicked = st.button(
                    "🚪 **Login**",
                    type="primary",
                    use_container_width=True,
                    key="admin_login_btn"
                )
            
           # Back to user mode button
            if st.button("← Kembali ke welcome page", use_container_width=True):
                st.session_state.app_mode = "welcome"   # ⬅️ balik ke welcome page
                st.session_state.admin_logged_in = False
                st.session_state.user_mode = None
                st.rerun()
    
    # Handle login attempt
    if login_clicked:
        if not username or not password:
            st.warning("⚠️ Harap isi username dan password")
            return

        # =============================
        # 1️⃣ Cek ke DATABASE dulu
        # =============================
        admin = authenticate_admin(username, password)

        if admin:
            activity_id = log_admin_login(admin['id'], admin['role'])
            
            st.session_state['admin_logged_in'] = True
            st.session_state['admin_username'] = admin['username']
            st.session_state['admin_name'] = admin['username']
            st.session_state['admin_role'] = admin['role']
            st.session_state.activity_id= activity_id 
            st.session_state['app_mode'] = 'admin'
            st.session_state.login_attempts = 0

            st.success(f"✅ Login berhasil! Selamat datang, {admin['username']}")
            time.sleep(1)
            st.rerun()
            return

        # =============================
        # 2️⃣ Fallback ke ADMIN_CREDENTIALS
        # =============================
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        if (
            username in ADMIN_CREDENTIALS and
            ADMIN_CREDENTIALS[username]["password_hash"] == password_hash
        ):
            st.session_state['admin_logged_in'] = True
            st.session_state['admin_username'] = username
            st.session_state['admin_name'] = ADMIN_CREDENTIALS[username]["name"]
            st.session_state['admin_role'] = 'Super Admin'
            st.session_state['app_mode'] = 'admin'
            st.session_state.login_attempts = 0

            st.success(f"✅ Login berhasil! Selamat datang, {ADMIN_CREDENTIALS[username]['name']}")
            time.sleep(1)
            st.rerun()
            return

        # =============================
        # 3️⃣ Gagal login
        # =============================
        st.session_state.login_attempts += 1

        if st.session_state.login_attempts >= 5:
            st.error("❌ Terlalu banyak percobaan gagal. Akun terkunci sementara.")
        else:
            st.error(f"❌ Username atau password salah ({st.session_state.login_attempts}/5)")

    
    # # Help section
    # with st.expander("ℹ️ **Bantuan Login**", expanded=False):
    #     st.markdown("""
    #     ### **Default Admin Accounts:**

    #     ### **Fitur Keamanan:**
    #     1. Password di-hash menggunakan SHA-256
    #     2. Limit 3 percobaan login
    #     3. Lockout 5 menit setelah 3 percobaan gagal
        
    #     ### **Jika lupa password:**
    #     Hubungi administrator sistem untuk reset password.
    #     """)
    
    # Add CSS for login page
    st.markdown("""
    <style>
    .login-card {
        background: white;
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border: 2px solid #e5e7eb;
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)