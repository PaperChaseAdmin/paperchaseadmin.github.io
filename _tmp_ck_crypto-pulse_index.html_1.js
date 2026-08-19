
const DATA_URL = 'https://raw.githubusercontent.com/PaperChaseAdmin/market-sentinel/main/data/market_data.json';

function fmtPrice(v) {
  if (v == null) return '—';
  if (v >= 1000) return '$' + v.toLocaleString('en', {maximumFractionDigits:0});
  if (v >= 1) return '$' + v.toFixed(2);
  if (v >= 0.01) return '$' + v.toFixed(4);
  return '$' + v.toFixed(6);
}

function fmtChg(v) { return v == null ? '' : (v >= 0 ? '+' : '') + v.toFixed(2) + '%'; }
function chgClass(v) { return v == null ? '' : v >= 0 ? 'text-green' : 'text-red'; }

// ── Countdown ────────────────────────────
let _cdTimer = null;
function onDataLoaded(updatedAt) {
  clearInterval(_cdTimer);
  const el = document.getElementById('countdown-wrap');
  if (!el || typeof window.startCountdown !== 'function') return;
  _cdTimer = window.startCountdown(el, 'Next Scan', 'crypto-pulse', loadData);
}

async function loadData() {
  try {
    const resp = await fetch(DATA_URL + '?t=' + Date.now());
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const raw = await resp.json();
    const c = raw.crypto || {};
    const s = raw.stocks || {};
    const data = {
      fear_greed: c.fear_greed,
      crypto_sentiment: c.news_sentiment || {score: 0, label: ''},
      crypto_prices: {},
      poly_markets: c.polymarket || [],
      news: c.news || [],
      reddit_activity: c.reddit || [],
      cg_trending: c.cg_trending || [],
      macro: s.macro || [],
      most_active: s.most_active || [],
    };
    if (Array.isArray(c.prices)) {
      c.prices.forEach(p => { data.crypto_prices[p.symbol] = {price: p.price_usd, change_pct: p.change_24h}; });
    }
    onDataLoaded(raw.updated_at || raw.timestamp || new Date().toISOString());
    render(data);
  } catch (e) {
    document.getElementById('main-loading').innerHTML = '<div style="color:var(--pc-text-3);padding:60px">⚠️ Unable to load crypto data. <a href="javascript:location.reload()" style="color:var(--pc-purple)">Retry</a></div>';
  }
}

