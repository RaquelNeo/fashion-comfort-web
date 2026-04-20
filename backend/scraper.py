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
    'honeys': 'https://www.honeys-onlineshop.com',
    'gdi': None,   # URL pendiente
    'dub': 'https://www.dubapparels.com',
}

BRAND_DISPLAY = {
    'pullbear': 'PULL&BEAR',
    'zara': 'ZARA',
    'zara man': 'ZARA MAN',
    'zara kids': 'ZARA KIDS',
    'zara baby boys': 'ZARA BABY BOYS',
    'zara baby girls': 'ZARA BABY GIRLS',
    'mango': 'MANGO',
    'mango teen': 'MANGO TEEN',
    'bershka': 'BERSHKA',
    'oysho': 'OYSHO',
    'honeys': 'HONEYS',
    'gdi': 'GDI',
    'dub': 'DUB',
}

# Map brand variants to their scraper key
BRAND_SCRAPER = {
    'pullbear': 'pullbear',
    'zara': 'zara',
    'zara man': 'zara',
    'zara kids': 'zara',
    'zara baby boys': 'zara',
    'zara baby girls': 'zara',
    'mango': 'mango',
    'mango teen': 'mango',
    'bershka': 'bershka',
    'oysho': 'oysho',
    'honeys': 'honeys',
    'gdi': 'gdi',
    'dub': 'dub',
}

# Brands to skip during scraping (wrong references, etc.)
SKIP_BRANDS = {'pullbear', 'pull&bear', 'gdi'}

# Generic Zara placeholder image hash — used to detect unpublished products
ZARA_PLACEHOLDER_HASHES = ['b9f2/a11a', '14a4/dea1']


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
                row_lower = {k.lower().strip(): v for k, v in row.items()}
                brand = str(row_lower.get('marca', '')).strip().lower()
                ref = str(row_lower.get('referencia', '')).strip()
                if brand and ref and brand not in SKIP_BRANDS:
                    entry = {'brand': brand, 'reference': ref}
                    # Optional manual fields (for brands that block scraping)
                    for field, key in [('image', 'image'), ('name', 'name'),
                                       ('composition', 'composition'),
                                       ('url', 'url'), ('product url', 'url')]:
                        val = str(row_lower.get(field, '')).strip()
                        if val:
                            entry[key] = val
                    references.append(entry)
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
                if brand and ref and brand not in SKIP_BRANDS:
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


def scrape_oysho_product(driver, reference):
    """Scrape Oysho product by reference (Inditex pattern)."""
    # Oysho refs come as "4682/987/712" (article/model/color)
    parts = reference.replace(' ', '').split('/')
    ref_all = ''.join(parts)            # 4682987712
    ref_article = ''.join(parts[:2])    # 4682987

    product_url = None
    product_name = None
    image_url = None
    composition = None

    # Strategy 1: Try direct product URLs with different ref formats
    url_variants = []
    for ref_clean in [ref_all, ref_article]:
        padded = ref_clean if ref_clean.startswith('0') else '0' + ref_clean
        url_variants.append(f'https://www.oysho.com/es/product-p{padded}.html')
        url_variants.append(f'https://www.oysho.com/es/es/product-p{padded}.html')

    for url in url_variants:
        try:
            driver.get(url)
            time.sleep(5)
            current = driver.current_url
            # Check we didn't land on homepage
            if current.rstrip('/') == 'https://www.oysho.com/es' or current.rstrip('/') == 'https://www.oysho.com/es/es':
                continue
            if 'product' in current or ref_article in current:
                product_url = current
                break
        except Exception:
            continue

    # Strategy 2: Try Oysho search (Inditex search pattern)
    if not product_url:
        for search_term in [ref_article, ref_all]:
            try:
                driver.get(f'https://www.oysho.com/es/buscar?q={search_term}')
                time.sleep(5)
                # Look for product links in search results
                links = driver.find_elements(By.CSS_SELECTOR,
                    'a[href*="product-p"], a[href*="-p0"], a[href*="/es/"]')
                for link in links:
                    href = link.get_attribute('href') or ''
                    if '/es/' in href and 'buscar' not in href and href != 'https://www.oysho.com/es/':
                        product_url = href
                        break
                if product_url:
                    break
            except Exception:
                continue

    # Strategy 3: Try Oysho static image URL directly (Inditex CDN pattern)
    if not image_url:
        for ref_clean in [ref_all, ref_article]:
            padded = ref_clean if ref_clean.startswith('0') else '0' + ref_clean
            # Inditex CDN pattern: static.oysho.net/assets/public/.../REFCOLOR-p/REFCOLOR-p.jpg
            test_url = f'https://static.oysho.net/assets/public/{padded}-p/{padded}-p.jpg'
            try:
                resp = requests.head(test_url, timeout=5, allow_redirects=True,
                                     headers={'User-Agent': 'Mozilla/5.0'})
                if resp.status_code == 200:
                    image_url = test_url
                    break
            except Exception:
                continue

    # Navigate to product page if found
    if product_url and product_url != driver.current_url:
        driver.get(product_url)
        time.sleep(4)

    # Extract from JSON-LD (Inditex standard)
    if product_url:
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
    if not product_name and product_url:
        try:
            h1 = driver.find_element(By.CSS_SELECTOR, 'h1')
            if h1.text.strip():
                product_name = h1.text.strip()
        except Exception:
            pass

    # Fallback: image from static.oysho
    if not image_url:
        try:
            imgs = driver.find_elements(By.CSS_SELECTOR,
                'img[src*="static.oysho"], img[src*="oysho.net"]')
            for img in imgs:
                src = img.get_attribute('src') or ''
                if src.startswith('http') and 'logo' not in src and 'icon' not in src:
                    image_url = src
                    break
        except Exception:
            pass

    # Fallback: composition from page source
    if not composition and product_url:
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

    return product_url, product_name, image_url, composition


