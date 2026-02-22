# guest/Home.py
import streamlit as st
import sys
from pathlib import Path

# Tambahkan path parent untuk import yang benar
sys.path.append(str(Path(__file__).parent.parent))

def show_guest_home():
    # CSS khusus untuk sidebar dan layout
    st.markdown("""
    <style>  
    
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.header("🧭 Home Page")
        
        # Navigation menggunakan radio button
        selected_page = st.radio(
            "",
            ["🏠 Home", "📋 Produk", "🔍 Rekomendasi"],
            key="guest_nav",
            label_visibility="collapsed"
        )

        st.markdown("---")
        if selected_page != "📋 Produk":
            # Tombol untuk switch ke admin
            if st.button("🔐 Switch to Admin", use_container_width=True):
                # Reset session state untuk guest
                if 'current_page' in st.session_state:
                    del st.session_state.current_page
                
                # Set ke mode admin
                st.session_state.user_mode = 'admin'
                st.session_state.admin_logged_in = False 
                st.rerun()
    
    # Routing berdasarkan pilihan sidebar
    if selected_page == "🏠 Home":
        show_home_content()
    elif selected_page == "📋 Produk":
        try:
            from guest.product import show_produk
            show_produk()
        except ImportError as e:
            st.error(f"Modul produk tidak ditemukan: {e}")
            show_home_content()
    elif selected_page == "🔍 Rekomendasi":
        # Gunakan import yang aman
        try:
            from guest.recommend import show_rekomendasi
            show_rekomendasi()
        except ImportError as e:
            st.error(f"Modul rekomendasi tidak ditemukan: {e}")
            show_home_content()

def show_home_content():
    # Hero section
    st.markdown("""
    <div class="hero-box">
        <h1 class="main-title">🌸 Selamat Datang di Wardah Skincare Recommender</h1>
        <p class="subtitle">Temukan produk Wardah yang sempurna untuk jenis kulit Anda!</p>
    </div>
    <hr style="height:3px; background-color:#f1f3f5;" />
    """, unsafe_allow_html=True)
    
    # Fitur yang tersedia
    st.markdown("""
    <h2 style="text-align: center; color: #2c3e50; margin-top: 1rem;">✨ Fitur yang Tersedia</h2>
    """, unsafe_allow_html=True)
    
    features = [
        {
            "icon": "🔍",
            "title": "Rekomendasi Produk",
            "desc": "Dapatkan rekomendasi produk Wardah berdasarkan jenis kulit dan preferensi Anda"
        },
        {
            "icon": "📋",
            "title": "Daftar Produk Lengkap",
            "desc": "Jelajahi semua produk Wardah dengan filter yang lengkap"
        },
        {
            "icon": "📊",
            "title": "Analisis Produk",
            "desc": "Lihat informasi detail tentang setiap produk termasuk komposisi dan manfaat"
        }
    ]
    
    # Tampilkan fitur dalam 3 kolom
    cols = st.columns(3, gap="large")
    for idx, feature in enumerate(features):
        with cols[idx]:
            st.markdown(f"""
            <div class="feature-card">
                <div class="feature-icon" align="center">{feature['icon']}</div>
                <h4 align="center">{feature['title']}</h4>
                <p align="center" style="color: #666;">{feature['desc']}</p>
            </div>
            """, unsafe_allow_html=True)

    # Category showcase
    st.markdown("---")
    st.markdown("""
    <h2 style="text-align: center; color: #2c3e50; margin-top: 1rem; margin-bottom: 1rem;">📌 Kategori Skincare</h2>
    """, unsafe_allow_html=True)
    
    CATEGORY_MAP = {
        "Serum": "assets/serum.webp",
        "Cleanser": "assets/cleanser.png",
        "Face Wash": "assets/facial.png",
        "Moisturizer": "assets/moisturizer.webp",
        "Sunscreen": "assets/sunscreen.webp",
        "Mask": "assets/facemask.webp",
        "Toner": "assets/toner.png",
        "Eye Cream": "assets/eyecream.webp",
        "Scrub": "assets/scrub.png",
        "Micellar Water": "assets/micellar.webp",
    }
    
    # Display categories in a responsive grid
    cols = st.columns(5)
    for idx, (category, image_path) in enumerate(CATEGORY_MAP.items()):
        with cols[idx % 5]:
            try:
                # Coba load gambar, jika gagal tampilkan placeholder
                st.image(image_path, use_container_width=True)
            except:
                # Fallback jika gambar tidak ditemukan
                st.markdown(f'''
                <div class="image-wrapper">
                    <div class="placeholder-text">
                        📷<br>
                        <small style="font-size: 0.8rem;">{category}</small>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            
            # Nama kategori
            st.markdown(f'<p class="category-name">{category}</p>', unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown('''
        <div style="text-align: center; padding: 40px; background: white; border-radius: 15px; box-shadow: 0 6px 20px rgba(0,0,0,0.08);">
            <h3 style="color: #1e40af; margin-bottom: 20px;">🎯 Mulai Perjalanan Skincare Anda</h3>
            <p style="color: #4b5563; margin-bottom: 25px; line-height: 1.6;">
                Isi profil kulit Anda pada form rekomendasi, pilih kategori produk yang diinginkan, 
                dan temukan rekomendasi produk Wardah yang paling sesuai!
            </p>
            <div style="background: linear-gradient(135deg, #dbeafe, #eff6ff); padding: 20px; border-radius: 10px; border: 2px solid #3b82f6;">
                <p style="color: #1e40af; font-weight: 600; margin: 0;">
                    💡 <strong>Tips:</strong> Pilih semua jenis kulit yang relevan untuk hasil yang lebih akurat
                </p>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px; font-size: 14px;">
        <p>🧴 <strong>Wardah Skincare Recommendation System</strong></p>
        <p>Content-Based Filtering using TF-IDF + Cosine Similarity</p>
    </div>
    """, unsafe_allow_html=True)