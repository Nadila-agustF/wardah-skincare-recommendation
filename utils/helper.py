import ast
import pandas as pd
import numpy as np
import streamlit as st
import requests
from io import BytesIO
from PIL import Image
from pathlib import Path
import json
import re

def load_and_merge_data():
    try:
        skincare_path = Path("data/wardah_skincare_clean.csv")
        images_path = Path("data/wardah_product_images.csv")

        if not skincare_path.exists():
            st.error(f"❌ File tidak ditemukan: {skincare_path}")
            return pd.DataFrame()

        df_skincare = pd.read_csv(skincare_path)
        # Cleaning category
        if 'category' in df_skincare.columns:
            df_skincare['category'] = df_skincare['category'].apply(
                lambda x: [c.strip().lower() for c in ast.literal_eval(x)]
                if isinstance(x, str) and x.startswith('[')
                else []
            )

        # Cleaning skin_type
        if 'skin_type' in df_skincare.columns:
            df_skincare['skin_type'] = df_skincare['skin_type'].apply(
                lambda x: [s.strip().lower() for s in ast.literal_eval(x)]
                if isinstance(x, str) and x.startswith('[')
                else []
            )

        # combined_text (WAJIB untuk TF-IDF)
        df_skincare['combined_text'] = (
            df_skincare['name'].fillna('') + ' ' +
            df_skincare['about'].fillna('') + ' ' +
            df_skincare['ingredients'].fillna('')
        )

        # ==== IMAGE MERGE ====
        if images_path.exists():
            df_images = pd.read_csv(images_path)

            df_skincare['name_clean'] = df_skincare['name'].str.lower().str.strip()
            df_images['name_clean'] = df_images['name'].str.lower().str.strip()

            df = df_skincare.merge(
                df_images[['name_clean', 'image_url']],
                left_on='name_clean',
                right_on='name_clean',
                how='left',
                suffixes=('', '_img')
            )

            df['image_url'] = df['image_url'].fillna('')
        else:
            df = df_skincare.copy()
            df['image_url'] = ''
        return df

    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return pd.DataFrame()


