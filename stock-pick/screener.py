#!/usr/bin/env python3
"""
Daily Stock Screener – S&P 500 mega-cap value + technical momentum scan.

Fetches fundamental & price data from yfinance, filters by strict criteria,
ranks by a weighted composite score, and outputs the top 30 picks as JSON.
"""

import json
import math
import sys
import time
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any

import yfinance as yf

# ── Hardcoded ~200 major US stocks (S&P 500 heavy hitters + broad sector coverage) ──
TICKERS = [
    # Communication Services
    "META", "GOOGL", "GOOG", "NFLX", "CMCSA", "DIS", "T", "VZ",
    # Consumer Discretionary
    "AMZN", "TSLA", "HD", "MCD", "BKNG", "NKE", "SBUX", "LOW", "TJX",
    "MAR", "GM", "F", "ROST", "DHI", "LEN", "EBAY", "ETSY", "ABNB",
    # Consumer Staples
    "PG", "KO", "PEP", "WMT", "COST", "CL", "KMB", "MO", "MDLZ",
    "EL", "GIS", "K", "CAG", "SJM", "CPB", "CLX", "CHD", "KDP",
    # Energy
    "XOM", "CVX", "COP", "EOG", "SLB", "OXY", "MPC", "PSX", "VLO",
    "HES", "FANG", "DVN", "WMB", "OKE", "TRGP",
    # Financials
    "JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "AXP", "C", "BLK",
    "SCHW", "CB", "MMC", "SPGI", "ICE", "CME", "PNC", "TFC", "USB",
    "COF", "AIG", "MET", "PRU", "ALL", "TRV", "BK", "FITB", "KEY",
    # Health Care
    "UNH", "JNJ", "LLY", "PFE", "MRK", "ABBV", "TMO", "ABT", "DHR",
    "BMY", "AMGN", "CVS", "CI", "HCA", "ISRG", "SYK", "BSX", "GILD",
    "VRTX", "REGN", "MRNA", "BIIB", "ILMN", "ZTS", "EW", "BDX", "ALGN",
    # Industrials
    "GE", "CAT", "RTX", "HON", "BA", "UPS", "UNP", "MMM", "LMT",
    "GD", "NOC", "DE", "ADP", "CARR", "ETN", "EMR", "ITW", "CSX",
    "NSC", "FDX", "PCAR", "CMI", "PH", "ROK", "PAYX", "ODFL",
    # Information Technology
    "AAPL", "MSFT", "NVDA", "AVGO", "CSCO", "ORCL", "ADBE", "CRM",
    "ACN", "INTC", "AMD", "IBM", "QCOM", "TXN", "MU", "AMAT", "ADI",
    "LRCX", "KLAC", "FIS", "FISV", "NOW", "WDAY", "ADSK", "ANET",
    "INTU", "PYPL", "SQ", "SHOP", "PANW", "CRWD", "DDOG", "MDB",
    "SNOW", "PLTR", "ZS", "NET", "DOCU", "TEAM", "HUBS", "OKTA",
    # Materials
    "LIN", "APD", "SHW", "ECL", "NEM", "FCX", "DOW", "DD", "PPG",
    "CTVA", "CF", "MOS", "ALB", "VMC", "MLM", "NUE", "STLD",
    # Real Estate
    "PLD", "AMT", "CCI", "EQIX", "PSA", "O", "DLR", "AVB", "EQR",
    "WELL", "SPG", "WY", "MAA", "ESS", "UDR", "BXP",
    # Utilities
    "NEE", "DUK", "SO", "D", "AEP", "EXC", "PCG", "ED", "SRE",
    "PEG", "WEC", "XEL", "ES", "FE", "DTE", "EIX", "AWK",
]


# ── Helpers ──

