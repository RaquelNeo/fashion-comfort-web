#!/usr/bin/env python3
"""
Fashion Comfort — Product Scraper
Reads products_references.csv, scrapes product info from brand websites,
downloads images, and generates products_data.json.

Usage:
    cd backend
    pip install -r requirements.txt
    python scraper.py
"""

import json
import sys
import time
import csv
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
import gspread
from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / 'data'
IMAGES_DIR = PROJECT_ROOT / 'assets' / 'images' / 'products'
CSV_PATH = PROJECT_ROOT / 'products_references.csv'
OUTPUT_JSON = DATA_DIR / 'products.json'
PRODUCTS_DATA_JSON = PROJECT_ROOT / 'products_data.json'

# Google Sheets config
CREDENTIALS_FILE = BACKEND_DIR / 'credentials.json'
SHEET_ID = '19aow05P-eZLxisih2vbC8rjTqDSXObxYWF511KiBJO8'

BRAND_URLS = {
    'pullbear': 'https://www.pullandbear.com',
    'zara': 'https://www.zara.com',
    'mango': 'https://shop.mango.com',
    'bershka': 'https://www.bershka.com',
    'oysho': 'https://www.oysho.com',
}

BRAND_DISPLAY = {
    'pullbear': 'PULL&BEAR',
    'zara': 'ZARA',
    'zara man': 'ZARA MAN',
    'zara kids': 'ZARA KIDS',
    'zara baby boys': 'ZARA BABY BOYS',
    'mango': 'MANGO',
    'mango teen': 'MANGO TEEN',
    'bershka': 'BERSHKA',
    'oysho': 'OYSHO',
}

# Map brand variants to their scraper key
BRAND_SCRAPER = {
    'pullbear': 'pullbear',
    'zara': 'zara',
    'zara man': 'zara',
    'zara kids': 'zara',
    'zara baby boys': 'zara',
    'mango': 'mango',
    'mango teen': 'mango',
    'bershka': 'bershka',
    'oysho': 'oysho',
}

# Generic Zara placeholder image hash — used to detect unpublished products
ZARA_PLACEHOLDER_HASHES = ['b9f2/a11a']


