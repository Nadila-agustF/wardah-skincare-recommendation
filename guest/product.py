# pages/product.py
import streamlit as st
import pandas as pd
from utils.helper import load_and_merge_data, get_product_image


# ===============================
# LOAD DATA
# ===============================
@st.cache_data
def get_products_data():
    """Load products data with fallback"""
    try:
        df = load_and_merge_data()
        if df.empty:
            # Fallback dummy data
            return create_sample_data()
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return create_sample_data()

def create_sample_data():
    """Create sample data if CSV not found"""
    dummy_data = {
        'name': [
            'Wardah Brightening Serum', 
            'Wardah Hydrating Moisturizer', 
            'Wardah UV Shield Sunscreen',
            'Wardah Gentle Cleanser',
            'Wardah Balancing Toner',
            'Wardah Acne Solution',
            'Wardah Anti-Aging Cream',
            'Wardah Night Repair'
        ],
        'skin_type': [
            ['oily', 'combination'],
            ['dry', 'normal'],
            ['all skin types'],
            ['sensitive', 'normal'],
            ['combination', 'oily'],
            ['oily', 'acne-prone'],
            ['dry', 'mature'],
            ['all skin types']
        ],
        'category': [
            ['serum'],
            ['moisturizer'],
            ['sunscreen'],
            ['cleanser'],
            ['toner'],
            ['treatment'],
            ['cream'],
            ['night cream']
        ],
        'about': [
            'Serum pencerah dengan Vitamin C',
            'Pelembab hydrating dengan Hyaluronic Acid',
            'Sunscreen protection SPF 50',
            'Pembersih wajah gentle',
            'Toner untuk menyeimbangkan pH',
            'Perawatan untuk kulit berjerawat',
            'Krim anti penuaan',
            'Krim malam untuk perbaikan kulit'
        ],
        'ingredients': [''] * 8,
        'url': [''] * 8,
        'image_url': [''] * 8
    }
    
    return pd.DataFrame(dummy_data)

# ===============================
# UI COMPONENTS
# ===============================
def display_product_card_simple(product):
    """Display simplified product card"""
    with st.container():
        st.markdown('<div class="product-card">', unsafe_allow_html=True)
        
        # Product name
        product_name = product.get('name', 'Produk tanpa nama')
        st.markdown(
            f'<h3 style="color: #2c3e50; margin-bottom: 10px; font-size: 1.1rem;">{product_name}</h3>', 
            unsafe_allow_html=True
        )
        
        # Image or placeholder
        try:
            img_url = product.get('image_url', '')
            if img_url and str(img_url).strip() not in ["", "nan"]:
                img = get_product_image(img_url, product_name)
                if img:
                    st.image(img, use_container_width=True)
                else:
                    show_image_placeholder()
            else:
                show_image_placeholder()
        except:
            show_image_placeholder()
        
        # Tags
        col1, col2 = st.columns(2)
        
        with col1:
            if product.get('category'):
                categories = product['category'][:2] if isinstance(product['category'], list) else []
                for cat in categories:
                    st.markdown(
                        f'<span style="background: #e3f2fd; color: #1565c0; padding: 4px 8px; border-radius: 10px; font-size: 0.8rem; margin-right: 5px;">{cat}</span>', 
                        unsafe_allow_html=True
                    )
        
        with col2:
            if product.get('skin_type'):
                skin_types = product['skin_type'][:2] if isinstance(product['skin_type'], list) else []
                for skin in skin_types:
                    st.markdown(
                        f'<span style="background: #f3e5f5; color: #7b1fa2; padding: 4px 8px; border-radius: 10px; font-size: 0.8rem; margin-right: 5px;">{skin}</span>', 
                        unsafe_allow_html=True
                    )
        
        # Quick info
        with st.expander("📝 Info", expanded=False):
            if product.get('about'):
                about = product['about']
                st.write(about[:100] + "..." if len(about) > 100 else about)
        
        st.markdown('</div>', unsafe_allow_html=True)


def show_image_placeholder():
    """Show image placeholder"""
    st.markdown("""
    <div class="product-image-placeholder">
        🧴<br>
        <small>No Image</small>
    </div>
    """, unsafe_allow_html=True)


