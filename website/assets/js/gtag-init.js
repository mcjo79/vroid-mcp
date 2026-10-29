/* Advanced Consent Mode: the Google tag loads immediately with everything denied.
   Nothing is stored before consent; consent.js sends the `update` on Accept. */
(function () {
  'use strict';

  var GA_ID = 'G-2NDE82V29F';
  var STORAGE_KEY = 'vroid-consent-v1';
  var debugMode = /[?&](gtm_debug|ga_debug|debug_mode)(=|&|$)/.test(location.search);

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };

  gtag('consent', 'default', {
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    analytics_storage: 'denied'
  });

  // Restore an existing choice before the first hit, so returning visitors who
  // already accepted are measured with cookies. In debug mode we deliberately
  // start from the default (denied) so Tag Assistant can test the real click.
  if (!debugMode) {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        var saved = JSON.parse(raw);
        if (saved && saved.value === 'granted' && saved.expires && saved.expires > Date.now()) {
          gtag('consent', 'update', { analytics_storage: 'granted' });
        }
      }
    } catch (e) {}
  }

  gtag('js', new Date());

  var host = location.hostname;
  var isIp = /^[\d.]+$/.test(host) || host.indexOf(':') !== -1;
  var config = { anonymize_ip: true, cookie_expires: 0 };
  if (host && host !== 'localhost' && !isIp) config.cookie_domain = host;
  if (debugMode) config.debug_mode = true;
  gtag('config', GA_ID, config);
})();
