
const DATA_URL = 'https://raw.githubusercontent.com/PaperChaseAdmin/market-sentinel/main/data/market_data.json';

let _cdTimer = null;
function onDataLoaded(updatedAt) {
  clearInterval(_cdTimer);
  const el = document.getElementById('countdown-wrap');
  if (!el || typeof window.startCountdown !== 'function') return;
  _cdTimer = window.startCountdown(el, 'Next update in', 'market-sentinel', loadData);
}

const fmtPrice = v => v == null ? '—' : v >= 1000 ? '$' + v.toLocaleString('en', {maximumFractionDigits:0}) : v >= 1 ? '$' + v.toFixed(2) : '$' + v.toFixed(4);
const fmtChg = v => v == null ? '' : (v >= 0 ? '+' : '') + v.toFixed(2) + '%';
const chgColor = v => v == null ? '' : v >= 0 ? 'var(--pc-green)' : 'var(--pc-red)';
const sentColor = function(s) {
  if (!s) return 'var(--pc-text-3)';
  var l = s.toLowerCase();
  if (l === 'bullish' || l === 'greed' || l === 'positive') return 'var(--pc-green)';
  if (l === 'bearish' || l === 'fear' || l === 'extreme fear' || l === 'negative') return 'var(--pc-red)';
  return 'var(--pc-text-3)';
};

function loadData() {
  fetch(DATA_URL + '?t=' + Date.now())
    .then(function(r) { return r.json(); })
    .then(function(d) { renderAll(d); })
    .catch(function(e) {
      document.getElementById('main-loading').innerHTML = '⚠️ Failed to load: ' + e.message;
    });
}

