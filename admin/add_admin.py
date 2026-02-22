# admin/add_admin.py
from os import name
import streamlit as st
import hashlib
import mysql.connector
import pandas as pd

from utils.generator_id import generate_id

# ===============================
# DB CONNECTION
# ===============================

def get_connection():
    """Membuat koneksi ke database MySQL (Aiven)"""
    try:
        connection = mysql.connector.connect(
                host=st.secrets["mysql"]["host"],
                port=st.secrets["mysql"]["port"],
                database=st.secrets["mysql"]["database"],
                user=st.secrets["mysql"]["user"],
                password=st.secrets["mysql"]["password"],
                ssl_ca=st.secrets["mysql"]["ssl_ca"],
                ssl_verify_cert=True,
                use_pure=True,
                connection_timeout=5
            )
        return connection
    except Exception as e:
            print(f"❌ Database connection error: {e}")
            connection = None
            return None
    
# ===============================
# MAIN PAGE
# ===============================
def show_add_admin_page():
    st.markdown("""
    <div class="hero-box">
        <h1 class="main-title">👤 Manajemen Admin</h1>
        <p class="subtitle">Kelola akun admin dan keamanan sistem.</p>
    </div>
    <hr style="height:3px; background-color:#f1f3f5; border:none;" />
    """, unsafe_allow_html=True)

    if not st.session_state.get("admin_logged_in"):
        st.error("⚠️ Harap login sebagai admin")
        return

    tab1, tab2 = st.tabs(["➕ Tambah Admin", "📋 Data Admin"])

    # ===============================
    # TAB 1 – ADD ADMIN
    # ===============================
    with tab1:
        with st.form("add_admin_form"):
            st.subheader("➕ Tambah Admin Baru")

            name = st.text_input("Nama Lengkap")
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["Admin", "Super Admin"])

            submit = st.form_submit_button("Tambah Admin", type="primary")

        if submit:
            if len(username) < 3 or len(password) < 8:
                st.error("Username min 3 karakter & password min 8 karakter")
            else:
                add_admin(name, username, email, password, role)

    # ===============================
    # TAB 2 – ADMIN TABLE
    # ===============================
    with tab2:
        st.subheader("📋 Data Admin Terdaftar")

        df = get_admins_with_status()

        if df.empty:
            st.info("Belum ada admin terdaftar.")
            return

        # Tampilkan dataframe dengan kolom status
        st.dataframe(
            df[['id', 'name', 'username', 'email', 'role', 'status', 'last_login', 'last_logout']], 
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": "🆔 ID",
                "name": "👤 Nama",
                "username": "🔑 Username",
                "email": "📧 Email",
                "role": "👔 Role",
                "status": st.column_config.TextColumn(
                    "📊 Status",
                    help="Online: Sedang aktif, Offline: Tidak aktif"
                ),
                "last_login": "⏰ Login Terakhir",
                "last_logout": "⏰ Logout Terakhir"
            }
        )

        st.markdown("---")
        st.subheader("🔐 Ubah Password Admin")

        selected_admin = st.selectbox(
            "Pilih Admin",
            df["username"]
        )

        new_password = st.text_input(
            "Password Baru",
            type="password",
            placeholder="Minimal 8 karakter"
        )

        if st.button("Update Password"):
            if len(new_password) < 8:
                st.error("Password minimal 8 karakter")
            else:
                update_password(selected_admin, new_password)


# ===============================
# DATABASE FUNCTIONS
# ===============================
def add_admin(name, username, email, password, role):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        admin_id = generate_id(cursor, "admin", "id", "ADM")

        cursor.execute("""
        INSERT INTO admin (id, name, username, email, password, role)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (admin_id, name, username, email, hashed_pw, role))

        conn.commit()
        st.success(f"✅ Admin {username} berhasil ditambahkan")
        st.rerun()

    except mysql.connector.Error as e:
        if "Duplicate" in str(e):
            st.error("Username sudah digunakan")
        else:
            st.error(e)
    finally:
        cursor.close()
        conn.close()


def get_admins():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM admin ORDER BY id DESC", conn)
    conn.close()
    return df


def get_admins_with_status():
    """Mengambil data admin beserta status online/offline terbaru"""
    conn = get_connection()
    
    query = """
    SELECT 
        a.id,
        a.name,
        a.username,
        a.email,
        a.role,
        a.password,
        CASE 
            WHEN act.status = 'Online' THEN '🟢 Online'
            ELSE '🔴 Offline'
        END as status,
        DATE_FORMAT(act.login_time, '%d-%m-%Y %H:%i') as last_login,
        DATE_FORMAT(act.logout_time, '%d-%m-%Y %H:%i') as last_logout
    FROM admin a
    LEFT JOIN (
        SELECT 
            admin_id,
            status,
            login_time,
            logout_time,
            ROW_NUMBER() OVER (PARTITION BY admin_id ORDER BY login_time DESC) as rn
        FROM admin_activity
    ) act ON a.id = act.admin_id AND act.rn = 1
    ORDER BY 
        CASE WHEN act.status = 'Online' THEN 1 ELSE 2 END,
        a.name ASC
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Isi nilai kosong dengan '-'
    df['last_login'] = df['last_login'].fillna('-')
    df['last_logout'] = df['last_logout'].fillna('-')
    df['status'] = df['status'].fillna('🔴 Offline')
    
    return df


def update_password(username, new_password):
    conn = get_connection()
    cursor = conn.cursor()

    hashed_pw = hashlib.sha256(new_password.encode()).hexdigest()

    cursor.execute("""
    UPDATE admin SET password=%s WHERE username=%s
    """, (hashed_pw, username))

    conn.commit()
    cursor.close()
    conn.close()

    st.success("🔐 Password berhasil diperbarui")