# Fashion Comfort Web — Design Spec

**Date:** 2026-03-29
**Client:** Fashion Comfort Group (FCBL)
**Type:** Corporate website + product scraper

---

## 1. Overview

Single-page corporate website for Fashion Comfort Group, a knitwear manufacturer based in Bangladesh with European offices. Bilingual (EN/ES), with animated timeline, product portfolio fed by a Python scraper, and contact form.

## 2. Stack

| Layer | Technology | Delivery |
|-------|-----------|----------|
| CSS | Tailwind CSS 3.x via CLI | Compiled to static CSS |
| Animations | GSAP 3 + ScrollTrigger | CDN |
| Carousel | Swiper.js 11 | CDN |
| Fonts | Inter (Google Fonts) 300,400,500,600 | CDN |
| i18n | JSON files + vanilla JS | Local |
| Forms | EmailJS | CDN |
| Scraper | Python + Selenium + BeautifulSoup | Local script |

No bundler, no framework. Static HTML served from any host.

## 3. File Structure

```
fashion-comfort-web/
├── index.html
├── css/
│   ├── input.css              ← Tailwind directives + custom
│   └── output.css             ← Compiled (gitignored in dev)
├── js/
│   ├── main.js                ← Nav, i18n, scroll, init
│   ├── timeline.js            ← GSAP timeline animations
│   ├── portfolio.js           ← Load products.json, filters
│   └── animations.js          ← Hero counters, fade-ins
├── locales/
│   ├── en.json
│   └── es.json
├── assets/
│   └── images/
│       └── products/          ← Scraped product images
├── data/
│   ├── products_references.xlsx  ← User-provided input
│   └── products.json             ← Scraper output
├── backend/
│   ├── scraper.py
│   ├── requirements.txt
│   └── README.md
├── tailwind.config.js
├── package.json
└── .gitignore
```

## 4. Design Tokens

### Colors
- `--primary-dark: #2C3E2F` — Nav scroll, footer, dark backgrounds
- `--primary-beige: #E8E4DD` — Alternate section backgrounds
- `--accent-green: #7A9B6F` — CTAs, links, highlights
- `--accent-hover: #647F5A` — Button hover
- `--lyk-dark: #4A5C43` — LYK section gradients
- `--background: #F9F9F7` — Main background
- `--text-dark: #2C2C2C` — Headings
- `--text-light: #6B6B6B` — Body text
- `--text-lighter: #9B9B9B` — Captions
- `--border-light: #D9D9D9` — Borders

### Typography
- H1: Inter 300, 4-5rem, tracking 0.02em
- H2: Inter 300, 2.5-3rem, tracking 0.01em
- H3: Inter 400, 1.8-2rem
- H4: Inter 500, 1.2-1.5rem
- Body: Inter 400, 1rem, leading 1.6
- Buttons: Inter 600, 0.95rem, tracking 0.02em
- Captions: Inter 400, 0.85rem

### Spacing
- Section padding: 6rem vertical minimum
- Container max-width: 1280px, centered

## 5. Sections

### 5.1 Navigation
- Sticky top, transparent → `#2C3E2F` on scroll with backdrop blur
- Logo: "fashion comfort" text + "FCBL" badge
- Links: Home, About, Founders, Our Work, LYK, Contact
- EN/ES toggle buttons, state saved in localStorage
- Mobile: hamburger menu, slide-in panel

### 5.2 Hero
- Full viewport height
- Centered: title "fashion comfort" (5rem, weight 200), subtitle, 3 animated counters (20+, 12, 5), CTA button
- GSAP: staggered fade-in, counter animation, subtle parallax on background

### 5.3 About Us
Six subsections, alternating white/beige backgrounds:
1. **Our Brand Story** — 2-col grid (text + image placeholder)
2. **Why Fashion Comfort** — Intro text + 5 bullet points with green markers
3. **International Teams** — World map visualization with 5 office pins (Barcelona, Prato, Shanghai, Tokyo, Dhaka)
4. **Sample Home** — Text + image, 6 capability bullets
5. **Production & Control** — Text left + image grid right, key capabilities list
6. **Responsible Approach** — 2x2 grid (water, solar, recycling, workforce) + certificates row (GOTS, GRS, RCS, RWS) + social responsibility