# ===============================
# MAIN FUNCTION
# ===============================
def show_produk():
    """Main function for products page"""
    
    # Load data
    df = get_products_data()
    
    # Header
    st.markdown("""
    <div class="hero-box">
        <h1 class="main-title">📋 Katalog Produk Wardah</h1>
        <p class="subtitle">
            Jelajahi semua produk skincare Wardah sesuai kebutuhan Anda
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar filters
    with st.sidebar:
        st.markdown("### 🔍 Filter Produk")
        
        # Search
        search_query = st.text_input("Cari produk...", placeholder="Nama produk...")
        
        # Get unique categories
        try:
            all_categories = sorted({c for sub in df["category"] for c in sub if isinstance(sub, list)})
        except:
            all_categories = ["serum", "moisturizer", "sunscreen", "cleanser", "toner"]
        
        # Category filter
        selected_categories = st.multiselect(
            "🏷️ Kategori",
            all_categories,
            default=all_categories[:min(3, len(all_categories))]
        )
        
        # Sort options
        sort_options = ["Nama A-Z", "Nama Z-A", "Kategori"]
        sort_by = st.selectbox("📊 Urutkan", sort_options)
        
        # Reset button
        if st.button("🔄 Reset Filter", use_container_width=True):
            st.rerun()
    
    # Apply filters
    filtered_df = df.copy()
    
    # Search filter
    if search_query:
        filtered_df = filtered_df[filtered_df['name'].str.contains(search_query, case=False, na=False)]
    
    # Category filter
    if selected_categories:
        filtered_df = filtered_df[filtered_df['category'].apply(
            lambda x: any(cat in x for cat in selected_categories) if isinstance(x, list) else False
        )]
    
    # Sort data
    if sort_by == "Nama A-Z":
        filtered_df = filtered_df.sort_values('name')
    elif sort_by == "Nama Z-A":
        filtered_df = filtered_df.sort_values('name', ascending=False)
    elif sort_by == "Kategori":
        filtered_df['first_category'] = filtered_df['category'].apply(
            lambda x: x[0] if isinstance(x, list) and x else ''
        )
        filtered_df = filtered_df.sort_values('first_category')
    
    # Display stats
    total_products = len(filtered_df)
    
    if total_products == 0:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">😔</div>
            <h3>Tidak ada produk ditemukan</h3>
            <p>Coba ubah filter pencarian Anda</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Stats row
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{total_products}</div>
            <div class="stat-label">Total Produk</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        cat_count = len(selected_categories) if selected_categories else len(all_categories)
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{cat_count}</div>
            <div class="stat-label">Kategori</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Products per page
    products_per_page = st.select_slider(
        "Tampilkan per halaman:",
        options=[6, 12, 18, 24],
        value=12
    )
    
    # Simple pagination
    total_pages = max(1, (total_products + products_per_page - 1) // products_per_page)
    
    # Page selector
    cols = st.columns([1, 2, 1])
    with cols[1]:
        page_number = st.number_input(
            "Halaman",
            min_value=1,
            max_value=total_pages,
            value=1,
            key="product_page"
        )
    
    # Calculate indices
    start_idx = (page_number - 1) * products_per_page
    end_idx = min(start_idx + products_per_page, total_products)
    
    # Page info
    st.markdown(f"""
    <div class="pagination-control">
        <div class="page-info">
            Menampilkan produk {start_idx + 1}-{end_idx} dari {total_products}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display products grid
    current_products = filtered_df.iloc[start_idx:end_idx]
    
    # Use columns for grid layout
    cols_per_row = 3
    rows = [current_products[i:i+cols_per_row] for i in range(0, len(current_products), cols_per_row)]
    
    for row_products in rows:
        cols = st.columns(cols_per_row)
        for col_idx, (_, product) in zip(range(cols_per_row), row_products.iterrows()):
            with cols[col_idx]:
                display_product_card_simple(product)


# ===============================
# PAGE ENTRY POINT
# ===============================
def show_products_page():
    """Main entry point for products page"""
    show_produk()

if __name__ == "__main__":
    show_products_page()