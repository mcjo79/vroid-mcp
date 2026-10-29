/* Consentement RGPD — Google Analytics 4 n'est chargé qu'après un accord explicite. */
(function () {
  'use strict';

  var GA_ID = 'G-2NDE82V29F';
  var STORAGE_KEY = 'vroid-consent-v1';
  var MAX_AGE = 180 * 24 * 60 * 60 * 1000; // 180 jours, puis la question est reposée
  var isFr = (document.documentElement.lang || 'en').toLowerCase().indexOf('fr') === 0;
  var privacyUrl = document.documentElement.getAttribute('data-privacy') || 'privacy/';
  var banner = null;
  var stateEl = null;
  // Tag Assistant / GTM debug. This only enables GA4 debug output and re-opens the
  // banner for testing; it is NEVER treated as consent.
  var debugMode = /[?&](gtm_debug|ga_debug|debug_mode)(=|&|$)/.test(location.search);

  var copy = isFr ? {
    title: 'Cookies et mesure d’audience',
    body: 'Ce site utilise Google Analytics 4 uniquement pour mesurer son audience et améliorer sa documentation. ' +
          'Aucun cookie de mesure n’est déposé avant votre accord.',
    accept: 'Accepter',
    refuse: 'Refuser',
    more: 'En savoir plus',
    stateGranted: 'Mesure d’audience acceptée.',
    stateDenied: 'Mesure d’audience refusée.'
  } : {
    title: 'Cookies and audience measurement',
    body: 'This site uses Google Analytics 4 only to measure its audience and improve its documentation. ' +
          'No analytics cookie is set before you agree.',
    accept: 'Accept',
    refuse: 'Decline',
    more: 'Learn more',
    stateGranted: 'Audience measurement accepted.',
    stateDenied: 'Audience measurement declined.'
  };

  function ensureGtag() {
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  }

  function readConsent() {
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      var data = JSON.parse(raw);
      if (!data || (data.value !== 'granted' && data.value !== 'denied')) return null;
      if (!data.expires || data.expires < Date.now()) return null;
      return data;
    } catch (e) {
      return null;
    }
  }

  function writeConsent(value) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify({
        value: value,
        ts: Date.now(),
        expires: Date.now() + MAX_AGE
      }));
    } catch (e) {
      /* Stockage indisponible : le choix vaut pour la page courante. */
    }
  }

  function clearGaCookies(includeGeneric) {
    try {
      var names = document.cookie.split(';').map(function (c) {
        return c.split('=')[0].trim();
      }).filter(function (n) {
        if (n === '_ga_2NDE82V29F') return true;
        return includeGeneric && (n === '_ga' || n.indexOf('_ga_') === 0 || n === '_gid' || n === '_gat');
      });
      if (!names.length) return;

      var host = location.hostname;
      var domains = ['', host, '.' + host];
      var paths = ['/', '/vroid-mcp/'];
      names.forEach(function (name) {
        domains.forEach(function (domain) {
          paths.forEach(function (path) {
            document.cookie = name + '=; Max-Age=0; path=' + path +
              (domain ? '; domain=' + domain : '') + '; SameSite=Lax';
          });
        });
      });
    } catch (e) {
      /* Les cookies peuvent être bloqués par le navigateur. */
    }
  }

  function grantGa() {
    window['ga-disable-' + GA_ID] = false;
    ensureGtag();
    gtag('consent', 'update', {
      ad_storage: 'denied',
      ad_user_data: 'denied',
      ad_personalization: 'denied',
      analytics_storage: 'granted'
    });
  }

  function revokeGa(includeGeneric) {
    clearGaCookies(includeGeneric);
    window['ga-disable-' + GA_ID] = true;
    if (window.gtag) {
      gtag('consent', 'update', {
        ad_storage: 'denied',
        ad_user_data: 'denied',
        ad_personalization: 'denied',
        analytics_storage: 'denied'
      });
    }
  }

  function updateState(value) {
    if (!stateEl) return;
    if (value === 'granted') {
      stateEl.textContent = copy.stateGranted;
      stateEl.hidden = false;
    } else if (value === 'denied') {
      stateEl.textContent = copy.stateDenied;
      stateEl.hidden = false;
    } else {
      stateEl.hidden = true;
    }
  }

  function hideBanner() {
    if (!banner) return;
    banner.hidden = true;
    document.body.classList.remove('consent-open');
  }

  function showBanner(focus) {
    if (!banner) buildBanner();
    var current = readConsent();
    updateState(current ? current.value : null);
    banner.hidden = false;
    document.body.classList.add('consent-open');
    if (focus) {
      var first = banner.querySelector('[data-consent="granted"]');
      if (first) first.focus({ preventScroll: true });
    }
  }

  function choose(value) {
    var previous = readConsent();
    var wasGranted = previous && previous.value === 'granted';
    writeConsent(value);
    updateState(value);
    hideBanner();

    if (value === 'granted') {
      grantGa();
      if (!wasGranted) {
        // The first page view was sent with analytics_storage=denied (cookieless).
        // Send one now that storage is allowed, so this visit is counted normally.
        gtag('event', 'page_view', {
          page_location: location.href,
          page_title: document.title
        });
      }
      return;
    }

    revokeGa(wasGranted);
  }

  function buildBanner() {
    banner = document.createElement('div');
    banner.className = 'consent-banner';
    banner.id = 'consent-banner';
    banner.setAttribute('role', 'region');
    banner.setAttribute('aria-labelledby', 'consent-title');
    banner.hidden = true;
    banner.innerHTML =
      '<div class="container consent-inner">' +
        '<div class="consent-text">' +
          '<h2 id="consent-title">' + copy.title + '</h2>' +
          '<p>' + copy.body + '</p>' +
          '<p class="consent-state" id="consent-state" aria-live="polite" hidden></p>' +
        '</div>' +
        '<div class="consent-actions">' +
          '<button type="button" class="btn btn-primary consent-btn" data-consent="granted">' + copy.accept + '</button>' +
          '<button type="button" class="btn btn-secondary consent-btn" data-consent="denied">' + copy.refuse + '</button>' +
          '<a class="consent-more" href="' + privacyUrl + '">' + copy.more + '</a>' +
        '</div>' +
      '</div>';
    var skip = document.querySelector('.skip-link');
    if (skip && skip.parentNode === document.body) skip.insertAdjacentElement('afterend', banner);
    else document.body.insertBefore(banner, document.body.firstChild);
    stateEl = banner.querySelector('#consent-state');

    banner.addEventListener('click', function (event) {
      var button = event.target.closest('[data-consent]');
      if (!button) return;
      choose(button.getAttribute('data-consent'));
    });
  }

  function init() {
    ensureGtag();
    buildBanner();
    var consent = readConsent();
    if (consent && consent.value === 'granted' && !debugMode) {
      grantGa();
    } else if (debugMode) {
      showBanner(false);
      // In debug, a stored "granted" is intentionally not applied; don't claim
      // it is active in the banner either.
      if (consent && consent.value === 'granted') updateState(null);
    } else if (!consent) {
      showBanner(false);
    } else {
      updateState('denied');
    }

    document.addEventListener('click', function (event) {
      var opener = event.target.closest('[data-consent-open]');
      if (!opener) return;
      event.preventDefault();
      showBanner(true);
    });
  }

  window.vroidConsent = {
    open: function () { showBanner(true); },
    get: function () { var c = readConsent(); return c ? c.value : null; },
    revoke: function () { choose('denied'); }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
