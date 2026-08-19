#!/usr/bin/env python3
"""PaperChase SEO fix round 2:
1) Convert <div class="page-title"> to <h1 class="page-title"> (real H1 for crawlers)
2) Insert static SEO blurb <p> after page-title-wrap (crawler-readable text on JS-heavy pages)
3) Rebuild sitemap.xml with all pages + lastmod
"""
import re, os

ROOT = "/opt/voice-agent/workspace/paperchase"

BLURBS = {
    "crypto-pulse/index.html": (
        "Crypto Pulse tracks live crypto prices, the Bitcoin Fear & Greed Index, AI news "
        "sentiment and market trends in real time. Monitor Bitcoin, Ethereum and altcoin "
        "momentum, spot market mood shifts, and see what news sentiment says about where "
        "crypto is heading next."
    ),
    "poly-watch/index.html": (
        "Poly Watch scans prediction markets in real time, ranking contracts by volume, "
        "movement and AI confidence. Track the latest odds on Fed rate cuts, elections, "
        "Bitcoin price targets and more — with AI analysis on every market."
    ),
    "trading-arena/index.html": (
        "Trading Arena runs 20 AI trading bots head-to-head in live paper trading. Watch "
        "real portfolios, strategies and P&L, compare momentum vs mean-reversion vs "
        "multi-strategy bots, and see which AI stock-picking approach actually works."
    ),
    "stock-pick/index.html": (
        "Stock Pick scans mega-cap US equities daily, ranking the top 30 by AI-scored "
        "value and momentum signals. See today's best AI stock picks with full screening "
        "criteria and live market data."
    ),
}

BLURB_HTML = (
    '<p class="seo-blurb" style="max-width:640px;font-size:13px;line-height:1.65;'
    'color:var(--pc-text-2,#6b7280);margin:10px 0 0;padding:10px 14px;'
    'background:var(--pc-surface-2,#f8f9fb);border:1px solid var(--pc-border,#e5e7eb);'
    'border-radius:8px;">{}</p>'
)

def fix_h1(path):
    with open(path, encoding="utf-8") as f:
        html = f.read()
    # Only the page-title inside page-title-wrap (first occurrence is the H1 candidate)
    new, n = re.subn(
        r'<div class="page-title">([^<]+)</div>',
        r'<h1 class="page-title">\1</h1>',
        html, count=1
    )
    # Also close the matching div? No — the wrap div stays; we only converted the inner div to h1.
    if n:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new)
    return n

def insert_blurb(path, blurb):
    with open(path, encoding="utf-8") as f:
        html = f.read()
    if "seo-blurb" in html:
        return 0
    marker = re.compile(r'(</div>\s*\n\s*<div id="countdown-wrap"[^>]*></div>)')
    m = marker.search(html)
    if not m:
        return -1
    insert_at = m.start(1)
    new_html = html[:insert_at] + BLURB_HTML.format(blurb) + "\n    " + html[insert_at:]
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_html)
    return 1

results = []
for rel, blurb in BLURBS.items():
    path = os.path.join(ROOT, rel)
    h1n = fix_h1(path)
    bn = insert_blurb(path, blurb)
    results.append((rel, h1n, bn))

for r in results:
    print(f"{r[0]}: h1_fixed={r[1]} blurb_inserted={r[2]}")
