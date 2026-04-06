/* Mobile Hamburger Menu — Fashion Comfort */
(function() {
  var nav = document.querySelector('.ds-nav');
  if (!nav) return;
  var inner = nav.querySelector('.ds-nav-inner');
  if (!inner) return;

  // Hamburger button
  var hamburger = document.createElement('button');
  hamburger.className = 'ds-hamburger';
  hamburger.setAttribute('aria-label', 'Menu');
  hamburger.innerHTML = '<span></span><span></span><span></span>';
  inner.appendChild(hamburger);

  // Overlay
  var overlay = document.createElement('div');
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.18);z-index:199;opacity:0;visibility:hidden;transition:opacity 0.25s ease;pointer-events:none;';
  document.body.appendChild(overlay);

  // Active page
  var currentPage = window.location.pathname.split('/').pop() || 'index.html';

  // Links
  var links = [
    { href: 'index.html#about', label: 'About Us', i18nKey: 'nav.about' },
    { href: 'products.html', label: 'Products', i18nKey: 'nav.products' },
    { href: 'manufacturing.html', label: 'Manufacturing', i18nKey: 'nav.manufacturing' },
    { href: 'responsibility.html', label: 'Responsibility', i18nKey: 'nav.responsibility' },
    { href: 'our-history.html', label: 'Our History', i18nKey: 'nav.history' },
    { href: 'lyk.html', label: 'LYK Project', i18nKey: 'nav.lyk' },
    { href: 'index.html#contact', label: 'Contact', i18nKey: 'nav.contact' }
  ];

  // Menu panel — inline styles to avoid any CSS conflicts
  var menu = document.createElement('div');
  menu.style.cssText = 'position:fixed;top:14px;right:12px;width:75vw;max-width:280px;background:rgba(29,43,31,0.90);border-radius:18px;box-shadow:0 8px 24px rgba(0,0,0,0.12);z-index:200;transform:translateX(calc(100% + 24px));opacity:0;visibility:hidden;transition:transform 0.28s ease-out,opacity 0.22s ease-out,visibility 0s linear 0.3s;display:flex;flex-direction:column;padding:24px 24px 20px;';

  var linksHTML = links.map(function(l) {
    var active = currentPage === l.href || (currentPage === 'founders.html' && l.href === 'our-history.html');
    var i18nAttr = l.i18nKey ? ' data-i18n="' + l.i18nKey + '"' : '';
    return '<a href="' + l.href + '"' + i18nAttr + ' style="display:block;font-family:Outfit,sans-serif;font-size:13px;font-weight:400;color:' + (active ? '#ffffff' : 'rgba(255,255,255,0.65)') + ';text-decoration:none;text-transform:uppercase;letter-spacing:0.08em;padding:11px 0;border-bottom:1px solid rgba(255,255,255,0.1);">' + l.label + '</a>';
  }).join('');

  var langBtnStyle = 'background:none;border:1px solid rgba(255,255,255,0.2);border-radius:6px;font-family:Outfit,sans-serif;font-size:11px;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;color:rgba(255,255,255,0.65);cursor:pointer;padding:7px 14px;display:flex;align-items:center;gap:6px;';
  var flagStyle = 'width:18px;height:12px;display:inline-block;vertical-align:middle;flex-shrink:0;';
  var flagEN = '<svg style="' + flagStyle + '" viewBox="0 0 60 30"><clipPath id="ms"><circle cx="30" cy="15" r="15"/></clipPath><rect width="60" height="30" fill="#012169"/><path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" stroke-width="6"/><path d="M0,0 L60,30 M60,0 L0,30" stroke="#C8102E" stroke-width="4" clip-path="url(#ms)"/><path d="M30,0V30 M0,15H60" stroke="#fff" stroke-width="10"/><path d="M30,0V30 M0,15H60" stroke="#C8102E" stroke-width="6"/></svg>';
  var flagES = '<svg style="' + flagStyle + '" viewBox="0 0 6 4"><rect width="6" height="4" fill="#c60b1e"/><rect y="1" width="6" height="2" fill="#ffc400"/></svg>';
  var flagJA = '<svg style="' + flagStyle + '" viewBox="0 0 60 40"><rect width="60" height="40" fill="#fff"/><circle cx="30" cy="20" r="12" fill="#bc002d"/></svg>';

  menu.innerHTML = '<div>' + linksHTML + '</div>' +
    '<div style="display:flex;gap:8px;margin-top:auto;padding-top:20px;">' +
      '<button style="' + langBtnStyle + '" class="ml-btn ds-mobile-lang-btn" data-lang="en" onclick="i18n.switchLanguage(\'en\')">' + flagEN + 'EN</button>' +
      '<button style="' + langBtnStyle + '" class="ml-btn ds-mobile-lang-btn" data-lang="es" onclick="i18n.switchLanguage(\'es\')">' + flagES + 'ES</button>' +
      '<button style="' + langBtnStyle + '" class="ml-btn ds-mobile-lang-btn" data-lang="ja" onclick="i18n.switchLanguage(\'ja\')">' + flagJA + 'JA</button>' +
    '</div>';
  document.body.appendChild(menu);

  // Highlight active language button
  function updateMobileLangButtons() {
    var currentLang = (typeof i18n !== 'undefined' && i18n.currentLang) ? i18n.currentLang : (localStorage.getItem('fc-lang') || 'en');
    menu.querySelectorAll('.ml-btn').forEach(function(btn) {
      if (btn.dataset.lang === currentLang) {
        btn.style.color = '#ffffff';
        btn.style.borderColor = 'rgba(255,255,255,0.8)';
        btn.style.background = 'rgba(255,255,255,0.15)';
      } else {
        btn.style.color = 'rgba(255,255,255,0.65)';
        btn.style.borderColor = 'rgba(255,255,255,0.2)';
        btn.style.background = 'none';
      }
    });
  }
  updateMobileLangButtons();

  var isOpen = false;
  var autoCloseTimer = null;

  function openMenu() {
    isOpen = true;
    hamburger.classList.add('open');
    menu.style.transform = 'translateX(0)';
    menu.style.opacity = '1';
    menu.style.visibility = 'visible';
    menu.style.transition = 'transform 0.28s ease-out, opacity 0.22s ease-out, visibility 0s linear 0s';
    overlay.style.opacity = '1';
    overlay.style.visibility = 'visible';
    overlay.style.pointerEvents = 'auto';
    document.body.style.overflow = 'hidden';

    if (autoCloseTimer) clearTimeout(autoCloseTimer);
  }

  function closeMenu() {
    isOpen = false;
    if (autoCloseTimer) { clearTimeout(autoCloseTimer); autoCloseTimer = null; }
    hamburger.classList.remove('open');
    menu.style.transform = 'translateX(calc(100% + 24px))';
    menu.style.opacity = '0';
    menu.style.transition = 'transform 0.28s ease-out, opacity 0.22s ease-out, visibility 0s linear 0.3s';
    menu.style.visibility = 'hidden';
    overlay.style.opacity = '0';
    overlay.style.visibility = 'hidden';
    overlay.style.pointerEvents = 'none';
    document.body.style.overflow = '';
  }

  hamburger.addEventListener('click', function(e) {
    e.stopPropagation();
    if (isOpen) closeMenu(); else openMenu();
  });

  overlay.addEventListener('click', closeMenu);

  menu.addEventListener('click', function(e) {
    if (e.target.tagName === 'A') {
      closeMenu();
    }
    if (e.target.tagName === 'BUTTON' && e.target.classList.contains('ml-btn')) {
      setTimeout(function() { updateMobileLangButtons(); }, 100);
    }
  });

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && isOpen) closeMenu();
  });
})();
