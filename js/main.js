// ============================================================
// Fashion Comfort — Main JS (Spread-inspired)
// Glassmorphism nav, i18n, scroll reveals, contact form
// ============================================================

// === i18n Engine ===
const i18n = {
  currentLang: localStorage.getItem('fc-lang') || 'en',
  translations: {},
  basePath: '',

  async init(basePath = '') {
    this.basePath = basePath;
    await this.loadLanguage(this.currentLang);
    this.applyTranslations();
    this.updateToggle();
  },

  async loadLanguage(lang) {
    try {
      const response = await fetch(`${this.basePath}locales/${lang}.json`);
      this.translations = await response.json();
      this.currentLang = lang;
      localStorage.setItem('fc-lang', lang);
    } catch (e) {
      console.warn(`Failed to load language: ${lang}`, e);
    }
  },

  async switchLanguage(lang) {
    if (lang === this.currentLang) return;
    await this.loadLanguage(lang);
    this.applyTranslations();
    this.updateToggle();
    if (typeof portfolio !== 'undefined' && portfolio.products.length > 0) {
      portfolio.render();
    }
  },

  applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const value = this.getNestedValue(el.getAttribute('data-i18n'));
      if (value) el.textContent = value;
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const value = this.getNestedValue(el.getAttribute('data-i18n-placeholder'));
      if (value) el.placeholder = value;
    });
    document.querySelectorAll('[data-i18n-html]').forEach(el => {
      const value = this.getNestedValue(el.getAttribute('data-i18n-html'));
      if (value) el.innerHTML = value;
    });
  },

  getNestedValue(key) {
    return key.split('.').reduce((obj, k) => obj?.[k], this.translations);
  },

  updateToggle() {
    document.querySelectorAll('.lang-btn, .ds-lang-btn, .ds-mobile-lang-btn').forEach(btn => {
      const isActive = btn.dataset.lang === this.currentLang;
      btn.classList.toggle('active', isActive);
    });
  }
};

// === Floating Pill Nav (Spread-style glassmorphism) ===
function initNavbar() {
  const navbar = document.getElementById('navbar');
  if (!navbar) return;
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('nav-scrolled', window.scrollY > 50);
  });
}

// === Mobile Menu ===
function initMobileMenu() {
  const toggle = document.getElementById('menu-toggle');
  const menu = document.getElementById('mobile-menu');
  if (!toggle || !menu) return;

  toggle.addEventListener('click', () => {
    const isOpen = menu.classList.contains('translate-x-0');
    if (isOpen) closeMobileMenu();
    else {
      menu.classList.remove('translate-x-full');
      menu.classList.add('translate-x-0');
      toggle.classList.add('menu-open');
      document.body.style.overflow = 'hidden';
    }
  });
}

function closeMobileMenu() {
  const menu = document.getElementById('mobile-menu');
  const toggle = document.getElementById('menu-toggle');
  if (menu) { menu.classList.add('translate-x-full'); menu.classList.remove('translate-x-0'); }
  if (toggle) toggle.classList.remove('menu-open');
  document.body.style.overflow = '';
}

// === Scroll Reveal (Spread-style: blur + translate) ===
function initScrollReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) entry.target.classList.add('visible');
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
}

// === Active Nav Highlight ===
function initActiveNavHighlight() {
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-link');

  window.addEventListener('scroll', () => {
    let current = '';
    sections.forEach(section => {
      if (window.scrollY >= section.offsetTop - 120) current = section.id;
    });
    navLinks.forEach(link => {
      link.classList.toggle('nav-active', link.getAttribute('href') === `#${current}`);
    });
  });
}

// === Contact Form ===
function initContactForm() {
  const form = document.getElementById('contact-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    const originalText = btn.textContent;
    btn.textContent = '...';
    btn.disabled = true;

    try {
      console.log('Contact form data:', Object.fromEntries(new FormData(form)));
      const msg = document.createElement('p');
      msg.className = 'text-accent mt-4 text-sm font-medium';
      msg.textContent = i18n.getNestedValue('contact.form_success') || 'Message sent successfully!';
      form.appendChild(msg);
      form.reset();
      setTimeout(() => msg.remove(), 5000);
    } catch (err) {
      const msg = document.createElement('p');
      msg.className = 'text-red-500 mt-4 text-sm font-medium';
      msg.textContent = i18n.getNestedValue('contact.form_error') || 'Something went wrong.';
      form.appendChild(msg);
      setTimeout(() => msg.remove(), 5000);
    } finally {
      btn.textContent = originalText;
      btn.disabled = false;
    }
  });
}

// === Smooth Scroll ===
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (href === '#') return;
      e.preventDefault();
      const target = document.querySelector(href);
      if (target) {
        window.scrollTo({ top: target.offsetTop - 80, behavior: 'smooth' });
        closeMobileMenu();
      }
    });
  });
}

// === Init ===
document.addEventListener('DOMContentLoaded', () => {
  const basePath = document.body.dataset.basePath || '';
  i18n.init(basePath);
  initNavbar();
  initMobileMenu();
  initScrollReveal();
  initActiveNavHighlight();
  initContactForm();
  initSmoothScroll();
});
