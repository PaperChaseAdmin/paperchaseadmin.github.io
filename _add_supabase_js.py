#!/usr/bin/env python3
"""Add supabase-client.js and auth nav to all main pages."""
import os

SITE = "/Users/davidtse/Documents/Hermes/paperchase_site"
pages = ["index.html", "market-sentinel/index.html", "crypto-pulse/index.html",
         "poly-watch/index.html", "stock-pick/index.html", "trading-arena/index.html"]

for p in pages:
    fp = os.path.join(SITE, p)
    html = open(fp).read()
    
    # Add supabase-client.js before </body>
    if 'supabase-client.js' not in html:
        html = html.replace('</body>', '<script src="/assets/supabase-client.js"></script>\n</body>')
    
    open(fp, 'w').write(html)
    print(f"  {p}: added supabase-client.js")

print("Done.")
