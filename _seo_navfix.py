#!/usr/bin/env python3
"""Batch add SEO meta tags + remove nav from all PaperChase pages."""
import re, glob, os

SITE = "https://paperchase.online"
PAGE_META = {
    "index.html": ("Home", "AI-powered trading & market intelligence dashboard. Real-time stock & crypto sentiment, prediction markets, and automated trading bots.", "AI trading, market intelligence, stock sentiment, crypto analysis, paper trading"),
    "market-sentinel/index.html": ("Market Sentinel", "Real-time market sentiment dashboard tracking stock indices, news sentiment, fear & greed index, and prediction markets.", "market sentiment, stock market dashboard, fear greed index, market intelligence"),
    "crypto-pulse/index.html": ("Crypto Pulse", "Live crypto market intelligence tracking Bitcoin, Ethereum, and top altcoins with news sentiment, 4chan trends, and Fear & Greed index.", "crypto dashboard, bitcoin news, ethereum price, crypto sentiment, altcoin tracker"),
    "poly-watch/index.html": ("Poly Watch", "Prediction market scanner tracking Polymarket contracts on Fed rates, crypto prices, geopolitics, and sports.", "polymarket, prediction markets, crypto prediction, fed rate prediction"),
    "stock-pick/index.html": ("Stock Pick", "AI-powered stock screener analyzing 200+ US stocks with MACD, RSI, and value metrics for the best picks.", "stock screener, AI stock picks, MACD analysis, RSI screener, value investing"),
    "trading-arena/index.html": ("Trading Arena", "Watch 20 AI-powered trading bots compete with $10,000 each in live paper trading featuring real-time P&L tracking.", "AI trading bots, paper trading, algorithmic trading, bot competition"),
}

def add_seo_and_remove_nav(filepath, title, desc, keywords):
    with open(filepath) as f:
        html = f.read()
    
    # Add SEO tags after <title>
    seo = f'''<meta name="description" content="{desc}"/>
<meta name="keywords" content="{keywords}"/>
<meta property="og:title" content="{title} · PaperChase"/>
<meta property="og:description" content="{desc}"/>
<meta property="og:url" content="{SITE}/{filepath.replace('/index.html','').replace('index.html','').replace('/','/')}"/>
<meta property="og:type" content="website"/>
<meta name="twitter:card" content="summary_large_image"/>
<link rel="canonical" href="{SITE}/{filepath.replace('/index.html','').replace('index.html','')}"/>'''
    
    # Insert after </title>
    html = html.replace("</title>", f"</title>\n{seo}", 1)
    
    # Remove nav — comment it out
    nav_pattern = re.compile(r'<nav class="topbar">.*?</nav>', re.DOTALL)
    html = nav_pattern.sub('<!-- Nav removed temporarily -->', html, count=1)
    
    with open(filepath, 'w') as f:
        f.write(html)
    print(f"  {filepath}")

# Main pages
for path, (title, desc, keywords) in PAGE_META.items():
    full = os.path.join(os.path.dirname(__file__) or '.', path)
    if os.path.exists(full):
        add_seo_and_remove_nav(full, title, desc, keywords)

print("\nDone.")
