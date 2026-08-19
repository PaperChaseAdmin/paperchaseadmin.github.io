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

    models_to_try = model or ["deepseek/deepseek-chat", "mistralai/mistral-small-24b-instruct-2501", "qwen/qwen2.5-72b-instruct", "deepseek/deepseek-r1", "anthropic/claude-sonnet-4"]

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
                    "messages": [
                        {"role": "system", "content": "You are a market analyst. ALWAYS respond with valid JSON only. No explanations, no markdown, no text outside the JSON object. Your entire response must be parseable JSON."},
                        {"role": "user", "content": prompt}
                    ],
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
    
    # Try to find JSON object first (poly watch, market sentinel)
    m = re.search(r'\{.*?\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except:
            pass
    # Fallback: try JSON array  
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
    """AI-powered market predictions via OpenRouter deepseek/deepseek-chat.
    Analyzes all available context: indices, news, macro, sentiment, etc."""
    if not md:
        return None

    stocks = md.get("stocks", {})
    idx = stocks.get("indices", {})
    crypto = md.get("crypto", {})
    fg = crypto.get("fear_greed", {})
    btc = next((p for p in crypto.get("prices", []) if p.get("symbol") == "BTC"), {})
    mood = stocks.get("market_mood", {})
    news = (stocks.get("news") or [])[:6]
    macro = (stocks.get("macro") or [])[:4]
    active = (stocks.get("most_active") or [])[:6]

    # Build a compact context string
    lines = ["Current market data for predictions:\n"]
    for key, label in [("sp500","S&P 500"),("nasdaq","NASDAQ"),("dow","DOW")]:
        d = idx.get(key, {}) if isinstance(idx, dict) else {}
        v = d.get("value", "?")
        c = d.get("change_24h")
        chg = f"{c:+.2f}%" if c is not None else "N/A"
        lines.append(f"{label}: {v} ({chg})")

    if mood:
        ms = mood.get("score")
        lines.append(f"\nMarket Mood: {ms} ({mood.get('label','?')})" if ms is not None else "\nMarket Mood: N/A")

    if fg:
        lines.append(f"Fear&Greed: {fg.get('value','?')} ({fg.get('label','?')})")

    if btc:
        bp = btc.get("price_usd")
        bc = btc.get("change_24h")
        lines.append(f"BTC: ${bp:,} ({bc:+.2f}%)" if bp is not None and bc is not None else "")

    if macro:
        lines.append("\nMacro:")
        for m in macro:
            lines.append(f"  {m.get('name','?')}: {m.get('value','?')} ({m.get('change_24h',0):+.2f}%)")

    if active:
        lines.append("\nMost Active:")
        for a in active:
            lines.append(f"  {a.get('symbol','?')}: ${a.get('price_usd',0):,.2f} ({a.get('change_24h',0):+.2f}%)")

    if news:
        lines.append("\nTop News:")
        for n in news[:4]:
            lines.append(f"  [{n.get('source','?')}] {n.get('title','?')[:60]}")

    context = "\n".join(lines)

    prompt = f"""{context}

Based on the above market data, predict the DIRECTION for the NEXT trading session for each index.

Rules:
- Predict ONLY for: S&P 500, NASDAQ, DOW
- Direction: "up" (bullish), "down" (bearish), or "neutral" (mixed/unclear)
- Confidence: 51-95 integer (how sure you are)
- Signal: 1 short sentence explaining the key reason

Reply ONLY valid JSON. No other text.
Format: {{"predictions": [{{"market":"S&P 500","prediction":"up","confidence":65,"signal":"Strong earnings and positive macro data"}}]}}"""

    ai_raw = call_openrouter(prompt)
    if not ai_raw:
        print("  ⚠️  AI unavailable — falling back to heuristic")
        return None

    ai_data = extract_json(ai_raw)
    if not ai_data or not isinstance(ai_data, dict):
        print(f"  ⚠️  AI parse failed — falling back to heuristic. Raw: {ai_raw[:100]}")
        return None

    preds = ai_data.get("predictions", [])
    if not preds:
        print("  ⚠️  AI returned empty predictions — falling back to heuristic")
        return None

    # Validate structure
    valid = []
    for p in preds:
        if not isinstance(p, dict): continue
        mkt = p.get("market", "")
        if mkt not in ("S&P 500", "NASDAQ", "DOW"): continue
        dir_ = p.get("prediction", "neutral")
        if dir_ not in ("up", "down", "neutral"): dir_ = "neutral"
        conf = p.get("confidence", 50)
        try:
            conf = max(51, min(95, int(conf)))
        except:
            conf = 50
        signal = (p.get("signal") or "")[:80]
        valid.append({"market": mkt, "prediction": dir_, "confidence": conf, "signal": signal})

    if len(valid) < 3:
        print(f"  ⚠️  AI returned only {len(valid)}/3 valid predictions — falling back")
        return None

    print(f"  ✅ AI predictions ({len(valid)} indices)")
    return valid


def ai_poly_predict(pd):
    """Poly watch using heuristic scoring (no AI)."""
    if not pd:
        return [{"market": "Top Prediction Market", "prediction": "neutral", "confidence": 50, "signal": "No data"}]
    markets = pd.get("markets", [])
    scored = sorted([m for m in markets if m.get("heuristic", {}).get("score", 0) >= 10],
                    key=lambda m: m.get("heuristic", {}).get("score", 0), reverse=True)
    if not scored:
        return [{"market": "Top Prediction Market", "prediction": "neutral", "confidence": 50, "signal": "No high-confidence markets"}]
    best = scored[0]
    yes_pct = int(best.get("yes_price", 0.5) * 100)
    no_pct = 100 - yes_pct
    direction = "up" if yes_pct >= 50 else "down"
    conf = max(51, yes_pct if yes_pct >= 50 else no_pct)
    sig = f"{best.get('question','?')[:50]} | Yes {yes_pct}% / No {no_pct}% | Vol ${best.get('volume',0):,.0f}"
    return [{"market": best.get("question", "Top Prediction Market")[:60], "prediction": direction, "confidence": conf, "signal": sig}]



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

    # Check if market is open today (simple weekday check, no AI dependency)
    weekday = datetime.now(timezone.utc).weekday()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"\n  Checking if US markets open on {today_str} (weekday={weekday})...")
    if weekday >= 5:
        print(f"  🏝️  Weekend — skipping predictions.")
        return
    print(f"  ✅ Weekday — generating predictions...\n")

    print("1️⃣  Fetching market data...")
    md = fetch_json(MARKET_DATA_URL)

    print("\n2️⃣  Fetching prediction markets...")
    pd = fetch_json(POLY_DATA_URL)

    # AI-powered predictions
    print("\n3️⃣  AI Market Predictions (OpenRouter)...")
    all_preds = ai_market_predictions(md)
    if not all_preds:
        # Fallback to heuristic
        print("  Using heuristic fallback")
        stocks = md.get("stocks", {}) if md else {}
        idx = stocks.get("indices", {}) if isinstance(stocks, dict) else {}
        crypto = md.get("crypto", {}) if md else {}
        fg = crypto.get("fear_greed", {}) if crypto else {}
        btc = next((p for p in crypto.get("prices", []) if p.get("symbol") == "BTC"), {}) if crypto else {}

        def calc_dir(chg):
            if chg is None or chg == 0:
                return "neutral", 50
            abs_chg = abs(chg)
            if abs_chg < 0.3:
                return "neutral", 50
            dir_ = "up" if chg > 0 else "down"
            conf = min(85, 50 + int(abs_chg * 12))
            return dir_, conf

        all_preds = []
        for key, label in [("sp500","S&P 500"),("nasdaq","NASDAQ"),("dow","DOW")]:
            d = idx.get(key, {}) if isinstance(idx, dict) else {}
            chg = d.get("change_24h")
            dir_, conf = calc_dir(chg)
            sig = f"{label} {chg:+.2f}% today" if chg is not None else "No data available"
            all_preds.append({"market": label, "prediction": dir_, "confidence": conf, "signal": sig})

        btc_chg = btc.get("change_24h") if btc else None
        if btc_chg is not None:
            dir_, conf = calc_dir(btc_chg)
            fg_str = f"Fear&Greed: {fg.get('value','?')} ({fg.get('label','?')})" if fg else ""
            sig = f"BTC {btc_chg:+.2f}% | {fg_str}" if fg_str else f"BTC {btc_chg:+.2f}%"
        else:
            dir_, conf, sig = "neutral", 50, "No crypto data"
        all_preds.append({"market": "Crypto Market", "prediction": dir_, "confidence": conf, "signal": sig})

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
