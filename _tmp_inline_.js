
var DATA_URL = 'https://paperchase.online/trade/data/leaderboard.json';
var BOT_PREFIX = '/trading-arena/';
var bots=[], mainChart=null, $=function(id){return document.getElementById(id);};

function kpi(bs){
  var a=bs.filter(function(b){return b.status!=='stopped';}), v=bs.reduce(function(s,b){return s+(b.total_value||10000);},0),
      r=a.length?bs.reduce(function(s,b){return s+(b.total_return_pct||0);},0)/bs.length:0,
      p=bs.filter(function(b){return(b.total_return_pct||0)>0;}).length,
      d=bs.reduce(function(s,b){return s+(b.today_pnl||0);},0),
      pos=bs.reduce(function(s,b){return s+Object.keys(b.positions||{}).length;},0);
  $('kpiDash').innerHTML='<div class="ki"><div class="kl">Active</div><div class="kv">'+a.length+'/'+bs.length+'</div></div><div class="ki"><div class="kl">AUM</div><div class="kv">$'+v.toLocaleString('en',{maximumFractionDigits:0})+'</div></div><div class="ki"><div class="kl">Avg Return</div><div class="kv" style="color:'+(r>=0?'var(--pc-green)':'var(--pc-red)')+'">'+(r>=0?'+':'')+r.toFixed(2)+'%</div></div><div class="ki"><div class="kl">Positions</div><div class="kv">'+pos+'</div></div><div class="ki"><div class="kl">In Profit</div><div class="kv" style="color:var(--pc-green)">'+p+'/'+bs.length+'</div></div><div class="ki"><div class="kl">Today P&L</div><div class="kv" style="color:'+(d>=0?'var(--pc-green)':'var(--pc-red)')+'">'+(d>=0?'+$':'-$')+Math.abs(d).toFixed(2)+'</div></div>';
}

function risk(bs){
  var l={low:0,medium:0,high:0,'very high':0,'very low':0}, t=bs.length||1, cl={low:'var(--pc-green)',medium:'var(--pc-yellow)',high:'var(--pc-red)','very high':'#7c3aed','very low':'#22c55e'}, h='';
  bs.forEach(function(b){var r=(b.risk_level||'medium').toLowerCase().replace(/^med$/,'medium');if(l[r]!==undefined)l[r]++;});
  Object.keys(l).forEach(function(k){var p=Math.max((l[k]/t*100).toFixed(0),4);h+='<div class="rb-i"><div class="rb-b" style="height:'+p+'px;background:'+cl[k]+'"></div><span style="font-size:11px;font-weight:700;color:var(--pc-heading)">'+l[k]+'</span><span style="font-size:9px;color:var(--pc-text-3);text-transform:uppercase">'+k+'</span></div>';});
  $('riskInner').innerHTML=h;
}

function perf(bs){
  var s=[].concat(bs).sort(function(a,b){return(b.total_return_pct||0)-(a.total_return_pct||0);}).slice(0,5),h='';
  s.forEach(function(b,i){var p=b.total_return_pct||0;h+='<div class="tp-i"><span class="tp-r">#'+(i+1)+'</span><span class="tp-n">'+(b.display_name||'Bot')+'</span><span class="tp-p" style="color:'+(p>=0?'var(--pc-green)':'var(--pc-red)')+'">'+(p>=0?'+':'')+p.toFixed(2)+'%</span></div>';});
  $('topPerf').innerHTML=h;
}

