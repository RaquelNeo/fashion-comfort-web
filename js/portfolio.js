// === Our Work — Product Portfolio (Spread-styled cards) ===
const portfolio = {
  products: [],
  currentFilter: 'all',

  async init() {
    try {
      const response = await fetch('data/products.json');
      if (!response.ok) throw new Error('No products file');
      this.products = await response.json();
      if (this.products.length > 0) { this.render(); this.updateFiltersVisibility(); }
      else this.showEmpty();
    } catch (e) { this.showEmpty(); }
    this.initFilters();
  },

  render() {
    const grid = document.getElementById('products-grid');
    const empty = document.getElementById('products-empty');
    const countEl = document.getElementById('products-count');
    if (!grid) return;

    const filtered = this.currentFilter === 'all'
      ? this.products
      : this.products.filter(p => p.brand === this.currentFilter);

    if (filtered.length === 0) { grid.innerHTML = ''; empty?.classList.remove('hidden'); if (countEl) countEl.textContent = ''; return; }
    empty?.classList.add('hidden');

    grid.innerHTML = filtered.map(product => {
      const isUnavailable = product.status === 'unavailable' || product.status === 'not_found';
      const hasUrl = product.productUrl && !isUnavailable;
      const hasImage = product.image && product.status === 'found';
      const displayName = product.name || 'Knitwear Product';
      const brandName = product.brandDisplay || this.brandDisplayName(product.brand);
      const placeholderSvg = encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 400" fill="#E8E4DD"><rect width="300" height="400"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#9B9B9B" font-family="Inter" font-size="14">No Image</text></svg>');
      const imageSrc = hasImage ? product.image : `data:image/svg+xml,${placeholderSvg}`;

      const compositionHtml = product.composition
        ? `<p class="text-[13px] text-text-muted mt-2 leading-relaxed"><span class="text-text-secondary font-medium">${i18n.getNestedValue('work.composition') || 'Composition'}:</span> ${product.composition}</p>`
        : '';

      const unavailableBadge = isUnavailable
        ? `<div class="absolute top-3 right-3 bg-red-500/90 text-white text-[11px] font-medium px-2.5 py-1 rounded-full z-10">${i18n.getNestedValue('work.unavailable') || 'Unavailable'}</div>`
        : '';

      const overlayHtml = hasUrl
        ? `<div class="absolute inset-0 bg-charcoal-deep/80 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-[0.35s]" style="transition-timing-function: cubic-bezier(0.16,1,0.3,1)">
            <a href="${product.productUrl}" target="_blank" rel="noopener" class="btn-pill btn-pill-white text-sm">${i18n.getNestedValue('work.view_on') || 'View on'} ${brandName} →</a>
           </div>`
        : '';

      const imgTag = `<img src="${imageSrc}" alt="${displayName}" class="w-full h-full object-cover transition-transform duration-[0.6s]" style="transition-timing-function:cubic-bezier(0.16,1,0.3,1)" loading="lazy" onerror="this.src='data:image/svg+xml,${placeholderSvg}'">`;

      const imageBlock = hasUrl
        ? `<a href="${product.productUrl}" target="_blank" rel="noopener" class="block relative aspect-[3/4] overflow-hidden rounded-t-[20px] bg-stone">${unavailableBadge}${imgTag}${overlayHtml}</a>`
        : `<div class="relative aspect-[3/4] overflow-hidden rounded-t-[20px] bg-stone">${unavailableBadge}${imgTag}</div>`;

      return `
        <div class="product-card group overflow-hidden bg-white border border-border rounded-[20px] transition-all duration-[0.35s] hover:-translate-y-1 ${isUnavailable ? 'opacity-50' : ''}" style="transition-timing-function:cubic-bezier(0.16,1,0.3,1);box-shadow:0 1px 4px rgba(44,62,47,0.04),0 8px 32px rgba(44,62,47,0.06)" data-brand="${product.brand}">
          ${imageBlock}
          <div class="p-5">
            <span class="tag-accent">${brandName}</span>
            <h4 class="text-[15px] font-medium text-text-primary mt-1.5 leading-snug">${displayName}</h4>
            <p class="text-[13px] text-text-muted font-mono mt-1">Ref: ${product.reference}</p>
            ${compositionHtml}
          </div>
        </div>`;
    }).join('');

    if (countEl) {
      const total = this.products.filter(p => p.status === 'found').length;
      const shown = filtered.filter(p => p.status === 'found').length;
      countEl.textContent = this.currentFilter === 'all' ? `${total} products` : `${shown} of ${total} products`;
      countEl.className = 'text-center mt-10 text-sm text-text-muted';
    }
  },

  showEmpty() { document.getElementById('products-empty')?.classList.remove('hidden'); },

  brandDisplayName(brand) {
    return { zara: 'ZARA', mango: 'MANGO', pullbear: "PULL&BEAR", bershka: 'BERSHKA', oysho: 'OYSHO' }[brand] || brand.toUpperCase();
  },

  updateFiltersVisibility() {
    const brands = new Set(this.products.map(p => p.brand));
    document.querySelectorAll('.btn-filter-pill').forEach(btn => {
      if (btn.dataset.filter !== 'all' && !brands.has(btn.dataset.filter)) btn.style.display = 'none';
    });
  },

  initFilters() {
    document.querySelectorAll('.btn-filter-pill').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.btn-filter-pill').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentFilter = btn.dataset.filter;
        this.render();
      });
    });
  }
};

document.addEventListener('DOMContentLoaded', () => portfolio.init());
