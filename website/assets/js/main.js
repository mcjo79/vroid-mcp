/* VRoid MCP Bridge — interactions légères, sans dépendance. */
(function () {
  'use strict';

  var root = document.documentElement;
  var doc = document;
  var body = doc.body;
  var I18N = window.SITE_I18N || {
    themeToDark: 'Passer au thème sombre',
    themeToLight: 'Passer au thème clair',
    menuOpen: 'Ouvrir le menu',
    menuClose: 'Fermer le menu',
    copied: 'Copié !',
    noTools: 'Aucun outil trouvé',
    tool: 'outil',
    tools: 'outils'
  };

  /* ---------- Thème ---------- */
  var themeToggle = doc.getElementById('themeToggle');

  function currentTheme() {
    return root.dataset.theme === 'dark' ? 'dark' : 'light';
  }

  function syncThemeButton() {
    if (!themeToggle) return;
    var dark = currentTheme() === 'dark';
    themeToggle.setAttribute('aria-pressed', String(dark));
    themeToggle.setAttribute('aria-label', dark ? I18N.themeToLight : I18N.themeToDark);
  }

  function setTheme(theme) {
    if (theme === 'dark') root.dataset.theme = 'dark';
    else delete root.dataset.theme;
    try { localStorage.setItem('vroid-theme', theme); } catch (e) {}
    syncThemeButton();
  }

  if (themeToggle) {
    syncThemeButton();
    themeToggle.addEventListener('click', function () {
      setTheme(currentTheme() === 'dark' ? 'light' : 'dark');
    });
  }

  /* ---------- En-tête, progression, menu ---------- */
  var header = doc.querySelector('.site-header');
  var progress = doc.getElementById('progressBar');
  var menuToggle = doc.getElementById('menuToggle');
  var nav = doc.getElementById('nav');
  var ticking = false;

  function onScroll() {
    var y = window.scrollY || window.pageYOffset;
    if (header) header.classList.toggle('is-scrolled', y > 8);
    if (progress) {
      var max = doc.documentElement.scrollHeight - window.innerHeight;
      var ratio = max > 0 ? Math.min(1, Math.max(0, y / max)) : 0;
      progress.style.width = (ratio * 100).toFixed(2) + '%';
    }
    ticking = false;
  }

  window.addEventListener('scroll', function () {
    if (!ticking) {
      window.requestAnimationFrame(onScroll);
      ticking = true;
    }
  }, { passive: true });
  onScroll();

  function closeMenu() {
    body.classList.remove('nav-open');
    if (menuToggle) {
      menuToggle.setAttribute('aria-expanded', 'false');
      menuToggle.setAttribute('aria-label', I18N.menuOpen);
    }
  }

  if (menuToggle && nav) {
    menuToggle.addEventListener('click', function () {
      var open = body.classList.toggle('nav-open');
      menuToggle.setAttribute('aria-expanded', String(open));
      menuToggle.setAttribute('aria-label', open ? I18N.menuClose : I18N.menuOpen);
    });

    nav.addEventListener('click', function (event) {
      if (event.target.closest('a')) closeMenu();
    });

    doc.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') closeMenu();
    });

    window.addEventListener('resize', function () {
      if (window.innerWidth > 980) closeMenu();
    });
  }

  /* ---------- Lien de navigation actif ---------- */
  var navLinks = Array.prototype.slice.call(doc.querySelectorAll('.nav a[href^="#"]'));
  var sections = navLinks.map(function (link) {
    return doc.querySelector(link.getAttribute('href'));
  }).filter(Boolean);

  if ('IntersectionObserver' in window && sections.length) {
    var navObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        navLinks.forEach(function (link) {
          link.classList.toggle('is-active', link.getAttribute('href') === '#' + entry.target.id);
        });
      });
    }, { rootMargin: '-42% 0px -52% 0px', threshold: 0 });

    sections.forEach(function (section) { navObserver.observe(section); });
  }

  /* ---------- Révélation au défilement ---------- */
  var revealItems = Array.prototype.slice.call(doc.querySelectorAll('[data-reveal]'));
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (!reduceMotion && 'IntersectionObserver' in window) {
    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -7% 0px', threshold: 0.08 });

    revealItems.forEach(function (item) { revealObserver.observe(item); });
  } else {
    revealItems.forEach(function (item) { item.classList.add('is-visible'); });
  }

  /* ---------- Copie des blocs de code ---------- */
  function fallbackCopy(text) {
    var area = doc.createElement('textarea');
    area.value = text;
    area.setAttribute('readonly', '');
    area.style.position = 'fixed';
    area.style.left = '-9999px';
    doc.body.appendChild(area);
    area.select();
    try { doc.execCommand('copy'); } catch (e) {}
    doc.body.removeChild(area);
  }

  Array.prototype.forEach.call(doc.querySelectorAll('[data-copy]'), function (button) {
    button.addEventListener('click', function () {
      var block = button.closest('.code-block');
      var code = block ? block.querySelector('pre code') : null;
      var text = code ? code.innerText : '';
      var done = function () {
        var original = button.textContent;
        button.textContent = I18N.copied;
        button.classList.add('is-copied');
        window.setTimeout(function () {
          button.textContent = original;
          button.classList.remove('is-copied');
        }, 1800);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { fallbackCopy(text); done(); });
      } else {
        fallbackCopy(text);
        done();
      }
    });
  });

  /* ---------- Recherche dans les outils ---------- */
  var toolSearch = doc.getElementById('toolSearch');
  var toolsCount = doc.getElementById('toolsCount');
  var toolGroups = Array.prototype.slice.call(doc.querySelectorAll('.tool-group'));
  var initialOpen = toolGroups.map(function (group) { return group.open; });

  function normalize(value) {
    return (value || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');
  }

  function filterTools() {
    if (!toolSearch) return;
    var query = normalize(toolSearch.value.trim());
    var total = 0;

    toolGroups.forEach(function (group, groupIndex) {
      var rows = Array.prototype.slice.call(group.querySelectorAll('tbody tr'));
      var visible = 0;

      rows.forEach(function (row) {
        var haystack = normalize(row.getAttribute('data-tool') + ' ' + row.textContent);
        var match = !query || haystack.indexOf(query) !== -1;
        row.classList.toggle('is-hidden', !match);
        if (match) visible += 1;
      });

      group.hidden = visible === 0;
      if (query && visible > 0) group.open = true;
      if (!query) group.open = initialOpen[groupIndex];
      total += visible;
    });

    if (toolsCount) {
      toolsCount.textContent = total === 0
        ? I18N.noTools
        : total + ' ' + (total === 1 ? I18N.tool : I18N.tools);
    }
  }

  if (toolSearch) {
    toolSearch.addEventListener('input', filterTools);
    toolSearch.addEventListener('search', filterTools);
  }

  /* ---------- Lightbox ---------- */
  var lightbox = doc.getElementById('lightbox');
  var lightboxImg = doc.getElementById('lightboxImg');
  var lightboxCaption = doc.getElementById('lightboxCaption');
  var lightboxClose = doc.getElementById('lightboxClose');
  var lastTrigger = null;

  function openLightbox(trigger) {
    if (!lightbox || !lightboxImg) return;
    var href = trigger.getAttribute('href');
    var caption = trigger.getAttribute('data-caption') || '';
    var inner = trigger.querySelector('img');
    lastTrigger = trigger;
    lightboxImg.src = href;
    lightboxImg.alt = inner ? inner.alt : '';
    if (lightboxCaption) lightboxCaption.textContent = caption;
    lightbox.hidden = false;
    body.style.overflow = 'hidden';
    if (lightboxClose) lightboxClose.focus();
  }

  function closeLightbox() {
    if (!lightbox) return;
    lightbox.hidden = true;
    lightboxImg.src = '';
    body.style.overflow = '';
    if (lastTrigger) lastTrigger.focus();
  }

  Array.prototype.forEach.call(doc.querySelectorAll('[data-lightbox]'), function (trigger) {
    trigger.addEventListener('click', function (event) {
      event.preventDefault();
      openLightbox(trigger);
    });
  });

  if (lightboxClose) lightboxClose.addEventListener('click', closeLightbox);
  if (lightbox) {
    lightbox.addEventListener('click', function (event) {
      if (event.target === lightbox) closeLightbox();
    });
  }
  doc.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && lightbox && !lightbox.hidden) closeLightbox();
  });

  /* ---------- Année ---------- */
  var year = doc.getElementById('year');
  if (year) year.textContent = String(new Date().getFullYear());
})();