def scrape_mango_product(driver, reference):
    """Scrape Mango product by reference.

    Mango accepts /es/es/p/{ref} as a short URL that redirects to the full
    canonical product page. Metadata comes from og:* tags.
    """
    ref_clean = str(reference).strip().replace('/', '').replace(' ', '')

    product_url = None
    product_name = None
    image_url = None
    composition = None

    try:
        driver.get(f'https://shop.mango.com/es/es/p/{ref_clean}')
        time.sleep(5)
    except Exception:
        return product_url, product_name, image_url, composition

    current = driver.current_url
    # If we didn't redirect to a real product page, bail out
    if '/p/' not in current or current.rstrip('/').endswith(f'/p/{ref_clean}'):
        # Still on the short URL or redirected away — product likely unavailable
        if current.rstrip('/').endswith(f'/p/{ref_clean}'):
            # short URL didn't resolve; page may contain 404 state
            return product_url, product_name, image_url, composition
    product_url = current

    def meta(prop):
        try:
            el = driver.find_element(By.CSS_SELECTOR, f'meta[property="{prop}"]')
            return (el.get_attribute('content') or '').strip() or None
        except Exception:
            return None

    og_title = meta('og:title')
    og_image = meta('og:image')
    og_desc = meta('og:description')

    if og_title:
        # Strip " - Teen | MANGO España (...)" suffix
        product_name = re.split(r'\s*\|\s*MANGO', og_title)[0].strip()
        product_name = re.sub(r'\s*-\s*(Teen|Kids|Baby|Man|Woman|Mujer|Hombre|Niña|Niño)\s*$',
                              '', product_name, flags=re.I).strip()

    if og_image:
        # Upgrade to higher resolution if size param is present
        image_url = re.sub(r'imwidth=\d+', 'imwidth=1920', og_image)

    # Extract composition from og:description only — page source is noisy
    # (contains strings like "10% de descuento"). Reject matches where the
    # fabric word is a Spanish preposition/article like "de", "del", "la".
    if og_desc:
        comp_re = re.compile(
            r'(\d{1,3}%\s+(?!de\b|del\b|la\b|en\b)[A-Za-zÁáÉéÍíÓóÚúÑñüÜ]+'
            r'(?:\s*,\s*\d{1,3}%\s+(?!de\b|del\b|la\b|en\b)[A-Za-zÁáÉéÍíÓóÚúÑñüÜ]+)*)',
            re.I)
        m = comp_re.search(og_desc)
        if m:
            composition = m.group(1)

    return product_url, product_name, image_url, composition


