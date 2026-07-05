#!/usr/bin/env python3
"""
PaperChase Prediction Generator (AI-powered via OpenRouter)
Runs BEFORE market open (~9:00 AM ET / 1:00 PM UTC).
Uses OpenRouter to analyze market data, news sentiment, Reddit buzz & prediction markets.
"""
import json, os, sys, urllib.request, re
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE, "predictions", "data", "predictions.json")
MARKET_DATA_URL = "https://raw.githubusercontent.com/PaperChaseAdmin/market-sentinel/main/data/market_data.json"
TRADE_DATA_URL = "https://raw.githubusercontent.com/PaperChaseAdmin/trade/main/data/leaderboard.json"
POLY_DATA_URL = "https://raw.githubusercontent.com/PaperChaseAdmin/trade/main/data/polymarket/scan_results.json"

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")


def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperChase/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  ⚠️  Fetch failed: {url.split('/')[-1]}: {e}")
        return None


def call_openrouter(prompt, model=None, max_tokens=500):
    """Call OpenRouter AI. Tries models in order until one works."""
    if not OPENROUTER_KEY:
        print("  ⚠️  OPENROUTER_API_KEY not set")
        return None

    models_to_try = model or ["openrouter/free", "nvidia/nemotron-3-super-120b-a12b:free", "google/gemma-4-26b-a4b-it:free", "cohere/north-mini-code:free", "liquid/lfm-2.5-1.2b-thinking:free", "qwen/qwen3-coder:free"]

    if isinstance(models_to_try, str):
        models_to_try = [models_to_try]

    for m in models_to_try:
        try:
            import requests
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://paperchase.online",
                },
                json={
                    "model": m,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.2,
                },
                timeout=60,
            )
            if resp.ok:
                content = resp.json()["choices"][0]["message"].get("content")
                if content:
                    return content.strip()
                # content is None — model refused or can't respond
                err = "empty content (model refusal or safety filter)"
                print(f"  ⚠️  {m}: {err}")
                continue
            err = resp.json().get("error", {}).get("message", "")[:80]
            print(f"  ⚠️  {m}: {err}")
        except Exception as e:
            print(f"  ⚠️  {m}: {e}")

    return None