def safe_float(val: Any) -> float | None:
    """Return a float or None if the value is absent / non-numeric."""
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def compute_rsi(prices, period: int = 14) -> float | None:
    """Compute RSI using Wilder's smoothing method."""
    if prices is None or len(prices) < period + 1:
        return None
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0.0 for d in deltas]
    losses = [-d if d < 0 else 0.0 for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def compute_macd(prices):
    """
    Compute MACD (12, 26, 9) and return 'golden', 'death', or 'none'.
    golden cross = MACD line crosses above signal line (most recent close).
    death cross  = MACD line crosses below signal line.
    Uses EMA approximation.
    """
    if prices is None or len(prices) < 35:
        return "none"

    def emma(data, period):
        k = 2.0 / (period + 1)
        out = [data[0]]
        for v in data[1:]:
            out.append(out[-1] + k * (v - out[-1]))
        return out

    ema12 = emma(prices, 12)
    ema26 = emma(prices, 26)
    macd_line = [e12 - e26 for e12, e26 in zip(ema12, ema26)]

    signal = emma(macd_line, 9)

    if len(macd_line) < 2:
        return "none"

    # Check if MACD crossed above signal (golden) or below (death) at last bar
    prev_diff = macd_line[-2] - signal[-2]
    curr_diff = macd_line[-1] - signal[-1]

    if prev_diff <= 0 and curr_diff > 0:
        return "golden"
    elif prev_diff >= 0 and curr_diff < 0:
        return "death"
    return "none"


def compute_score(row: dict) -> float:
    """
    Weighted composite score (higher = better).
    technical 40%  |  value 30%  |  growth 20%  |  quality 10%
    Each sub-score is normalised to 0-100.
    """
    t = 0.0  # technical (RSI ideal ~50, MACD golden = good, volume ratio)
    v = 0.0  # value   (lower P/E better, FCF yield higher better)
    g = 0.0  # growth  (revenue growth higher better)
    q = 0.0  # quality (low debt/equity, high FCF yield)

    # ── Technical (40%) ──
    rsi = row.get("rsi", 50) or 50
    # Bell curve: peak at 50, tails at 30 and 70
    if rsi <= 50:
        t_rsi = 100 * (rsi - 30) / 20 if rsi >= 30 else 0
    else:
        t_rsi = 100 * (70 - rsi) / 20 if rsi <= 70 else 0
    t += t_rsi * 0.5  # 50% of technical weight

    macd = row.get("macd_signal", "none")
    t_macd = 100 if macd == "golden" else (0 if macd == "death" else 50)
    t += t_macd * 0.25  # 25% of technical weight

    vol_ratio = row.get("volume_ratio", 1.0) or 1.0
    t_vol = min(100, max(0, (vol_ratio - 1.0) * 100))
    t += t_vol * 0.25  # 25% of technical weight

    # ── Value (30%) ──
    pe = row.get("pe_ratio", 20) or 20
    v_pe = max(0, 100 * (20 - pe) / 18) if pe < 20 else 0
    v += v_pe * 0.5  # 50% of value weight

    fcf_yield = row.get("fcf_yield", 3) or 3
    v_fcf = min(100, fcf_yield * 10)  # 10% yield = 100
    v += v_fcf * 0.5  # 50% of value weight

    # ── Growth (20%) ──
    rev_growth = row.get("revenue_growth", 10) or 10
    g = min(100, rev_growth * 3)  # 33%+ growth = 100

    # ── Quality (10%) ──
    de = row.get("debt_equity", 1.0) or 1.0
    q_de = max(0, 100 * (1.5 - de) / 1.5)  # 0 D/E = 100, 1.5 = 0
    q += q_de * 0.5

    fcf_q = min(100, fcf_yield * 10)
    q += fcf_q * 0.5

    return round(t * 0.40 + v * 0.30 + g * 0.20 + q * 0.10, 2)


def generate_summary(row: dict) -> str:
    """One-sentence AI-style reason for the pick."""
    parts = []
    if row.get("macd_signal") == "golden":
        parts.append("bullish MACD crossover")
    rsi = row.get("rsi")
    if rsi is not None:
        parts.append(f"RSI at {rsi:.0f}")
    if (row.get("volume_ratio") or 0) > 1.2:
        parts.append("strong volume confirmation")
    if (row.get("fcf_yield") or 0) > 5:
        parts.append(f"high FCF yield of {row['fcf_yield']:.1f}%")
    if (row.get("revenue_growth") or 0) > 20:
        parts.append(f"solid {row['revenue_growth']:.0f}% revenue growth")
    if (row.get("pe_ratio") or 99) < 15:
        parts.append(f"low P/E of {row['pe_ratio']:.1f}")
    if (row.get("debt_equity") or 999) < 0.5:
        parts.append("strong balance sheet")

    if parts:
        return f"{row['symbol']} — {'; '.join(parts)}."
    return f"{row['symbol']} — balanced fundamentals with momentum."


def ai_analysis(picks: list[dict]) -> list[dict]:
    """Use OpenRouter AI to generate a brief analysis for each pick."""
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not openrouter_key or not picks:
        return picks

    # Batch analyze top 15 picks
    batch = "\n".join(
        f"{i+1}. {p['symbol']} ({p['company_name']}) | Sector: {p['sector']} | P/E: {p.get('pe_ratio','?')} | "
        f"RSI: {p.get('rsi','?')} | MACD: {p.get('macd_signal','none')} | "
        f"Rev Growth: {p.get('revenue_growth','?')}% | FCF Yield: {p.get('fcf_yield','?')}% | "
        f"D/E: {p.get('debt_equity','?')} | Score: {p.get('composite_score','?')}"
        for i, p in enumerate(picks[:15])
    )

    prompt = f"""Analyze each stock pick below. For each, give a ONE-SENTENCE investment thesis.

Reply ONLY with a JSON array of objects, one per stock:
[{{"symbol":"AAPL","analysis":"Strong buy — robust FCF yield combined with bullish MACD crossover and reasonable valuation."}},...]

Be specific — mention actual metrics from the data (P/E, RSI, MACD, FCF yield, revenue growth, debt/equity).
Max 25 words per analysis. No markdown, no extra text.

Stocks:
{batch}"""

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://paperchase.online",
            },
            json={
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024,
                "temperature": 0.1,
            },
            timeout=30,
        )
        if not resp.ok:
            print(f"  [AI Analysis] HTTP {resp.status_code}")
            return picks

        text = resp.json()["choices"][0]["message"]["content"].strip()
        # Extract JSON array
        import re
        m = re.search(r'\[.*\]', text, re.DOTALL)
        if not m:
            print(f"  [AI Analysis] Could not parse response: {text[:150]}")
            return picks

        analyses = json.loads(m.group())
        analysis_map = {a["symbol"]: a["analysis"] for a in analyses if "symbol" in a and "analysis" in a}

        for p in picks:
            if p["symbol"] in analysis_map:
                p["ai_analysis"] = analysis_map[p["symbol"]]

        print(f"  [AI Analysis] Generated for {len(analysis_map)} stocks")
    except Exception as e:
        print(f"  [AI Analysis] {e}")

    return picks