def scrape_honeys_product(driver, reference):
    """Scrape Honeys product by searching their website."""
    # Extract numeric reference (strip descriptive suffixes like "SKIRT", "CAT", etc.)
    ref_numeric = re.match(r'[\d\-]+', reference.strip())
    ref_search = ref_numeric.group(0).rstrip('-') if ref_numeric else reference.strip()
    ref_digits = ref_search.replace('-', '')  # e.g. "587311298"

    product_url = None
    product_name = None
    image_url = None
    composition = None

    base = BRAND_URLS['honeys']

    # Strategy 1: Try direct product URL with different code formats
    # Honeys uses 12-digit codes like /shop/g/g587311298XX/
    # Try padding with common suffixes to reach 12 digits
    code_variants = [ref_digits]
    if len(ref_digits) < 12:
        for pad in ['01', '31', '37', '00', '10', '20', '30', '40', '50']:
            padded = ref_digits + pad
            if len(padded) <= 12:
                code_variants.append(padded.ljust(12, '0'))
                code_variants.append(padded)

    for code in code_variants:
        test_url = f'{base}/shop/g/g{code}/'
        try:
            driver.get(test_url)
            time.sleep(3)
            # Check for actual product content (not just nav/homepage)
            page_text = driver.find_element(By.TAG_NAME, 'body').text
            # Look for price indicators (¥) as sign of a product page
            if '¥' in page_text and len(page_text) > 500:
                # Verify this isn't just a category/nav page
                try:
                    # Look for product-specific elements
                    for sel in ['.goods_name', '#item_detail', '.itemDetail',
                                '[class*="goodsDetail"]', '[class*="product-detail"]',
                                'h1.item-name', '.good_detail_box']:
                        els = driver.find_elements(By.CSS_SELECTOR, sel)
                        if els and els[0].text.strip():
                            product_url = driver.current_url
                            product_name = els[0].text.strip()
                            break
                except Exception:
                    pass

                if not product_name:
                    # Try h1 as last resort, but verify it's not navigation
                    try:
                        h1 = driver.find_element(By.CSS_SELECTOR, 'h1')
                        h1_text = h1.text.strip()
                        if h1_text and len(h1_text) < 100 and 'honeys' not in h1_text.lower():
                            product_url = driver.current_url
                            product_name = h1_text
                    except Exception:
                        pass

            if product_url:
                break
        except Exception:
            continue

    # Strategy 2: Use search
    if not product_url:
        search_url = f'{base}/shop/goods/search.aspx?search=x&keyword={ref_search}'
        try:
            driver.get(search_url)
            time.sleep(5)
            # Look for product links containing the reference digits
            links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/shop/g/g"]')
            for link in links:
                href = link.get_attribute('href') or ''
                # Only take links whose product code starts with our ref digits
                code_match = re.search(r'/g/g(\d+)/', href)
                if code_match and code_match.group(1).startswith(ref_digits):
                    product_url = href if href.startswith('http') else base + href
                    break
        except Exception:
            pass

    # Navigate to product page if found via search
    if product_url and product_url != driver.current_url:
        driver.get(product_url)
        time.sleep(4)

    # Extract product name from page
    if not product_name and product_url:
        for sel in ['.goods_name', '#item_detail h1', '.itemDetail h1',
                    'h1', '[class*="product-name"]', '[class*="goodsName"]']:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                text = el.text.strip()
                if text and len(text) < 100 and 'honeys' not in text.lower():
                    product_name = text
                    break
            except Exception:
                continue

    # Extract image
    if not image_url and product_url:
        for sel in ['img[src*="img/goods"]', '#mainImage', '.goods_image img',
                    '.main-image img', 'img[src*="honeys"]']:
            try:
                imgs = driver.find_elements(By.CSS_SELECTOR, sel)
                for img in imgs:
                    src = img.get_attribute('src') or img.get_attribute('data-src') or ''
                    if src.startswith('http') and 'logo' not in src and 'icon' not in src and 'banner' not in src:
                        image_url = src
                        break
                if image_url:
                    break
            except Exception:
                continue

    # Extract composition/material
    if product_url:
        try:
            source = driver.page_source
            # Japanese composition patterns: NN%素材名
            comp_match = re.search(
                r'(\d{1,3}%\s*[\w\u3000-\u9FFF\uFF00-\uFFEF]+'
                r'(?:\s*[,/、]\s*\d{1,3}%\s*[\w\u3000-\u9FFF\uFF00-\uFFEF]+)*)',
                source)
            if comp_match:
                composition = comp_match.group(1)
        except Exception:
            pass

    # Try JSON-LD
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
        except Exception:
            pass

    return product_url, product_name, image_url, composition


