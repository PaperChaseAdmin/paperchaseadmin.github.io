#!/usr/bin/env python3
"""
PaperChase Prediction Generator
Runs BEFORE market open (~9:00 AM ET / 1:00 PM UTC).
Predicts stock index direction using pre-market data + sentiment.
"""
import json, os, sys, urllib.request
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE, "predictions", "data", "predictions.json")
MARKET_DATA_URL = "https://raw.githubusercontent.com/PaperChaseAdmin/market-sentinel/main/data/market_data.json"
TRADE_DATA_URL = "https://raw.githubusercontent.com/PaperChaseAdmin/trade/main/data/leaderboard.json"
POLY_DATA_URL = "https://raw.githubusercontent.com/PaperChaseAdmin/trade/main/data/polymarket/scan_results.json"

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperChase/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  ⚠️  Fetch failed: {url.split('/')[-1]}: {e}")
        return None

def market_sentinel_predict(md):
    """Predict S&P 500, NASDAQ, Dow direction using sentiment + momentum."""
    stocks = md.get("stocks", {})
    indices = stocks.get("indices", {})
    mood = stocks.get("market_mood", {})

    results = []
    for key, label in [("sp500", "S&P 500"), ("nasdaq", "NASDAQ"), ("dow", "DOW")]:
        idx = indices.get(key, {})
        chg = idx.get("change_24h", 0)
        score = mood.get("score", 0.5) if mood else 0.5

        # Direction: momentum + sentiment weighted
        if chg > 0.3 and score > 0.5:
            direction, signal, conf = "up", "Momentum + bullish sentiment", 70
        elif chg > 0 and score > 0.4:
            direction, signal, conf = "up", "Slight positive momentum", 55
        elif chg < -0.3 and score < 0.5:
            direction, signal, conf = "down", "Negative momentum + bearish sentiment", 70
        elif chg < 0 and score < 0.6:
            direction, signal, conf = "down", "Slight negative momentum", 55
        elif score > 0.6:
            direction, signal, conf = "up", "Bullish market sentiment", 60
        elif score < 0.4:
            direction, signal, conf = "down", "Bearish market sentiment", 60
        else:
            direction, signal, conf = "neutral", "Mixed signals — wait and see", 50

        results.append({
            "market": label, "prediction": direction,
            "confidence": conf, "signal": signal
        })
    return results

def crypto_pulse_predict(md):
    """Predict crypto direction using Fear & Greed (contrarian)."""
    crypto = md.get("crypto", {})
    fg = crypto.get("fear_greed", {})
    val = fg.get("value", 50)
    label = fg.get("label", "Neutral")

    if val <= 20:
        direction, signal, conf = "up", f"Extreme Fear ({val}) — contrarian buy signal", 75
    elif val <= 35:
        direction, signal, conf = "up", f"Fear ({val}) — potential recovery", 60
    elif val >= 80:
        direction, signal, conf = "down", f"Extreme Greed ({val}) — contrarian sell signal", 75
    elif val >= 65:
        direction, signal, conf = "down", f"Greed ({val}) — potential pullback", 60
    else:
        # Momentum-based
        prices = crypto.get("prices", [])
        btc = next((p for p in prices if p.get("symbol") == "BTC"), {})
        btc_chg = btc.get("change_24h", 0)
        if btc_chg > 2:
            direction, signal, conf = "up", f"BTC momentum +{btc_chg:.1f}%", 60
        elif btc_chg < -2:
            direction, signal, conf = "down", f"BTC selloff {btc_chg:.1f}%", 60
        else:
            direction, signal, conf = "neutral", F"Neutral sentiment ({label})", 50

    return [{
        "market": "Crypto Market",
        "prediction": direction,
        "confidence": conf,
        "signal": signal
    }]

def poly_watch_predict(pd):
    """Use top pick from prediction markets as the prediction."""
    if not pd:
        return [{"market": "Top Prediction Market", "prediction": "neutral", "confidence": 50, "signal": "No data available"}]
    markets = pd.get("markets", [])
    scored = [m for m in markets if m.get("heuristic", {}).get("score", 0) >= 15]
    scored.sort(key=lambda m: m.get("heuristic", {}).get("score", 0), reverse=True)
    if not scored:
        return [{"market": "Top Prediction Market", "prediction": "neutral", "confidence": 50, "signal": "No top picks today"}]

    top = scored[0]
    yes_pct = top.get("yes_price", 0.5) * 100
    bet_yes = yes_pct >= 50
    direction = "up" if bet_yes else "down"
    question = top.get("question", "Unknown market")[:60]

    return [{
        "market": question,
        "prediction": direction,
        "confidence": round(max(yes_pct, 100 - yes_pct)),
        "signal": f"Yes: {yes_pct:.0f}% — heuristic score: {top['heuristic']['score']}"
    }]

def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(f"📊 PaperChase Prediction Generator — {today}")
    print("=" * 50)

    # Load current predictions
    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    # Check if already predicted today
    if data.get("last_prediction_date") == today:
        print("  Already predicted today. Skipping.")
        return

    print("\n1️⃣  Fetching market data...")
    md = fetch_json(MARKET_DATA_URL)

    print("\n2️⃣  Market Sentinel — Stock Index Predictions...")
    ms_preds = market_sentinel_predict(md) if md else []
    for p in ms_preds:
        print(f"    {p['market']}: {p['prediction'].upper()} ({p['confidence']}%) — {p['signal']}")

    print("\n3️⃣  Crypto Pulse — Crypto Prediction...")
    cp_preds = crypto_pulse_predict(md) if md else []
    for p in cp_preds:
        print(f"    {p['market']}: {p['prediction'].upper()} ({p['confidence']}%) — {p['signal']}")

    print("\n4️⃣  Poly Watch — Prediction Market Top Pick...")
    pd = fetch_json(POLY_DATA_URL)
    pw_preds = poly_watch_predict(pd)
    for p in pw_preds:
        print(f"    {p['market']}: {p['prediction'].upper()} ({p['confidence']}%) — {p['signal']}")

    # Save predictions
    tools = data.get("tools", {})
    for tool_key, preds in [("market_sentinel", ms_preds), ("crypto_pulse", cp_preds), ("poly_watch", pw_preds)]:
        tool = tools.get(tool_key, {})
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
        tool["total"] = len(tool["predictions"])

    data["last_prediction_date"] = today
    data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Predictions saved to predictions.json ({sum(len(t.get('predictions',[])) for t in tools.values())} total)")

if __name__ == "__main__":
    main()
