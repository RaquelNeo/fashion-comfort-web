// === Hero Entrance Animation (GSAP + Spread-style easing) ===
function initHeroAnimation() {
  const ease = 'power3.out';
  gsap.set(['.hero-title', '.hero-subtitle', '.hero-stats', '.hero-cta'], { y: 40, opacity: 0, filter: 'blur(4px)' });

  const tl = gsap.timeline({ defaults: { ease, duration: 1 } });
  tl.to('.hero-title', { opacity: 1, y: 0, filter: 'blur(0px)', delay: 0.2 })
    .to('.hero-subtitle', { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.8 }, '-=0.6')
    .to('.hero-stats', { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.8 }, '-=0.5')
    .to('.hero-cta', { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.8 }, '-=0.4');
}

// === Counter Animation ===
function initCounters() {
  const counters = document.querySelectorAll('.counter');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        animateCounter(el, parseInt(el.dataset.target), el.dataset.suffix || '');
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.5 });
  counters.forEach(c => observer.observe(c));
}

function animateCounter(el, target, suffix) {
  const duration = 2000;
  const start = performance.now();
  function update(now) {
    const p = Math.min((now - start) / duration, 1);
    el.textContent = Math.floor((1 - Math.pow(1 - p, 3)) * target) + suffix;
    if (p < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

// === Init ===
document.addEventListener('DOMContentLoaded', () => {
  initHeroAnimation();
  initCounters();
});