function botsList(bs){
  var s=[].concat(bs).sort(function(a,b){return(b.total_return_pct||0)-(a.total_return_pct||0);}), h='', ac=['#533afd','#15be53','#f59e0b','#ef4444','#3b82f6','#8b5cf6','#ec4899','#14b8a6'];
  s.forEach(function(b,i){
  var p=b.total_return_pct||0, slug=b.slug||b.bot_id||(b.display_name||'').toLowerCase().replace(/\s+/g,'-');
  var last=b.last_updated||'',ta='';
  if(last){var d=new Date(last),n=new Date(),diff=Math.floor((n-d)/60000);ta=diff<1?'now':diff<60?diff+'m':Math.floor(diff/60)+'h';}
  h+='<a class="br" href="'+BOT_PREFIX+slug+'/"><span class="rk">#'+(i+1)+'</span><div><div class="nm">'+(b.display_name||'Bot')+'</div><div class="st">'+(b.strategy||'AI Trader')+' · '+ta+'</div></div><span class="pv">$'+((b.total_value||10000).toLocaleString('en',{maximumFractionDigits:0}))+'</span><span class="pn" style="color:'+(p>=0?'var(--pc-green)':'var(--pc-red)')+'">'+(p>=0?'+':'')+p.toFixed(2)+'%</span><span class="tr">'+(Object.keys(b.positions||{}).length)+' pos</span><button class="fv" onclick="event.preventDefault();fv(\''+slug+'\')">☆</button></a>';
  });
  $('botList').innerHTML=h;
  $('botCount').textContent='· '+bs.length+' bots';
  $('botLoading').style.display='none';
  $('botWrap').style.display='block';
}

function fv(slug){var f=JSON.parse(localStorage.getItem('trading_favs')||'[]'),i=f.indexOf(slug);if(i>=0)f.splice(i,1);else f.push(slug);localStorage.setItem('trading_favs',JSON.stringify(f));rf();}
function rf(){var f=JSON.parse(localStorage.getItem('trading_favs')||'[]');document.querySelectorAll('.fv').forEach(function(el,i){el.textContent=f.includes(bots[i]?.slug||bots[i]?.id)?'★':'☆';});}

function buildChart(hist,r){
  if(!mainChart)return;
  var lb={all:hist,'1m':hist.slice(-22),'1w':hist.slice(-5),'1d':hist.slice(-2)};
  var d=lb[r]||hist;
  mainChart.data.labels=d.map(function(v,i){var dt=new Date();dt.setDate(dt.getDate()-(hist.length-1-(hist.indexOf(v)>=0?hist.indexOf(v):i))*0.2);return(dt.getMonth()+1)+'/'+dt.getDate();});
  mainChart.data.datasets[0].data=d;
  mainChart.update();
}
function sw(r,btn){document.querySelectorAll('.cp-c button').forEach(function(b){b.classList.remove('on');});btn.classList.add('on');if(window._ch)buildChart(window._ch,r);}

var _cd=null;
function onDataLoaded(){clearInterval(_cd);var el=$('countdown-wrap');if(!el||typeof window.startCountdown!=='function')return;_cd=window.startCountdown(el,'Next Update','trading-arena',loadData);}

async function loadData(){
  try{
    var resp=await fetch(DATA_URL+'');
    if(!resp.ok)throw new Error('HTTP '+resp.status);
    var data=await resp.json();
    bots=data.bots||[];var hist=data.portfolio_history||[10000];
    kpi(bots);risk(bots);perf(bots);botsList(bots);
    var ctx=document.getElementById('mainChart').getContext('2d');window._ch=hist;
    if(mainChart)mainChart.destroy();
    mainChart=new Chart(ctx,{type:'line',data:{labels:hist.map(function(v,i){var d=new Date();d.setDate(d.getDate()-(hist.length-1-i)*0.2);return(d.getMonth()+1)+'/'+d.getDate();}),datasets:[{label:'Portfolio Value ($)',data:hist,borderColor:'#533afd',backgroundColor:'rgba(83,58,253,0.08)',borderWidth:2,fill:true,tension:0.3,pointRadius:0}]},options:{responsive:true,maintainAspectRatio:true,aspectRatio:3,plugins:{legend:{display:false}},scales:{x:{grid:{display:false},ticks:{font:{size:10},color:'#94a3b8',maxTicksLimit:10}},y:{grid:{color:'rgba(0,0,0,0.05)'},ticks:{font:{size:10},color:'#94a3b8',callback:function(v){return'$'+v.toLocaleString();}}}}}});
    onDataLoaded();
  }catch(e){$('botLoading').innerHTML='<div style="color:var(--pc-text-3);padding:40px;text-align:center">⚠️ Data not yet available</div>';}
}
loadData();
document.addEventListener('DOMContentLoaded',rf);