def extract_json(text):
    """Extract JSON array or object from AI response text."""
    if not text:
        return None
    # Strip markdown code blocks first
    text = re.sub(r'```(?:json)?\s*', '', text)
    text = text.strip()
    
    # Try to find JSON array
    m = re.search(r'\[.*?\]', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except:
            pass
    # Try to find JSON object  
    m = re.search(r'\{.*?\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except:
            pass
    # Last resort: try parsing the whole thing
    try:
        return json.loads(text)
    except:
        pass
    return None


def ai_market_predictions(md):
    """Use OpenRouter AI to predict index directions from all available data."""
    if not md:
        return []

    stocks = md.get("stocks", {})
    crypto = md.get("crypto", {})

    # Build context from ALL available data
    indices_str = json.dumps(stocks.get("indices", {}), indent=2)
    mood = stocks.get("market_mood", {})
    mood_str = json.dumps(mood, indent=2)

    # News summaries
    news = stocks.get("news", [])
    news_text = "\n".join(f"- [{n.get('source','?')}] {n['title']} ({n.get('sentiment','neutral')})" for n in news[:10]) if news else "No news data"

    # Reddit data
    reddit = stocks.get("reddit", [])
    reddit_text = ""
    if reddit:
        for r in reddit[:5]:
            mentions = r.get("mentions", {})
            top_mentions = sorted(mentions.items(), key=lambda x: x[1], reverse=True)[:5]
            m_str = ", ".join(f"{s}({c})" for s, c in top_mentions)
            reddit_text += f"- r/{r.get('subreddit','?')}: activity {r.get('activity_score',0)} | top mentioned: {m_str}\n"

    # Macro indicators (new)
    macro = stocks.get("macro", [])
    macro_text = "\n".join(f"- {m['name']}: {m.get('value','?')} ({m.get('change_24h',0):+.2f}%)" for m in macro) if macro else ""

    # Most active stocks (new)
    most_active = stocks.get("most_active", [])
    active_text = "\n".join(f"- {m['symbol']}: ${m.get('price_usd','?')} ({m.get('change_24h',0):+.2f}%) vol:{m.get('volume',0):,}" for m in most_active[:5]) if most_active else ""

    # Google Trends
    gt = stocks.get("google_trends", {})
    gt_stocks = gt.get("stocks", [])
    gt_crypto = gt.get("crypto", [])
    trends_text = ""
    if gt_stocks:
        trends_text += "Stock search interest (0-100):\n"
        trends_text += "\n".join(f"- {t['symbol']}: {t['interest_score']}" for t in gt_stocks[:8])
    if gt_crypto:
        trends_text += "\nCrypto search interest:\n"
        trends_text += "\n".join(f"- {t['keyword']}: {t['interest_score']}" for t in gt_crypto)

    # Reddit summary
    reddit_summary = stocks.get("reddit_summary", {}).get("summary", "")
    news_summary = stocks.get("news_summary", {}).get("summary", "")

    # Crypto data
    fg = crypto.get("fear_greed", {})
    btc = next((p for p in crypto.get("prices", []) if p.get("symbol") == "BTC"), {})
    crypto_reddit = crypto.get("reddit", [])
    crypto_reddit_text = ""
    if crypto_reddit:
        for r in crypto_reddit[:3]:
            mentions = r.get("mentions", {})
            top_m = sorted(mentions.items(), key=lambda x: x[1], reverse=True)[:3]
            m_str = ", ".join(f"{s}({c})" for s, c in top_m)
            crypto_reddit_text += f"- r/{r.get('subreddit','?')}: {m_str}\n"

    prompt = f"""You are a professional market analyst. Based on ALL the data below, predict the direction (up/down/neutral) for each major index today.

Indices:
{indices_str}

Market Mood: {mood_str}

Recent News Sentiment:
{news_text}

{("AI News Summary: " + news_summary) if news_summary else ""}

Reddit Stock Buzz:
{reddit_text or "No Reddit stock data"}
{("Reddit AI Summary: " + reddit_summary) if reddit_summary else ""}

Crypto:
- Fear & Greed: {fg.get('value', 'N/A')} ({fg.get('label', 'N/A')})
- BTC: ${btc.get('price_usd', 'N/A')} (24h: {btc.get('change_24h', 'N/A')}%)

Crypto Reddit:
{crypto_reddit_text or "No Reddit crypto data"}

Macro Indicators:
{macro_text or "No macro data"}

Most Active Stocks (by volume):
{active_text or "No volume data"}

Google Trends Search Interest:
{trends_text or "No trends data"}

Reply ONLY with a JSON object in this EXACT format:
{{"sp500":{{"direction":"up","confidence":75,"signal":"Bullish momentum from strong earnings and positive Reddit sentiment"}},"nasdaq":{{"direction":"up","confidence":70,"signal":"..."}},"dow":{{"direction":"neutral","confidence":50,"signal":"..."}},"crypto":{{"direction":"up","confidence":65,"signal":"..."}}}}

Rules:
- direction MUST be "up", "down", or "neutral"
- confidence: 1-100 integer reflecting how confident you are
- signal: brief reason mentioning actual data (news, reddit, momentum, F&G, etc.)
- Be honest — neutral + 50 is fine when signals are mixed
- CRITICAL: Base your analysis on the actual data provided above, NOT generic knowledge"""

    print("  Calling OpenRouter AI for predictions...")
    text = call_openrouter(prompt, max_tokens=600)
    if not text:
        print("  ⚠️  AI call failed, falling back to neutral")
        return None

    parsed = extract_json(text)
    if not parsed:
        print(f"  ⚠️  Could not parse AI response: {text[:200]}")
        return None

    # Extract stock index predictions
    results = []
    for key, label in [("sp500", "S&P 500"), ("nasdaq", "NASDAQ"), ("dow", "DOW")]:
        p = parsed.get(key, {})
        if isinstance(p, dict):
            results.append({
                "market": label,
                "prediction": p.get("direction", "neutral"),
                "confidence": min(100, max(1, int(p.get("confidence", 50)))),
                "signal": p.get("signal", "AI analysis")
            })
        else:
            results.append({"market": label, "prediction": "neutral", "confidence": 50, "signal": "AI analysis unavailable"})

    # Crypto prediction
    cp = parsed.get("crypto", {})
    if isinstance(cp, dict):
        results.append({
            "market": "Crypto Market",
            "prediction": cp.get("direction", "neutral"),
            "confidence": min(100, max(1, int(cp.get("confidence", 50)))),
            "signal": cp.get("signal", "AI analysis")
        })
    else:
        results.append({"market": "Crypto Market", "prediction": "neutral", "confidence": 50, "signal": "AI analysis unavailable"})

    return results


def ai_poly_predict(pd):
    """Use OpenRouter to analyze the top poly market bets."""
    if not pd:
        return [{"market": "Top Prediction Market", "prediction": "neutral", "confidence": 50, "signal": "No data available"}]

    markets = pd.get("markets", [])
    scored = sorted([m for m in markets if m.get("heuristic", {}).get("score", 0) >= 10],
                    key=lambda m: m.get("heuristic", {}).get("score", 0), reverse=True)

    if not scored:
        return [{"market": "Top Prediction Market", "prediction": "neutral", "confidence": 50, "signal": "No high-confidence markets today"}]

    top5 = scored[:5]
    context = "\n".join(
        f"- {m['question']} | Yes: {m['yes_price']*100:.0f}% | Ends: {m.get('end_date','?')[:10]} | Vol: ${m.get('volume',0):,.0f} | Heuristic: {m.get('heuristic',{}).get('score',0)}"
        for m in top5
    )

    prompt = f"""Analyze these prediction markets. Pick the SINGLE best bet for today.

Markets:
{context}

Reply with EXACTLY this JSON (no other text):
{{"question":"exact market question","bet":"YES","confidence":80,"rationale":"why this is the best bet"}}
- bet: "YES" or "NO" (YES = think it will happen, NO = won't happen)
- confidence: 1-100
- rationale: one brief sentence"""

    print("  Calling OpenRouter AI for poly watch pick...")
    text = call_openrouter(prompt, max_tokens=300)
    if not text:
        return [{"market": "Top Prediction Market", "prediction": "neutral", "confidence": 50, "signal": "AI unavailable"}]

    parsed = extract_json(text)
    if not parsed or not isinstance(parsed, dict):
        return [{"market": "Top Prediction Market", "prediction": "neutral", "confidence": 50, "signal": "AI parse failed"}]

    question = parsed.get("question", "Top Prediction Market")[:60]
    bet = parsed.get("bet", "YES")
    direction = "up" if bet == "YES" else "down"
    conf = min(100, max(1, int(parsed.get("confidence", 50))))
    rationale = parsed.get("rationale", "AI analysis")

    return [{"market": question, "prediction": direction, "confidence": conf, "signal": rationale}]


def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(f"📊 PaperChase AI Prediction Generator — {today}")
    print("=" * 50)

    # Load current predictions
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    # Check if already predicted today
    if data.get("last_prediction_date") == today:
        print("  Already predicted today. Skipping.")
        return

    # Check if market is open today via AI
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    weekday = datetime.now(timezone.utc).strftime("%A")
    print(f"\n  Checking if US markets open on {today_str} ({weekday})...")
    market_check = call_openrouter(
        f"Is the US stock market (NYSE/NASDAQ) open for regular trading today {today_str} ({weekday})? "
        "Reply with exactly: OPEN or CLOSED. If weekend or US holiday, reply CLOSED.",
        max_tokens=10
    )
    if market_check and 'CLOSED' in market_check.upper():
        print(f"  🏝️  Market CLOSED today ({market_check.strip()}). Skipping predictions.")
        return
    print(f"  ✅ Market OPEN — generating predictions...\n")

    print("1️⃣  Fetching market data...")
    md = fetch_json(MARKET_DATA_URL)

    print("\n2️⃣  Fetching prediction markets...")
    pd = fetch_json(POLY_DATA_URL)

    # AI-powered predictions
    print("\n3️⃣  AI Market Predictions (OpenRouter)...")
    all_preds = ai_market_predictions(md)
    if not all_preds:
        # Fallback to neutral
        print("  Using neutral fallback")
        all_preds = [
            {"market": "S&P 500", "prediction": "neutral", "confidence": 50, "signal": "AI unavailable"},
            {"market": "NASDAQ", "prediction": "neutral", "confidence": 50, "signal": "AI unavailable"},
            {"market": "DOW", "prediction": "neutral", "confidence": 50, "signal": "AI unavailable"},
            {"market": "Crypto Market", "prediction": "neutral", "confidence": 50, "signal": "AI unavailable"},
        ]

    # Separate by tool
    ms_preds = [p for p in all_preds if p["market"] in ("S&P 500", "NASDAQ", "DOW")]
    cp_preds = [p for p in all_preds if p["market"] == "Crypto Market"]

    print("\n4️⃣  AI Poly Watch Pick (OpenRouter)...")
    pw_preds = ai_poly_predict(pd)
    for p in pw_preds:
        print(f"    {p['market']}: {p['prediction'].upper()} ({p['confidence']}%) — {p['signal']}")

    # ═══════════════════════════════════════════
    # FIXED: Save predictions — use setdefault instead of .get(..., {})
    # ═══════════════════════════════════════════
    tools = data.setdefault("tools", {})
    for tool_key, preds in [("market_sentinel", ms_preds), ("crypto_pulse", cp_preds), ("poly_watch", pw_preds)]:
        tool = tools.setdefault(tool_key, {"label": tool_key.replace("_", " ").title(), "predictions": []})
        if "predictions" not in tool:
            tool["predictions"] = []
        for p in preds:
            tool["predictions"].append({
                "date": today,
                "market": p["market"],
                "prediction": p["prediction"],
                "confidence": p["confidence"],
                "signal": p["signal"],
                "actual": None,
                "correct": None,
                "settled": False
            })

    data["last_prediction_date"] = today
    data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    total_preds = sum(len(t.get("predictions", [])) for t in data["tools"].values())
    print(f"\n✅ Predictions saved ({total_preds} total)")
    for p in ms_preds:
        print(f"    {p['market']}: {p['prediction'].upper()} ({p['confidence']}%) — {p['signal']}")
    for p in cp_preds:
        print(f"    {p['market']}: {p['prediction'].upper()} ({p['confidence']}%) — {p['signal']}")


if __name__ == "__main__":
    main()
