# admin/dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from mysql.connector import Error
import random
from utils.db import DatabaseConnection
    
def show_admin_dashboard():
    """Display admin dashboard with analytics"""
    st.markdown("""
    <div class="hero-box">
        <h1 class="main-title">📊 Dashboard Admin Sistem Rekomendasi</h1>
        <p class="subtitle">
            Selamat datang, <strong>{}</strong>!
        </p>
    </div>
    <hr style="height:3px; background-color:#f1f3f5; border:none;" />
    """.format(st.session_state.get('admin_username', 'Admin')),
    unsafe_allow_html=True)
    
    # Check if user is logged in as admin
    if not st.session_state.get('admin_logged_in'):
        st.error("⚠️ Anda harus login sebagai admin untuk mengakses dashboard.")
        st.session_state['current_page'] = 'admin_login'
        st.rerun()
        return
    
    db = DatabaseConnection()
    conn = db.connect()

    if conn is None:
        st.error("❌ Gagal terhubung ke database. Silakan coba lagi nanti.")
        return
    
    # Quick stats row
    st.markdown("### 📈 Ringkasan Statistik")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_users = get_total_users(conn)
        st.metric(
            "👥 Total Pengguna", 
            f"{total_users:,}"
        )
    
    with col2:
        total_recommendations = get_total_recommendations(conn)
        st.metric(
            "🔍 Rekomendasi", 
            f"{total_recommendations:,}"
        )
    
    with col3:
        products_viewed = random.randint(12000, 15000)
        st.metric(
            "👁️ Produk Dilihat", 
            f"{products_viewed:,}",
            f"+{random.randint(50, 200)} hari ini"
        )
    
    # Charts section
    st.markdown("---")
    st.markdown("### 📊 Analytics")
    
    tab1, tab2, tab3 = st.tabs(["📈 Aktivitas Pengguna", "🏷️ Kategori Populer", "🧬 Jenis Kulit"])
    
    with tab1:
        # User activity chart
        st.markdown("#### Aktivitas Harian (7 Hari Terakhir)")
        user_activity_data = get_user_activity_data(conn)
        
        fig1 = go.Figure(data=[
            go.Scatter(
            name='Aktivitas Pengguna',
            x=user_activity_data['date'],
            y=user_activity_data['activity_count'].astype(int),
            mode='lines+markers',
            line=dict(color='#3b82f6')
            )
        ])
        
        fig1.update_layout(
            height=400,
            xaxis_title="Tanggal",
            yaxis_title="Jumlah aktivitas",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig1, use_container_width=True, key="user_activity_chart")
    
    with tab2:
        # Popular categories chart
        st.markdown("#### Distribusi Kategori Produk")
        categories_data = get_popular_categories(conn)
        
        fig2 = px.pie(
            categories_data, 
            values='count', 
            names='category',
            hole=0.3,
            color_discrete_sequence=px.colors.sequential.Blues_r
        )
        
        fig2.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hoverinfo='label+percent+value'
        )
        
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True, key="popular_categories_pie")
        
        # Category details table
        with st.expander("📋 Detail Kategori", expanded=False):
            categories_data['persentase'] = (categories_data['count'] / categories_data['count'].sum() * 100).round(1)
            st.dataframe(
                categories_data.sort_values('count', ascending=False),
                use_container_width=True,
                hide_index=True
            )
    
    with tab3:
        # Skin type distribution
        st.markdown("#### Distribusi Jenis Kulit Pengguna")
        skin_type_data = get_skin_type_data(conn)
        
        fig3 = px.bar(
            skin_type_data,
            x='skin_type',
            y='count',
            color='count',
            color_continuous_scale='blues',
            text='count'
        )
        
        fig3.update_layout(
            height=400,
            xaxis_title="Jenis Kulit",
            yaxis_title="Jumlah Pengguna",
            coloraxis_showscale=False
        )
        
        fig3.update_traces(texttemplate='%{text:,}', textposition='outside')
        st.plotly_chart(fig3, use_container_width=True, key="skin_type_bar")
    
    # =========================
    # Recent activity section
    # =========================
    st.markdown("---")
    st.markdown("### 📋 Aktivitas Database")

    # Init session state
    if "db_test_result" not in st.session_state:
        st.session_state.db_test_result = None

    # Test connection button
    if st.button("🔗 Test Database Connection", type="secondary"):
        with st.spinner("🔍 Testing connection to MySQL..."):
            st.session_state.db_test_result = test_database_connection()

    # Tampilkan hasil test
    if st.session_state.db_test_result:
        success, info = st.session_state.db_test_result

        if success:
            st.success("✅ Database Connected!")

            with st.expander("📊 Database Information", expanded=True):
                st.write(f"**🗄️ Database:** {info['database']}")
                st.write(f"**🧩 MySQL Version:** {info['version']}")
                st.write(f"**👤 Connected as:** {info['user']}")

                st.markdown("**📦 Tables:**")
                if info["tables"]:
                    for table in info["tables"]:
                        st.write(f"- `{table}`")
                else:
                    st.info("Tidak ada tabel ditemukan")

        else:
            st.error("❌ Connection Failed")
            st.code(info.get("error", "Unknown error"))
                
def get_total_users(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user")
    result = cursor.fetchone()[0]
    cursor.close()
    return result

def get_total_recommendations(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM recommendation_item")
    result = cursor.fetchone()[0]
    cursor.close()
    return result

def get_user_activity_data(conn):
    """Generate sample user activity data"""
    query = """
        SELECT DATE(created_at) as date,
               COUNT(*) as activity_count
        FROM user
        WHERE created_at >= CURDATE() - INTERVAL 6 DAY
        GROUP BY DATE(created_at)
        ORDER BY date
    """
    df = pd.read_sql(query, conn)          
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%d/%m') 
    df['activity_count'] = df['activity_count'].astype(int)
    return df

def get_popular_categories(conn):
    query = """
        select category, COUNT(*) as count
        from recommendation_item
        GROUP BY category
        ORDER BY count DESC
    """
    return pd.read_sql(query, conn)

def get_skin_type_data(conn):
    query = """
        SELECT skin_type, COUNT(*) as count
        FROM user
        GROUP BY skin_type
        ORDER BY count DESC
    """
    return pd.read_sql(query, conn)

def test_database_connection():
    """Test koneksi database dan ambil metadata"""
    try:
        db = DatabaseConnection()
        conn = db.connect()

        if not conn or not conn.is_connected():
            return False, {"error": "Koneksi database gagal"}

        cursor = conn.cursor()

        cursor.execute("SELECT DATABASE()")
        database = cursor.fetchone()[0]

        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]

        cursor.execute("SHOW TABLES")
        tables = [t[0] for t in cursor.fetchall()]

        cursor.execute("SELECT USER()")
        user = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return True, {
            "database": database,
            "version": version,
            "tables": tables,
            "user": user
        }

    except Error as e:
        return False, {"error": str(e)}
    
print()