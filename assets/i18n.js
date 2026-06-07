/**
 * PaperChase i18n Loader
 * -----------------------------------------------
 * Detects language from localStorage > browser > default.
 * No URL path prefix detection — URLs stay clean (/trade/).
 *
 * Supported langs: en, tc (繁體中文), sc (简体中文),
 *                  ja (日本語), fr (Français), es (Español)
 *
 * Usage:
 *   <script src="/trade/assets/i18n.js"></script>
 *   <h1 data-i18n="page_title_trade"></h1>
 *   <span data-i18n="kpi_active_bots">Active Bots</span>
 *   <span data-i18n="count_bots" data-i18n-args='{"count":5}'></span>
 *
 *   // In JS:
 *   __('kpi_active_bots')              // => "Active Bots"
 *   __('count_bots', {count: 5})       // => "5 bots" (or translated equivalent)
 *   __('nav_home')                     // => "Home"
 *
 * Locale override via URL param: ?lang=fr
 * localStorage key: 'pap_tfav_lang'
 */
(function () {
  'use strict';

  // ---------------------------------------------------------------------------
  // Configuration
  // ---------------------------------------------------------------------------
  var SUPPORTED_LANGS = ['en', 'tc', 'sc', 'ja', 'fr', 'es'];
  var DEFAULT_LANG    = 'en';
  var STORAGE_KEY     = 'pap_tfav_lang';
  var TRANSLATIONS    = {};   // loaded key-value pairs (flat map)
  var CURRENT_LANG    = DEFAULT_LANG;

  // ---------------------------------------------------------------------------
  // Language detection (priority: URL param > localStorage > browser > default)
  // ---------------------------------------------------------------------------
  function detectLanguage() {
    var lang;

    // 1. URL query parameter ?lang=xx
    var match = window.location.search.match(/[?&]lang=([a-z]+)/i);
    if (match && SUPPORTED_LANGS.indexOf(match[1]) !== -1) {
      return match[1].toLowerCase();
    }

    // 2. localStorage preference
    lang = localStorage.getItem(STORAGE_KEY);
    if (lang && SUPPORTED_LANGS.indexOf(lang) !== -1) {
      return lang;
    }

    // 3. Browser language (navigator.language returns e.g. "en-US", "zh-TW", "zh-CN", "ja", "fr", "es")
    lang = (navigator.language || navigator.userLanguage || '').toLowerCase();
    if (lang.indexOf('zh-tw') !== -1 || lang.indexOf('zh-hk') !== -1) return 'tc';
    if (lang.indexOf('zh-cn') !== -1 || lang.indexOf('zh-sg') !== -1) return 'sc';
    if (lang.indexOf('zh') !== -1) return 'sc';          // generic Chinese → simplified
    if (lang.indexOf('ja') !== -1)  return 'ja';
    if (lang.indexOf('fr') !== -1)  return 'fr';
    if (lang.indexOf('es') !== -1)  return 'es';

    // 4. Fallback
    return DEFAULT_LANG;
  }

  // ---------------------------------------------------------------------------
  // Load translation JSON
  // ---------------------------------------------------------------------------
  function loadTranslations(lang, callback) {
    if (lang === DEFAULT_LANG) {
      // For English, inline a minimal fallback so the site works even if
      // the JSON file fails to load. The full file still loads async.
      var fallbackKeys = {
        site_name: 'PaperChase',
        nav_home: 'Home',
        nav_trading: 'Trading Arena',
        nav_sentinel: 'Market Sentinel',
        nav_polymarket: 'Poly Watch',
        nav_account: 'Account',
        nav_login: 'Log In',
        nav_register: 'Register',
        nav_logout: 'Log Out',
        nav_lang: 'Language',
        nav_all_bots: '← All Bots',
        nav_leaderboard: '← Leaderboard',
        nav_full_records: 'Full Records →',
        lang_en: 'English',
        lang_tc: '繁體中文',
        lang_sc: '简体中文',
        lang_ja: '日本語',
        lang_fr: 'Français',
        lang_es: 'Español',
        page_title_trade: 'Trading Arena',
        page_title_home: 'PaperChase — AI Trading & Market Intelligence',
        page_title_sentinel: 'Market Sentinel',
        page_title_login: 'Log In | PaperChase',
        page_title_register: 'Register | PaperChase',
        page_title_account: 'My Account | PaperChase',
        page_sub_trade: '20 AI bots · $10,000 each · Real market data · Transparent decisions',
        page_sub_sentinel: 'Crowd sentiment dashboard',
        kpi_active_bots: 'Active Bots',
        kpi_combined_aum: 'Combined AUM',
        kpi_avg_return: 'Avg Return',
        kpi_total_trades: 'Total Trades',
        kpi_in_profit: 'In Profit',
        kpi_today_pl: "Today's P&L",
        kpi_all_running: 'all running',
        kpi_total_portfolio: 'total portfolio',
        kpi_vs_start: 'vs start',
        kpi_avg_per_bot: 'avg per bot',
        kpi_win_rate: 'win rate',
        chart_portfolio: 'Portfolio Performance',
        chart_1d: '1D',
        chart_1w: '1W',
        chart_1m: '1M',
        chart_all: 'All',
        dist_risk: 'Risk Distribution',
        dist_top: 'Top Performers',
        section_bot_rankings: 'Bot Rankings',
        count_bots: 'bots',
        today: 'Today',
        next_review: 'Next Review',
        checking_now: 'Checking now...',
        trades: 'trades',
        positions: 'positions',
        loading_bot: 'Loading {name}...',
        detail_current_positions: 'Current Positions',
        detail_recent_trades: 'Recent Trades',
        records_back_to_bot: '← Back to Bot',
        records_title: 'Trade Records',
        records_subtitle: 'Complete history · All times UTC',
        records_filter_all: 'All',
        records_filter_buys: 'Buys',
        records_filter_sells: 'Sells',
        footer: 'PaperChase · Trading Arena · Data refreshes every 30 min during US market hours',
        login_title: 'Welcome Back',
        login_subtitle: 'Sign in to your PaperChase account',
        login_email: 'Email',
        login_password: 'Password',
        login_btn: 'Sign In',
        login_no_account: "Don't have an account?",
        login_register_link: 'Register',
        register_title: 'Create Account',
        register_subtitle: 'Join PaperChase and track your favourite bots',
        register_name: 'Display Name',
        register_email: 'Email',
        register_password: 'Password',
        register_btn: 'Create Account',
        register_have_account: 'Already have an account?',
        register_login_link: 'Sign In',
        account_title: 'My Account',
        account_favourites: 'Favourite Bots',
        account_no_favourites: 'No favourite bots yet. Browse the leaderboard and add some!',
        account_settings: 'Account Settings',
        account_language: 'Preferred Language',
        favourite_add: 'Add to Favourites',
        favourite_remove: 'Remove from Favourites',
        error_loading: 'Something went wrong. Please try again.',
        error_auth: 'Authentication error. Please log in again.',
        login_success: 'Logged in successfully!',
        register_success: 'Account created! Welcome to PaperChase.',
        register_password_hint: 'At least 8 characters',
        page_title_polymarket: 'Poly Watch',
        page_sub_polymarket: 'AI-powered prediction market analysis · High-confidence bet finder',
        filter_all: 'All',
        filter_recommended: '✅ Recommended',
        filter_review: '⚠️ Review',
        filter_politics: 'Politics',
        filter_crypto: 'Crypto',
        filter_finance: 'Finance',
        filter_news: 'News',
        stat_markets: 'Markets',
        stat_recommended: 'Recommended',
        stat_avg_yes: 'Avg Yes%',
        stat_total_volume: 'Total Volume',
        meta_yes: 'Yes',
        meta_ends: 'Ends',
        meta_vol: 'Vol',
        ai_confidence: 'confidence',
        scanning_polymarket: 'Scanning Poly Watch...',
        count_markets: 'markets',
        no_markets_filter: 'No markets found for this filter',
        updated: 'Updated',
        just_now: 'just now',
        min_ago: 'm ago',
        hour_ago: 'h ago',
        refresh: '⟳ Refresh',
        error_could_not_load: 'Could not load',
        error_run_scanner: 'Run python3 polymarket/scanner.py to generate data'
      };

      // Seed with inline fallback, then overlay with fetched JSON
      for (var k in fallbackKeys) {
        if (fallbackKeys.hasOwnProperty(k)) {
          TRANSLATIONS[k] = fallbackKeys[k];
        }
      }
    }

    var url = '/assets/i18n/' + lang + '.json';

    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState !== 4) return;

      if (xhr.status >= 200 && xhr.status < 400) {
        try {
          var parsed = JSON.parse(xhr.responseText);
          var data = parsed[lang];
          if (data && typeof data === 'object') {
            for (var key in data) {
              if (data.hasOwnProperty(key)) {
                TRANSLATIONS[key] = data[key];
              }
            }
          }
        } catch (e) {
          console.warn('[i18n] Failed to parse translation file for "' + lang + '":', e);
        }
      } else {
        console.warn('[i18n] Failed to load translation file "' + url + '" (HTTP ' + xhr.status + '). Using fallback.');
      }

      if (typeof callback === 'function') {
        callback();
      }
    };
    xhr.onerror = function () {
      console.warn('[i18n] Network error loading "' + url + '". Using fallback.');
      if (typeof callback === 'function') {
        callback();
      }
    };
    xhr.send();
  }

  // ---------------------------------------------------------------------------
  // Translation function (exposed globally)
  // ---------------------------------------------------------------------------
  /**
   * Translate a key.
   *
   * @param {string} key          - Dot-notation or flat key (e.g. 'nav_home')
   * @param {Object} [interp]     - Optional interpolation values, e.g. {count: 5}
   * @returns {string}            - Translated string, or the key itself if not found
   *
   * Handles {{variable}} placeholders.
   * If a key returns an object (nested structure), returns the original key.
   */
  window.__ = function (key, interp) {
    if (typeof key !== 'string' || !key) return '';

    var value = TRANSLATIONS.hasOwnProperty(key) ? TRANSLATIONS[key] : null;

    // Fallback: return the key itself so the UI is still readable
    if (value === null || value === undefined) {
      // Try splitting by dots for nested lookups
      var parts = key.split('.');
      var nested = TRANSLATIONS;
      for (var i = 0; i < parts.length; i++) {
        if (nested && typeof nested === 'object' && parts[i] in nested) {
          nested = nested[parts[i]];
        } else {
          nested = null;
          break;
        }
      }
      value = (nested !== null && typeof nested === 'string') ? nested : key;
    }

    // If the translation is an object, return key as fallback
    if (typeof value !== 'string') {
      return key;
    }

    // Interpolation: replace {{key}} with values from interp object
    if (interp && typeof interp === 'object') {
      value = value.replace(/\{\{(\w+)\}\}/g, function (match, prop) {
        return interp.hasOwnProperty(prop) ? interp[prop] : match;
      });
    }

    return value;
  };

  // ---------------------------------------------------------------------------
  // Update <title> via data-i18n-title
  // ---------------------------------------------------------------------------
  function updateTitle() {
    var el = document.querySelector('[data-i18n-title]');
    if (el) {
      var titleKey = el.getAttribute('data-i18n-title');
      if (titleKey) {
        var args = null;
        var argsAttr = el.getAttribute('data-i18n-args');
        if (argsAttr) {
          try { args = JSON.parse(argsAttr); } catch (e) { args = null; }
        }
        document.title = window.__(titleKey, args);
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Update DOM elements with data-i18n attribute
  // ---------------------------------------------------------------------------
  function translateDOM() {
    var elements = document.querySelectorAll('[data-i18n]');

    for (var i = 0; i < elements.length; i++) {
      var el = elements[i];
      var key = el.getAttribute('data-i18n');

      if (!key) continue;

      // Parse optional interpolation args from data-i18n-args
      var args = null;
      var argsAttr = el.getAttribute('data-i18n-args');
      if (argsAttr) {
        try { args = JSON.parse(argsAttr); } catch (e) { args = null; }
      }

      var translation = window.__(key, args);
      if (translation !== null && translation !== undefined) {
        // If the element is an <input>/<textarea>, set placeholder/value
        var tag = el.tagName.toLowerCase();
        if (tag === 'input' || tag === 'textarea') {
          var type = (el.getAttribute('type') || 'text').toLowerCase();
          if (type === 'text' || type === 'email' || type === 'password' || type === 'search' || type === 'submit' || type === 'button') {
            if (type === 'submit' || type === 'button') {
              el.setAttribute('value', translation);
            } else {
              el.setAttribute('placeholder', translation);
            }
          }
        } else {
          el.textContent = translation;
        }
      }
    }

    // Also handle data-i18n-title for <title> tag
    updateTitle();
  }

  // ---------------------------------------------------------------------------
  // Get current language (public accessor)
  // ---------------------------------------------------------------------------
  window.__lang = function () {
    return CURRENT_LANG;
  };

  // ---------------------------------------------------------------------------
  // Get all loaded translations (for debugging / dynamic use)
  // ---------------------------------------------------------------------------
  window.__translations = function () {
    return TRANSLATIONS;
  };

  // ---------------------------------------------------------------------------
  // Initialize
  // ---------------------------------------------------------------------------
  function init() {
    var detectedLang = detectLanguage();

    CURRENT_LANG = detectedLang;

    // Persist to localStorage
    try {
      localStorage.setItem(STORAGE_KEY, detectedLang);
    } catch (e) {
      // localStorage may be unavailable (private browsing, etc.)
    }

    // Load translation file, then translate the DOM
    loadTranslations(detectedLang, function () {
      translateDOM();

      // Dispatch a custom event so other scripts know i18n is ready
      var event;
      try {
        event = new CustomEvent('i18nReady', {
          detail: { lang: CURRENT_LANG }
        });
      } catch (e) {
        event = document.createEvent('Event');
        event.initEvent('i18nReady', true, true);
        event.detail = { lang: CURRENT_LANG };
      }
      document.dispatchEvent(event);
    });
  }

  // ---------------------------------------------------------------------------
  // DOMContentLoaded vs async
  // ---------------------------------------------------------------------------
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // ---------------------------------------------------------------------------
  // Utility: manually retranslate the DOM (useful after dynamic content loads)
  // ---------------------------------------------------------------------------
  window.__retranslate = function () {
    translateDOM();
  };

  // ---------------------------------------------------------------------------
  // Utility: set language and reload
  // ---------------------------------------------------------------------------
  /**
   * Switch to a different language.
   * Saves preference and reloads the page (without changing the URL path).
   *
   * @param {string} lang - One of 'en', 'tc', 'sc', 'ja', 'fr', 'es'
   */
  window.__setLang = function (lang) {
    if (SUPPORTED_LANGS.indexOf(lang) === -1) return;

    // Save preference
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch (e) { /* ignore */ }

    // Reload the page at the same URL — i18n.js will pick up the new language
    // from localStorage on next load
    window.location.reload();
  };

})();
