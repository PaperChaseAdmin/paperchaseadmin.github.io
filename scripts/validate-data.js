#!/usr/bin/env node
/* PaperChase Data Integrity Check — run after every data update */
const https = require('https');
const URL = 'https://raw.githubusercontent.com/PaperChaseAdmin/paperchaseadmin.github.io/main/data/market_data.json';

function get(url) {
  return new Promise((resolve, reject) => {
    https.get(url, r => {
      let d = '';
      r.on('data', c => d += c);
      r.on('end', () => resolve(JSON.parse(d)));
    }).on('error', reject);
  });
}

async function main() {
  const errors = [];
  const d = await get(URL);

  // 1. Check updated_at is recent (< 2 hours)
  const age = (Date.now() - new Date(d.updated_at).getTime()) / 3600000;
  if (age > 2) errors.push(`STALE: data age ${age.toFixed(1)}h > 2h`);

  // 2. Check stocks data
  const st = d.stocks || {};
  if (!st.indices || Object.values(st.indices).every(v => !v))
    errors.push('FAIL: all indices are None');
  if (!st.market_mood || st.market_mood.score === undefined)
    errors.push('FAIL: market_mood missing');
  if (!st.prices || st.prices.length === 0)
    errors.push('FAIL: no stock prices');

  // 3. Check news freshness (no source older than 7 days)
  const news = st.news || [];
  const staleSources = {};
  for (const n of news) {
    if (n.date) {
      const d = new Date(n.date);
      if (!isNaN(d) && (Date.now() - d) / 86400000 > 7)
        staleSources[n.source] = (staleSources[n.source] || 0) + 1;
    }
  }
  for (const [src, count] of Object.entries(staleSources))
    errors.push(`STALE NEWS: ${src} (${count} articles >7d old)`);

  // 4. Check crypto data
  const cr = d.crypto || {};
  if (!cr.fear_greed || cr.fear_greed.value === undefined)
    errors.push('FAIL: crypto fear_greed missing');
  if (!cr.prices || cr.prices.length === 0)
    errors.push('FAIL: no crypto prices');

  // 5. Check mood label matches score
  const mood = st.market_mood;
  if (mood && mood.score !== undefined && mood.label) {
    const expected = mood.score > 0.1 ? 'Bullish' : mood.score < -0.1 ? 'Bearish' : 'Neutral';
    if (mood.label !== expected && Math.abs(mood.score) > 0.3)
      errors.push(`SUSPICIOUS: mood score=${mood.score.toFixed(3)} but label="${mood.label}"`);
  }

  if (errors.length) {
    console.log('DATA VALIDATION FAILED:');
    errors.forEach(e => console.log(`  ❌ ${e}`));
    process.exit(1);
  }

  // 6. Check predictions + stock-pick freshness (deploy-dependent)
  const extra = [
    ['predictions', 'https://paperchase.online/predictions/data/predictions.json', 'updated_at'],
    ['stock-pick', 'https://paperchase.online/stock-pick/data/picks.json', 'updated_at'],
  ];
  for (const [name, url, key] of extra) {
    try {
      const r = await fetch(url + '?t=' + Date.now());
      const j = await r.json();
      const age = (Date.now() - new Date(j[key]).getTime()) / 3600000;
      if (age > 30) errors.push(`STALE ${name.toUpperCase()}: ${age.toFixed(0)}h old`);
    } catch { errors.push(`FAIL: cannot fetch ${name}`); }
  }
  if (errors.length) {
    console.log('DATA VALIDATION FAILED:');
    errors.forEach(e => console.log(`  ❌ ${e}`));
    process.exit(1);
  }
  console.log(`DATA VALIDATION PASSED ✅ (${news.length} articles, ${st.prices?.length || 0} stocks, ${cr.prices?.length || 0} crypto)`);
}

main().catch(e => { console.error('VALIDATION ERROR:', e.message); process.exit(1); });
