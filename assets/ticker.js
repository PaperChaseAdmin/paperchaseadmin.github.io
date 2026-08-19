/* Ticker tape — PaperChase signature element.
   Renders a scrolling strip of live indices + crypto from market_data.json.
   Requires a <div class="ticker-wrap"><div class="ticker-track" id="tickerTrack"></div></div>
   in the page. Content duplicated for a seamless CSS loop. */
(function () {
  var track = document.getElementById('tickerTrack');
  if (!track) return;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function fmt(v) {
    return v == null ? '—' : '$' + Number(v).toLocaleString('en-US', { maximumFractionDigits: 2 });
  }

  fetch('https://paperchase.online/data/market_data.json', { cache: 'no-store' })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      var items = [];
      // indices: stocks.indices = { sp500: {value, change_24h}, nasdaq, dow, vix }
      var idx = (d.stocks && d.stocks.indices) || {};
      Object.keys(idx).forEach(function (k) {
        var v = idx[k];
        if (v && v.value != null) {
          items.push({ sym: k.toUpperCase(), price: v.value, chg: v.change_24h });
        }
      });
      // crypto: crypto.prices = [ {symbol, price_usd, change_24h}, ... ]
      (d.crypto && d.crypto.prices || []).slice(0, 6).forEach(function (c) {
        items.push({ sym: (c.symbol || '').toUpperCase(), price: c.price_usd, chg: c.change_24h });
      });
      if (!items.length) return;
      var html = items.map(function (it) {
        var cls = it.chg >= 0 ? 't-up' : 't-down';
        var arrow = it.chg >= 0 ? '▲' : '▼';
        return '<span class="ticker-item"><span class="t-sym">' + esc(it.sym) + '</span>' +
          '<span>' + fmt(it.price) + '</span>' +
          '<span class="' + cls + '">' + arrow + ' ' + Math.abs(it.chg).toFixed(2) + '%</span></span>';
      }).join('');
      track.innerHTML = html + html; // duplicate for seamless loop
    })
    .catch(function () { /* silent — ticker is decorative */ });
})();
