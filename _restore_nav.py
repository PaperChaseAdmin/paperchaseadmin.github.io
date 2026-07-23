#!/usr/bin/env python3
"""Restore top nav on all pages, remove only login/register auth section."""
import re, os, glob

SITE = "/Users/davidtse/Documents/Hermes/paperchase_site"

NAV_HTML = '''<nav class="topbar"><div class="topbar-inner">
  <a class="logo" href="/">PaperChase<span>.</span></a>
  <div class="topbar-nav">
    <a class="nav-link" href="/market-sentinel/" data-i18n="nav_sentinel">Market Sentinel</a>
    <a class="nav-link" href="/crypto-pulse/" data-i18n="nav_cryptopulse">Crypto Pulse</a>
    <a class="nav-link" href="/poly-watch/" data-i18n="nav_polymarket">Poly Watch</a>
    <a class="nav-link" href="/stock-pick/">Stock Pick</a>
    <a class="nav-link" href="/trading-arena/" data-i18n="nav_trading">Trading Arena</a>
  </div>
</div></nav>'''

# Fix main pages
pages = ["index.html", "market-sentinel/index.html", "crypto-pulse/index.html",
         "poly-watch/index.html", "stock-pick/index.html", "trading-arena/index.html"]

for p in pages:
    fp = os.path.join(SITE, p)
    if not os.path.exists(fp):
        continue
    html = open(fp).read()
    # Replace removal comment with nav
    html = html.replace("<!-- Nav removed temporarily -->", NAV_HTML, 1)
    open(fp, 'w').write(html)
    print(f"  {p}")

print("\nDone.")
