from datetime import datetime
import json
import streamlit as st
import pandas as pd
from mysql.connector import Error
from utils.generator_id import generate_id
from utils.recommender import SkincareRecommender
from utils.helper import load_and_merge_data, get_product_image, get_local_fallback_image
from utils.db import DatabaseConnection


# ===============================
# LOAD DATA
# ===============================
@st.cache_data
def load_data():
    try:
        df = load_and_merge_data()
        if df.empty:
            return pd.DataFrame()
        return df
    except Exception as e:
        st.error(f"❌ Error memuat data: {e}")
        return pd.DataFrame()


df = load_data()


# ===============================
# INIT RECOMMENDER
# ===============================
@st.cache_resource
def init_recommender(data):
    try:
        return SkincareRecommender(data)
    except Exception as e:
        st.error(f"❌ Recommender error: {e}")
        return None


recommender = init_recommender(df)


# ===============================
# HALAMAN REKOMENDASI
# ===============================
def show_rekomendasi():
    st.markdown("""
    <div class="hero-box">
        <h1 class="main-title">🔍 Rekomendasi Produk Skincare Wardah</h1>
        <p class="subtitle">
            Temukan produk yang sesuai dengan kebutuhan kulit Anda
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ===============================
    # FORM INPUT
    # ===============================
    with st.container():
        st.markdown('<div class="form-section">', unsafe_allow_html=True)
        user_name = st.text_input("Nama Lengkap", "Guest")
        user_age = st.number_input("Usia", 10, 80, 25)
        gender = st.selectbox("Jenis Kelamin", ["Perempuan", "Laki-laki"])

    # ===============================
    # OPTIONS (FIXED)
    # ===============================
    # Extract options from data
    skin_type_options = sorted({s for sub in df["skin_type"] for s in sub})
    category_options = sorted({c for sub in df["category"] for c in sub})
    
    col1, col2 = st.columns(2)
    with col1:
        selected_skin_type = st.multiselect(
            "Jenis Kulit",
            skin_type_options,
            default=["all skin types"] if "all skin types" in skin_type_options else skin_type_options[:1]
        )

        skin_info = {
            "normal": "Kulit seimbang",
            "oily": "Kulit berminyak",
            "dry": "Kulit kering",
            "sensitive": "Kulit sensitif",
            "combination": "Kulit kombinasi",
            "all skin types": "Cocok untuk semua jenis kulit"
        }

        info_texts = []
        for s in selected_skin_type:
            key = s.lower().strip()
            if key in skin_info:
                info_texts.append(f"{s.title()}: {skin_info[key]}")

        if info_texts:
            st.info(" | ".join(info_texts))

    with col2:
        selected_category = st.multiselect(
            "Kategori Produk",
            category_options,
            default=["serum"] if "serum" in category_options else category_options[:1]
        )

        category_info = {
            "serum": "Konsentrat bahan aktif",
            "moisturizer": "Pelembab",
            "cleanser": "Pembersih wajah",
            "sunscreen": "Pelindung wajah dari UV",
            "toner": "Penyegar wajah"
        }

        info_texts = []
        for c in selected_category:
            key = c.lower().strip()
            if key in category_info:
                info_texts.append(f"{c.title()}: {category_info[key]}")

        if info_texts:
            st.info(" | ".join(info_texts))
    st.markdown('</div>', unsafe_allow_html=True)

    top_n = st.slider("Jumlah Rekomendasi", 3, 12, 6)
    use_fallback = st.checkbox("Gunakan gambar default", True)

    search_clicked = st.button("🔍 Cari Rekomendasi", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ===============================
    # VALIDASI & REKOMENDASI
    # ===============================
    if search_clicked:

        if recommender is None:
            st.error("❌ Sistem rekomendasi belum siap")
            return

        if not selected_category:
            st.error("⚠️ Pilih minimal satu kategori produk")
            return

        with st.spinner("Mencari rekomendasi terbaik..."):
            recs = recommender.recommend(
                selected_skin_type,
                selected_category,
                top_n
            )

        if recs.empty:
            st.warning("❌ Tidak ditemukan produk yang sesuai")
            return

        # ===============================
        # SIMPAN KE DATABASE (FINAL & BENAR)
        # ===============================
        conn = None
        try:
            conn = DatabaseConnection()
            connection = conn.connect()

            if connection is None:  # Cek apakah connect berhasil
                st.error("❌ Gagal terhubung ke database")
                return
            cursor = conn.cursor()

            # ================= USER =================
            user_id = generate_id(cursor, "user", "id", "USR")

            cursor.execute("""
                INSERT INTO user (id, name, age, gender, skin_type, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                user_name,
                user_age,
                gender,
                ",".join(selected_skin_type),
                datetime.now()
            ))

            # ================= SECTION =================
            section_id = generate_id(cursor, "recommendation_section", "id", "SEC")

            cursor.execute("""
                INSERT INTO recommendation_section (id, user_id, category_input, created_at)
                VALUES (%s, %s, %s, %s)
            """, (
                section_id,
                user_id,
                json.dumps(selected_category),
                datetime.now()
            ))

            # ================= ITEMS =================
            max_recommendations = 3
            for i in range(min(max_recommendations, len(recs))):
                item_id = generate_id(cursor, "recommendation_item", "id", "RCI")

                # ---- FIX CATEGORY ----
                row = recs.iloc[i]
                category_val = row.get("category")

                if isinstance(category_val, list):
                    category_val = category_val[0] if category_val else None

                if category_val is not None:
                    category_val = str(category_val)

                # ---- FIX URL ----
                product_url = row.get("product_url") or row.get("url")

                # ---- FIX SIMILARITY ----
                similarity_score = row.get("similarity_score")
                if similarity_score is not None:
                    similarity_score = float(similarity_score)

                cursor.execute("""
                    INSERT INTO recommendation_item
                    (id, section_id, product_name, category, similarity_score, rank_no, product_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    item_id,
                    section_id,
                    row.get('product_name') or row.get('name'),
                    category_val,
                    similarity_score,
                    i+1,
                    product_url
                ))

            conn.commit()
            st.success("✅ Rekomendasi berhasil disimpan ke database")

        except Exception as e:
            st.warning(f"Database error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            if conn:
                conn.close()


        # ===============================
        # DISPLAY PRODUK
        # ===============================
        if search_clicked:
            if not selected_skin_type or not selected_category:
                st.warning("⚠️ Silakan pilih minimal 1 jenis kulit dan 1 kategori.")
            else:
                # Results header
                st.markdown(f'''
                <div class="result-header">
                    <h2 class="result-title">✨ Rekomendasi Personal untuk Anda</h2>
                    <p class="result-subtitle">
                        👤 {user_name} • 📅 {user_age} tahun<br>
                        🧬 {', '.join(selected_skin_type)} • 📦 {', '.join(selected_category)}
                    </p>
                </div>
                ''', unsafe_allow_html=True)
                cols_per_row = 3
                rows = [recs[i:i + cols_per_row] for i in range(0, len(recs), cols_per_row)]
                for recs in rows:
                    cols = st.columns(cols_per_row)
                    for col_idx, (_, product) in zip(range(cols_per_row), recs.iterrows()):
                        with cols[col_idx]:
                            # Product Card
                            st.markdown('<div class="product-card">', unsafe_allow_html=True)
                            # Header dengan nama produk
                            st.markdown(f'<div class="product-name">{product["name"]}</div>', unsafe_allow_html=True)

                            img = None
                            # img_source = "original"
                            if pd.notna(product.get("image_url")):
                                img = get_product_image(product["image_url"], product["name"])

                            if not img and use_fallback:
                                if product["category"]:
                                    img = get_local_fallback_image(product["category"][0])

                    # Tampilkan gambar
                            if img:
                                st.image(img, use_container_width=True)
                                # badge_class = "badge-success" if img_source == "original" else "badge-info"
                                # badge_text = "Gambar produk" if img_source == "original" else "Gambar ilustrasi"
                                # st.markdown(f'<span class="image-badge {badge_class}">{badge_text}</span>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'''
                                <div class="image-wrapper">
                                    <div class="placeholder-text">
                                        📸<br>
                                            <small>Gambar tidak tersedia</small>
                                        </div>
                                    </div>
                                        ''', unsafe_allow_html=True)
                                st.markdown(f'<span class="image-badge badge-warning">❌ Tanpa gambar</span>', unsafe_allow_html=True)
                                    
                            # Metadata dalam satu baris
                            st.markdown('<div class="meta-row">', unsafe_allow_html=True)
                                    
                            tags_html = '<div class="tag-container">'
                            # Categories
                            if product['category']:
                                for cat in product['category'][:2]:
                                    tags_html += f'<span class="category-tag">{cat.title()}</span>'

                            # Skin types
                            if product['skin_type']:
                                for skin in product['skin_type'][:2]:
                                    tags_html += f'<span class="skin-tag">{skin.title()}</span>'

                            tags_html += '</div>'
                            st.markdown(tags_html, unsafe_allow_html=True)

                            # About Product (collapsible)
                            with st.expander("📝 **About**", expanded=False):
                                about_text = product["about"][:300] + "..." if len(product["about"]) > 300 else product["about"]
                                st.markdown(f'<div class="expand-content">{about_text}</div>', unsafe_allow_html=True)
                                    
                            # Ingredients (collapsible)
                            with st.expander("🧪 **Ingredients**", expanded=False):
                                ingredients_text = product["ingredients"][:250] + "..." if len(product["ingredients"]) > 250 else product["ingredients"]
                                st.markdown(f'<div class="expand-content">{ingredients_text}</div>', unsafe_allow_html=True)
                                    
                            # Product Link Button
                            st.markdown(f'''
                            <a href="{product['url']}" target="_blank" class="btn-product-link">
                                🔗 Lihat Produk Lengkap
                            </a>
                            ''', unsafe_allow_html=True)
                                    
                            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
     <div style="text-align: center; color: #666; padding: 20px; font-size: 14px;">
        <p>🧴 <strong>Wardah Skincare Recommendation System</strong></p>
        <p>Content-Based Filtering using TF-IDF + Cosine Similarity</p>
    </div>
    """, unsafe_allow_html=True)

