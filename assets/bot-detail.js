/* Bot detail page — v2 with real-time prices, clickable positions, countdown */
'use strict';

const BASE = `https://raw.githubusercontent.com/PaperChaseAdmin/trade/main/data/bots/${BOT_ID}/`;
let chart = null;
let expandedRow = null;

const $ = id => document.getElementById(id);
function fmt(v){ return '$'+Math.abs(+v).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}); }
function sign(v){ const c=+v>=0?'profit':'loss'; return '<span class="'+c+'">'+(+v>=0?'+':'-')+fmt(Math.abs(+v))+'</span>'; }
function ago(ts){ const m=Math.floor((Date.now()-new Date(ts))/60000); return m<1?'just now':m<60?`${m}m ago`:m<1440?`${Math.floor(m/60)}h ago`:`${Math.floor(m/1440)}d ago`; }
function fmtTs(ts){ const d=new Date(ts); return d.toLocaleDateString('en-US',{month:'short',day:'numeric'})+' '+d.toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit',hour12:false})+' UTC'; }

// ── Countdown to next review or market open ──
let _cdTimer = null;
function startCountdown(pf) {
  clearInterval(_cdTimer);
  const el = $('countdown-wrap');
  if (!el) return;
  
  function nextMarketOpen() {
    const now = new Date();
    const day = now.getUTCDay();
    const hour = now.getUTCHours();
    const min = now.getUTCMinutes();
    const next = new Date(now);
    
    if (day === 0 || day === 6 || (day === 5 && hour >= 21)) {
      const daysUntilMonday = day === 0 ? 1 : day === 6 ? 2 : (8 - day);
      next.setDate(next.getDate() + daysUntilMonday);
      next.setUTCHours(13, 30, 0, 0);
    } else if (hour < 13 || (hour === 13 && min < 30)) {
      next.setUTCHours(13, 30, 0, 0);
    } else if (hour >= 21) {
      next.setDate(next.getDate() + 1);
      next.setUTCHours(13, 30, 0, 0);
    } else {
      const nextHalf = Math.ceil((hour * 60 + min) / 30) * 30;
      next.setUTCHours(Math.floor(nextHalf/60), nextHalf%60, 0, 0);
    }
    return next;
  }
  
  const target = nextMarketOpen();
  
  function tick() {
    const diff = target - Date.now();
    if (diff <= 0) { el.innerHTML = '<span class="countdown-num">Checking now...</span>'; return; }
    const h = Math.floor(diff / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    
    if (h >= 24) {
      const d = Math.floor(h / 24);
      el.innerHTML = '<span class="countdown-lbl">Next Review</span><span class="countdown-num">' + d + 'd ' + (h%24) + 'h ' + m + 'm</span>';
    } else if (h >= 1) {
      el.innerHTML = '<span class="countdown-lbl">Next Review</span><span class="countdown-num">' + h + 'h ' + m + 'm ' + s + 's</span>';
    } else {
      el.innerHTML = '<span class="countdown-lbl">Next Review</span><span class="countdown-num">' + m + 'm ' + s + 's</span>';
    }
  }
  tick();
  _cdTimer = setInterval(tick, 1000);
}

// ── Current Prices Bar (ticker prices above last session) ──
function renderPricesBar(pf) {
  const pos = pf.positions || {};
  const keys = Object.keys(pos);
  if (!keys.length) { $('prices-bar').innerHTML = ''; return; }
  
  let html = '<div class="prices-bar"><div class="prices-bar-title">Current Positions <span class="prices-bar-sub">live prices</span></div><div class="prices-bar-items">';
  keys.forEach(t => {
    const p = pos[t];
    const cur = p.current_price || p.avg_cost;
    const chg = ((cur - p.avg_cost) / p.avg_cost * 100);
    html += '<div class="price-chip">' +
      '<span class="price-chip-sym">' + t + '</span>' +
      '<span class="price-chip-val">' + fmt(cur) + '</span>' +
      '<span class="price-chip-chg ' + (chg>=0?'profit':'loss') + '">' + (chg>=0?'+':'') + chg.toFixed(2) + '%</span>' +
    '</div>';
  });
  html += '</div></div>';
  $('prices-bar').innerHTML = html;
}

// ── Clickable Position Rows ──
function renderPositions(pf){
  const pos = pf.positions || {};
  const el = $('positions');
  if (!Object.keys(pos).length) { el.innerHTML='<div class="empty">No open positions \u2014 all cash</div>'; return; }
  
  // Get trade history for this bot to find entry details
  // We'll store it as a map ticker->latest trade
  fetch(BASE+'trades.json?t='+Date.now()).then(r=>r.json()).then(tr => {
    const tradeMap = {};
    (tr.trades||[]).forEach(t => {
      if (t.action === 'BUY' && !tradeMap[t.ticker]) tradeMap[t.ticker] = t;
    });
    // Override with most recent buy for each ticker
    (tr.trades||[]).forEach(t => {
      if (t.action === 'BUY') tradeMap[t.ticker] = t;
    });
    
    let rows = '';
    for(const t in pos) {
      const p = pos[t];
      const cur = p.current_price || p.avg_cost;
      const pnl = (cur - p.avg_cost) * p.shares;
      const pct = (cur - p.avg_cost) / p.avg_cost * 100;
      const entry = tradeMap[t];
      
      rows += '<tr class="pos-row" onclick="toggleExpand(\'' + t + '\',this)" style="cursor:pointer">' +
        '<td class="mono" style="font-weight:600">' + t + '</td>' +
        '<td class="mono">' + p.shares + '</td>' +
        '<td class="mono">' + fmt(p.avg_cost) + '</td>' +
        '<td class="mono">' + fmt(cur) + '</td>' +
        '<td class="mono">' + fmt(p.shares*cur) + '</td>' +
        '<td class="mono ' + (pnl>=0?'profit':'loss') + '">' + (pnl>=0?'+':'-') + fmt(Math.abs(pnl)) + 
        ' <span style="font-size:11px">(' + (pct>=0?'+':'') + pct.toFixed(2) + '%)</span></td>' +
        '<td class="mono" style="color:var(--tv-text-3);font-size:10px">\u25bc</td>' +
      '</tr>' +
      '<tr class="pos-expand" id="expand-' + t + '" style="display:none">' +
        '<td colspan="7">' +
          '<div class="pos-detail">' +
            (entry ? 
              '<div class="pos-detail-row"><span class="pos-detail-lbl">Entry Time</span><span class="pos-detail-val">' + fmtTs(entry.timestamp) + '</span></div>' +
              '<div class="pos-detail-row"><span class="pos-detail-lbl">Entry Price</span><span class="pos-detail-val">' + fmt(entry.price) + '</span></div>' +
              '<div class="pos-detail-row"><span class="pos-detail-lbl">Shares</span><span class="pos-detail-val">' + entry.shares + '</span></div>' +
              '<div class="pos-detail-row"><span class="pos-detail-lbl">Total Cost</span><span class="pos-detail-val">' + fmt(entry.total_value) + '</span></div>' +
              (entry.reasoning ? '<div class="pos-detail-row" style="flex-direction:column;gap:4px"><span class="pos-detail-lbl">Signal</span><span class="pos-detail-val" style="font-size:11px;line-height:1.5;max-width:500px">' + entry.reasoning + '</span></div>' : '') +
              (entry.signal_context ? '<div class="pos-detail-row"><span class="pos-detail-lbl">Market Context</span><span class="pos-detail-val" style="display:flex;flex-wrap:wrap;gap:3px">' + 
                (entry.signal_context.ticker_chg_pct != null ? '<span class="ctx-item ' + (entry.signal_context.ticker_chg_pct>=0?'ctx-up':'ctx-down') + '">' + t + ': ' + (entry.signal_context.ticker_chg_pct>=0?'+':'') + Number(entry.signal_context.ticker_chg_pct).toFixed(1) + '%</span>' : '') +
                (entry.signal_context.fg_value != null ? '<span class="ctx-item">F&G: ' + entry.signal_context.fg_value + (entry.signal_context.fg_label?' ('+entry.signal_context.fg_label+')':'') + '</span>' : '') +
                (entry.signal_context.sp500_chg != null ? '<span class="ctx-item ' + (entry.signal_context.sp500_chg>=0?'ctx-up':'ctx-down') + '">S&P: ' + (entry.signal_context.sp500_chg>=0?'+':'') + Number(entry.signal_context.sp500_chg).toFixed(1) + '%</span>' : '') +
                (entry.signal_context.vix != null ? '<span class="ctx-item">VIX: ' + Number(entry.signal_context.vix).toFixed(1) + '</span>' : '') +
              '</span></div>' : '')
            : '<div class="pos-detail-row"><span class="pos-detail-val" style="color:var(--tv-text-3)">Entry details not available</span></div>'
            ) +
          '</div>' +
        '</td>' +
      '</tr>';
    }
    el.innerHTML = '<div class="table-wrap"><table><thead><tr><th>Ticker</th><th>Shares</th><th>Avg Cost</th><th>Current</th><th>Mkt Value</th><th>Unrealised P&amp;L</th><th style="width:30px"></th></tr></thead><tbody>' + rows + '</tbody></table></div>';
  });
}

function toggleExpand(ticker, row) {
  const expandRow = document.getElementById('expand-' + ticker);
  if (!expandRow) return;
  const isVisible = expandRow.style.display !== 'none';
  
  // Close all others
  document.querySelectorAll('.pos-expand').forEach(el => el.style.display = 'none');
  
  if (!isVisible) {
    expandRow.style.display = 'table-row';
  }
}

function renderSpecs() {
  if (typeof BOT_WATCHLIST === 'undefined') return;
  const pct = (BOT_MAX_POSITION * 100).toFixed(0);
  const tickers = BOT_WATCHLIST.map(t =>
    '<a class="ticker-chip" href="https://finance.yahoo.com/quote/' + t + '" target="_blank" rel="noopener">' + t + '</a>'
  ).join('');

  // SIMPLIFIED: No AI Engine or Market Data sections
  $('specs').innerHTML =
    '<div class="spec-card">' +
      '<div class="spec-card-title">Bot Specifications</div>' +
      '<div class="spec-grid">' +
        '<div class="spec-item">' +
          '<div class="spec-label">Update Frequency</div>' +
          '<div class="spec-val">Every 30 min</div>' +
          '<div class="spec-sub">During market hours</div>' +
        '</div>' +
        '<div class="spec-item">' +
          '<div class="spec-label">Active Hours</div>' +
          '<div class="spec-val">Mon\u2013Fri</div>' +
          '<div class="spec-sub">09:00\u201317:00 ET</div>' +
        '</div>' +
        '<div class="spec-item">' +
          '<div class="spec-label">Max Position Size</div>' +
          '<div class="spec-val">' + pct + '%</div>' +
          '<div class="spec-sub">of portfolio per stock</div>' +
        '</div>' +
        '<div class="spec-item">' +
          '<div class="spec-label">Max Trades / Session</div>' +
          '<div class="spec-val">' + BOT_MAX_TRADES + '</div>' +
          '<div class="spec-sub">per 30-min run</div>' +
        '</div>' +
        '<div class="spec-item">' +
          '<div class="spec-label">Min Cash Reserve</div>' +
          '<div class="spec-val">' + fmt(BOT_MIN_CASH) + '</div>' +
          '<div class="spec-sub">always kept liquid</div>' +
        '</div>' +
        '<div class="spec-item">' +
          '<div class="spec-label">Starting Capital</div>' +
          '<div class="spec-val">$10,000</div>' +
          '<div class="spec-sub">paper money</div>' +
        '</div>' +
      '</div>' +
      '<div class="spec-label" style="margin:20px 0 10px">Watchlist \u2014 ' + BOT_WATCHLIST.length + ' tickers monitored each session</div>' +
      '<div class="ticker-list">' + tickers + '</div>' +
    '</div>';
}

function renderFollowGuide(){
  $('follow').innerHTML=
    '<div class="follow-card">'+
      '<div class="spec-card-title">How to Follow This Bot</div>'+
      '<div class="follow-steps">'+
        '<div class="follow-step"><span class="follow-num">1</span><span>Scroll down to <strong>Recent Trades</strong> \u2014 the bot\'s latest signals appear here. The page auto-refreshes every 90 seconds.</span></div>'+
        '<div class="follow-step"><span class="follow-num">2</span><span>When you see a <span class="badge badge-buy">BUY</span>, consider opening a position at market price in your broker for the same ticker.</span></div>'+
        '<div class="follow-step"><span class="follow-num">3</span><span>When you see a <span class="badge badge-sell">SELL</span>, consider closing or trimming your position in that ticker.</span></div>'+
        '<div class="follow-step"><span class="follow-num">4</span><span>Read the <strong>Reasoning</strong> column \u2014 the AI explains its logic for every trade so you can judge whether it aligns with your own view.</span></div>'+
        '<div class="follow-step"><span class="follow-num">5</span><span>Check <a href="/trading-arena/'+BOT_ID+'/records/" style="color:var(--tv-blue)">Full Trade Records \u2192</a> for the complete history, win rate, and total volume.</span></div>'+
      '</div>'+
      '<div class="follow-warning">'+
        '\u26a0 This bot trades with <strong>simulated paper money only</strong>. Past performance does not guarantee future results. Nothing on this page is financial advice. Always do your own due diligence before trading real money.'+
      '</div>'+
    '</div>';
}

async function load(){
  const [pf, tr] = await Promise.all([
    fetch(BASE+'portfolio.json?t='+Date.now()).then(r=>r.json()),
    fetch(BASE+'trades.json?t='+Date.now()).then(r=>r.json())
  ]);
  
  // Marketplace data for current prices
  try {
    const mp = await fetch('https://raw.githubusercontent.com/PaperChaseAdmin/market-sentinel/main/data/market_data.json?t='+Date.now()).then(r=>r.json());
    const stocks = mp.stocks || {};
    const sp = stocks.prices || [];
    // Enrich positions with current market prices
    if (pf.positions) {
      sp.forEach(s => {
        if (pf.positions[s.symbol]) {
          pf.positions[s.symbol].current_price = s.price_usd;
        }
      });
    }
  } catch(e) {}
  
  renderHero(pf);
  renderOutlook(pf);
  renderPricesBar(pf);
  renderLastSession(pf);
  startCountdown(pf);
  renderPositions(pf);
  renderSpecs();
  renderFollowGuide();
  renderChart(pf);
  renderTrades(tr.trades||[]);
  $('loading').style.display='none';
  $('app').style.display='block';
  setTimeout(load,90000);
}

function renderHero(pf){
  const ret=+pf.total_return_pct||0;
  $('hero').innerHTML=
    '<div class="bot-hero" style="--bot-color:'+BOT_COLOR+'">'+
      '<div class="hero-row">'+
        '<div class="hero-icon">'+BOT_AVATAR+'</div>'+
        '<div class="hero-meta">'+
          '<div class="hero-name">'+BOT_NAME+'</div>'+
          '<div class="hero-bio">'+BOT_BIO+'</div>'+
          '<div class="hero-strategy">'+BOT_STRATEGY+'</div>'+
          '<div class="risk-meter" style="margin-top:8px">'+
            '<div class="risk-track"><div class="risk-fill" style="width:'+(BOT_RISK_BAR*10)+'%;background:'+BOT_COLOR+'"></div></div>'+
            '<span class="risk-text">'+BOT_RISK+' RISK</span>'+
          '</div>'+
        '</div>'+
        '<div id="countdown-wrap" class="countdown-wrap"></div>'+
      '</div>'+
      '<div class="metrics-row">'+
        '<div class="metric"><div class="metric-lbl">Portfolio</div><div class="metric-val">'+fmt(pf.total_value||0)+'</div></div>'+
        '<div class="metric"><div class="metric-lbl">Return</div><div class="metric-val '+(ret>=0?'profit':'loss')+'">'+(ret>=0?'+':'')+ret.toFixed(2)+'%</div></div>'+
        '<div class="metric"><div class="metric-lbl">P&amp;L</div><div class="metric-val">'+sign((pf.total_value||0)-10000)+'</div></div>'+
        '<div class="metric"><div class="metric-lbl">Today</div><div class="metric-val">'+sign(pf.today_pnl||0)+'</div></div>'+
        '<div class="metric"><div class="metric-lbl">Cash</div><div class="metric-val">'+fmt(pf.cash||0)+'</div></div>'+
        '<div class="metric"><div class="metric-lbl">Positions</div><div class="metric-val">'+Object.keys(pf.positions||{}).length+'</div></div>'+
        '<div class="metric"><div class="metric-lbl">Trades</div><div class="metric-val">'+(pf.total_trades||0)+'</div></div>'+
        '<div class="metric"><div class="metric-lbl">Updated</div><div class="metric-val" style="font-size:12px"><span class="live"></span>'+ago(pf.last_updated)+'</div></div>'+
      '</div>'+
    '</div>';
}

function renderOutlook(pf){
  if(!pf.last_action||pf.last_action.startsWith('Init')) return;
  $('outlook').innerHTML='<div class="outlook" style="--bot-color:'+BOT_COLOR+'"><div class="outlook-lbl">Latest Thinking</div>'+pf.last_action+'</div>';
}

function renderLastSession(pf){
  const s=pf.last_session;
  const el=$('last-session');
  if(!s||!s.at){ el.innerHTML=''; return; }

  const fg=s.fear_greed;
  const fgLabel=s.fear_greed_label||'';
  const fgClass=fg!=null?(fg<30?'fear':fg>70?'greed':''):'';
  const sp=s.sp500_change;
  const spStr=sp!=null?(sp>=0?'+':'')+Number(sp).toFixed(2)+'%':'N/A';
  const spClass=sp!=null?(sp>=0?'up':'down'):'';
  const vixVal=s.vix!=null?Number(s.vix).toFixed(1):'N/A';

  const chips=
    '<span class="chip '+(fgClass||'')+'">Fear&amp;Greed: '+(fg??'N/A')+(fgLabel?' ('+fgLabel+')':'')+'</span>'+
    '<span class="chip '+(spClass||'')+'">S&amp;P 500: '+spStr+'</span>'+
    '<span class="chip">VIX: '+vixVal+'</span>';

  const newsItems=(s.news_read||[]).map(function(h){ return '<li>'+h+'</li>'; }).join('');

  const extra=s.domain_extra?'<div class="session-block"><div class="session-block-lbl">Domain Context</div><div class="domain-extra">'+s.domain_extra+'</div></div>':'';

  const reasoning=s.ai_analysis?'<div class="session-block"><div class="session-block-lbl">AI Reasoning</div><div class="ai-reasoning" style="--bot-color:'+BOT_COLOR+'">'+s.ai_analysis+'</div></div>':'';

  const n=s.trades_made||0;
  const badgeClass=n>0?'traded':'';
  const badgeText=n>0?n+' trade'+(n>1?'s':'')+' executed':'No trades \u2014 held position';

  const sessionAt=new Date(s.at);
  const timeStr=sessionAt.toLocaleDateString('en-US',{month:'short',day:'numeric'})+' '+
    sessionAt.toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit',hour12:false})+' UTC';

  el.innerHTML=
  '<div class="session-card" style="--bot-color:'+BOT_COLOR+'">'+
    '<div class="session-header">'+
      '<span class="session-title">\ud83d\udd0d Last Session Analysis</span>'+
      '<span class="session-time">'+timeStr+'</span>'+
    '</div>'+

    '<div class="session-block">'+
      '<div class="session-block-lbl">Market Conditions Observed</div>'+
      '<div class="condition-chips">'+chips+'</div>'+
    '</div>'+

    (newsItems?'<div class="session-block">'+
      '<div class="session-block-lbl">News Analyzed (filtered to this bot\'s domain)</div>'+
      '<ul class="session-news">'+newsItems+'</ul>'+
    '</div>':'')+

    extra+
    reasoning+

    '<div class="session-footer">'+
      '<span class="decision-badge '+(badgeClass||'')+'">'+badgeText+'</span>'+
    '</div>'+
  '</div>';
}

function renderChart(pf){
  const hist=(pf.portfolio_history||[]).slice(-120);
  if(hist.length<2){ document.querySelector('.chart-wrap canvas').style.display='none'; return; }
  const labels=hist.map(function(h){ const d=new Date(h.timestamp); return (d.getMonth()+1)+'/'+d.getDate()+' '+String(d.getUTCHours()).padStart(2,'0')+':'+String(d.getUTCMinutes()).padStart(2,'0'); });
  const vals=hist.map(function(h){ return h.value; });
  const isUp=vals[vals.length-1]>=10000;
  const color=isUp?'#089981':'#f23645';
  if(chart) chart.destroy();
  const canvas=$('chart');
  chart=new Chart(canvas,{
    type:'line',
    data:{
      labels:labels,
      datasets:[{
        data:vals,
        borderColor:color,
        backgroundColor:color.replace(')',',0.06)').replace('rgb','rgba'),
        borderWidth:2,
        pointRadius:0,
        pointHoverRadius:4,
        pointHoverBackgroundColor:color,
        fill:true,
        tension:0.3
      }]
    },
    options:{
      responsive:true,
      maintainAspectRatio:false,
      plugins:{
        legend:{display:false},
        tooltip:{
          backgroundColor:'#1e222d',
          titleColor:'#d1d4dc',
          bodyColor:'#d1d4dc',
          borderColor:'#2a2e39',
          borderWidth:1,
          padding:12,
          cornerRadius:6,
          callbacks:{
            label:function(ctx){ return ' $'+ctx.parsed.y.toLocaleString('en-US',{minimumFractionDigits:2}); }
          }
        }
      },
      scales:{
        x:{
          ticks:{color:'#787b86',maxTicksLimit:8,font:{family:'JetBrains Mono',size:10}},
          grid:{color:'rgba(255,255,255,0.04)'}
        },
        y:{
          ticks:{color:'#787b86',font:{family:'JetBrains Mono',size:10},callback:function(v){ return '$'+v.toLocaleString('en-US',{maximumFractionDigits:0}); }},
          grid:{color:'rgba(255,255,255,0.04)'}
        }
      },
      interaction:{intersect:false,mode:'index'}
    }
  });
}

function renderTrades(trades){
  const el=$('trades');
  const recent=[...trades].reverse().slice(0,10);
  if(!recent.length){ el.innerHTML='<div class="empty">No trades yet \u2014 bot activates when US market opens</div>'; return; }
  let rows='';
  recent.forEach(function(t){
    const badge=t.action==='BUY'?'<span class="badge badge-buy">BUY</span>':'<span class="badge badge-sell">SELL</span>';
    let ctxHtml='';
    const sc=t.signal_context;
    if(sc){
      const parts=[];
      if(sc.ticker_chg_pct!=null){
        const cls=sc.ticker_chg_pct>0?'ctx-up':'ctx-down';
        parts.push('<span class="ctx-item '+cls+'">'+t.ticker+': '+(sc.ticker_chg_pct>=0?'+':'')+Number(sc.ticker_chg_pct).toFixed(1)+'%</span>');
      }
      if(sc.fg_value!=null) parts.push('<span class="ctx-item">F&amp;G: '+sc.fg_value+(sc.fg_label?' ('+sc.fg_label+')':'')+'</span>');
      if(sc.sp500_chg!=null){
        const cls=sc.sp500_chg>=0?'ctx-up':'ctx-down';
        parts.push('<span class="ctx-item '+cls+'">S&amp;P: '+(sc.sp500_chg>=0?'+':'')+Number(sc.sp500_chg).toFixed(1)+'%</span>');
      }
      if(sc.vix!=null) parts.push('<span class="ctx-item">VIX: '+Number(sc.vix).toFixed(1)+'</span>');
      if(parts.length) ctxHtml='<div class="signal-ctx">'+parts.join('')+'</div>';
    }
    const reasonCell='<div style="color:var(--tv-text-2);font-size:12px;line-height:1.5;max-width:260px">'+(t.reasoning||'\u2014')+'</div>'+ctxHtml;
    rows+='<tr>'+
      '<td class="mono" style="color:var(--tv-text-2);white-space:nowrap">'+fmtTs(t.timestamp)+'</td>'+
      '<td>'+badge+'</td>'+
      '<td class="mono" style="font-weight:600">'+t.ticker+'</td>'+
      '<td class="mono">'+t.shares+'</td>'+
      '<td class="mono">'+fmt(t.price)+'</td>'+
      '<td class="mono">'+fmt(t.total_value)+'</td>'+
      '<td>'+reasonCell+'</td>'+
    '</tr>';
  });
  el.innerHTML='<div class="table-wrap"><table><thead><tr><th>Time (UTC)</th><th>Action</th><th>Ticker</th><th>Shares</th><th>Price</th><th>Total</th><th>Reasoning &amp; Signal</th></tr></thead><tbody>'+rows+'</tbody></table></div>';
}

document.addEventListener('DOMContentLoaded',function(){
  document.title=BOT_NAME+' \u00b7 PaperChase Trading Arena';
  $('app').style.display='none';
  load().catch(function(e){ $('loading').textContent='Error: '+e.message; });
});
