<script>
(function () {
  const toggle = document.querySelector('[data-menu-toggle]');
  const menu = document.querySelector('.mobile-menu');
  const overlay = document.querySelector('.menu-overlay');
  const body = document.body;

  if (!toggle || !menu || !overlay) return;

  function openMenu() {
    menu.classList.add('is-open');
    overlay.classList.add('is-active');
    body.classList.add('menu-open');
  }

  function closeMenu() {
    menu.classList.remove('is-open');
    overlay.classList.remove('is-active');
    body.classList.remove('menu-open');
  }

  toggle.addEventListener('click', openMenu);
  overlay.addEventListener('click', closeMenu);
})();
</script>
