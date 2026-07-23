/* Records page — shared logic. Requires BOT_ID and BOT_COLOR globals. */
'use strict';

const BASE2 = `/trade/data/bots/${BOT_ID}/`;
let allTrades=[], filter='all';

const $2 = id => document.getElementById(id);
function fmt2(v){ return '$'+Math.abs(+v).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}); }
function fmtTs2(ts){ const d=new Date(ts); return d.toLocaleDateString('en-US',{year:'numeric',month:'short',day:'numeric'})+' '+d.toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit',hour12:false}); }

function setFilter(f,btn){
  filter=f;
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active'); renderTable();
}

function renderStats(trades){
  const buys=trades.filter(t=>t.action==='BUY');
  const sells=trades.filter(t=>t.action==='SELL');
  const vol=trades.reduce((s,t)=>s+(+t.total_value||0),0);
  $2('stats').innerHTML=`
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-label">Total Trades</div><div class="stat-value">${trades.length}</div></div>
      <div class="stat-card"><div class="stat-label">Buys</div><div class="stat-value profit">${buys.length}</div></div>
      <div class="stat-card"><div class="stat-label">Sells</div><div class="stat-value loss">${sells.length}</div></div>
      <div class="stat-card"><div class="stat-label">Total Volume</div><div class="stat-value">${fmt2(vol)}</div></div>
    </div>`;
}

function renderTable(){
  const filtered=filter==='all'?allTrades:allTrades.filter(t=>t.action===filter);
  $2('count').textContent=`${filtered.length} trade${filtered.length!==1?'s':''}`;
  const el=$2('records');
  if(!filtered.length){ el.innerHTML=`<div class="empty">${allTrades.length?'No trades match this filter.':'No trades yet — bot activates when US market opens.'}</div>`; return; }
  let rows='';
  [...filtered].reverse().forEach((t,i)=>{
    const badge=t.action==='BUY'?'<span class="badge badge-buy">BUY</span>':'<span class="badge badge-sell">SELL</span>';
    rows+=`<tr><td class="mono" style="color:var(--text-2)">${filtered.length-i}</td><td class="mono" style="color:var(--text-2);white-space:nowrap">${fmtTs2(t.timestamp)}</td><td>${badge}</td><td class="mono" style="font-weight:600">${t.ticker}</td><td class="mono">${t.shares}</td><td class="mono">${fmt2(t.price)}</td><td class="mono">${fmt2(t.total_value)}</td><td style="color:var(--text-2);font-size:12px;max-width:280px;line-height:1.5">${t.reasoning||'—'}</td></tr>`;
  });
  el.innerHTML=`<div class="table-wrap"><table><thead><tr><th>#</th><th>Date &amp; Time (UTC)</th><th>Action</th><th>Ticker</th><th>Shares</th><th>Price</th><th>Total</th><th>Reasoning</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

document.addEventListener('DOMContentLoaded',async()=>{
  document.title=`${BOT_NAME} Records · PaperChase`;
  $2('bot-name').textContent=BOT_NAME;
  $2('bot-avatar').textContent=BOT_AVATAR;
  const data=await fetch(BASE2+'trades.json?t='+Date.now()).then(r=>r.json());
  allTrades=data.trades||[];
  renderStats(allTrades); renderTable();
  setTimeout(()=>location.reload(),90000);
});
