#!/usr/bin/env python3
"""
PaperChase Prediction Settlement
Runs AFTER market close (~4:30 PM ET / 8:30 PM UTC).
Compares predictions with actual market performance.
"""
import json, os, sys, urllib.request
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE, "predictions", "data", "predictions.json")
MARKET_DATA_URL = "https://raw.githubusercontent.com/PaperChaseAdmin/market-sentinel/main/data/market_data.json"

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")


def call_openrouter(prompt, max_tokens=50):
    """Quick OpenRouter call for simple checks. Returns text or None."""
    if not OPENROUTER_KEY:
        return None
    try:
        import requests
        for model in ["google/gemma-4-31b-it:free", "nvidia/nemotron-3-super-120b-a12b:free"]:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json", "HTTP-Referer": "https://paperchase.online"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "temperature": 0},
                timeout=15,
            )
            if r.ok:
                return r.json()["choices"][0]["message"]["content"].strip()
    except:
        pass
    return None


def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperChase/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"  ⚠️  Fetch failed: {e}")
        return None

def settle_market_prediction(pred, indices_map):
    """Check if a market direction prediction was correct."""
    market = pred.get("market", "")
    prediction = pred.get("prediction", "neutral")
    if prediction == "neutral":
        return None  # Neutral = no settle

    # Find matching index
    idx_key = None
    for key, label in [("sp500", "S&P 500"), ("nasdaq", "NASDAQ"), ("dow", "DOW")]:
        if market == label or market.lower() in label.lower():
            idx_key = key
            break

    if not idx_key or idx_key not in indices_map:
        return None

    idx = indices_map[idx_key]
    actual_chg = idx.get("change_24h", 0)

    if actual_chg > 0:
        actual_dir = "up"
    elif actual_chg < 0:
        actual_dir = "down"
    else:
        actual_dir = "neutral"

    correct = prediction == actual_dir
    return correct, actual_dir, actual_chg

def settle_crypto_prediction(pred, md):
    """Check crypto prediction using BTC performance."""
    crypto = md.get("crypto", {})
    prices = crypto.get("prices", [])
    btc = next((p for p in prices if p.get("symbol") == "BTC"), {})
    btc_chg = btc.get("change_24h", 0)

    if btc_chg > 0:
        actual_dir = "up"
    elif btc_chg < 0:
        actual_dir = "down"
    else:
        actual_dir = "neutral"

    prediction = pred.get("prediction", "neutral")
    if prediction == "neutral":
        return None

    correct = prediction == actual_dir
    return correct, actual_dir, btc_chg

def main():
    today_dt = datetime.now(timezone.utc)
    today = today_dt.strftime("%Y-%m-%d")

    print(f"📊 PaperChase Prediction Settlement — {today}")
    print("=" * 50)

    # Check if market was open today via AI
    weekday = today_dt.strftime("%A")
    check = call_openrouter(
        f"Was the US stock market (NYSE/NASDAQ) open for regular trading today {today} ({weekday})? "
        "Reply with exactly: OPEN or CLOSED.",
        max_tokens=10
    )
    if check and 'CLOSED' in check.upper():
        print(f"  🏝️  Market CLOSED today. Skipping settlement.")
        return
    print(f"  ✅ Market was OPEN — settling predictions...\n")

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    if data.get("last_settle_date") == today:
        print("  Already settled today. Skipping.")
        return

    print("\n1️⃣  Fetching market data for settlement...")
    md = fetch_json(MARKET_DATA_URL)
    if not md:
        print("  ❌ Cannot settle without market data.")
        sys.exit(1)

    stocks = md.get("stocks", {})
    indices_map = stocks.get("indices", {})

    if not indices_map:
        print("  ❌ No index data available for settlement.")
        sys.exit(1)

    print(f"\n  Actual index changes:")
    for key, label in [("sp500", "S&P 500"), ("nasdaq", "NASDAQ"), ("dow", "DOW")]:
        idx = indices_map.get(key, {})
        chg = idx.get("change_24h", 0)
        print(f"    {label}: {chg:+.2f}% {'📈' if chg > 0 else '📉' if chg < 0 else '➡️'}")

    tools = data.get("tools", {})
    total_settled = 0
    total_correct = 0

    for tool_key, tool in tools.items():
        preds = tool.get("predictions", [])
        today_preds = [p for p in preds if p.get("date") == today and not p.get("settled")]

        if not today_preds:
            continue

        for pred in today_preds:
            result = None
            if tool_key == "market_sentinel":
                result = settle_market_prediction(pred, indices_map)
            elif tool_key == "crypto_pulse":
                result = settle_crypto_prediction(pred, md)
            elif tool_key == "poly_watch":
                result = None  # Poly Watch predictions don't settle same-day

            if result:
                correct, actual_dir, actual_chg = result
                pred["actual"] = actual_dir
                pred["change_pct"] = round(actual_chg, 2)
                pred["correct"] = correct
                pred["settled"] = True
                total_settled += 1
                if correct:
                    total_correct += 1

                icon = "✅" if correct else "❌"
                print(f"\n    {tool['label']} — {pred['market']}")
                print(f"      Predicted: {pred['prediction'].upper()} | Actual: {actual_dir.upper()} ({actual_chg:+.2f}%)")
                print(f"      {icon} {'CORRECT' if correct else 'WRONG'}")

    # Update accuracy stats
    for tool_key, tool in tools.items():
        settled = [p for p in tool.get("predictions", []) if p.get("settled")]
        correct = [p for p in settled if p.get("correct")]
        tool["total"] = len(settled)
        tool["correct"] = len(correct)
        tool["accuracy_pct"] = round(len(correct) / len(settled) * 100, 1) if settled else None

    data["last_settle_date"] = today
    data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    if total_settled > 0:
        print(f"\n{'=' * 50}")
        print(f"✅ Settled {total_settled}/{len(today_preds)} predictions — {total_correct}/{total_settled} correct ({round(total_correct/total_settled*100,1) if total_settled else 0}%)")
    else:
        print("\n  No predictions to settle today.")

if __name__ == "__main__":
    main()
