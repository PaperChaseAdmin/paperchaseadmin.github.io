/**
 * Shared Countdown Script — PaperChase
 * Provides nextUpdateFor(tool) and startCountdown(el, label, tool)
 *
 * Update schedules:
 *   market-sentinel: every 10 min market hours, every 30 min otherwise
 *   crypto-pulse:    every 30 min, 24/7
 *   poly-watch:      daily 9:00 AM ET (13:00 UTC) Mon-Fri
 *   trading-arena:   daily 4:30 PM ET (20:30 UTC) Mon-Fri
 *   stock-pick:      daily 8:30 AM ET (12:30 UTC) Mon-Fri
 */

function nextUpdateFor(tool) {
  const now = new Date();
  const dow = now.getUTCDay();       // 0=Sun, 6=Sat
  const h = now.getUTCHours();
  const m = now.getUTCMinutes();
  const s = now.getUTCSeconds();
  const totalMin = h * 60 + m;

  // Market hours: Mon-Fri 9:30-16:00 ET = 13:30-20:00 UTC
  const MARKET_OPEN = 13 * 60 + 30;   // 13:30 UTC
  const MARKET_CLOSE = 20 * 60;        // 20:00 UTC
  const isMarketDay = dow >= 1 && dow <= 5;
  const isMarketHours = isMarketDay && totalMin >= MARKET_OPEN && totalMin < MARKET_CLOSE;

  // ── Helper: next occurrence at exact UTC minute offset from midnight ──
  function nextAtMinute(minOfDay) {
    const nx = new Date(now);
    nx.setUTCHours(0, 0, 0, 0);
    nx.setUTCMinutes(minOfDay);
    if (nx <= now) nx.setUTCDate(nx.getUTCDate() + 1);
    return nx;
  }

  // ── Helper: next weekday at given UTC hour+minute ──
  function nextWeekdayAt(hoursUTC, minutesUTC) {
    const nx = new Date(now);
    nx.setUTCHours(hoursUTC, minutesUTC, 0, 0);
    if (nx <= now) nx.setUTCDate(nx.getUTCDate() + 1);
    // Skip to Monday if weekend
    while (nx.getUTCDay() === 0 || nx.getUTCDay() === 6) {
      nx.setUTCDate(nx.getUTCDate() + 1);
    }
    return nx;
  }

  // ── Helper: next interval mark (XX:00 or XX:30) ──
  function nextInterval(minutes) {
    const totalSeconds = (h * 60 + m) * 60 + s;
    const intervalSec = minutes * 60;
    const nextSec = Math.ceil(totalSeconds / intervalSec) * intervalSec;
    const nx = new Date(now);
    nx.setUTCHours(0, 0, 0, 0);
    nx.setUTCSeconds(nextSec);
    return nx;
  }

  switch (tool) {

    case 'market-sentinel':
      if (isMarketHours) {
        // Every 10 min during market hours
        return nextInterval(10);
      }
      // Every 30 min outside market hours
      return nextInterval(30);

    case 'crypto-pulse':
      // Every 30 min, 24/7
      return nextInterval(30);

    case 'poly-watch':
      // Daily at 9:00 AM ET (13:00 UTC) Mon-Fri
      return nextWeekdayAt(13, 0);

    case 'trading-arena':
      // Daily at 4:30 PM ET (20:30 UTC) Mon-Fri
      return nextWeekdayAt(20, 30);

    case 'stock-pick':
      // Daily at 8:30 AM ET (12:30 UTC) Mon-Fri
      return nextWeekdayAt(12, 30);

    default:
      return nextInterval(30);
  }
}

/**
 * Start a countdown in the given container element.
 * @param {HTMLElement} el - The container element (usually #countdown-wrap)
 * @param {string}      label - The label text (e.g. "Next Review")
 * @param {string}      tool - Tool key passed to nextUpdateFor()
 * @param {function}    [onRefresh] - Optional callback when countdown reaches zero
 * @returns {number} timer ID
 */
function startCountdown(el, label, tool, onRefresh) {
  if (!el) return 0;
  const target = nextUpdateFor(tool);
  let timer = setInterval(tick, 1000);
  tick();
  return timer;

  function tick() {
    const diff = target - Date.now();
    if (diff <= 0) {
      el.innerHTML = '<span class="countdown-lbl">' + label + '</span><span class="countdown-num">Now</span>';
      if (onRefresh) onRefresh();
      target.setDate(target.getDate() + 1); // Show "Now" until the next tick falls through
      clearInterval(timer);
      timer = setInterval(tick, 1000);
      return;
    }
    const hh = Math.floor(diff / 3600000);
    const mm = Math.floor((diff % 3600000) / 60000);
    const ss = Math.floor((diff % 60000) / 1000);

    let display;
    if (hh >= 24) {
      display = Math.floor(hh / 24) + 'd ' + (hh % 24) + 'h ' + mm + 'm';
    } else if (hh >= 1) {
      display = String(hh).padStart(2, '0') + ':' + String(mm).padStart(2, '0') + ':' + String(ss).padStart(2, '0');
    } else {
      display = String(mm).padStart(2, '0') + ':' + String(ss).padStart(2, '0');
    }
    el.innerHTML = '<span class="countdown-lbl">' + label + '</span><span class="countdown-num">' + display + '</span>';
  }
}
