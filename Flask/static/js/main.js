(function () {
  'use strict';

  /* Mobile navigation */
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');
  if (toggle && nav) {
    var setNav = function (open) {
      nav.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', String(open));
    };
    toggle.addEventListener('click', function () {
      setNav(!nav.classList.contains('open'));
    });
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) setNav(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('open')) {
        setNav(false);
        toggle.focus();
      }
    });
    document.addEventListener('click', function (e) {
      if (!e.target.closest('.site-header')) setNav(false);
    });
  }
})();
