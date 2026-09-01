const toggle = document.querySelector('.menu-toggle');
const drawer = document.querySelector('.drawer');
const close = document.querySelector('.drawer-close');

function setDrawer(open) {
  drawer.classList.toggle('open', open);
  drawer.setAttribute('aria-hidden', String(!open));
  toggle.setAttribute('aria-expanded', String(open));
  if (open) {
    close.focus();
  } else {
    toggle.focus();
  }
}

toggle.addEventListener('click', () => setDrawer(true));
close.addEventListener('click', () => setDrawer(false));
drawer.querySelectorAll('a').forEach(a => a.addEventListener('click', () => setDrawer(false)));

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && drawer.classList.contains('open')) {
    setDrawer(false);
  }
});
