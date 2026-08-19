#!/usr/bin/env python3
"""PaperChase SEO batch update: og tags + twitter cards + JSON-LD + robots fixes."""
import os, re, json

ROOT = "/opt/voice-agent/workspace/paperchase"
OG_IMAGE = "https://paperchase.online/assets/og-image.png"
SITE = "https://paperchase.online"

# ---- Per-page overrides for title/description (SEO-optimised) ----
PAGE_META = {
    "index.html": {
        "title": "PaperChase — Free AI Trading Bots & Market Intelligence Platform",
        "desc": "Watch 20 AI trading bots compete in real-time paper trading. Free market sentiment, crypto fear & greed index, stock screener and prediction market scanner — all in one place.",
        "og_type": "website",
    },
    "market-sentinel/index.html": {
        "title": "Market Sentiment Dashboard — Fear & Greed Index & AI Market Mood | PaperChase",
        "desc": "Real-time market sentiment dashboard: Fear & Greed index, S&P 500 / NASDAQ / DOW tracking, AI-powered market mood scoring and news sentiment analysis.",
        "og_type": "website",
    },
    "crypto-pulse/index.html": {
        "title": "Crypto Fear & Greed Index & Crypto Market Pulse — Live Prices & AI Sentiment | PaperChase",
        "desc": "Live crypto market pulse: Bitcoin & Ethereum prices, crypto fear & greed index, CoinGecko trending coins, news sentiment and AI-powered crypto predictions.",
        "og_type": "website",
    },
    "poly-watch/index.html": {
        "title": "Poly Watch — AI Prediction Market Scanner & High-Confidence Bets | PaperChase",
        "desc": "AI-powered prediction market scanner. Find high-confidence Polymarket bets with heuristic scoring, AI analysis and accuracy tracking.",
        "og_type": "website",
    },
    "stock-pick/index.html": {
        "title": "AI Stock Screener — Top Daily Stock Picks Ranked by Composite Score | PaperChase",
        "desc": "Daily AI-powered stock screener: top 30 stock picks ranked by composite score combining technical, value, growth and quality factors.",
        "og_type": "website",
    },
    "trading-arena/index.html": {
        "title": "Trading Arena — Watch 20 Live AI Trading Bots Compete in Paper Trading | PaperChase",
        "desc": "Watch 20 AI-powered trading bots compete with $10,000 each in real-time paper trading. Transparent AI decisions, live leaderboard and full trade history.",
        "og_type": "website",
    },
    "predictions/index.html": {
        "title": "AI Market Predictions — S&P 500, NASDAQ & Crypto Forecasts with Tracked Accuracy | PaperChase",
        "desc": "AI-powered market predictions for S&P 500, NASDAQ, DOW and crypto. Daily forecasts with full accuracy tracking and history.",
        "og_type": "website",
    },
}

# ---- FAQ JSON-LD per core page ----
FAQ_DATA = {
    "market-sentinel/index.html": [
        ("What is the market fear and greed index?", "The Fear & Greed index measures investor sentiment on a 0-100 scale, where 0 means extreme fear and 100 means extreme greed. PaperChase tracks it live alongside AI-powered market mood scoring."),
        ("How does AI market sentiment analysis work?", "PaperChase's Market Sentinel uses AI to analyse financial news headlines, assign sentiment scores to each story, and aggregate them into a single market mood score for major indices."),
    ],
    "crypto-pulse/index.html": [
        ("What is the crypto fear and greed index?", "The crypto Fear & Greed index measures overall cryptocurrency market sentiment from 0 (extreme fear) to 100 (extreme greed), based on volatility, volume, social media and surveys."),
        ("Which crypto prices does Crypto Pulse track?", "Crypto Pulse tracks live Bitcoin and Ethereum prices plus major altcoin data, CoinGecko trending coins, macro indicators and AI-generated crypto market predictions."),
    ],
    "poly-watch/index.html": [
        ("What is a prediction market scanner?", "A prediction market scanner automatically analyses prediction markets (like Polymarket) to find trades where the market price may differ from the true probability, flagging potential high-confidence opportunities."),
        ("How accurate are PaperChase prediction market signals?", "PaperChase tracks every AI-generated prediction signal with full accuracy history, showing hit rates across markets so you can judge the scanner's performance yourself."),
    ],
    "stock-pick/index.html": [
        ("How does the AI stock screener work?", "The screener ranks stocks daily using a composite score that blends technical analysis, valuation, growth and quality factors — each with transparent weightings shown on the page."),
        ("What factors are used to rank stock picks?", "Four factor groups are weighted: technical (trend, momentum, MACD), value (P/E, P/B), growth (revenue, earnings growth) and quality (profitability, balance sheet strength)."),
    ],
    "trading-arena/index.html": [
        ("What is PaperChase Trading Arena?", "Trading Arena pits 20 AI trading bots against each other, each starting with a virtual $10,000 paper trading portfolio. You can watch every trade, strategy and decision in real time."),
        ("Are the trading bots real or simulated?", "All bots run on paper trading — simulated portfolios with real market data. Every trade is recorded transparently so you can audit each bot's decisions and performance."),
    ],
    "predictions/index.html": [
        ("How accurate are the AI market predictions?", "PaperChase tracks every prediction's outcome and publishes an accuracy score per market (S&P 500, NASDAQ, DOW, crypto) with full historical records."),
        ("How often are market predictions updated?", "Predictions are generated daily per trading session, covering direction, magnitude and confidence for major indices and crypto markets."),
    ],
}

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)

