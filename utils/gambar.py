import pandas as pd
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

BASE_URL = "https://www.wardahbeauty.com"
START_URL = "https://www.wardahbeauty.com/id/product/list/skincare"


def safe_text(el):
    return el.inner_text().strip() if el else ""


def scrape_wardah():
    results = []
    visited_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("🌐 Membuka halaman utama...")
        page.goto(START_URL, timeout=60000)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(2)

        # =========================
        # AMBIL LINK KATEGORI
        # =========================
        category_links = page.query_selector_all("ul.nav-category li a")
        category_urls = []

        for a in category_links:
            href = a.get_attribute("href")
            if href:
                category_urls.append(
                    href if href.startswith("http") else BASE_URL + href
                )

        category_urls = list(set(category_urls))
        print(f"📂 Total kategori ditemukan: {len(category_urls)}")

        # =========================
        # LOOP SETIAP KATEGORI
        # =========================
        for cat_url in category_urls:
            print(f"\n📁 Kategori: {cat_url}")
            page.goto(cat_url, timeout=60000)
            page.wait_for_load_state("networkidle")
            time.sleep(2)

            product_cards = page.query_selector_all(".item.col-6.col-lg-4")
            print(f"📦 Produk ditemukan: {len(product_cards)}")

            for card in product_cards:
                link_el = card.query_selector("a")
                product_url = link_el.get_attribute("href") if link_el else None
                if not product_url:
                    continue

                product_url = (
                    product_url if product_url.startswith("http")
                    else BASE_URL + product_url
                )

                if product_url in visited_urls:
                    continue

                visited_urls.add(product_url)

                # =========================
                # MASUK KE DETAIL PRODUK
                # =========================
                try:
                    page.goto(product_url, timeout=60000)
                    page.wait_for_load_state("domcontentloaded")
                    time.sleep(2)
                except PlaywrightTimeout:
                    print(f"⏭️ Skip timeout: {product_url}")
                    continue

                name = safe_text(page.query_selector("h1"))
                image_el = page.query_selector(".product-image img")
                image_url = image_el.get_attribute("src") if image_el else ""

                about = safe_text(page.query_selector("#description"))
                ingredients = safe_text(page.query_selector("#ingredients"))

                # =========================
                # SKIN TYPE
                # =========================
                skin_types = []
                skin_tags = page.query_selector_all(".skin-type span")
                for s in skin_tags:
                    txt = s.inner_text().lower().strip()
                    if txt:
                        skin_types.append(txt)

                if not skin_types:
                    skin_types = ["all skin types"]

                # =========================
                # CATEGORY
                # =========================
                category = cat_url.split("/")[-1].replace("-", " ").lower()

                results.append({
                    "name": name,
                    "category": [category],
                    "skin_type": skin_types,
                    "about": about,
                    "ingredients": ingredients,
                    "image_url": image_url,
                    "url": product_url
                })

                print(f"✔ {name}")

        browser.close()

    df = pd.DataFrame(results)
    df.drop_duplicates(subset=["url"], inplace=True)
    df.to_csv("wardah_skincare_dataset.csv", index=False)

    print("\n🎉 Scraping selesai!")
    print(f"📊 Total produk unik: {len(df)}")
    print("💾 File disimpan: wardah_skincare_dataset.csv")


if __name__ == "__main__":
    scrape_wardah()
