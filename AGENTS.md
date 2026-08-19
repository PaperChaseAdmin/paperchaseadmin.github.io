# PaperChase Site — Agent Guidelines (READ THIS FIRST)

This file is **binding** for any agent working on this repository (SEO, blog, content, or code).
It exists because a previous workspace-sync destroyed working features and reverted months of fixes.
**Violating these rules breaks the site. When in doubt, ask before acting.**

---

## 0. The Golden Rules (never break these)

1. **NEVER blanket-sync or mass-overwrite files from a local/workspace copy.**
   The repo's `main` branch is the single source of truth. Your workspace is a VIEW, not a source.
   Always `git pull --rebase` before editing, edit files in place, and push only your changes.
   A `sync: full site update from workspace` commit is **forbidden** — it silently reverted
   XSS protections, workflow fixes, and live data (stock picks rolled back 6 weeks).

2. **NEVER `git push --force` on `main`.** It destroys the data-bot's commits and breaks rollback.

3. **NEVER hand-edit or restore old copies of generated data files** (see §5). They are
   produced by automated workflows; if one looks stale, fix the workflow, not the file.

4. **NEVER add a second visual theme.** The site has exactly one design system
   (`assets/design-system.css`). New content MUST use its tokens and classes. No inline
   `<style>` blocks with custom colors, no hardcoded `#hex` colors in HTML, no third-party
   CSS frameworks, no "looks nice in isolation" styles. This includes blog pages.

---

## 1. Architecture

- **Static site on GitHub Pages** — no backend, no build step. HTML is served as-is.
- Root repo: `PaperChaseAdmin/paperchaseadmin.github.io` → `paperchase.online`
- Trade engine repo: `PaperChaseAdmin/trade` (bot runner + bot data) — do not edit unless asked.
- **Data flow**: workflows (`.github/workflows/`) scrape → commit JSON to `data/` → trigger
  deploy (see §6). Pages fetch JSON at runtime via `fetch()` — no server-side rendering.
- Language: static HTML + vanilla JS. Chart.js (deferred) only on `trading-arena/index.html`.
  Bot pages use inline SVG charts.

## 2. Design System (UI rules)

### Tokens (use these, never raw hex in HTML)
All design tokens are CSS custom properties in `assets/design-system.css` `:root`:
`--pc-bg`, `--pc-surface`, `--pc-text`, `--pc-text-2`, `--pc-text-3`, `--pc-heading`,
`--pc-brand` (gold), `--pc-border`, `--pc-green`, `--pc-red`, `--pc-yellow`, `--pc-blue`,
`--pc-purple`, `--pc-shadow-*`, `--pc-radius*`, `--pc-mono`, `--pc-font`, `--pc-max-width`.

### Allowed classes (extend the design system, don't bypass it)
- Layout: `.container`, `.wrap`, `.dash-grid`, `.split-view`, `.dash-full`
- Topbar: `.topbar`, `.topbar-inner`, `.logo`, `.topbar-nav`, `.nav-link` (+`.active`), `.topbar-auth`
- Content: `.card`, `.tool-card`, `.section-head`, `.stat-card`, `.indice`, `.news-card`,
  `.news-item`, `.mood-bar`, `.table-wrap` + `table/th/td`
- Actions: `.btn`, `.btn-primary`, `.btn-ghost`, `.btn-sm`
- Status: `.badge`, `.badge-correct/wrong/pending`, `.b-bull/bear/neut`
- Articles: `.article` / `.article-body`, `.meta`, `.tip`, `.warn`, `.info`, `.cta`, `.related-links`, `.live`
- Countdown: `.countdown-wrap`, `.countdown-lbl`, `.countdown-num`

### Structure every page the same way
1. `<head>`: charset → viewport → title → description → canonical → og:* → robots →
   JSON-LD (if applicable) → favicon `<link rel="icon" href="/assets/icons/icon-192.png"/>`
   → gtag → fonts (Inter + JetBrains Mono) → `<link rel="stylesheet" href="/assets/design-system.css">`
2. `<nav class="topbar">…</nav>` — identical across pages, with the active page marked `.nav-link.active`
3. `<div class="container">` (or `.wrap` for articles) → content
4. `<footer class="footer">…</footer>` — identical across pages

