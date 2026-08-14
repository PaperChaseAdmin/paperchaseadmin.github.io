/* Records page — shared logic. Requires BOT_ID/BOT_NAME/BOT_AVATAR/BOT_COLOR globals.
   Matches the generated records template: #stats (stat-cell grid) + #records-list (record-row grid). */
'use strict';

const BASE2 = `/trade/data/bots/${BOT_ID}/`;
let allTrades = [], filter = 'all';

const $2 = id => document.getElementById(id);
function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c])); }
function fmt2(v) { return '$' + Math.abs(+v).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2}); }
function fmtTs2(ts) { const d = new Date(ts); return d.toLocaleDateString('en-US', {year: 'numeric', month: 'short', day: 'numeric'}) + ' ' + d.toLocaleTimeString('en-US', {hour: '2-digit', minute: '2-digit', hour12: false}); }

function setFilter(f, btn) {
  filter = f;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  renderTable();
}

function renderStats(trades) {
  const buys = trades.filter(t => t.action === 'BUY');
  const sells = trades.filter(t => t.action === 'SELL');
  const vol = trades.reduce((s, t) => s + (+t.total_value || 0), 0);
  $2('stats').innerHTML =
    '<div class="stat-cell"><div class="stat-lbl">Total Trades</div><div class="stat-val">' + trades.length + '</div></div>' +
    '<div class="stat-cell"><div class="stat-lbl">Buys</div><div class="stat-val profit">' + buys.length + '</div></div>' +
    '<div class="stat-cell"><div class="stat-lbl">Sells</div><div class="stat-val loss">' + sells.length + '</div></div>' +
    '<div class="stat-cell"><div class="stat-lbl">Total Volume</div><div class="stat-val">' + fmt2(vol) + '</div></div>';
}

function renderTable() {
  const filtered = filter === 'all' ? allTrades : allTrades.filter(t => t.action === filter);
  const el = $2('records-list');
  if (!el) return;
  if (!filtered.length) {
    el.innerHTML = '<div class="empty">' + (allTrades.length ? 'No trades match this filter.' : 'No trades yet — bot activates when US market opens.') + '</div>';
    return;
  }
  let rows = '';
  [...filtered].reverse().forEach(t => {
    const badge = t.action === 'BUY' ? '<span class="badge badge-buy">BUY</span>' : '<span class="badge badge-sell">SELL</span>';
    rows += '<div class="record-row">' +
      '<span class="record-date">' + fmtTs2(t.timestamp) + '</span>' +
      '<span class="record-action">' + badge + '</span>' +
      '<span class="record-sym">' + esc(t.ticker) + '</span>' +
      '<span class="record-qty">' + esc(t.shares) + '</span>' +
      '<span class="record-price">' + fmt2(t.price) + '</span>' +
      '<div class="record-reason">' + esc(t.reasoning) + '</div>' +
      '</div>';
  });
  el.innerHTML = rows;
}

document.addEventListener('DOMContentLoaded', async () => {
  document.title = (typeof BOT_NAME !== 'undefined' ? BOT_NAME : 'Bot') + ' Records · PaperChase';
  try {
    const data = await fetch(BASE2 + 'trades.json').then(r => r.json());
    allTrades = data.trades || [];
  } catch (e) {
    console.error('Records load error:', e);
  }
  renderStats(allTrades);
  renderTable();
});