# ── Processor ──

def process_stock(ticker: str) -> dict | None:
    """
    Fetch and analyse a single ticker.
    Returns a dict if all filters pass, otherwise None.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info:
            return None

        # ── Fundamentals ──
        market_cap = safe_float(info.get("marketCap"))
        pe_ratio = safe_float(info.get("trailingPE"))
        revenue_growth = safe_float(info.get("revenueGrowth"))
        # revenueGrowth from yfinance is a decimal (e.g. 0.15 = 15%)
        if revenue_growth is not None:
            revenue_growth *= 100

        fcf = safe_float(info.get("freeCashflow"))
        total_debt = safe_float(info.get("totalDebt"))
        total_equity = safe_float(info.get("totalStockholderEquity"))
        sector = info.get("sector", "N/A")
        company_name = info.get("longName") or info.get("shortName") or ticker
        current_price = safe_float(info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose"))

        # Compute FCF yield (%)
        fcf_yield = None
        if fcf is not None and market_cap is not None and market_cap > 0:
            fcf_yield = (fcf / market_cap) * 100

        # Compute Debt/Equity
        debt_equity = None
        if total_debt is not None and total_equity is not None and total_equity > 0:
            debt_equity = total_debt / total_equity

        # ── Price / volume data (60 days) ──
        hist = stock.history(period="3mo")
        if hist.empty:
            return None

        closes = hist["Close"].dropna().tolist()
        volumes = hist["Volume"].dropna().tolist()

        if len(closes) < 35 or len(volumes) < 30:
            return None

        rsi = compute_rsi(closes, 14)
        macd_signal = compute_macd(closes)

        # 50-day average volume
        avg_vol_50d = sum(volumes[-50:]) / min(50, len(volumes[-50:]))
        latest_vol = volumes[-1]
        volume_ratio = latest_vol / avg_vol_50d if avg_vol_50d > 0 else 1.0

        # ── MINIMUM HARD FILTERS (only eliminate truly unsuitable) ──
        # Market Cap > 100B
        if market_cap is None or market_cap <= 100_000_000_000:
            return None
        # P/E — reject only extreme (>50)
        if pe_ratio is not None and pe_ratio > 50:
            return None
        # MACD death cross — reject (strong sell signal)
        if macd_signal == "death":
            return None
            return None

        row = {
            "symbol": ticker,
            "company_name": company_name,
            "sector": sector,
            "price": round(current_price, 2) if current_price is not None else None,
            "market_cap": round(market_cap / 1e9, 2),  # in billions
            "pe_ratio": round(pe_ratio, 2) if pe_ratio is not None else None,
            "macd_signal": macd_signal,
            "rsi": round(rsi, 1) if rsi is not None else None,
            "volume_ratio": round(volume_ratio, 2) if volume_ratio is not None else None,
            "revenue_growth": round(revenue_growth, 1) if revenue_growth is not None else None,
            "fcf_yield": round(fcf_yield, 2) if fcf_yield is not None else None,
            "debt_equity": round(debt_equity, 2) if debt_equity is not None else None,
        }
        row["composite_score"] = compute_score(row)
        row["summary"] = generate_summary(row)
        return row

    except Exception as e:
        print(f"  [!] {ticker}: {e}")
        return None


def main():
    all_results = []
    passes = []

    tickers = TICKERS
    total = len(tickers)

    # Sequential processing to avoid yfinance rate limiting
    for i, ticker in enumerate(tickers):
        result = process_stock(ticker)
        if result:
            passes.append(result)
        # Light progress indicator
        if (i + 1) % 25 == 0 or (i + 1) == total:
            print(f"Progress: {i + 1}/{total} processed, {len(passes)} passed so far...",
                  file=sys.stderr)
        # Delay to avoid rate limiting
        time.sleep(0.5)

    # Sort by composite_score descending, take top 30
    passes.sort(key=lambda x: x["composite_score"], reverse=True)
    top_picks = passes[:30]

    # AI analysis
    print(f"\n  Running AI analysis on top {min(15, len(top_picks))} picks...")
    top_picks = ai_analysis(top_picks)

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total_screened": total,
        "passing": len(passes),
        "picks": top_picks,
    }

    output_path = "/mnt/c/Hermes/paperchase_site/stock-pick/data/picks.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
