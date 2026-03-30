/* Mobile Hamburger Menu — Fashion Comfort */
(function() {
  // Only run on mobile-capable viewports
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
    '<ul class="ds-mobile-menu-links">' + linksHTML + '</ul>' +
    '<div class="ds-mobile-menu-langs">' +
      '<button class="ds-mobile-lang-btn">EN</button>' +
      '<button class="ds-mobile-lang-btn">ES</button>' +
    '</div>';
  document.body.appendChild(menu);

  // Toggle function
  function toggleMenu() {
    var isOpen = hamburger.classList.contains('open');
    hamburger.classList.toggle('open');
    menu.classList.toggle('open');
    overlay.classList.toggle('open');
    document.body.style.overflow = isOpen ? '' : 'hidden';
  }

  function closeMenu() {
    hamburger.classList.remove('open');
    menu.classList.remove('open');
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  // Event listeners
  hamburger.addEventListener('click', toggleMenu);
  overlay.addEventListener('click', closeMenu);

  // Close on any click inside menu (links + lang buttons)
  menu.addEventListener('click', function(e) {
    if (e.target.classList.contains('ds-mobile-menu-link') ||
        e.target.classList.contains('ds-mobile-lang-btn')) {
      closeMenu();
    }
  });

  // Close on escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeMenu();
  });
})();
