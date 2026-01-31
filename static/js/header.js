const btn = document.querySelector('[data-menu-toggle]');
const menu = document.querySelector('.mobile-menu');
const overlay = document.querySelector('.menu-overlay');

btn.addEventListener('click', () => {
  menu.classList.add('is-open');
  overlay.classList.add('is-active');
});

overlay.addEventListener('click', () => {
  menu.classList.remove('is-open');
  overlay.classList.remove('is-active');
});
