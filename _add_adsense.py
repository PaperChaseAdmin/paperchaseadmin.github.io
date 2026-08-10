#!/usr/bin/env python3
"""Add Google AdSense script to all pages + create privacy policy page."""
import os

SITE = "/Users/davidtse/Documents/Hermes/paperchase_site"
ADSENSE = '''<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5238177146851721" crossorigin="anonymous"></script>'''

pages = ["index.html", "market-sentinel/index.html", "crypto-pulse/index.html",
         "poly-watch/index.html", "stock-pick/index.html", "predictions/index.html",
         "trading-arena/index.html", "login/index.html", "register/index.html",
         "account/index.html", "confirmed/index.html"]

for p in pages:
    fp = os.path.join(SITE, p)
    if not os.path.exists(fp):
        continue
    html = open(fp).read()
    if 'adsbygoogle' not in html:
        html = html.replace('<link rel="stylesheet" href="/assets/design-system.css"/>',
                            ADSENSE + '\n<link rel="stylesheet" href="/assets/design-system.css"/>')
        open(fp, 'w').write(html)
        print(f"  {p}: AdSense added")
    else:
        print(f"  {p}: already has AdSense")

# Also add to bot detail pages (in generate_pages.py)
gp = "/Users/davidtse/Documents/Hermes/paper_trading/generate_pages.py"
g = open(gp).read()
if 'adsbygoogle' not in g:
    g = g.replace('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap"/>',
                  ADSENSE + '\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap"/>')
    open(gp, 'w').write(g)
    print(f"  generate_pages.py: AdSense added")

print("Done.")
