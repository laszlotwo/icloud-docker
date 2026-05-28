// Navbar scroll effect
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  navbar.classList.toggle('scrolled', window.scrollY > 20);
});

// Mobile menu
const hamburger = document.getElementById('hamburger');
const mobileMenu = document.getElementById('mobileMenu');

hamburger.addEventListener('click', () => {
  mobileMenu.classList.toggle('open');
});

mobileMenu.querySelectorAll('.mobile-link').forEach(link => {
  link.addEventListener('click', () => {
    mobileMenu.classList.remove('open');
  });
});

// Skill bars animate on scroll
const skillFills = document.querySelectorAll('.skill-fill');

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const el = entry.target;
      el.style.width = el.dataset.width;
      observer.unobserve(el);
    }
  });
}, { threshold: 0.3 });

skillFills.forEach(el => observer.observe(el));

// Fade-in on scroll
const fadeEls = document.querySelectorAll(
  '.skill-card, .project-card, .timeline-item, .biz-card, .ps-card, .highlight-item'
);

const fadeObserver = new IntersectionObserver(entries => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = '1';
      entry.target.style.transform = 'translateY(0)';
      fadeObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });

fadeEls.forEach((el, i) => {
  el.style.opacity = '0';
  el.style.transform = 'translateY(24px)';
  el.style.transition = `opacity 0.5s ease ${i * 0.08}s, transform 0.5s ease ${i * 0.08}s`;
  fadeObserver.observe(el);
});

// Contact form
document.getElementById('contactForm').addEventListener('submit', function(e) {
  e.preventDefault();
  const btn = this.querySelector('button[type="submit"]');
  const originalText = btn.textContent;
  btn.textContent = '✓ 消息已发送！';
  btn.disabled = true;
  btn.style.background = 'linear-gradient(135deg, #48bb78, #38a169)';
  setTimeout(() => {
    btn.textContent = originalText;
    btn.disabled = false;
    btn.style.background = '';
    this.reset();
  }, 3000);
});

// Smooth active nav highlight
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-links a');

const navObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const id = entry.target.getAttribute('id');
      navLinks.forEach(link => {
        link.style.color = link.getAttribute('href') === `#${id}`
          ? '#e2e8f0'
          : '';
      });
    }
  });
}, { threshold: 0.5 });

sections.forEach(s => navObserver.observe(s));