### Typography & tone
- Financial dashboard, professional. Inter for UI, JetBrains Mono for numbers/prices.
- Headings: h1 = page title (max 1 per page), h2 = sections, h3 = sub-sections. Never skip levels.
- No emoji in headings or table cells on data pages (headers may use small icons).
- Copy must be factual and transparent. No hype, no "revolutionary AI", no guaranteed profits.

### Mobile
- All responsive behavior comes from the design system's `@media` rules. Don't add per-page
  mobile hacks; keep the design-system breakpoints (768px) as the single source.

## 3. Blog / Content pages

- New articles go in `blog/` (e.g. `blog/my-topic.html`), styled EXACTLY like the existing ones:
  `<div class="wrap article-body"><article class="article-body">…</article></div>` +
  `<p class="related-links">…</p>`.
- Full head meta (title, description, canonical, og, robots, JSON-LD Article) — copy the pattern
  from `blog/crypto-fear-greed-index.html`.
- Add the article to `sitemap.xml` and link it from at least one other page (internal linking).
- Never invent live data (prices, Fear & Greed readings, bot P&L). For live numbers, link to the
  tool page that shows them (e.g. `/market-sentinel/`, `/trading-arena/`). Static dates/claims must be true.

## 4. Adding/editing pages

- Prefer reusing the existing topbar/footer markup verbatim.
- JS: no inline event handlers with user data (use `esc()` from `assets/countdown.js` for any
  value inserted into `innerHTML`). Treat every API/LLM-derived string as untrusted.
- If a page needs a new component style, add it to `assets/design-system.css` (and this file's
  allowed-class list), never as a page-local `<style>`.

## 5. Data files — NEVER hand-edit (bot-generated)

| Path | Produced by |
|---|---|
| `data/market_data.json` | `.github/workflows/update_data.yml` (hourly) |
| `stock-pick/data/picks.json` | `.github/workflows/predict.yml` (daily 12:30 UTC, Mon–Fri) |
| `predictions/data/predictions.json` | `predict.yml` + `settle.yml` |
| `trading-arena/data/bots/*` | trade repo `trade_bots.yml` (copied via PAT) |

These are committed by automation. If one looks stale: check the workflow run log first,
fix the workflow, then (if needed) trigger `workflow_dispatch`. Do NOT paste in old copies —
that is exactly how the July picks came back.

## 6. How deploys work (do not "fix" this chain)

- GITHUB_TOKEN pushes do **NOT** trigger other workflows. Therefore every data workflow ends
  with a `workflow_dispatch` call to `deploy.yml` (`actions: write` permission).
- `update_data.yml`, `predict.yml`, `settle.yml`, and the trade repo's `trade_bots.yml` /
  `poly_scan.yml` all dispatch deploy after committing. Keep that pattern.
- Never add `schedule:` triggers that duplicate cron-job.org jobs (double-trigger races).
- Deploy is a `peaceiris/actions-gh-pages` force-push to `gh-pages` — normal and expected.

## 7. Verification (run before pushing)

```bash
npm run test          # canonical data validation — must pass
node --check <any changed .js>   # and extract inline <script> blocks to check them
```

- Check the live page after deploy with a browser. Look at the console for errors.
- If a change is UI-only, still run `npm test` (fast) and verify one desktop + one mobile viewport.

## 8. Commit conventions

- Messages: `fix: …`, `feat: …`, `content: …`, `data: …`, `chore: …` — short, specific.
- `git pull --rebase origin main` before pushing. Resolve conflicts by keeping BOTH changes
  (never discard the data bot's commits).
- One logical change per commit. No "full site update" mega-commits.

## 9. What the site's tools are (for accurate copy)

- **Market Sentinel** — hourly AI-read of stock news, sentiment, fear/greed, macro, politics.
- **Crypto Pulse** — hourly crypto sentiment + prices + trending.
- **Poly Watch** — Polymarket market scanner with AI analysis every 4h.
- **Stock Pick** — daily AI stock picks (Mon–Fri).
- **Trading Arena** — 20 AI trading bots with real paper portfolios, live every 30 min in market hours.
- **Predictions** — daily market-direction predictions per tool, settled automatically.