def scrape_dub_product(driver, reference):
    """Scrape DUB Apparels product. DUB uses internal refs (1005/XXX) and sells via Wildberries."""
    ref_clean = reference.replace('/', '')
    base = BRAND_URLS['dub']

    product_url = None
    product_name = None
    image_url = None
    composition = None

    # DUB's website is a showcase with collections; try browsing pages for the reference
    # First try searching for the article code in page content
    collection_pages = [
        f'{base}/bestsellers',
        f'{base}/urban-i',
        f'{base}/urban-ii',
        f'{base}/sk8-park',
        f'{base}/denim-cut',
        f'{base}/natures-canvas',
    ]

    for page_url in collection_pages:
        try:
            driver.get(page_url)
            time.sleep(4)

            # Search for the reference in page source (article codes may appear as text)
            source = driver.page_source
            if ref_clean in source or reference in source:
                # Found the reference on this page, try to extract product info nearby
                # Look for product cards/items
                items = driver.find_elements(By.CSS_SELECTOR,
                    '[class*="product"], [class*="item"], [class*="card"], article')
                for item in items:
                    item_text = item.text or ''
                    item_html = item.get_attribute('innerHTML') or ''
                    if ref_clean in item_text or ref_clean in item_html or reference in item_html:
                        # Found the matching product card
                        try:
                            link = item.find_element(By.CSS_SELECTOR, 'a[href]')
                            product_url = link.get_attribute('href')
                        except Exception:
                            product_url = page_url

                        try:
                            img = item.find_element(By.CSS_SELECTOR, 'img')
                            image_url = img.get_attribute('src') or img.get_attribute('data-src')
                        except Exception:
                            pass

                        try:
                            name_el = item.find_element(By.CSS_SELECTOR,
                                'h2, h3, h4, [class*="name"], [class*="title"]')
                            product_name = name_el.text.strip()
                        except Exception:
                            pass

                        break

                if image_url:
                    break
        except Exception:
            continue

    # If not found in collections, try product images from the page
    if not image_url:
        try:
            driver.get(base)
            time.sleep(4)
            # Try to find any reference to the article
            imgs = driver.find_elements(By.CSS_SELECTOR, 'img[src*="dub"], img[src*="product"]')
            for img in imgs:
                alt = (img.get_attribute('alt') or '').lower()
                src = img.get_attribute('src') or ''
                if ref_clean in alt or ref_clean in src:
                    image_url = src
                    product_name = img.get_attribute('alt')
                    break
        except Exception:
            pass

    return product_url, product_name, image_url, composition


