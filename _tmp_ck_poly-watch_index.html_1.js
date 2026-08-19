
const DATA_URL = 'https://raw.githubusercontent.com/PaperChaseAdmin/trade/main/data/polymarket/scan_results.json';
let allMarkets = [];
let currentFilter = 'all';

function fmt(v) { if (v == null) return '—'; if (v >= 1e6) return '$'+(v/1e6).toFixed(1)+'M'; if (v >= 1e3) return '$'+(v/1e3).toFixed(1)+'K'; return '$'+v.toFixed(0); }
function setFilter(f, btn) { currentFilter = f; document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active')); btn.classList.add('active'); renderMarkets(); }

function renderMarkets() {
  let filtered = allMarkets;
  if (currentFilter === 'recommended') filtered = allMarkets.filter(m => m.heuristic && m.heuristic.score >= 15);
  else if (currentFilter === 'review') filtered = allMarkets.filter(m => m.heuristic && m.heuristic.score < 15 && m.heuristic.score >= 5);
  else if (currentFilter !== 'all') filtered = allMarkets.filter(m => m.tag === currentFilter);
  document.getElementById('countLabel').textContent = filtered.length + ' markets';
  if (!filtered.length) { document.getElementById('marketList').innerHTML = '<div class="loading" style="padding:40px">No markets found for this filter</div>'; return; }
  let html = '<div class="market-grid">';
  filtered.forEach(m => {
    const h = m.heuristic || {}; const ai = m.ai || {}; const pct = (m.yes_price * 100).toFixed(1);
    const badge = h.score >= 15 ? 'badge-yes' : h.score >= 5 ? 'badge-review' : 'badge-no';
    const badgeText = h.score >= 15 ? '✅ Yes' : h.score >= 5 ? '⚠️ Review' : '❌ No';
    const barColor = m.yes_price >= 0.9 ? 'var(--pc-green)' : m.yes_price >= 0.7 ? 'var(--pc-yellow)' : 'var(--pc-red)';
    const endDate = m.end_date ? new Date(m.end_date).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'}) : 'N/A';
    const aiHtml = ai.ai_analysis ? '<div class="market-card-ai open"><span class="ai-outlook" style="color:'+(ai.ai_outlook==='yes'?'var(--pc-green)':'var(--pc-red)')+'">'+esc(ai.ai_outlook||'neutral').toUpperCase()+'</span><span class="ai-conf">('+esc(ai.ai_confidence||0)+'% confidence)</span> — '+esc(ai.ai_analysis||'')+'</div>' : '';
    html += '<div class="market-card" onclick="toggleAI(this)"><div class="market-card-header"><div class="market-card-question">'+esc(m.question)+'</div><span class="market-card-badge '+badge+'">'+badgeText+'</span></div><div class="market-card-meta"><span class="meta-item">Yes: <strong class="'+(m.yes_price>=0.9?'text-green':m.yes_price>=0.7?'text-yellow':'')+'">'+pct+'%</strong></span><span class="meta-item">Ends: <strong>'+endDate+'</strong></span><span class="meta-item">Vol: <strong>'+fmt(m.volume)+'</strong></span><span class="badge-tag">'+esc(m.tag||'')+'</span>'+(h.reasons?'<span class="meta-item" style="color:var(--pc-text-3);font-size:10px">'+esc(h.reasons)+'</span>':'')+'</div><div class="prob-bar-wrap"><div class="prob-bar-fill" style="width:'+pct+'%;background:'+barColor+'"></div></div>'+aiHtml+'</div>';
  });
  html += '</div>';
  document.getElementById('marketList').innerHTML = html;
}

function toggleAI(el) { const aiEl = el.querySelector('.market-card-ai'); if (aiEl) aiEl.classList.toggle('open'); }

function renderTopPick(markets) {
  const section = document.getElementById('topPickSection');
  const scored = markets.filter(m => m.heuristic && m.heuristic.score > 0).sort((a,b)=>(b.heuristic.score||0)-(a.heuristic.score||0));
  if (scored.length===0){section.style.display='none';return;}
  const top=scored[0];const h=top.heuristic||{};const ai=top.ai||{};const pct=(top.yes_price*100).toFixed(1);const betYes=top.yes_price>=0.5;
  document.getElementById('topPickDate').textContent=new Date().toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
  document.getElementById('topPickQuestion').textContent=top.question;
  const ae=document.getElementById('topPickAction');ae.textContent=betYes?'▸ BET YES':'▸ BET NO';ae.style.background=betYes?'var(--pc-green-bg)':'var(--pc-red-bg)';ae.style.color=betYes?'var(--pc-green)':'var(--pc-red)';ae.style.border='1px solid '+(betYes?'rgba(21,190,83,0.3)':'rgba(239,68,68,0.3)');
  document.getElementById('topPickProb').innerHTML='Yes: <strong>'+pct+'%</strong>';document.getElementById('topPickVol').textContent='Vol: '+fmt(top.volume);
  document.getElementById('topPickTag').textContent=(top.tag||'').toUpperCase();document.getElementById('topPickScore').textContent=h.score||'';
  if(ai.ai_analysis){document.getElementById('topPickAIOutlook').textContent=(ai.ai_outlook||'neutral').toUpperCase();document.getElementById('topPickAIOutlook').style.color=ai.ai_outlook==='yes'?'var(--pc-green)':'var(--pc-red)';document.getElementById('topPickAIConf').textContent='('+esc(ai.ai_confidence||0)+'% confidence)';document.getElementById('topPickAIAnalysis').textContent=' — '+ai.ai_analysis;}
  section.style.display='block';savePrediction(top,betYes);
}

function savePrediction(market,betYes){const today=new Date().toISOString().split('T')[0];let history=JSON.parse(localStorage.getItem('polywatch_predictions')||'[]');if(history.length>0&&history[0].date===today)return;history.unshift({date:today,question:market.question,bet:betYes?'YES':'NO',prob:(market.yes_price*100).toFixed(1)+'%',tag:market.tag||'',score:(market.heuristic||{}).score||0,result:null,correct:null});history=history.slice(0,15);localStorage.setItem('polywatch_predictions',JSON.stringify(history));renderPredHist(history);}

function renderPredHist(history){const section=document.getElementById('predHistSection');if(!history||history.length===0){section.style.display='none';return;}const resolved=history.filter(h=>h.correct!==null);const correct=resolved.filter(h=>h.correct).length;const total=resolved.length;const accPct=total>0?Math.round(correct/total*100):0;document.getElementById('predHistAcc').textContent=total>0?accPct+'% accuracy ('+correct+'/'+total+')':'';const tableHtml=history.slice(0,10).map(h=>{const isResolved=h.correct!==null;const cls=isResolved?(h.correct?'resolved-correct':'resolved-wrong'):'pending';const betColor=h.bet==='YES'?'var(--pc-green)':'var(--pc-red)';return'<div class="pred-row '+cls+'"><span class="pred-date">'+h.date.slice(5)+'</span><span class="pred-question">'+esc(h.question)+'</span><span class="pred-bet" style="color:'+betColor+'">'+h.bet+'</span>'+(isResolved?'<span class="pred-result" style="color:'+(h.correct?'var(--pc-green)':'var(--pc-red)')+'">'+(h.correct?'✅ CORRECT':'❌ WRONG')+'</span>':'<span class="pred-result" style="color:var(--pc-text-3)">⏳ Pending</span>')+'</div>';}).join('');document.getElementById('predHistTable').innerHTML=tableHtml;section.style.display='block';}

let _cdTimer=null;
function onDataLoaded(){clearInterval(_cdTimer);const el=document.getElementById("countdown-wrap");if(!el||typeof window.startCountdown!=="function")return;_cdTimer=window.startCountdown(el,"Next Update","poly-watch",loadData);}

async function loadData(){const today=new Date().toISOString().split('T')[0];const hist=JSON.parse(localStorage.getItem('polywatch_predictions')||'[]');localStorage.setItem('polywatch_predictions',JSON.stringify(hist.filter(h=>h.date>=today)));try{const resp=await fetch(DATA_URL+'?t='+Date.now());if(!resp.ok)throw new Error('HTTP '+resp.status);const data=await resp.json();allMarkets=data.markets||[];const total=allMarkets.length;const recommended=allMarkets.filter(m=>m.heuristic&&m.heuristic.score>=15).length;const avgYes=total?(allMarkets.reduce((s,m)=>s+m.yes_price,0)/total*100).toFixed(1):0;const totalVol=allMarkets.reduce((s,m)=>s+(m.volume||0),0);document.getElementById('statsBar').innerHTML='<div class="stat-item"><div class="stat-lbl">Markets</div><div class="stat-val">'+total+'</div></div><div class="stat-item"><div class="stat-lbl">Recommended</div><div class="stat-val" style="color:var(--pc-green)">'+recommended+'</div></div><div class="stat-item"><div class="stat-lbl">Avg Yes%</div><div class="stat-val">'+avgYes+'%</div></div><div class="stat-item"><div class="stat-lbl">Total Volume</div><div class="stat-val">'+fmt(totalVol)+'</div></div>';renderMarkets();renderTopPick(allMarkets);onDataLoaded();const history=JSON.parse(localStorage.getItem('polywatch_predictions')||'[]');renderPredHist(history);}catch(e){document.getElementById('marketList').innerHTML='<div class="loading" style="color:var(--pc-red)">⚠ Could not load: '+e.message+'</div>';}}
loadData();
