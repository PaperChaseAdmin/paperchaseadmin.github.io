"""Generate bot detail + records pages with Stripe design for root repo."""
import os, json

# Read bot profiles from trade repo
BOT_PROFILES_PATH = "/mnt/c/Hermes/paper_trading/bot_profiles.py"

# Execute bot_profiles to get BOT_PROFILES
exec(open(BOT_PROFILES_PATH).read())

OUTPUT_DIR = "/mnt/c/Hermes/paperchase_site/trading-arena"

DETAIL_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>BOTNAME · AI Trading Bot · PaperChase</title>
<meta name="description" content="Watch BOTNAME, an AI-powered trading bot with a BOTSTRATEGY strategy. Real portfolio, live trades, transparent AI decisions on PaperChase."/>
<meta name="robots" content="index, follow"/>
<link rel="canonical" href="https://paperchase.online/trading-arena/BOTID/"/>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W3V49QCMT0"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-W3V49QCMT0');</script>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="/assets/design-system.css">
<style>
/* Override old tv-* CSS vars used by bot-detail.js to match white+purple design */
:root {
  --tv-bg: #ffffff; --tv-surface: #ffffff; --tv-surface-2: #f8fafc; --tv-surface-3: #f1f5f9;
  --tv-border: #e2e8f0; --tv-border-2: #cbd5e1;
  --tv-text: #061b31; --tv-text-2: #64748b; --tv-text-3: #94a3b8;
  --tv-green: #15be53; --tv-red: #ef4444; --tv-yellow: #f59e0b; --tv-blue: #533afd; --tv-amber: #d29922;
  --tv-font: var(--pc-font); --tv-mono: var(--pc-mono);
  --tv-radius: var(--pc-radius); --tv-radius-sm: var(--pc-radius-sm);
  --tv-glow-green: 0 0 20px rgba(21,190,83,0.15);
  --tv-glow-red: 0 0 20px rgba(239,68,68,0.15);
}
/* Bot detail overrides */
.bot-crest{width:56px;height:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:800;color:#fff;flex-shrink:0}
.back-link{display:inline-flex;align-items:center;gap:4px;font-size:13px;font-weight:500;color:var(--pc-purple);text-decoration:none;margin-bottom:16px}
.back-link:hover{text-decoration:underline}
.hero-wrap{display:flex;align-items:center;gap:16px;margin-bottom:20px}
.hero-text h1{font-size:24px;font-weight:700;color:var(--pc-heading);letter-spacing:-0.3px;margin-bottom:4px}
.hero-text p{font-size:13px;color:var(--pc-text-2);line-height:1.5}
.outlook-card{background:var(--pc-surface);border:1px solid var(--pc-border);border-radius:var(--pc-radius-lg);padding:16px;margin-bottom:16px;display:flex;align-items:center;gap:12px}
.outlook-signal{font-size:13px;font-weight:700;padding:3px 10px;border-radius:4px}
.profit{color:var(--pc-green)}.loss{color:var(--pc-red)}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:1px;background:var(--pc-border);border-radius:var(--pc-radius-lg);overflow:hidden;margin-bottom:16px}
.stat-cell{background:var(--pc-surface);padding:12px 14px;text-align:center}
.stat-lbl{font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--pc-text-3);margin-bottom:2px}
.stat-val{font-size:16px;font-weight:700;font-family:var(--pc-mono);color:var(--pc-heading)}
.prices-bar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}
.price-chip{background:var(--pc-surface-2);border:1px solid var(--pc-border);border-radius:var(--pc-radius);padding:6px 10px;font-size:12px;display:flex;align-items:center;gap:6px}
.price-chip .sym{font-weight:600;color:var(--pc-heading)}
.price-chip .val{font-family:var(--pc-mono);color:var(--pc-text)}
.section-card{background:var(--pc-surface);border:1px solid var(--pc-border);border-radius:var(--pc-radius-lg);padding:16px;margin-bottom:16px}
.section-title{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--pc-text-3);margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--pc-border)}
.position-row,.trade-row{display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr;gap:6px;align-items:center;padding:8px 10px;border-radius:var(--pc-radius);font-size:12px;border:1px solid var(--pc-border);margin-bottom:4px;cursor:pointer;transition:background .1s}
.position-row:hover,.trade-row:hover{background:var(--pc-surface-hover)}
.position-row .sym,.trade-row .sym{font-weight:600;color:var(--pc-heading);font-family:var(--pc-mono)}
.position-row .qty,.trade-row .action{font-size:11px;color:var(--pc-text-2)}
.trade-row .reason{font-size:11px;color:var(--pc-text-2);grid-column:1/-1;padding-top:4px;border-top:1px solid var(--pc-border);margin-top:4px;display:none}
.trade-row.expanded .reason{display:block}
.position-detail{background:var(--pc-surface-2);border:1px solid var(--pc-border);border-radius:var(--pc-radius);padding:10px 12px;margin-top:4px;font-size:12px;display:none}
.position-row.expanded+.position-detail{display:block}
.badge-buy{background:var(--pc-green-bg);color:var(--pc-green);padding:1px 6px;border-radius:2px;font-size:10px;font-weight:700}
.badge-sell{background:var(--pc-red-bg);color:var(--pc-red);padding:1px 6px;border-radius:2px;font-size:10px;font-weight:700}
.badge-hold{background:var(--pc-surface-3);color:var(--pc-text-3);padding:1px 6px;border-radius:2px;font-size:10px;font-weight:700}
.follow-section{display:flex;flex-direction:column;gap:10px}
.follow-step{display:flex;align-items:flex-start;gap:8px;font-size:13px;color:var(--pc-text);line-height:1.5}
.follow-num{width:22px;height:22px;border-radius:50%;background:var(--pc-purple);color:#fff;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px}
.follow-warning{background:var(--pc-yellow-bg);border:1px solid rgba(245,158,11,.2);border-radius:var(--pc-radius);padding:10px 12px;font-size:11px;color:var(--pc-text-2);line-height:1.5}
#chart{height:300px}
.favourite-bar{display:flex;justify-content:flex-end;padding:4px 0 8px}
.fav-btn{background:none;border:1px solid var(--pc-border);border-radius:var(--pc-radius);padding:6px 12px;cursor:pointer;font-size:13px;color:var(--pc-text-2);transition:all .15s}
.fav-btn:hover{background:var(--pc-surface-hover);color:var(--pc-heading)}
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
  const BOT_ID='BOTID',BOT_COLOR='BOTCOLOR',BOT_NAME='BOTNAME';
  const BOT_AVATAR='BOTAVATAR',BOT_BIO='BOTBIO',BOT_STRATEGY='BOTSTRATEGY';
  const BOT_RISK='BOTRISK',BOT_RISK_BAR=BOTRISKBAR;
  const BOT_MODEL='BOTMODEL',BOT_FALLBACK='BOTFALLBACK';
  const BOT_WATCHLIST=BOTWATCHLIST;
  const BOT_MAX_POSITION=BOTMAXPOSITION,BOT_MAX_TRADES=BOTMAXTRADES,BOT_MIN_CASH=BOTMINCASH;
</script>
</head>
<body>

<nav class="topbar"><div class="topbar-inner">
  <a class="logo" href="/"><span class="logo-dot"></span>PaperChase</a>
  <div class="topbar-nav">
    <a class="nav-link" href="/market-sentinel/">Market Sentinel</a>
    <a class="nav-link" href="/crypto-pulse/">Crypto Pulse</a>
    <a class="nav-link" href="/poly-watch/">Poly Watch</a>
    <a class="nav-link active" href="/trading-arena/">Trading Arena</a>
  </div>
  <div class="topbar-spacer"></div>
  <div class="topbar-auth">
    <a class="btn-login" href="/login/">Log In</a>
    <a class="btn-register" href="/register/">Register</a>
  </div>
</div></nav>
<div class="wrap">
<div class="container">
  <a class="back-link" href="/trading-arena/">&#8592; All Bots</a>
  <div class="favourite-bar">
    <button id="favBtn" class="fav-btn" onclick="toggleFavourite()" style="display:none">
      <span id="favIcon">&#9734;</span> <span id="favLabel">Add to Favourites</span>
    </button>
  </div>
  <div id="loading" style="text-align:center;padding:60px;color:var(--pc-text-2)"><div class="spinner"></div>Loading BOTNAME...</div>
  <div id="app" style="display:none">
    <div id="hero"></div>
    <div id="outlook"></div>
    <div id="countdown-wrap"></div>
    <div id="prices-bar"></div>
    <div id="last-session"></div>
    <div id="specs"></div>
    <div id="chart" style="height:300px"></div>
    <div id="positions"></div>
    <div id="trades"></div>
    <div id="follow"></div>
  </div>
  <a href="/trading-arena/BOTID/records/" class="btn btn-ghost btn-sm" style="margin-top:12px">&#128196; Full Trade Records</a>
</div>
</div>

<script src="/assets/bot-detail.js"></script>
<script>
async function checkFavStatus() {
  if (!window.PaperChaseAuth) return;
  var session = await PaperChaseAuth.getSession();
  var btn = document.getElementById('favBtn');
  if (!btn) return;
  if (!session) { btn.style.display = 'none'; return; }
  btn.style.display = '';
  var isFav = await PaperChaseAuth.isFavourite(BOT_ID);
  document.getElementById('favIcon').textContent = isFav ? '\u2605' : '\u2606';
  document.getElementById('favLabel').textContent = isFav ? 'Remove from Favourites' : 'Add to Favourites';
}
async function toggleFavourite() {
  if (!window.PaperChaseAuth) return;
  var session = await PaperChaseAuth.getSession();
  if (!session) { alert('Please log in to add favourites.'); return; }
  var isFav = await PaperChaseAuth.isFavourite(BOT_ID);
  if (isFav) { await PaperChaseAuth.removeFavourite(BOT_ID); }
  else { await PaperChaseAuth.addFavourite(BOT_ID, BOT_NAME, BOT_AVATAR); }
  checkFavStatus();
}
checkFavStatus();
</script>
</body></html>"""

RECORDS_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>BOTNAME Trade Records · PaperChase</title>
<meta name="description" content="Complete trade history for BOTNAME AI trading bot on PaperChase."/>
<meta name="robots" content="index, follow"/>
<link rel="canonical" href="https://paperchase.online/trading-arena/BOTID/records/"/>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-W3V49QCMT0"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-W3V49QCMT0');</script>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="/assets/design-system.css">
<style>
:root {
  --tv-bg: #ffffff; --tv-surface: #ffffff; --tv-surface-2: #f8fafc; --tv-surface-3: #f1f5f9;
  --tv-border: #e2e8f0; --tv-border-2: #cbd5e1;
  --tv-text: #061b31; --tv-text-2: #64748b; --tv-text-3: #94a3b8;
  --tv-green: #15be53; --tv-red: #ef4444; --tv-yellow: #f59e0b; --tv-blue: #533afd;
  --tv-font: var(--pc-font); --tv-mono: var(--pc-mono);
  --tv-radius: var(--pc-radius); --tv-radius-sm: var(--pc-radius-sm);
}
.back-link{display:inline-flex;align-items:center;gap:4px;font-size:13px;font-weight:500;color:var(--pc-purple);text-decoration:none;margin-bottom:16px}
.back-link:hover{text-decoration:underline}
.profit{color:var(--pc-green)}.loss{color:var(--pc-red)}
.stats-grid{display:grid;gap:1px;background:var(--pc-border);border-radius:var(--pc-radius-lg);overflow:hidden;margin-bottom:16px;grid-template-columns:repeat(4,1fr)}
.stat-cell{background:var(--pc-surface);padding:12px 14px;text-align:center}
.stat-lbl{font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--pc-text-3);margin-bottom:2px}
.stat-val{font-size:18px;font-weight:700;font-family:var(--pc-mono);color:var(--pc-heading)}
.filter-bar{display:flex;gap:4px;margin-bottom:12px}
.filter-btn{font-size:11px;font-weight:600;padding:4px 10px;border-radius:20px;border:1px solid var(--pc-border);background:var(--pc-surface);color:var(--pc-text-2);cursor:pointer;font-family:var(--pc-font);transition:all .15s}
.filter-btn:hover{background:var(--pc-surface-hover)}
.filter-btn.active{background:var(--pc-purple);color:#fff;border-color:var(--pc-purple)}
.records-list{display:flex;flex-direction:column;gap:1px;background:var(--pc-border);border-radius:var(--pc-radius-lg);overflow:hidden}
.record-row{display:grid;grid-template-columns:80px 80px 1fr 80px 70px;gap:6px;align-items:center;padding:8px 12px;background:var(--pc-surface);font-size:12px;border-bottom:1px solid var(--pc-border)}
.record-row:last-child{border-bottom:none}
.record-date{color:var(--pc-text-3);font-size:10px;font-weight:600}
.record-action{font-weight:700;font-size:11px;padding:1px 6px;border-radius:2px;text-align:center}
.record-sym{font-weight:600;color:var(--pc-heading);font-family:var(--pc-mono)}
.record-qty{font-family:var(--pc-mono);color:var(--pc-text)}
.record-price{font-family:var(--pc-mono);color:var(--pc-text);text-align:right}
.record-reason{font-size:11px;color:var(--pc-text-2);grid-column:1/-1;padding-top:6px;border-top:1px solid var(--pc-border);display:none;margin-top:4px}
.record-row.expanded .record-reason{display:block}
.badge-buy{background:var(--pc-green-bg);color:var(--pc-green)}
.badge-sell{background:var(--pc-red-bg);color:var(--pc-red)}
</style>
</head>
<body>

<nav class="topbar"><div class="topbar-inner">
  <a class="logo" href="/"><span class="logo-dot"></span>PaperChase</a>
  <div class="topbar-nav">
    <a class="nav-link" href="/market-sentinel/">Market Sentinel</a>
    <a class="nav-link" href="/crypto-pulse/">Crypto Pulse</a>
    <a class="nav-link" href="/poly-watch/">Poly Watch</a>
    <a class="nav-link active" href="/trading-arena/">Trading Arena</a>
  </div>
  <div class="topbar-spacer"></div>
  <div class="topbar-auth">
    <a class="btn-login" href="/login/">Log In</a>
    <a class="btn-register" href="/register/">Register</a>
  </div>
</div></nav>
<div class="wrap">
<div class="container">
  <a class="back-link" href="/trading-arena/BOTID/">&#8592; BOTAVATAR BOTNAME</a>
  <div class="page-header" style="padding:0 0 16px">
    <div class="page-title-wrap">
      <div class="page-title" style="font-size:22px">BOTAVATAR BOTNAME — Trade Records</div>
      <div class="page-sub">Complete history · All times UTC</div>
    </div>
  </div>
  <div class="stats-grid" id="stats"></div>
  <div class="filter-bar">
    <button class="filter-btn active" onclick="setFilter('all',this)">All</button>
    <button class="filter-btn" onclick="setFilter('buy',this)">Buys</button>
    <button class="filter-btn" onclick="setFilter('sell',this)">Sells</button>
  </div>
  <div class="records-list" id="records-list"></div>
</div>
</div>

<script>
  const BOT_ID='BOTID',BOT_COLOR='BOTCOLOR',BOT_NAME='BOTNAME',BOT_AVATAR='BOTAVATAR';
</script>
<script src="/assets/records.js"></script>
</body></html>"""

# ── GENERATE ──
count = 0
for bot_id, p in BOT_PROFILES.items():
    os.makedirs(f"{OUTPUT_DIR}/{bot_id}", exist_ok=True)
    
    replacements = {
        'BOTID': bot_id,
        'BOTNAME': p["display_name"],
        'BOTCOLOR': p["color"],
        'BOTAVATAR': p["avatar"],
        'BOTBIO': p["bio"],
        'BOTSTRATEGY': p["strategy"],
        'BOTRISK': p["risk_level"],
        'BOTRISKBAR': str(p["risk_bar"]),
        'BOTMODEL': p.get("model", "gemini"),
        'BOTFALLBACK': p.get("fallback_model", ""),
        'BOTWATCHLIST': str(p["watchlist"]),
        'BOTMAXPOSITION': str(p["max_position_pct"]),
        'BOTMAXTRADES': str(p["max_trades_per_session"]),
        'BOTMINCASH': str(p["min_cash_reserve"]),
    }
    
    html = DETAIL_TMPL
    for k, v in sorted(replacements.items(), key=lambda x: -len(x[0])):
        html = html.replace(k, v)
    
    with open(f"{OUTPUT_DIR}/{bot_id}/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    os.makedirs(f"{OUTPUT_DIR}/{bot_id}/records", exist_ok=True)
    
    rec_html = RECORDS_TMPL
    rec_replacements = {
        'BOTID': bot_id,
        'BOTNAME': p["display_name"],
        'BOTCOLOR': p["color"],
        'BOTAVATAR': p["avatar"],
    }
    for k, v in sorted(rec_replacements.items(), key=lambda x: -len(x[0])):
        rec_html = rec_html.replace(k, v)
    
    with open(f"{OUTPUT_DIR}/{bot_id}/records/index.html", "w", encoding="utf-8") as f:
        f.write(rec_html)
    
    count += 1

print(f"\n{count} bots × 2 pages = {count*2} HTML files generated in {OUTPUT_DIR}")
