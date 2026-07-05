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

    models_to_try = model or ["nvidia/nemotron-3-super-120b-a12b:free", "google/gemma-4-26b-a4b-it:free", "cohere/north-mini-code:free", "nvidia/nemotron-3-ultra-550b-a55b:free", "qwen/qwen3-coder:free", "openrouter/free"]

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
    """Heuristic market predictions based on actual index data (no AI dependency)."""
    if not md:
        return []
    stocks = md.get("stocks", {})
    idx = stocks.get("indices", {})
    crypto = md.get("crypto", {})
    fg = crypto.get("fear_greed", {})
    btc = next((p for p in crypto.get("prices", []) if p.get("symbol") == "BTC"), {})

    def calc_dir(chg):
        """Determine direction and confidence from % change."""
        if chg is None or chg == 0:
            return "neutral", 50
        abs_chg = abs(chg)
        if abs_chg < 0.3:
            return "neutral", 50
        dir_ = "up" if chg > 0 else "down"
        conf = min(85, 50 + int(abs_chg * 12))
        return dir_, conf

    results = []
    for key, label in [("sp500","S&P 500"),("nasdaq","NASDAQ"),("dow","DOW")]:
        d = idx.get(key, {}) if isinstance(idx, dict) else {}
        chg = d.get("change_24h")
        dir_, conf = calc_dir(chg)
        sig = f"{label} {chg:+.2f}% today" if chg is not None else "No data available"
        results.append({"market": label, "prediction": dir_, "confidence": conf, "signal": sig})

    btc_chg = btc.get("change_24h")
    if btc_chg is not None:
        dir_, conf = calc_dir(btc_chg)
        fg_str = f"Fear&Greed: {fg.get('value','?')} ({fg.get('label','?')})" if fg else ""
        sig = f"BTC {btc_chg:+.2f}% | {fg_str}" if fg_str else f"BTC {btc_chg:+.2f}%"
    else:
        dir_, conf, sig = "neutral", 50, "No crypto data"
    results.append({"market": "Crypto Market", "prediction": dir_, "confidence": conf, "signal": sig})
    return results


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