def get_product_image(image_url, product_name="", max_retries=2):
    """
    Load product image from URL or local cache
    
    Parameters:
    - image_url: URL of the image
    - product_name: Name of product (for caching)
    - max_retries: Maximum number of retry attempts
    
    Returns:
    - PIL Image object or None
    """
    # If no image URL, return None
    if not image_url or pd.isna(image_url) or str(image_url).strip() in ["", "nan", "None"]:
        return None
    
    try:
        # Clean URL
        image_url = str(image_url).strip()
        
        # Check if URL is valid
        if not (image_url.startswith('http://') or image_url.startswith('https://')):
            # Try to load from local path
            try:
                image_path = Path(image_url)
                if image_path.exists():
                    return Image.open(image_path)
                else:
                    return None
            except:
                return None
        
        # Try to get from URL with retries
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.get(image_url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Check if response is actually an image
                if 'image' in response.headers.get('content-type', ''):
                    img = Image.open(BytesIO(response.content))
                    
                    # Resize if too large
                    max_size = (400, 400)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    return img
                else:
                    return None
                    
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    return None
                continue
                
    except Exception as e:
        # Silently fail for image loading errors
        return None
    
    return None

def get_local_fallback_image(category):
    """
    Get fallback image based on category
    
    Parameters:
    - category: Product category
    
    Returns:
    - PIL Image object or None
    """
    try:
        # Map categories to image files
        category_map = {
            'serum': 'serum.webp',
            'cleanser': 'cleanser.png',
            'face wash': 'facial.png',
            'moisturizer': 'moisturizer.webp',
            'sunscreen': 'sunscreen.webp',
            'mask': 'facemask.webp',
            'toner': 'toner.png',
            'eye cream': 'eyecream.webp',
            'scrub': 'scrub.png',
            'micellar water': 'micellar.webp',
        }
        
        # Clean category name
        category_lower = str(category).strip().lower()
        
        # Find matching category
        for cat_key, filename in category_map.items():
            if cat_key in category_lower or category_lower in cat_key:
                # Try to load image
                current_dir = Path(__file__).parent
                project_root = current_dir.parent
                assets_dir = project_root / "assets"
                
                image_path = assets_dir / filename
                
                if image_path.exists():
                    img = Image.open(image_path)
                    # Resize if needed
                    max_size = (300, 300)
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    return img
        
        # Default fallback image
        default_path = project_root / "assets" / "default_product.png"
        if default_path.exists():
            img = Image.open(default_path)
            max_size = (300, 300)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            return img
        
        return None
        
    except Exception as e:
        return None

def clean_text(text):
    """
    Clean and preprocess text data
    """
    if pd.isna(text):
        return ""
    
    text = str(text)
    # Remove extra whitespace, newlines, etc.
    text = ' '.join(text.split())
    return text.lower().strip()

def extract_keywords(text, max_words=10):
    """
    Extract keywords from text
    """
    if not text:
        return []
    
    # Simple keyword extraction (can be enhanced)
    words = text.split()
    # Remove common stopwords
    stopwords = {'dan', 'yang', 'untuk', 'dengan', 'pada', 'oleh', 'dari'}
    keywords = [word for word in words if word not in stopwords and len(word) > 2]
    
    return keywords[:max_words]

def format_product_card_data(product):
    """
    Format product data for display in cards
    """
    if isinstance(product, pd.Series):
        product = product.to_dict()
    
    formatted = {
        'name': product.get('name', 'Produk tanpa nama'),
        'category': product.get('category', []),
        'skin_type': product.get('skin_type', []),
        'about': product.get('about', 'Tidak ada deskripsi'),
        'ingredients': product.get('ingredients', 'Tidak ada informasi komposisi'),
        'url': product.get('url', '#'),
        'image_url': product.get('image_url', '')
    }
    
    return formatted

def save_to_cache(key, data, cache_dir="cache"):
    """
    Save data to cache directory
    """
    try:
        current_dir = Path(__file__).parent
        cache_path = current_dir / cache_dir
        cache_path.mkdir(exist_ok=True)
        
        cache_file = cache_path / f"{key}.json"
        
        if isinstance(data, pd.DataFrame):
            data = data.to_dict(orient='records')
        elif isinstance(data, np.ndarray):
            data = data.tolist()
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return True
    except Exception as e:
        return False

def load_from_cache(key, cache_dir="cache"):
    """
    Load data from cache directory
    """
    try:
        current_dir = Path(__file__).parent
        cache_path = current_dir / cache_dir
        cache_file = cache_path / f"{key}.json"
        
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        else:
            return None
    except:
        return None

def clear_cache(cache_dir="cache"):
    """
    Clear all cache files
    """
    try:
        current_dir = Path(__file__).parent
        cache_path = current_dir / cache_dir
        
        if cache_path.exists():
            for file in cache_path.glob("*.json"):
                file.unlink()
            return True
    except:
        return False

def validate_user_input(user_data):
    """
    Validate user input data
    """
    errors = []
    
    # Check name
    if not user_data.get('name', '').strip():
        errors.append("Nama tidak boleh kosong")
    
    # Check age
    age = user_data.get('age', 0)
    if age < 10 or age > 80:
        errors.append("Usia harus antara 10-80 tahun")
    
    # Check skin type
    skin_types = user_data.get('skin_type', [])
    if not skin_types:
        errors.append("Pilih minimal satu jenis kulit")
    
    # Check category
    categories = user_data.get('category', [])
    if not categories:
        errors.append("Pilih minimal satu kategori produk")
    
    return errors

def calculate_similarity_score(text1, text2):
    """
    Calculate simple text similarity score (0-1)
    """
    if not text1 or not text2:
        return 0
    
    # Convert to sets of words
    words1 = set(str(text1).lower().split())
    words2 = set(str(text2).lower().split())
    
    if not words1 or not words2:
        return 0
    
    # Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    if union == 0:
        return 0
    
    return intersection / union

def safe_get(dictionary, key, default=None):
    """
    Safely get value from dictionary
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, default)
    elif isinstance(dictionary, pd.Series):
        return dictionary.get(key, default)
    else:
        return default