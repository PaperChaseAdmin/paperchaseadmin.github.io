# PaperChase.online — SEO Audit 報告
日期：2026-08-19　執行：Iris（用 seo-specialist 方法論）

## 現狀總覽
- 靜態網站（GitHub Pages）+ Supabase backend，50 個 HTML 頁面
- 6 種語言（en/tc/sc/ja/fr/es），client-side i18n（無獨立語言 URL）
- 已有 robots.txt（允許全部 + sitemap 聲明）＋ sitemap.xml（但唔齊）

## 已確認問題（按嚴重度排序）

### 🔴 高影響
1. **Sitemap 嚴重唔齊**：只有 8 條 URL，實際 50 頁。缺 stock-pick、predictions、20 個 bot 頁、20 個 records 頁。冇 lastmod。
2. **全站冇 Open Graph / Twitter Card tags（0/50）**：社交分享冇 preview，Reddit/Twitter 分享時淨係得 URL。
3. **全站冇 JSON-LD 結構化資料（0/50）**：錯過 rich results（WebSite、SoftwareApplication、FAQ、Breadcrumb）。
4. **5 個核心工具頁冇 H1 同靜態內文**：crypto-pulse / poly-watch / stock-pick / trading-arena 連 H1 都冇（用 div）；Google 對 JS-only 內容嘅理解能力弱，靜態文本有助 keyword relevance。
5. **predictions/index.html 冇 robots meta**（連 index/follow 都冇宣告）。

### 🟡 中影響
6. **login / register / account 應該 noindex**：呢 3 個係功能頁，crawl 佢哋只係嘥 crawl budget，而且 register 頁同 login 頁內容近乎空白。
7. **Title tag 優化空間**：首頁 title 冇長尾關鍵字（free AI trading bots）；market-sentinel title 用「Market Intelligence Dashboard」太 generic。
8. **首頁 H1 係「Home」**：完全冇關鍵字，浪費最強嘅 on-page 信號位。

### 🟢 策略性（今次唔做／記錄）
9. **多語言冇 hreflang**：因為冇獨立語言 URL（全靠 ?lang= JS 切換），而家加 hreflang 會有害（Google 唔接受 query-param 為主嘅 hreflang set）。建議未來做 /zh/ /ja/ 等子目錄版本先至加 hreflang。現階段保持 <html lang="en"> + 確保 JS 翻譯唔影響 server HTML。
10. **robots.txt 未對 AI crawlers 表態**：可以明確 allow GPTBot/ClaudeBot/PerplexityBot 等（AI 搜索流量機會）。
11. **og:image 未製作**：需要一張 1200x630 嘅品牌圖做社交 preview。

## 執行改動清單
- [x] 寫 audit 報告（本檔）
- [x] 生成 og:image（assets/og-image.png）
- [x] 全站加 og + twitter card tags（50 頁，script 批量）
- [x] 全站加 JSON-LD（WebSite/WebApplication/FAQ 按頁）
- [x] 優化 7 個核心頁 title + meta description
- [x] 5 個工具頁加 H1 + 靜態描述內容 + 內部連結
- [x] predictions 加 robots meta
- [x] login/register/account 改 noindex
- [x] 更新 sitemap.xml（50 條 URL + lastmod）
- [x] 更新 robots.txt（AI crawlers allow + sitemap）
- [x] 更新 generate_bot_pages.py（下次生成自動含 og/JSON-LD）
- [x] 驗證（grep 檢查全部頁面）

## 預期效果
- 社交平台分享出靚 preview → 增加點擊率同自然 backlink 機會
- 所有頁面入 sitemap → 加快 indexing 覆蓋率由 8/50 → 50/50
- 靜態內容 + 關鍵字 → 提升 topical relevance，長尾關鍵字（AI stock screener、crypto fear greed index、prediction market scanner、AI trading bot）開始有排名機會
- FAQ + JSON-LD → 搶 featured snippet / People Also Ask 位置
