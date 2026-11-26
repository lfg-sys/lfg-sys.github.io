// Tracked links (LFG decision 134): lookingforgame.co.uk/r/<slug> or lfgame.co.uk/r/?<slug>.
// Counts the click (no IP or personal data is stored) and forwards to Google Play with the link's install referrer,
// or to the App Store on iPhone and iPad.
(function () {
  var URL_ = 'https://vulgyfzelewuceatdloj.supabase.co/rest/v1/rpc/link_click';
  var KEY = 'sb_publishable_9TxQtrSnAyZKyibFMWpOqQ_fosdZqnm';
  var PLAY = 'https://play.google.com/store/apps/details?id=uk.co.lfgame.app';
  var APPLE = 'https://apps.apple.com/app/id6835639075';   // iPhone and iPad go to the App Store (26 Nov 2026)
  // App Store campaign tag (26 Nov 2026): once PT holds Rung App Ltd's provider number (App Store Connect → Analytics
  // → Sources → generate a campaign link; the pt= value), iPhone clicks carry the link's name as the campaign, so App
  // Analytics shows store visits and downloads per link. Empty = plain App Store link, as before.
  var PT = '129812972';
  var m = location.pathname.match(/\/r\/([a-z0-9-]+)\/?$/i);
  var slug = (m ? m[1] : (location.search.replace(/^\?/, '').split('&')[0] || '')).toLowerCase().slice(0, 48);
  var ua = navigator.userAgent || '';
  var device = /android/i.test(ua) ? 'android' : /iphone|ipad|ipod/i.test(ua) ? 'ios' : /windows|macintosh|linux/i.test(ua) ? 'desktop' : 'other';
  if (PT && slug) APPLE = 'https://apps.apple.com/app/apple-store/id6835639075?pt=' + PT + '&ct=' + encodeURIComponent(slug) + '&mt=8';
  var gone = false;
  function go(url) { if (gone) return; gone = true; location.replace(device === 'ios' ? APPLE : (url || PLAY)); }
  setTimeout(function () { go(PLAY); }, 2500);   // never leave anyone waiting on a slow connection
  if (!slug) { go(PLAY); return; }
  fetch(URL_, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'apikey': KEY },
    body: JSON.stringify({ p_slug: slug, p_device: device })
  }).then(function (r) { return r.ok ? r.json() : null; })
    .then(function (url) { go(typeof url === 'string' && /^https:\/\//.test(url) ? url : PLAY); })
    .catch(function () { go(PLAY); });
})();
