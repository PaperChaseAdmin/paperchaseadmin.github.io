#!/usr/bin/env python3
"""Add auth links back to all page navs (with IDs for supabase toggling)."""
import os

SITE = "/Users/davidtse/Documents/Hermes/paperchase_site"
AUTH_HTML = '''  <div class="topbar-spacer"></div>
  <div class="topbar-auth">
    <a class="nav-link" href="/login/" id="nav-login">Log In</a>
    <a class="nav-link nav-reg" href="/register/" id="nav-register" style="background:var(--pc-brand);color:#fff;border-radius:var(--pc-radius);padding:6px 14px">Register</a>
    <a class="nav-link" href="/account/" id="nav-account" style="display:none">Account</a>
    <a class="nav-link" href="#" id="nav-logout" style="display:none" onclick="PaperChaseAuth.signOut();return false">Log Out</a>
  </div>'''

pages = ["index.html", "market-sentinel/index.html", "crypto-pulse/index.html",
         "poly-watch/index.html", "stock-pick/index.html", "trading-arena/index.html",
         "login/index.html", "register/index.html", "account/index.html"]

for p in pages:
    fp = os.path.join(SITE, p)
    if not os.path.exists(fp):
        continue
    html = open(fp).read()
    # Check if auth section already exists
    if 'nav-login' in html:
        print(f"  {p}: already has auth links, skipping")
        continue
    
    # Find the nav closing and insert auth section
    if '</div></nav>' in html:
        html = html.replace('</div></nav>', AUTH_HTML + '\n</div></nav>', 1)
        open(fp, 'w').write(html)
        print(f"  {p}: added auth links")
    else:
        print(f"  {p}: no nav found")

print("\nDone.")
