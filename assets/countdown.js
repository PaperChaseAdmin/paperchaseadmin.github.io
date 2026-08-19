/**
 * Shared Countdown Script — PaperChase
 * Provides nextUpdateFor(tool) and startCountdown(el, label, tool)
 *
 * Update schedules (real cadence, 2026-08-14):
 *   market-sentinel / crypto-pulse / poly-watch / home: hourly (:00 UTC, GH Actions schedule)
 *   predictions / stock-pick: daily 12:30 UTC, Mon–Fri (predict.yml)
 *   trading-arena: every 30 min during market hours (cron-job.org 8148615)
 */

// HTML-escape user-generated / AI content before innerHTML injection
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}

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
    // floor+1: always the NEXT boundary (ceil would return the current one at exact marks)
    const nextSec = (Math.floor(totalSeconds / intervalSec) + 1) * intervalSec;
    const nx = new Date(now);
    nx.setUTCHours(0, 0, 0, 0);
    nx.setUTCSeconds(nextSec);
    return nx;
  }

  // ── Helper: next market open (Mon–Fri 13:30 UTC) ──
  function nextMarketOpen() {
    const nx = new Date(now);
    nx.setUTCHours(13, 30, 0, 0);
    if (nx <= now) nx.setUTCDate(nx.getUTCDate() + 1);
    while (nx.getUTCDay() === 0 || nx.getUTCDay() === 6) {
      nx.setUTCDate(nx.getUTCDate() + 1);
    }
    return nx;
  }

  switch (tool) {
    case 'market-sentinel':
    case 'crypto-pulse':
    case 'poly-watch':
      // Market data refreshes hourly on the hour
      return nextInterval(60);
    case 'predictions':
    case 'stock-pick':
      // AI predictions + stock picks: daily 12:30 UTC, Mon–Fri
      return nextWeekdayAt(12, 30);
    case 'trading-arena':
      // Bot runs every 30 min during market hours, else next market open
      if (isMarketHours) return nextInterval(30);
      return nextMarketOpen();
    default:
      return nextInterval(60);
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
    el.innerHTML = '<span class="dot"></span><span class="countdown-lbl">' + label + '</span><span class="countdown-num">' + display + '</span>';
  }
}
