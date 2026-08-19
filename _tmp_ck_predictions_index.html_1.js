
const DATA_URL='https://raw.githubusercontent.com/PaperChaseAdmin/paperchaseadmin.github.io/main/predictions/data/predictions.json?t='+Date.now();
const DIR_EMOJI={up:'📈',down:'📉',neutral:'➡️'};
const DIR_CLASS={up:'dir-up',down:'dir-down',neutral:'dir-neutral'};

let allPredictions=[];
let filter='all';
let toolsTotal={};

function loadData(){
fetch(DATA_URL).then(r=>r.json()).then(d=>{
  allPredictions=[];
  toolsTotal={};
  let todayPredictions=[];
  let totalPreds=0,settledPreds=0,correctPreds=0;
  const toolAcc={};

  for(const[key,tool]of Object.entries(d.tools||{})){
    toolsTotal[key]=tool.total||0;
    toolAcc[key]={label:tool.label,total:tool.total||0,correct:tool.correct||0};
    totalPreds+=tool.predictions.length;
    for(const p of tool.predictors||[]){
      totalPreds++;
      if(p.settled){settledPreds++;if(p.correct)correctPreds++;}
      allPredictions.push({...p,toolKey:key,toolLabel:tool.label});
    }
    for(const p of tool.predictions||[]){
      totalPreds++;
      if(p.settled){settledPreds++;if(p.correct)correctPreds++;}
      const item={...p,toolKey:key,toolLabel:tool.label};
      allPredictions.push(item);
      if(p.date===d.last_prediction_date)todayPredictions.push(item);
    }
  }

  renderStats(totalPreds,settledPreds,correctPreds,totalPreds);
  renderToday(todayPredictions);
  renderAccuracy(toolAcc);
  renderFilters();
  renderHistory();
  if(window.startCountdown)startCountdown(document.getElementById('countdown')||document.querySelector('.page-desc'),'Next Prediction','predictions',loadData);
}).catch(e=>{console.error('Predictions load error:',e);});
}

function renderStats(total,settled,correct,grand){
  document.getElementById('stats-bar').innerHTML=
    `<div class="pred-stat-card"><div class="pred-stat-val">${total}</div><div class="pred-stat-lbl">Total Predictions</div></div>`+
    `<div class="pred-stat-card"><div class="pred-stat-val">${settled}</div><div class="pred-stat-lbl">Settled</div></div>`+
    `<div class="pred-stat-card"><div class="pred-stat-val">${grand>0?Math.round(correct/grand*100):'—'}%</div><div class="pred-stat-lbl">Overall Accuracy</div></div>`+
    `<div class="pred-stat-card"><div class="pred-stat-val">${Object.keys(toolsTotal).length}</div><div class="pred-stat-lbl">Active Tools</div></div>`;
}

function renderToday(preds){
  const el=document.getElementById('today-grid');
  if(!preds.length){
    el.innerHTML='<div class="pred-card-empty" style="grid-column:1/-1;text-align:center;padding:32px;color:var(--pc-text-3)">No predictions for today. Markets may be closed.</div>';
    return;
  }
  el.innerHTML=preds.map(p=>{
    const dirClass=p.prediction==='up'?'dir-up':p.prediction==='down'?'dir-down':'dir-neutral';
    const color=p.prediction==='up'?'var(--pc-green)':p.prediction==='down'?'var(--pc-red)':'var(--pc-text-3)';
    return `<div class="pred-card">
      <div class="pred-card-title">${esc(p.market||'Market')}</div>
      <div class="pred-card-index">${esc(p.toolLabel||'')}</div>
      <div class="pred-card-dir" style="color:${color}">${DIR_EMOJI[p.prediction]||'➡️'} ${p.prediction?.toUpperCase()||'N/A'}</div>
      <div class="pred-card-conf">Confidence: ${p.confidence||'?'}%</div>
      <div class="pred-card-bar"><div class="pred-card-fill" style="width:${p.confidence||0}%;background:${color}"></div></div>
      <div style="font-size:10px;color:var(--pc-text-3);margin-top:6px">${esc(p.signal||'').substring(0,80)}</div>
    </div>`;
  }).join('');
}

function renderAccuracy(acc){
  document.getElementById('acc-grid').innerHTML=Object.entries(acc).map(([k,v])=>{
    const pct=v.total>0?Math.round(v.correct/v.total*100):'—';
    return `<div class="acc-card"><div class="acc-card-title">${v.label||k}</div>
      <div class="acc-pct">${pct}%</div>
      <div class="acc-count">${v.correct}/${v.total} correct</div></div>`;
  }).join('');
}

function renderFilters(){
  const tools=[...new Set(allPredictions.map(p=>p.toolKey))];
  document.getElementById('filter-bar').innerHTML=
    `<button class="filter-btn active" onclick="setFilter('all')">All</button>`+
    tools.map(t=>`<button class="filter-btn" onclick="setFilter('${t.replace(/'/g,"\\'")}')">${esc(allPredictions.find(p=>p.toolKey===t)?.toolLabel||t)}</button>`).join('');
}

function setFilter(f){filter=f;
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.toggle('active',b.textContent.toLowerCase()===f||(f==='all'&&b.textContent==='All')));
  renderHistory();
}

function renderHistory(){
  let items=filter==='all'?allPredictions:allPredictions.filter(p=>p.toolKey===filter);
  items.sort((a,b)=>b.date?.localeCompare(a.date));
  document.getElementById('history-body').innerHTML=items.slice(0,100).map(p=>{
    const dc=DIR_CLASS[p.prediction]||'';
    const badge=p.settled?p.correct?'<span class="badge badge-correct">✓</span>':'<span class="badge badge-wrong">✗</span>':'<span class="badge badge-pending">Pending</span>';
    const toolTagClass=`tool-tag tool-${p.toolKey?.split('_').map(s=>s[0]?.toUpperCase()).join('')||'NA'}`;
    return `<tr>
      <td>${p.date||'—'}</td>
      <td><span class="${toolTagClass}">${esc(p.toolLabel||p.toolKey||'—')}</span></td>
      <td>${esc(p.market||'—')}</td>
      <td class="${dc}">${DIR_EMOJI[p.prediction]||''} ${p.prediction?.toUpperCase()||'—'}</td>
      <td>${p.confidence||'—'}%</td>
      <td>${badge}</td>
    </tr>`;
  }).join('')||'<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--pc-text-3)">No predictions found.</td></tr>';
}

loadData();
