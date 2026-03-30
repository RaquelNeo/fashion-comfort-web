/* Mobile Hamburger Menu — Fashion Comfort */
(function() {
  var nav = document.querySelector('.ds-nav');
  if (!nav) return;

  var inner = nav.querySelector('.ds-nav-inner');
  if (!inner) return;

  // Create hamburger button
  var hamburger = document.createElement('button');
  hamburger.className = 'ds-hamburger';
  hamburger.setAttribute('aria-label', 'Menu');
  hamburger.innerHTML = '<span></span><span></span><span></span>';
  inner.appendChild(hamburger);

  // Create overlay
  var overlay = document.createElement('div');
  overlay.className = 'ds-mobile-overlay';
  document.body.appendChild(overlay);

  // Determine active page
  var currentPage = window.location.pathname.split('/').pop() || 'index.html';

  // Build menu links
  var links = [
    { href: 'index.html#about', label: 'About Us' },
    { href: 'products.html', label: 'Products' },
    { href: 'manufacturing.html', label: 'Manufacturing' },
    { href: 'responsibility.html', label: 'Responsibility' },
    { href: 'our-history.html', label: 'Our History' },
    { href: 'lyk.html', label: 'LYK Project' },
    { href: 'index.html#contact', label: 'Contact' }
  ];

  var linksHTML = links.map(function(link) {
    var isActive = currentPage === link.href ||
                   (currentPage === 'founders.html' && link.href === 'our-history.html');
    return '<a href="' + link.href + '" class="ds-mobile-menu-link' +
           (isActive ? ' active' : '') + '">' + link.label + '</a>';
  }).join('');

  // Create mobile menu panel
  var menu = document.createElement('div');
  menu.className = 'ds-mobile-menu';
  menu.innerHTML =
    '<div class="ds-mobile-menu-links">' + linksHTML + '</div>' +
    '<div class="ds-mobile-menu-langs">' +
      '<button class="ds-mobile-lang-btn">EN</button>' +
      '<button class="ds-mobile-lang-btn">ES</button>' +
    '</div>';
  document.body.appendChild(menu);

  var isOpen = false;

  function openMenu() {
    isOpen = true;
    hamburger.classList.add('open');
    menu.classList.add('open');
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeMenu() {
    isOpen = false;
    hamburger.classList.remove('open');
    menu.classList.remove('open');
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  // Hamburger toggle
  hamburger.addEventListener('click', function(e) {
    e.stopPropagation();
    if (isOpen) { closeMenu(); } else { openMenu(); }
  });

  // Close on overlay click
  overlay.addEventListener('click', function() {
    closeMenu();
  });

  // Close on any link or button inside menu
  menu.addEventListener('click', function(e) {
    var target = e.target;
    if (target.tagName === 'A' || target.tagName === 'BUTTON') {
      closeMenu();
    }
  });

  // Close on escape
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && isOpen) closeMenu();
  });

  // Close on touch outside (mobile)
  document.addEventListener('touchstart', function(e) {
    if (isOpen && !menu.contains(e.target) && !hamburger.contains(e.target)) {
      closeMenu();
    }
  });
})();
