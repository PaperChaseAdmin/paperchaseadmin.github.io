
const DATA_URL = 'data/picks.json';
let _cdTimer = 0;

function fmtPrice(v) {
  if (v == null) return '—';
  return v >= 1 ? '$' + v.toLocaleString('en', {minimumFractionDigits:2, maximumFractionDigits:2}) : '$' + v.toFixed(4);
}
function fmtCap(v) {
  if (v == null) return '—';
  return '$' + v.toFixed(1) + 'B';
}
function fmtPE(v) {
  if (v == null) return '—';
  return v.toFixed(1);
}
function fmtRSI(v) {
  if (v == null) return '—';
  return v.toFixed(1);
}

function scoreClass(s) {
  if (s == null) return 'score-low';
  if (s >= 50) return 'score-high';
  if (s >= 40) return 'score-mid';
  return 'score-low';
}

function macdClass(s) {
  if (s === 'golden') return 'macd-golden';
  if (s === 'death') return 'macd-death';
  return 'macd-none';
}
function macdLabel(s) {
  if (s === 'golden') return 'Golden';
  if (s === 'death') return 'Death';
  return '—';
}

function renderPicks(data) {
  const picks = data.picks || [];
  document.getElementById('table-loading').style.display = 'none';
  document.getElementById('table-wrap').style.display = 'block';

  document.getElementById('stat-total').textContent = data.total_screened || '—';
  document.getElementById('stat-passing').textContent = data.passing || '—';
  const updated = data.updated_at ? new Date(data.updated_at).toLocaleDateString('en-US', {month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'}) : '—';
  document.getElementById('stat-updated').textContent = updated;

  let html = '';
  picks.forEach((p, i) => {
    const rank = i + 1;
    const sClass = scoreClass(p.composite_score);
    const mClass = macdClass(p.macd_signal);
    const mLbl = macdLabel(p.macd_signal);
    html += '<tr>' +
      '<td style="text-align:center;font-weight:600;color:var(--pc-text-3);font-family:var(--pc-mono)">' + rank + '</td>' +
      '<td><strong>' + p.symbol + '</strong></td>' +
      '<td style="font-size:12px">' + esc(p.company_name || '—') + '</td>' +
      '<td style="font-size:11px;color:var(--pc-text-2)">' + esc(p.sector || '—') + '</td>' +
      '<td style="text-align:right;font-family:var(--pc-mono);font-size:12px">' + fmtPrice(p.price) + '</td>' +
      '<td style="text-align:right;font-family:var(--pc-mono);font-size:12px">' + fmtCap(p.market_cap) + '</td>' +
      '<td style="text-align:right;font-family:var(--pc-mono);font-size:12px">' + fmtPE(p.pe_ratio) + '</td>' +
      '<td style="text-align:center"><span class="macd-badge ' + mClass + '">' + mLbl + '</span></td>' +
      '<td style="text-align:center;font-family:var(--pc-mono);font-size:12px">' + fmtRSI(p.rsi) + '</td>' +
      '<td style="text-align:center"><span class="score-badge ' + sClass + '">' + (p.composite_score != null ? p.composite_score.toFixed(1) : '—') + '</span></td>' +
      '<td><div class="summary-cell">' + esc(p.summary || '') + '</div></td>' +
      '<td><div class="summary-cell" style="color:var(--pc-purple);font-size:11px">' + esc(p.ai_analysis || '') + '</div></td>' +
      '</tr>';
  });
  document.getElementById('picks-body').innerHTML = html;
}

async function loadData() {
  try {
    const resp = await fetch(DATA_URL + '?t=' + Date.now());
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    const data = await resp.json();
    renderPicks(data);
    const el = document.getElementById('countdown-wrap');
    if (window.startCountdown) {
      clearInterval(_cdTimer);
      _cdTimer = startCountdown(el, 'Next Pick', 'stock-pick', loadData);
    }
  } catch (e) {
    document.getElementById('table-loading').innerHTML = '<div style="color:var(--pc-text-3);padding:60px;text-align:center">⚠️ Unable to load picks. <a href="javascript:location.reload()" style="color:var(--pc-purple)">Retry</a></div>';
  }
}

loadData();
