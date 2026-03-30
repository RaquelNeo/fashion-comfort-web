// === GSAP ScrollTrigger Timeline (Spread-style animations) ===
function initTimeline() {
  gsap.registerPlugin(ScrollTrigger);

  const line = document.querySelector('.timeline-line');
  if (!line) return;

  // Line draws as you scroll
  gsap.fromTo(line, { scaleY: 0 }, {
    scaleY: 1, ease: 'none',
    scrollTrigger: { trigger: '.timeline-container', start: 'top 80%', end: 'bottom 20%', scrub: 0.3 }
  });

  // Each timeline entry animates in
  document.querySelectorAll('.timeline-item').forEach((item, i) => {
    const dot = item.querySelector('.timeline-dot');
    const left = item.querySelector('.timeline-content-left');
    const right = item.querySelector('.timeline-content-right');
    const mobile = item.querySelector('.timeline-content-mobile');

    const trigger = { trigger: item, start: 'top 85%', toggleActions: 'play none none none' };

    if (dot) gsap.from(dot, { scale: 0, duration: 0.5, ease: 'back.out(2)', scrollTrigger: trigger });
    if (left) gsap.from(left, { opacity: 0, x: -60, filter: 'blur(4px)', duration: 0.7, ease: 'power2.out', scrollTrigger: trigger });
    if (right) gsap.from(right, { opacity: 0, x: 60, filter: 'blur(4px)', duration: 0.7, ease: 'power2.out', scrollTrigger: trigger });
    if (mobile) gsap.from(mobile, { opacity: 0, x: 30, filter: 'blur(4px)', duration: 0.6, ease: 'power2.out', scrollTrigger: trigger });
  });

  // Founder cards stagger
  const cards = document.querySelectorAll('.founder-card');
  if (cards.length) {
    gsap.from(cards, {
      opacity: 0, y: 40, filter: 'blur(4px)', duration: 0.7, stagger: 0.12,
      ease: 'power2.out',
      scrollTrigger: { trigger: '.founders-grid', start: 'top 80%', toggleActions: 'play none none none' }
    });
  }
}

document.addEventListener('DOMContentLoaded', initTimeline);