### 5.4 Founders + Timeline
- 3 founder cards with circular photo placeholders, name, title, description
- Vertical timeline (2002-2018), 9 entries alternating left/right
- GSAP ScrollTrigger: line draws progressively, dots scale in, content cards slide from sides
- Mobile: single-column, line on left

### 5.5 Our Work
- Brand filter buttons: All, ZARA, MANGO, PULL&BEAR, BERSHKA, OYSHO
- Product grid (3 cols desktop, 2 tablet, 1 mobile)
- Each card: image (aspect 3:4), brand badge, product name, reference
- Hover: dark overlay with "View on [Brand]" link
- Data source: `data/products.json` loaded via fetch
- Empty state: message with instructions when no products.json exists

### 5.6 LYK Project
- Hero with dark green gradient, title, 3 large stats
- Executive Summary: 2-col problem/solution
- What Makes LYK Different: 4 feature cards
- Product Portfolio: 4 yarn products with prices
- Competitive Advantage: comparison table
- Capacity & Scale: 3 stat cards
- Why This Matters: 3 impact cards
- Vision Roadmap: 3-phase horizontal progression
- Mission statement

### 5.7 Contact
- 2 columns: Barcelona + Bangladesh info (left), contact form (right)
- Form fields: Name, Email, Company (optional), Message
- Submit via EmailJS (no backend needed)
- Input focus: green border transition

### 5.8 Footer
- 3 columns: brand info, nav links, contact/social
- Dark background (#2C3E2F), white text
- Copyright line

## 6. i18n System

- `data-i18n="hero.title"` attributes on translatable elements
- `data-i18n-placeholder` for form placeholders
- JSON structure mirrors section hierarchy
- Language toggle updates all elements instantly
- Default: EN, persisted in localStorage

## 7. Animations

### GSAP + ScrollTrigger
- Timeline: line stroke animation, dot scale-in, card slide-in from alternating sides
- Hero: staggered title/subtitle/stats reveal

### Vanilla JS
- Counter animation: requestAnimationFrame from 0 to target
- Intersection Observer: fade-up class toggled on scroll for section elements

### CSS
- Nav: background-color transition on scroll
- Buttons: translateY(-2px) + shadow on hover
- Cards: translateY(-5px) + shadow on hover
- Images in cards: scale(1.05) on hover
- All transitions: 300ms ease

## 8. Scraper

### Input
`data/products_references.xlsx` with columns: marca, referencia

### Process
1. Read Excel with pandas/openpyxl
2. For each row, build search URL based on brand config
3. Use Selenium (headless Chrome) to load page
4. Extract: product name, image URL, product page URL
5. Download image to `assets/images/products/{brand}_{ref}.jpg`
6. Write `data/products.json`

### Output — products.json
```json
[
  {
    "brand": "zara",
    "reference": "1234567890",
    "name": "Product Name",
    "image": "assets/images/products/zara_1234567890.jpg",
    "url": "https://www.zara.com/...",
    "status": "found",
    "scrapedAt": "2026-03-29T14:30:00Z"
  }
]
```

### Brand configs
Each brand has: base URL, search URL pattern, CSS selectors for image/title/price, 3s rate limit between requests.

### Usage
```bash
cd backend
pip install -r requirements.txt
python scraper.py
```

### Error handling
- Product not found → `status: "not_found"`, placeholder image
- Network error → retry once, then skip with log
- Console output with progress: `[3/24] Scraping zara 1234567890... OK`

## 9. Responsive Breakpoints

- Mobile: < 768px (1 col, hamburger nav, timeline single-side)
- Tablet: 768-1024px (2 col grids)
- Desktop: > 1024px (full layout)

## 10. SEO

- Semantic HTML5 (header, nav, main, section, footer)
- Meta tags: title, description, OG, Twitter cards
- Lazy loading on images below fold
- Preload Inter font
- Defer non-critical JS

## 11. Out of Scope (Future)

- Flask API wrapper for scraper
- Database (PostgreSQL/SQLite)
- Admin panel web UI
- Celery/Redis cron jobs
- Image optimization pipeline (WebP conversion)
- Locomotive Scroll / smooth scrolling