def scrape_product(driver, brand, reference, manual=None):
    """Scrape a single product, or use manual data from spreadsheet."""
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

    # If manual data provided from spreadsheet, use it directly
    if manual and manual.get('image') and manual.get('name'):
        print("(manual) ", end='')
        result['name'] = manual['name']
        result['image'] = manual['image']
        result['productUrl'] = manual.get('url')
        result['composition'] = manual.get('composition')

        image_path = IMAGES_DIR / f'{brand_file}_{ref_clean}.jpg'
        if download_image(manual['image'], image_path):
            result['imageLocal'] = f'assets/images/products/{brand_file}_{ref_clean}.jpg'
            result['status'] = 'found'
        else:
            result['status'] = 'image_failed'
        return result

    try:
        scraper_key = BRAND_SCRAPER.get(brand)
        if scraper_key == 'pullbear':
            product_url, name, image_url, composition = scrape_pullbear_product(driver, reference)
        elif scraper_key == 'zara':
            product_url, name, image_url, composition = scrape_zara_product(driver, reference)
        elif scraper_key == 'oysho':
            product_url, name, image_url, composition = scrape_oysho_product(driver, reference)
        elif scraper_key == 'mango':
            product_url, name, image_url, composition = scrape_mango_product(driver, reference)
        elif scraper_key == 'honeys':
            product_url, name, image_url, composition = scrape_honeys_product(driver, reference)
        elif scraper_key == 'dub':
            product_url, name, image_url, composition = scrape_dub_product(driver, reference)
        else:
            print(f"brand {brand} not yet implemented")
            result['status'] = 'not_implemented'
            return result

        result['productUrl'] = product_url
        result['name'] = name
        result['composition'] = composition

        # Auto-detect Mango Teen sub-brand from product URL
        if scraper_key == 'mango' and product_url and '/teen/' in product_url.lower():
            result['brandDisplay'] = 'MANGO TEEN'

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

    # Load existing products to avoid re-scraping
    existing = {}
    if PRODUCTS_DATA_JSON.exists():
        try:
            with open(PRODUCTS_DATA_JSON, 'r', encoding='utf-8') as f:
                for p in json.load(f):
                    if p.get('status') == 'found':
                        key = (p['brand'], p['reference'])
                        existing[key] = p
            print(f"Loaded {len(existing)} existing products (will skip)")
        except Exception:
            pass

    # Filter out already-scraped references
    def normalize_ref(brand, ref):
        """Normalize reference for comparison."""
        ref_clean = ref.replace('/', '').replace(' ', '')
        # Zara refs: "3284/419" in sheet vs "03284419" in JSON
        if 'zara' in brand:
            if not ref_clean.startswith('0'):
                ref_clean = '0' + ref_clean
        return ref_clean

    new_references = []
    for ref in references:
        brand = ref['brand']
        reference = ref['reference']
        # Check both raw and normalized forms
        if (brand, reference) in existing:
            continue
        norm_ref = normalize_ref(brand, reference)
        # Check with normalized ref across all brand variants
        found = False
        for (eb, er) in existing:
            if normalize_ref(eb, er) == norm_ref and BRAND_SCRAPER.get(eb) == BRAND_SCRAPER.get(brand):
                found = True
                break
        if not found:
            new_references.append(ref)

    if not new_references:
        print("No new references to scrape. All up to date!")
        return

    print(f"New references to process: {len(new_references)} "
          f"(skipped {len(references) - len(new_references)} existing)")

    # Check if any refs need scraping (no manual data)
    needs_scraping = any(not (r.get('image') and r.get('name')) for r in new_references)

    driver = None
    if needs_scraping:
        print("Launching browser...")
        driver = create_driver()

        # Initialize sessions: visit homepages and accept cookies
        brands_in_refs = set(BRAND_SCRAPER.get(r['brand'], r['brand']) for r in new_references
                             if not (r.get('image') and r.get('name')))
        for scraper_brand in brands_in_refs:
            url = BRAND_URLS.get(scraper_brand)
            if url:
                print(f"Initializing {scraper_brand} session...")
                # Honeys is Japanese, no /es/ path
                home = url if scraper_brand == 'honeys' else f'{url}/es/'
                driver.get(home)
                time.sleep(4)
                dismiss_cookies(driver)
                time.sleep(1)
    else:
        print("All entries have manual data, no scraping needed.")

    # Start with existing products
    products = list(existing.values())

    try:
        for idx, ref in enumerate(new_references, 1):
            brand = ref['brand']
            reference = ref['reference']

            print(f"[{idx}/{len(new_references)}] {BRAND_DISPLAY.get(brand, brand)} ref {reference}... ",
                  end='', flush=True)

            # Pass manual data if available from spreadsheet
            manual = {}
            for field in ('image', 'name', 'composition', 'url'):
                if ref.get(field):
                    manual[field] = ref[field]

            result = scrape_product(driver, brand, reference, manual=manual or None)
            products.append(result)

            status = result['status'].upper()
            name = f" — {result['name']}" if result.get('name') else ""
            comp = f" | {result['composition'][:60]}" if result.get('composition') else ""
            print(f"{status}{name}{comp}")

            if idx < len(new_references) and not manual:
                time.sleep(3)

    except KeyboardInterrupt:
        print("\nInterrupted. Saving partial results...")
    finally:
        if driver:
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