def create_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es', 'en']});
            window.chrome = { runtime: {} };
        '''
    })
    driver.set_page_load_timeout(30)
    return driver


def read_references():
    """Read product references from Google Sheets, fallback to local CSV."""
    references = []

    # Try Google Sheets first
    if CREDENTIALS_FILE.exists():
        try:
            print("Reading from Google Sheets...")
            scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
            creds = Credentials.from_service_account_file(str(CREDENTIALS_FILE), scopes=scopes)
            gc = gspread.authorize(creds)
            sheet = gc.open_by_key(SHEET_ID).sheet1
            rows = sheet.get_all_records()
            for row in rows:
                # Case-insensitive header lookup
                row_lower = {k.lower(): v for k, v in row.items()}
                brand = str(row_lower.get('marca', '')).strip().lower()
                ref = str(row_lower.get('referencia', '')).strip()
                if brand and ref:
                    references.append({'brand': brand, 'reference': ref})
            print(f"Found {len(references)} references from Google Sheets")
            return references
        except Exception as e:
            print(f"Google Sheets error: {e}")
            print("Falling back to local CSV...")

    # Fallback to local CSV
    if CSV_PATH.exists():
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                brand = row.get('Marca', '').strip().lower()
                ref = row.get('Referencia', '').strip()
                if brand and ref:
                    references.append({'brand': brand, 'reference': ref})
        print(f"Found {len(references)} references from local CSV")
    else:
        print("ERROR: No Google Sheets credentials and no local CSV found")
        sys.exit(1)

    return references


def dismiss_cookies(driver):
    selectors = [
        '#onetrust-accept-btn-handler',
        '[data-testid="cookie-accept"]',
        'button[id*="accept"]',
    ]
    for sel in selectors:
        try:
            btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
            )
            btn.click()
            time.sleep(0.5)
            return
        except Exception:
            continue


def download_image(url, filepath):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        }
        response = requests.get(url, headers=headers, timeout=15, stream=True)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        if filepath.stat().st_size < 1024:
            filepath.unlink()
            return False
        return True
    except Exception as e:
        print(f"    img download failed: {e}")
        if filepath.exists():
            filepath.unlink()
        return False


def intercept_search_api(driver, ref_clean):
    """Check performance logs for XHR responses containing product data."""
    try:
        logs = driver.get_log('performance')
        for entry in logs:
            msg = json.loads(entry['message'])['message']
            if msg['method'] == 'Network.responseReceived':
                url = msg['params']['response']['url']
                if 'search' in url and ('product' in url or 'catalog' in url):
                    request_id = msg['params']['requestId']
                    try:
                        body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                        return json.loads(body.get('body', '{}'))
                    except Exception:
                        continue
    except Exception:
        pass
    return None


def scrape_pullbear_product(driver, reference):
    """Scrape Pull&Bear product using their internal search."""
    ref_clean = reference.replace('/', '')
    base = BRAND_URLS['pullbear']

    # Navigate to search page
    driver.get(f'{base}/es/buscar?q={ref_clean}')
    time.sleep(5)

    # Try to find product links in search results
    product_url = None
    product_name = None
    image_url = None
    composition = None

    # Check if products appeared in grid
    try:
        # PB renders product grid with links containing the product ref
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*=".html"]')
        for link in links:
            href = link.get_attribute('href') or ''
            if '/es/' in href and '.html' in href and 'buscar' not in href:
                product_url = href
                break
    except Exception:
        pass

    # If no grid results, try extracting from page scripts/JSON-LD
    if not product_url:
        try:
            scripts = driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
            for script in scripts:
                data = json.loads(script.get_attribute('innerHTML'))
                if isinstance(data, dict) and data.get('@type') == 'Product':
                    product_name = data.get('name')
                    image_url = data.get('image')
                    product_url = data.get('url') or data.get('offers', {}).get('url')
                    break
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'Product':
                            product_name = item.get('name')
                            image_url = item.get('image')
                            product_url = item.get('url')
                            break
        except Exception:
            pass

    # If still no product, try navigating to product page directly
    if not product_url:
        # Try common Inditex URL patterns
        patterns = [
            f'{base}/es/jersey-punto-{ref_clean[:4]}-l{ref_clean}.html',
            f'{base}/es/-l{ref_clean}.html',
        ]
        for url in patterns:
            try:
                driver.get(url)
                time.sleep(3)
                if '/buscar' not in driver.current_url and driver.current_url != f'{base}/es/':
                    product_url = driver.current_url
                    break
            except Exception:
                continue

    # If we have a product URL, navigate there and extract details
    if product_url and product_url != driver.current_url:
        driver.get(product_url)
        time.sleep(4)

    # Extract product name from page
    if not product_name:
        for sel in ['h1', '.product-title', '[class*="product-name"]', '[class*="ProductName"]']:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                if el.text.strip():
                    product_name = el.text.strip()
                    break
            except Exception:
                continue

    # Extract image
    if not image_url:
        for sel in ['img[src*="static.pull"]', '.product-media img', 'picture img',
                     'img[loading="eager"]', 'img[fetchpriority="high"]']:
            try:
                imgs = driver.find_elements(By.CSS_SELECTOR, sel)
                for img in imgs:
                    src = img.get_attribute('src') or img.get_attribute('data-src') or ''
                    if src.startswith('http') and 'logo' not in src and 'icon' not in src:
                        image_url = src
                        break
                if image_url:
                    break
            except Exception:
                continue

    # Extract composition - try clicking detail sections
    for sel in ['[class*="composition"]', '[class*="material"]',
                '.product-detail-extra-detail li', '.product-info-care']:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            for el in els:
                text = el.text.strip()
                if '%' in text:
                    composition = text
                    break
            if composition:
                break
        except Exception:
            continue

    # Try expanding accordion/detail panels for composition
    if not composition:
        try:
            buttons = driver.find_elements(By.CSS_SELECTOR,
                'button[class*="detail"], button[class*="accordion"], '
                '[data-testid*="detail"], .product-detail-extra button')
            for btn in buttons:
                btn_text = (btn.text or '').lower()
                if any(kw in btn_text for kw in ['composición', 'composition', 'material', 'detalle']):
                    btn.click()
                    time.sleep(1)
                    # Re-check for composition
                    source = driver.page_source
                    match = re.search(r'(\d{1,3}%\s*[A-Za-zÁáÉéÍíÓóÚúÑñü]+(?:\s*[,/]\s*\d{1,3}%\s*[A-Za-zÁáÉéÍíÓóÚúÑñü]+)*)', source)
                    if match:
                        composition = match.group(1)
                    break
        except Exception:
            pass

    # Try JSON-LD for structured data
    if not product_name or not image_url:
        try:
            scripts = driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
            for script in scripts:
                data = json.loads(script.get_attribute('innerHTML'))
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict) and item.get('@type') == 'Product':
                        if not product_name:
                            product_name = item.get('name')
                        if not image_url:
                            img = item.get('image')
                            image_url = img[0] if isinstance(img, list) else img
                        if not composition:
                            desc = item.get('description', '')
                            match = re.search(r'(\d{1,3}%\s*\w+)', desc)
                            if match:
                                composition = match.group(1)
        except Exception:
            pass

    return product_url, product_name, image_url, composition


def scrape_zara_product(driver, reference):
    """Scrape Zara product by reference (works for all Zara sub-brands)."""
    ref_clean = reference.replace('/', '')
    if not ref_clean.startswith('0'):
        ref_clean = '0' + ref_clean

    product_url = None
    product_name = None
    image_url = None
    composition = None

    driver.get(f'https://www.zara.com/es/es/product-p{ref_clean}.html')
    time.sleep(5)

    product_url = driver.current_url

    # Extract from JSON-LD structured data
    try:
        scripts = driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
        for script in scripts:
            try:
                data = json.loads(script.get_attribute('innerHTML'))
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict) and item.get('@type') == 'Product':
                        product_name = item.get('name')
                        img = item.get('image')
                        if isinstance(img, list) and img:
                            image_url = img[0]
                        elif img:
                            image_url = img
                        desc = item.get('description', '')
                        comp_match = re.search(
                            r'(\d{1,3}%\s*[A-Za-zÁáÉéÍíÓóÚúÑñüÜ]+'
                            r'(?:\s*[,]\s*\d{1,3}%\s*[A-Za-zÁáÉéÍíÓóÚúÑñüÜ]+)*)',
                            desc)
                        if comp_match:
                            composition = comp_match.group(1)
            except Exception:
                continue
    except Exception:
        pass

    # Fallback: h1
    if not product_name:
        try:
            h1 = driver.find_element(By.CSS_SELECTOR, 'h1')
            if h1.text.strip():
                product_name = h1.text.strip()
        except Exception:
            pass

    # Fallback: image from static.zara.net
    if not image_url:
        try:
            imgs = driver.find_elements(By.CSS_SELECTOR, 'img[src*="static.zara.net"]')
            for img in imgs:
                src = img.get_attribute('src') or ''
                if src.startswith('http') and 'logo' not in src and 'icon' not in src:
                    image_url = src
                    break
        except Exception:
            pass

    # Fallback: composition from page source
    if not composition:
        try:
            source = driver.page_source
            comp_match = re.search(
                r'(\d{1,3}%\s*[A-Za-zÁáÉéÍíÓóÚúÑñüÜ]+'
                r'(?:\s*[,]\s*\d{1,3}%\s*[A-Za-zÁáÉéÍíÓóÚúÑñüÜ]+)*)',
                source)
            if comp_match:
                composition = comp_match.group(1)
        except Exception:
            pass

    # Detect placeholder/unpublished products
    if image_url:
        for placeholder in ZARA_PLACEHOLDER_HASHES:
            if placeholder in image_url:
                print("(placeholder image — product not yet published) ", end='')
                image_url = None
                product_name = None
                composition = None
                break

    return product_url, product_name, image_url, composition


def scrape_product(driver, brand, reference):
    """Scrape a single product."""
    ref_clean = reference.replace('/', '-')
    brand_file = brand.replace(' ', '_')  # "zara man" -> "zara_man" for filenames

    result = {
        'brand': brand,
        'brandDisplay': BRAND_DISPLAY.get(brand, brand.upper()),
        'reference': reference,
        'name': None,
        'image': None,
        'imageLocal': None,
        'productUrl': None,
        'composition': None,
        'status': 'not_found',
        'scrapedAt': datetime.now(timezone.utc).isoformat()
    }

    try:
        scraper_key = BRAND_SCRAPER.get(brand)
        if scraper_key == 'pullbear':
            product_url, name, image_url, composition = scrape_pullbear_product(driver, reference)
        elif scraper_key == 'zara':
            product_url, name, image_url, composition = scrape_zara_product(driver, reference)
        else:
            print(f"brand {brand} not yet implemented")
            result['status'] = 'not_implemented'
            return result

        result['productUrl'] = product_url
        result['name'] = name
        result['composition'] = composition

        if image_url:
            result['image'] = image_url
            image_path = IMAGES_DIR / f'{brand_file}_{ref_clean}.jpg'
            if download_image(image_url, image_path):
                result['imageLocal'] = f'assets/images/products/{brand_file}_{ref_clean}.jpg'
                result['status'] = 'found'
            else:
                result['status'] = 'image_failed'
        elif name:
            result['status'] = 'no_image'
        else:
            result['status'] = 'not_found'

    except Exception as e:
        print(f"ERROR: {str(e)[:100]}")
        result['status'] = 'error'

    return result


def main():
    print("=" * 60)
    print("  Fashion Comfort — Product Scraper")
    print("=" * 60)

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    references = read_references()
    if not references:
        return

    print("Launching browser...")
    driver = create_driver()
    products = []

    # Initialize sessions: visit homepages and accept cookies
    brands_in_refs = set(BRAND_SCRAPER.get(r['brand'], r['brand']) for r in references)
    for scraper_brand in brands_in_refs:
        if scraper_brand in BRAND_URLS:
            url = BRAND_URLS[scraper_brand]
            print(f"Initializing {scraper_brand} session...")
            driver.get(f'{url}/es/')
            time.sleep(4)
            dismiss_cookies(driver)
            time.sleep(1)

    try:
        for idx, ref in enumerate(references, 1):
            brand = ref['brand']
            reference = ref['reference']

            print(f"[{idx}/{len(references)}] {BRAND_DISPLAY.get(brand, brand)} ref {reference}... ",
                  end='', flush=True)

            result = scrape_product(driver, brand, reference)
            products.append(result)

            status = result['status'].upper()
            name = f" — {result['name']}" if result.get('name') else ""
            comp = f" | {result['composition'][:60]}" if result.get('composition') else ""
            print(f"{status}{name}{comp}")

            if idx < len(references):
                time.sleep(3)

    except KeyboardInterrupt:
        print("\nInterrupted. Saving partial results...")
    finally:
        driver.quit()

    # Save results
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    with open(PRODUCTS_DATA_JSON, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    found = sum(1 for p in products if p['status'] == 'found')
    print()
    print("=" * 60)
    print(f"  Total: {len(products)} | Found: {found} | Failed: {len(products) - found}")
    print(f"  Output: {PRODUCTS_DATA_JSON}")
    print("=" * 60)


if __name__ == '__main__':
    main()