def get_tag(html, tag, attr):
    m = re.search(r'<%s[^>]*%s="([^"]*)"[^>]*>' % (tag, attr), html) or \
        re.search(r'<%s[^>]*>[^<]*</%s>' % (tag, tag), html)
    return m.group(1) if m else ""

def get_title(html):
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S)
    return m.group(1).strip() if m else ""

def get_meta_desc(html):
    m = re.search(r'<meta name="description" content="([^"]*)"', html)
    return m.group(1) if m else ""

def get_canonical(html):
    m = re.search(r'<link rel="canonical" href="([^"]*)"', html)
    return m.group(1) if m else ""

def bot_slug(path):
    # e.g. /trading-arena/warren/index.html -> warren
    m = re.search(r"/trading-arena/([^/]+)/index\.html$", path)
    return m.group(1) if m else None

def main():
    changed = 0
    for dirpath, _, files in os.walk(ROOT):
        for fn in files:
            if not fn.endswith(".html"):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, ROOT)
            html = read(p)

            # Skip if og:title already present
            if 'property="og:title"' in html:
                continue

            # Determine page identity
            rel_key = rel.replace("\\", "/")
            slug = bot_slug(rel_key)
            is_records = rel_key.endswith("/records/index.html") or "records/" in rel_key
            is_auth = rel_key in ("login/index.html", "register/index.html", "account/index.html")
            is_home = rel_key == "index.html"

            title = get_title(html).strip()
            desc = get_meta_desc(html)
            canon = get_canonical(html) or SITE + "/" + rel_key
            canon = canon.rstrip("/") + "/" if canon.endswith("/") else canon

            if rel_key in PAGE_META:
                title = PAGE_META[rel_key]["title"]
                desc = PAGE_META[rel_key]["desc"]
            og_type = PAGE_META.get(rel_key, {}).get("og_type", "website")

            # Build og + twitter tags (insert after canonical)
            og = (
                f'<meta property="og:site_name" content="PaperChase"/>\n'
                f'<meta property="og:type" content="{og_type}"/>\n'
                f'<meta property="og:title" content="{title}"/>\n'
                f'<meta property="og:description" content="{desc}"/>\n'
                f'<meta property="og:url" content="{canon}"/>\n'
                f'<meta property="og:image" content="{OG_IMAGE}"/>\n'
                f'<meta property="og:locale" content="en_US"/>\n'
                f'<meta name="twitter:card" content="summary_large_image"/>\n'
                f'<meta name="twitter:title" content="{title}"/>\n'
                f'<meta name="twitter:description" content="{desc}"/>\n'
                f'<meta name="twitter:image" content="{OG_IMAGE}"/>\n'
            )

            # Build JSON-LD
            ld = {"@context": "https://schema.org", "@type": "WebPage",
                  "name": title, "description": desc, "url": canon}
            if is_home:
                ld["@type"] = "WebSite"
                ld["name"] = "PaperChase"
                ld["alternateName"] = "PaperChase AI Trading"
                ld["publisher"] = {"@type": "Organization", "name": "PaperChase", "logo": {"@type": "ImageObject", "url": OG_IMAGE}}
            elif slug and not is_records:
                ld["@type"] = "WebApplication"
                ld["applicationCategory"] = "FinanceApplication"
                ld["operatingSystem"] = "Web"
                ld["offers"] = {"@type": "Offer", "price": "0", "priceCurrency": "USD"}
                ld["breadcrumb"] = {"@type": "BreadcrumbList", "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Trading Arena", "item": SITE + "/trading-arena/"},
                    {"@type": "ListItem", "position": 3, "name": slug.title() + " AI Trading Bot", "item": canon},
                ]}
            elif is_records:
                ld["breadcrumb"] = {"@type": "BreadcrumbList", "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Trading Arena", "item": SITE + "/trading-arena/"},
                    {"@type": "ListItem", "position": 3, "name": "Trade Records", "item": canon},
                ]}
            elif rel_key in FAQ_DATA:
                faq = [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ_DATA[rel_key]]
                ld["mainEntity"] = faq

            # Robots handling: auth pages -> noindex
            if is_auth:
                if '<meta name="robots"' in html:
                    html = re.sub(r'<meta name="robots" content="[^"]*"', '<meta name="robots" content="noindex, nofollow"', html)
                else:
                    html = html.replace('<link rel="canonical"', '<meta name="robots" content="noindex, nofollow"/>\n<link rel="canonical"', 1)

            # predictions page missing robots -> add index,follow
            if rel_key == "predictions/index.html" and '<meta name="robots"' not in html:
                html = html.replace('<link rel="canonical"', '<meta name="robots" content="index, follow"/>\n<link rel="canonical"', 1)

            # Insert og tags after canonical
            html = html.replace('<link rel="canonical"', '<link rel="canonical"', 1)  # no-op safety
            html = re.sub(r'(<link rel="canonical"[^>]*/>)', r'\1\n' + og, html, count=1)

            # Insert JSON-LD before </head>
            ld_json = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>\n'
            html = html.replace("</head>", ld_json + "</head>", 1)

            write(p, html)
            changed += 1
            print(f"OK {rel_key}")

    print(f"\nDone: {changed} files updated")

if __name__ == "__main__":
    main()
