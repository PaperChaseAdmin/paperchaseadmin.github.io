#!/usr/bin/env python3
"""Add PWA manifest link + SW registration to all page heads."""
import os
SITE = "/Users/davidtse/Documents/Hermes/paperchase_site"
MANIFEST = '<link rel="manifest" href="/manifest.json"/>'
SW_SCRIPT = '<script src="/assets/sw-register.js"></script>'

pages = ["index.html", "market-sentinel/index.html", "crypto-pulse/index.html",
         "poly-watch/index.html", "stock-pick/index.html", "trading-arena/index.html",
         "login/index.html", "register/index.html", "account/index.html",
         "confirmed/index.html"]

for p in pages:
    fp = os.path.join(SITE, p)
    if not os.path.exists(fp): continue
    html = open(fp).read()
    changed = False
    if MANIFEST not in html:
        html = html.replace('<link rel="canonical"', MANIFEST + '\n<link rel="canonical"')
        changed = True
    if SW_SCRIPT not in html:
        html = html.replace('</body>', SW_SCRIPT + '\n</body>')
        changed = True
    if changed:
        open(fp, 'w').write(html)
        print(f"  {p}: PWA links added")

print("Done.")