function renderAll(d) {
  document.getElementById('main-loading').style.display = 'none';
  document.getElementById('main-content').style.display = 'block';

  var st = d.stocks || {};
  var md = d.market_mood || st.market_mood || {};
  var moodScore = md.score !== undefined ? Math.round(md.score * 100) : null;
  var moodLabel = md.label || 'Neutral';

  // ── Mood hero ──
  var mhEl = document.getElementById('mhScore');
  var mhLabel = document.getElementById('mhLabel');
  var mhFill = document.getElementById('mhFill');
  if (moodScore !== null) {
    mhEl.textContent = moodScore + '/100';
    mhEl.style.color = sentColor(moodLabel);
    mhLabel.textContent = moodLabel.toUpperCase();
    mhLabel.style.color = sentColor(moodLabel);
    mhFill.style.width = moodScore + '%';
    mhFill.style.background = sentColor(moodLabel);
  }
  document.getElementById('mhSub').textContent = 'Overall market sentiment · ' + (d.updated_at || '').slice(0,10) || 'Latest';

  // ── Indices (dict: {sp500:{value,change_24h}, ...}) ──
  var indices = st.indices || {};
  var idxHtml = '';
  var idxNames = {'sp500':'S&P 500','nasdaq':'NASDAQ','dow':'DOW','vix':'VIX'};
  var idxOrder = ['sp500','nasdaq','dow','vix'];
  idxOrder.forEach(function(k) {
    var idx = indices[k];
    if (!idx) return;
    var price = idx.value;
    var chg = idx.change_24h || 0;
    idxHtml += '<div class="idx-mini">' +
      '<div class="im-name">' + (idxNames[k]||k) + '</div>' +
      '<div class="im-val">' + (price != null ? (price >= 1000 ? '$' + Math.round(price).toLocaleString() : '$' + price.toFixed(2)) : '—') + '</div>' +
      '<div class="im-chg" style="color:' + chgColor(chg) + '">' + fmtChg(chg) + '</div></div>';
  });
  document.getElementById('idxGrid').innerHTML = idxHtml || '<div style="color:var(--pc-text-3);font-size:11px">No data</div>';

  // ── Fear & Greed ──
  var fg = (d.crypto || {}).fear_greed || {};
  var fgVal = fg.value !== undefined ? parseInt(fg.value) : null;
  var fgClass = (fg.label || '').toLowerCase();
  var fgHtml = '';
  if (fgVal !== null) {
    var fgColor = fgClass === 'greed' || fgClass === 'extreme greed' ? 'var(--pc-green)' : (fgClass === 'fear' || fgClass === 'extreme fear') ? 'var(--pc-red)' : 'var(--pc-yellow)';
    fgHtml = '<span class="fg-val" style="color:' + fgColor + '">' + fgVal + '</span>' +
      '<span class="fg-label" style="background:var(--pc-surface-2);color:' + fgColor + '">' + (fg.label||'').toUpperCase() + '</span>' +
      '<div class="fg-bar"><div class="fg-fill" style="width:' + fgVal + '%;background:' + fgColor + '"></div></div>';
  } else {
    fgHtml = '<span style="color:var(--pc-text-3);font-size:12px">Loading...</span>';
  }
  document.getElementById('fgMini').innerHTML = fgHtml;

  // ── News Media ──
  var newsItems = st.news || [];
  var newsSent = st.news_sentiment || {};
  var nsScore = newsSent.score !== undefined ? Math.round((newsSent.score + 1) * 50) : null;
  var nsLabel = newsSent.label || '';
  var nsHtml = '';
  if (nsScore !== null) {
    nsHtml = '<span class="ss-val" style="color:' + sentColor(nsLabel) + '">' + nsScore + '</span>' +
      '<span class="ss-label" style="background:var(--pc-surface-2);color:' + sentColor(nsLabel) + '">' + (nsLabel||'').toUpperCase() + '</span>' +
      '<div class="ss-bar"><div class="ss-fill" style="width:' + nsScore + '%;background:' + sentColor(nsLabel) + '"></div></div>';
  } else {
    nsHtml = '<span style="color:var(--pc-text-3);font-size:12px">' + newsItems.length + ' articles loaded</span>';
  }
  document.getElementById('newsScore').innerHTML = nsHtml;

  var newsHtml = '';
  newsItems.slice(0,12).forEach(function(n) {
    var s = (n.sentiment||'neutral').toLowerCase();
    newsHtml += '<li>' +
      '<span class="ms-news-src">' + esc(n.source||'') + '</span> ' +
      '<span class="ms-news-title">' + esc(n.title) + '</span>' +
      '<span class="ms-news-sent" style="color:' + sentColor(s) + '">' + s.toUpperCase() + '</span></li>';
  });
  document.getElementById('newsList').innerHTML = newsHtml || '<li style="color:var(--pc-text-3)">No recent news</li>';

  // ── Social / Forums ──
  var socialHtml = '';
  // Poly watch
  var poly = st.polymarket || [];
  var polySum = st.polymarket_summary || {};
  if (polySum.outlook) {
    socialHtml += '<div class="src-score" style="margin-bottom:6px">' +
      '<span class="ss-label" style="background:var(--pc-surface-2);color:' + sentColor(polySum.outlook) + ';font-size:10px">POLY: ' + (polySum.outlook||'').toUpperCase() + '</span></div>';
  }
  // Reddit
  var reddit = st.reddit || [];
  if (reddit.length) {
    socialHtml += '<div style="font-size:11px;margin-bottom:4px;color:var(--pc-text-2)">Reddit: ' + reddit.length + ' threads</div>';
  } else {
    // Try crypto reddit
    var cryReddit = (d.crypto || {}).reddit || [];
    if (cryReddit.length) {
      socialHtml += '<div style="font-size:11px;margin-bottom:4px;color:var(--pc-text-2)">Reddit (crypto): ' + cryReddit.length + ' mentions</div>';
    }
  }
  // Poly markets
  if (poly.length) {
    poly.slice(0,4).forEach(function(p) {
      var yesPrice = p.yes_price != null ? Math.round(p.yes_price * 100) : 0;
      socialHtml += '<div class="poly-item"><span>' + esc(p.title||'').slice(0,40) + '</span><span style="font-weight:600;font-family:var(--pc-mono)">' + yesPrice + '%</span></div>';
    });
  }
  document.getElementById('socialSection').innerHTML = socialHtml || '<div style="color:var(--pc-text-3);font-size:11px">Loading forum data...</div>';

  // ── Macro ──
  var macroHtml = '';
  var macroArr = st.macro || [];
  if (macroArr.length) {
    macroArr.slice(0,4).forEach(function(m) {
      var val = m.value != null ? (m.symbol === '^TNX' ? m.value.toFixed(2) + '%' : m.symbol === 'DX-Y.NYB' ? m.value.toFixed(2) : m.value >= 100 ? '$' + Math.round(m.value).toLocaleString() : '$' + m.value.toFixed(2)) : '—';
      macroHtml += '<div class="macro-item"><span class="mi-name">' + (m.name||'') + '</span><span class="mi-val">' + val + '</span></div>';
    });
  } else {
    macroHtml = '<div style="color:var(--pc-text-3);font-size:11px">No macro data</div>';
  }
  document.getElementById('macroGrid').innerHTML = macroHtml;

  // ── Politics / Geopolitical ──
  var polHtml = '<ul class="ms-news">';
  // Scan news for political keywords
  var politicalNews = newsItems.filter(function(n) {
    var t = (n.title || '').toLowerCase();
    return t.includes('trump') || t.includes('china') || t.includes('iran') || t.includes('russia') || t.includes('ukraine') ||
           t.includes('tariff') || t.includes('trade war') || t.includes('sanction') || t.includes('congress') ||
           t.includes('fed') || t.includes('federal reserve') || t.includes('political') || t.includes('president') ||
           t.includes('senate') || t.includes('strike') || t.includes('military') || t.includes('diplomat');
  });
  if (politicalNews.length) {
    politicalNews.slice(0,8).forEach(function(n) {
      var s = (n.sentiment||'neutral').toLowerCase();
      polHtml += '<li><span class="ms-news-src">' + esc(n.source||'') + '</span> ' +
        '<span class="ms-news-title">' + esc(n.title) + '</span>' +
        '<span class="ms-news-sent" style="color:' + sentColor(s) + '">' + s.toUpperCase() + '</span></li>';
    });
  } else {
    polHtml += '<li style="color:var(--pc-text-3)">No political news in current feed</li>';
  }
  polHtml += '</ul>';
  document.getElementById('politicsSection').innerHTML = polHtml;

  // Countdown
  onDataLoaded(d.updated_at);
}

// ── Load on page load ──
document.addEventListener('DOMContentLoaded', function() { loadData(); });
