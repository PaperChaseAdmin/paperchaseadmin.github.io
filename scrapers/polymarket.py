"""
Polymarket public API — no key required.
Fetches top 10 markets by 24h volume, no categorization.
"""
import requests, json

API = "https://gamma-api.polymarket.com/markets"
HEADERS = {"User-Agent": "MarketSentinelBot/1.0"}
SPORTS_KW = [" vs. ", " vs ", "o/u ", "spread", "moneyline",
    "nba", "nfl", "mlb", "nhl", "fifa", "super bowl", "playoffs"]


def is_sports(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in SPORTS_KW)


def fetch_polymarket(limit: int = 500) -> dict:
    all_markets = []
    try:
        r = requests.get(
            API,
            params={"limit": limit, "active": "true", "order": "volume24hr", "ascending": "false"},
            headers=HEADERS, timeout=10,
        )
        r.raise_for_status()
        for m in r.json():
            title = m.get("question") or m.get("title") or ""
            if is_sports(title):
                continue
            vol_raw = m.get("volume24hr") or m.get("volume") or 0
            volume = float(str(vol_raw).split()[0]) if vol_raw else 0
            prices_raw = m.get("outcomePrices", '["0.5","0.5"]')
            try:
                if isinstance(prices_raw, str):
                    prices_raw = json.loads(prices_raw)
                yes_bid = float(prices_raw[0]) if prices_raw else 0.5
            except (ValueError, TypeError, json.JSONDecodeError):
                yes_bid = 0.5
            if yes_bid <= 0.02 or yes_bid >= 0.98:
                continue
            all_markets.append({
                "title": title,
                "volume_24h": round(volume),
                "yes_price": round(yes_bid, 2),
                "url": f"https://polymarket.com/market/{m.get('slug', '')}",
            })
    except Exception as e:
        print(f"  [Polymarket] failed: {e}")

    all_markets.sort(key=lambda x: x["volume_24h"], reverse=True)
    return {"markets": all_markets[:10]}