function render(d) {
  document.getElementById('main-loading').style.display = 'none';
  document.getElementById('main-content').style.display = 'block';

  // Fear & Greed
  const fg = d.fear_greed || {};
  const fgVal = fg.value;
  if (fgVal != null) {
    const angle = -90 + (fgVal / 100) * 180;
    document.getElementById('gauge-needle').setAttribute('transform', 'rotate(' + angle + ',100,100)');
    document.getElementById('fg-value').textContent = fgVal;
    document.getElementById('fg-label').textContent = fg.label || (fgVal >= 75 ? 'Extreme Greed' : fgVal >= 55 ? 'Greed' : fgVal >= 45 ? 'Neutral' : fgVal >= 25 ? 'Fear' : 'Extreme Fear');
    if (fg.change != null) {
      const chg = fg.change;
      document.getElementById('fg-delta').innerHTML = '<span class="' + chgClass(chg) + '">' + (chg >= 0 ? '▲' : '▼') + ' ' + Math.abs(chg) + '</span>';
    }
  }

  // Crypto sentiment
  const cs = d.crypto_sentiment || {};
  if (cs.score != null) {
    document.getElementById('crypto-sentiment-score').textContent = cs.score.toFixed(1);
    document.getElementById('crypto-sentiment-label').textContent = cs.label || '';
    document.getElementById('crypto-sentiment-score').style.color = cs.score > 0 ? 'var(--pc-green)' : cs.score < 0 ? 'var(--pc-red)' : 'var(--pc-text-3)';
  }
  if (cs.breakdown) {
    let bars = '';
    Object.entries(cs.breakdown).slice(0,4).forEach(([k,v]) => {
      const pct = Math.min(Math.abs(v||0)*100, 100);
      const color = v >= 0 ? 'var(--pc-green)' : 'var(--pc-red)';
      bars += '<div class="sentiment-row"><span class="sentiment-label">' + k + '</span><div class="bar-track"><div class="bar-fill" style="width:' + pct + '%;background:' + color + '"></div></div></div>';
    });
    document.getElementById('crypto-sentiment-bars').innerHTML = bars;
  }

  // Crypto prices
  if (d.crypto_prices) {
    let html = '';
    Object.entries(d.crypto_prices).slice(0,12).forEach(([sym, c]) => {
      if (!c || c.price == null) return;
      html += '<div class="price-row"><span class="price-sym">' + sym + '</span><span class="price-val">' + fmtPrice(c.price) + '</span><span class="' + chgClass(c.change_pct) + '">' + fmtChg(c.change_pct) + '</span></div>';
    });
    document.getElementById('crypto-prices').innerHTML = html;
  }

  // Poly Watch crypto
  if (d.poly_markets && d.poly_markets.length) {
    let html = '';
    d.poly_markets.slice(0,5).forEach(m => {
      const pct = (m.yes_price||0)*100;
      html += '<div class="price-row"><span class="price-sym" style="font-size:11px;min-width:0;max-width:180px;white-space:normal;line-height:1.3;font-family:var(--pc-font)">' + esc(m.title||m.question||'?') + '</span><span class="price-val" style="font-size:12px;text-align:right">' + pct.toFixed(1) + '%</span></div>';
    });
    document.getElementById('crypto-polymarket').innerHTML = html || '<div style="color:var(--pc-text-3);font-size:12px;padding:8px 0">No crypto markets</div>';
  }

  // Crypto news
  if (d.news && d.news.length) {
    let html = '';
    d.news.slice(0,6).forEach(n => {
      html += '<div class="news-item"><span class="news-source">' + esc(n.source||'') + '</span><a class="news-title" href="' + esc(n.url||'#') + '" target="_blank">' + esc(n.title) + '</a></div>';
    });
    document.getElementById('crypto-news').innerHTML = html;
  }

  // CoinGecko trending
  if (d.cg_trending && d.cg_trending.length) {
    let html = '';
    d.cg_trending.slice(0,8).forEach(t => {
      html += '<div class="trending-row"><span class="trending-sym">' + (t.symbol||'').toUpperCase() + '</span><span class="trending-name">' + esc(t.name||'') + '</span></div>';
    });
    document.getElementById('crypto-cg-trending').innerHTML = html;
  } else if (d.trending_searches) {
    let html = '';
    d.trending_searches.slice(0,8).forEach(t => {
      html += '<div class="trending-row"><span class="trending-sym">' + (t.symbol||'').toUpperCase() + '</span><span class="trending-name">' + esc(t.name||t.symbol||'') + '</span></div>';
    });
    document.getElementById('crypto-cg-trending').innerHTML = html;
  }

  // ── Macro ──
  if (d.macro && d.macro.length) {
    let h = '';
    d.macro.forEach(m => {
      const chg = m.change_24h;
      h += '<div class="price-row"><span class="price-sym" style="min-width:100px;font-family:var(--pc-font);font-size:12px">' + (m.name||m.symbol) + '</span><span class="price-val">' + (m.value != null ? m.value : '—') + '</span><span class="' + (chg >= 0 ? 'text-green' : 'text-red') + '">' + (chg >= 0 ? '+' : '') + (chg||0).toFixed(2) + '%</span></div>';
    });
    document.getElementById('crypto-macro').innerHTML = h;
  }

  // ── Most Active ──
  if (d.most_active && d.most_active.length) {
    let h = '';
    d.most_active.slice(0,8).forEach(m => {
      h += '<div class="price-row"><span class="price-sym">' + m.symbol + '</span><span class="price-val">$' + (m.price_usd||0).toLocaleString('en',{maximumFractionDigits:2}) + '</span><span class="' + (m.change_24h >= 0 ? 'text-green' : 'text-red') + '">' + (m.change_24h >= 0 ? '+' : '') + (m.change_24h||0).toFixed(2) + '%</span></div>';
    });
    document.getElementById('crypto-active').innerHTML = h;
  }

  // Save crypto prediction to localStorage for home page
  const today = new Date().toISOString().slice(0,10);
  let cryptoHist = JSON.parse(localStorage.getItem('cryptopulse_predictions') || '[]');
  if (!cryptoHist.find(h => h.date === today)) {
    cryptoHist.unshift({ date: today, result: null, direction: null });
    localStorage.setItem('cryptopulse_predictions', JSON.stringify(cryptoHist.slice(0,10)));
  }
}

loadData();
