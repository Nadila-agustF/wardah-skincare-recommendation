import streamlit as st
import pandas as pd
from mysql.connector import Error
from utils.db import DatabaseConnection

def show_user_history_page():
    """Display user history and recommendation logs"""
    # Check admin login
    if not st.session_state.get("admin_logged_in"):
        st.error("⚠️ Anda harus login sebagai admin.")
        st.rerun()
        return
    
    st.markdown("""
    <div class="hero-box">
        <h1 class="main-title">📊 Data Pengguna dan Rekomendasi</h1>
        <p class="subtitle">Lihat riwayat pengguna dan log rekomendasi produk Wardah.</p>
    </div>
    <hr style="height:3px; background-color:#f1f3f5; border:none;" />
    """,
    unsafe_allow_html=True)

    st.markdown("### 📈Ringkasan")
    st.markdown("---")

    # ===============================
    # DB CONNECTION
    # ===============================
    db = DatabaseConnection()
    conn = db.connect()

    if conn is None:
        st.error("❌ Gagal terhubung ke database")
        return

    # ===============================
    # QUERY DATA - Menggabungkan 3 tabel
    # ===============================
    query = """
        SELECT 
            u.id            AS user_id,
            u.name          AS Nama,
            u.age           AS Usia,
            u.gender        AS Gender,
            u.skin_type     AS Jenis_Kulit,
            u.created_at    AS Tanggal_Daftar,
            s.id            AS section_id,
            s.category_input AS Kategori_Dipilih,
            s.created_at    AS Tanggal_Rekomendasi,
            i.id            AS item_id,
            i.product_name  AS Produk,
            i.category      AS Kategori_Produk,
            i.similarity_score AS Skor_Similaritas,
            i.rank_no       AS Peringkat,
            i.product_url   AS URL_Produk
        FROM user u
        LEFT JOIN recommendation_section s ON u.id = s.user_id
        LEFT JOIN recommendation_item i ON s.id = i.section_id
        ORDER BY u.created_at DESC, s.created_at DESC, i.rank_no ASC
    """

    try:
        df = pd.read_sql(query, conn)

        if df.empty:
            st.info("📭 Belum ada data history.")
            return

        # ===============================
        # SUMMARY METRIC 
        # ===============================
        # Hitung total pengguna unik
        col1, col2, col3 = st.columns(3)
        with col1:
            total_users = df['user_id'].nunique()
            st.metric("👥 Total Pengguna", total_users)
        
        with col2:
            total_rekomendasi = df['item_id'].count()
            st.metric("🔍 Total Rekomendasi", total_rekomendasi)
        
        with col3:
            kategori_unik = df['Kategori_Produk'].nunique()
            st.metric("🧴 Kategori Unik", kategori_unik)

        st.markdown("---")

        # ===============================
        # TOMBOL EXPORT
        # ===============================
        st.download_button(
                "📥 Export CSV",
                df.to_csv(index=False).encode('utf-8'),
                "history_rekomendasi.csv",
                "text/csv"
            )

        # ===============================
        # DATA UNTUK TABEL UTAMA (per pengguna)
        # ===============================
        users_data = []
        for user_id in df['user_id'].unique():
            user_df = df[df['user_id'] == user_id]
            first_row = user_df.iloc[0]

            users_data.append({
                'user_id': user_id,
                'Nama': first_row['Nama'],
                'Usia': first_row['Usia'],
                'Gender': first_row['Gender'],
                'Jenis Kulit': first_row['Jenis_Kulit'],
                'Tanggal Rekomendasi': pd.to_datetime(first_row['Tanggal_Rekomendasi']).strftime('%Y-%m-%d %H:%M')
            })
        
        users_df = pd.DataFrame(users_data)

        # ===============================
        # TABEL HISTORY
        # ===============================
        st.subheader("📊 Tabel History Pengguna")
        st.dataframe(
            users_df[['Nama', 'Usia', 'Gender', 'Jenis Kulit', 'Tanggal Rekomendasi']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Nama": "👤 Nama",
                "Usia": "🎂 Usia",
                "Gender": "⚥ Gender",
                "Jenis Kulit": "🧴 Jenis Kulit",
                "Tanggal Rekomendasi": "📅 Tanggal Rekomendasi"
            }
        )
        user_options = {
            f"{row['Nama']} ({row['Usia']} th) - ID: {row['user_id']}": row['user_id'] 
            for _, row in users_df.iterrows()
        }
        
        # Tambahkan opsi default
        user_options_list = ["-- Pilih Pengguna --"] + list(user_options.keys())
        
        # Tampilkan selectbox
        selected_option = st.selectbox(
            "Pilih Pengguna untuk Melihat Detail Rekomendasi",
            options=user_options_list,
            index=0,
            key="user_selectbox"
        )

        st.markdown("---")

        # ===============================
        # DETAIL REKOMENDASI (TABEL KEDUA)
        # ===============================
        if selected_option != "-- Pilih Pengguna --":
            selected_user_id = user_options[selected_option]
            selected_user_df = users_df[users_df['user_id'] == selected_user_id]

            if not selected_user_df.empty:
                selected_user_data = selected_user_df.iloc[0]
                st.subheader(f"📦 Detail Rekomendasi: {selected_user_data['Nama']}")

                # Mengambil semua rekomendasi user
                user_detail_df = df[df['user_id'] == selected_user_id].copy()

                if not user_detail_df.empty:
                    # Urutkan berdasarkan peringkat
                    user_detail_df = user_detail_df.sort_values("Peringkat")

                    # Ambil kolom yang dibutuhkan
                    detail_table = user_detail_df[
                        ['Peringkat', 'Produk', 'Kategori_Produk', 'Skor_Similaritas']
                    ].copy()

                    detail_table.columns = [
                        '🏆 Peringkat',
                        '📦 Nama Produk',
                        '📌 Kategori',
                        '📊 Score'
                    ]

                    # Tampilkan tabel detail
                    st.dataframe(
                        detail_table,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("Tidak ada rekomendasi untuk user ini.")

    except Error as e:
        st.error(f"❌ Error: {e}")

    finally:
        if conn:
            conn.close()