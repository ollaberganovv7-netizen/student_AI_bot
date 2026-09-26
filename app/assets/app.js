/*
 * Shared Mini App runtime: window.MiniApp.
 *
 * Every page loads telegram-web-app.js, assets/i18n.js, then this file, and
 * keeps only its own form logic. Nothing in here knows about a particular
 * page, so a later full Mini App can reuse it as is. Small modules:
 *
 *   telegram  - the Telegram.WebApp object, version checks, inTelegram
 *   params    - query params, `p` (display price table) and `s` (prefill)
 *   i18n      - language choice and t()
 *   format    - fmtNumber / fmtPrice
 *   pricing   - reads the bot's `p` table (display only; the bot recomputes)
 *   theme     - --tg-theme-* tokens, data-theme, safe-area insets
 *   buttons   - MainButton / BackButton helpers
 *   feedback  - haptics, alerts, closing confirmation
 *   store     - CloudStorage with a localStorage fallback
 *   transport - how a payload leaves the page: sendData (chat keyboard
 *               pages) or, in api mode, POST drafts/<svc>/apply
 *   api       - api mode (the Mini App under /tg/): MiniApp.api (fetch/XHR
 *               with the `tma` header, retries, never throws), nav (page
 *               stack in sessionStorage), setLang, onResume, poll
 *   dom       - el() builder, applyI18n(), radio groups, notices
 *
 * Money note: prices are shown only from `p`. No price is ever sent back;
 * the bot ignores any price a page sends anyway.
 */
(function (window, document) {
  'use strict';

  var I18N = window.MiniAppI18n;
  var PAYLOAD_VERSION = 2;
  var MAX_PAYLOAD_BYTES = 4096;          // Telegram's sendData limit
  var STORE_PREFIX = 'sab_';             // CloudStorage keys: [A-Za-z0-9_-]{1,128}
  var CLOUD_TIMEOUT_MS = 1500;

  // ── telegram ──────────────────────────────────────────────────────────────

  var tg = (window.Telegram && window.Telegram.WebApp) || null;

  function atLeast(version) {
    try {
      return !!tg && typeof tg.isVersionAtLeast === 'function' && tg.isVersionAtLeast(version);
    } catch (e) {
      return false;
    }
  }

  // Outside Telegram the script still defines WebApp, with platform 'unknown'
  // and empty initData. Keyboard-button apps may have empty initData, so the
  // platform decides too.
  var inTelegram = !!tg && (
    (typeof tg.initData === 'string' && tg.initData !== '') ||
    (typeof tg.platform === 'string' && tg.platform !== '' && tg.platform !== 'unknown'));

  function safeCall(fn) {
    try {
      return fn();
    } catch (e) {
      if (window.console) console.warn('MiniApp:', e);
      return undefined;
    }
  }

  // ── params ────────────────────────────────────────────────────────────────

  function readParams(search) {
    var out = {};
    try {
      new URLSearchParams(search || '').forEach(function (value, key) { out[key] = value; });
    } catch (e) { /* no params */ }
    return out;
  }

  /** base64url (no padding) -> UTF-8 JSON value; null when anything is off. */
  function decodeParam(value) {
    if (typeof value !== 'string' || !value) return null;
    try {
      var b64 = value.replace(/-/g, '+').replace(/_/g, '/');
      while (b64.length % 4) b64 += '=';
      var binary = window.atob(b64);
      var bytes = new Uint8Array(binary.length);
      for (var i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      return JSON.parse(new TextDecoder('utf-8').decode(bytes));
    } catch (e) {
      return null;
    }
  }

  function isObject(v) {
    return !!v && typeof v === 'object' && !Array.isArray(v);
  }

  var params = readParams(window.location.search);
  var prices = decodeParam(params.p);
  if (!isObject(prices)) prices = null;
  var prefill = decodeParam(params.s);
  if (!isObject(prefill)) prefill = {};

  /**
   * Page-level settings from <meta name="miniapp:NAME" content="...">, so this
   * file names no particular bot and a later Mini App can reuse it unchanged.
   */
  function pageConfig(name) {
    var node = document.querySelector('meta[name="miniapp:' + name + '"]');
    var value = node && node.getAttribute('content');
    return value ? value.trim() : '';
  }

  // The bot the "open from the bot" notice names; empty = a generic wording.
  var BOT_USERNAME = pageConfig('bot');

  // Api mode: the page belongs to the full Mini App and talks to the bot's
  // HTTPS API. New pages say so in <meta name="miniapp:mode" content="api">;
  // the chat's settings / catalog pages are put in it by their link
  // (via=app), so the same files serve both. Strings then prefer their
  // "api" wording (MiniAppI18n variants).
  // The same settings/catalog files are also published on GitHub Pages for
  // the chat, where a crafted via=app link must never make them send the
  // user's initData anywhere: the query only counts off github.io.
  var apiMode = pageConfig('mode') === 'api' ||
    (params.via === 'app' && !/(^|\.)github\.io$/i.test(location.hostname));
  if (apiMode && typeof I18N.setVariant === 'function') I18N.setVariant('api');

  function telegramUser() {
    return (tg && tg.initDataUnsafe && isObject(tg.initDataUnsafe.user)) ? tg.initDataUnsafe.user : null;
  }

  // ── i18n ──────────────────────────────────────────────────────────────────

  var lang = I18N.normalize(params.lang) ||
    I18N.normalize(telegramUser() && telegramUser().language_code) ||
    I18N.DEFAULT_LANG;
  document.documentElement.setAttribute('lang', lang);

  function t(key, vars) {
    return I18N.translate(lang, key, vars);
  }

  // ── format ────────────────────────────────────────────────────────────────

  function fmtNumber(n) {
    var value = Math.round(Number(n) || 0);
    var sign = value < 0 ? '-' : '';
    // Digits in groups of three with a no-break space, as the bot writes them.
    return sign + String(Math.abs(value)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  }

  function fmtPrice(n) {
    return fmtNumber(n) + ' ' + t('cur');
  }

  // ── pricing (display only) ──────────────────────────────────────────────────

  function toInt(v, fallback) {
    var n = parseInt(v, 10);
    return isFinite(n) ? n : fallback;
  }

  function clamp(n, lo, hi) {
    return Math.max(lo, Math.min(hi, n));
  }

  function qualityKey(quality) {
    return quality === 'premium' || quality === 'pro' ? 'premium' : 'standard';
  }

  /** [{max, price}] for a quality, or null when `p` has no usable tiers. */
  function tiers(table, quality) {
    if (!isObject(table) || !isObject(table.tiers)) return null;
    var list = table.tiers[qualityKey(quality)] || table.tiers.standard;
    if (!Array.isArray(list) || !list.length) return null;
    var out = [];
    for (var i = 0; i < list.length; i++) {
      var row = list[i];
      if (!Array.isArray(row) || row.length < 2) return null;
      var max = toInt(row[0], NaN);
      var price = toInt(row[1], NaN);
      if (!isFinite(max) || !isFinite(price) || price < 0) return null;
      out.push({ max: max, price: price });
    }
    return out;
  }

  /** The tier that applies to size n (the last one above every bound). */
  function tierFor(table, quality, n) {
    var list = tiers(table, quality);
    if (!list) return null;
    for (var i = 0; i < list.length; i++) {
      if (n <= list[i].max) return list[i];
    }
    return list[list.length - 1];
  }

  /**
   * Paid pictures an order of size n can hold: img.max, and for decks also
   * n - rsv - free (slides that never carry a picture, and the free ones).
   */
  function maxPaidImages(table, n) {
    if (!isObject(table) || !isObject(table.img)) return 0;
    var img = table.img;
    var max = Math.max(0, toInt(img.max, 0));
    if (img.rsv != null) {
      max = Math.min(max, toInt(n, 0) - toInt(img.rsv, 0) - Math.max(0, toInt(img.free, 0)));
    }
    return Math.max(0, max);
  }

  /**
   * Price of one ordered unit (slide or page) for a quality, from
   * `p.per = {standard, premium}`; null when the table prices by tiers
   * instead (kurs/diplom) or has no usable number.
   */
  function unitPrice(table, quality) {
    if (!isObject(table) || !isObject(table.per)) return null;
    var v = toInt(table.per[qualityKey(quality)], NaN);
    if (!isFinite(v)) v = toInt(table.per.standard, NaN);
    return isFinite(v) && v >= 0 ? v : null;
  }

  /**
   * What the order would cost, from `p` alone:
   * {base, tierMax, paid, unit, images, total, payable, trial, perUnit, n}
   * or null. The base is n x per-unit price when `p.per` is given, else the
   * matching tier. `payable` is what the student pays: the free trial covers
   * the base only, pictures are always paid.
   */
  function quote(table, opts) {
    var per = unitPrice(table, opts.quality);
    var n = Math.max(0, toInt(opts.n, 0));
    var tier = per != null ? { max: n, price: per * n } : tierFor(table, opts.quality, opts.n);
    if (!tier) return null;
    var unit = Math.max(0, toInt(table.img && table.img.unit, 0));
    var paid = clamp(toInt(opts.extra, 0), 0, maxPaidImages(table, opts.n));
    var images = paid * unit;
    var trial = table.trial === true;
    return {
      base: tier.price,
      tierMax: tier.max,
      paid: paid,
      unit: unit,
      images: images,
      total: tier.price + images,
      payable: trial ? images : tier.price + images,
      trial: trial,
      perUnit: per,
      n: n
    };
  }

  // ── theme ─────────────────────────────────────────────────────────────────

  var THEME_KEYS = ['bg_color', 'text_color', 'hint_color', 'link_color', 'button_color',
    'button_text_color', 'secondary_bg_color', 'header_bg_color', 'bottom_bar_bg_color',
    'accent_text_color', 'section_bg_color', 'section_header_text_color',
    'section_separator_color', 'subtitle_text_color', 'destructive_text_color'];

  function colorScheme() {
    if (tg && (tg.colorScheme === 'dark' || tg.colorScheme === 'light')) return tg.colorScheme;
    try {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    } catch (e) {
      return 'light';
    }
  }

  // Secondary text colours whose Telegram values are often too faint on
  // Telegram's own backgrounds (iOS light: hint #8e8e93 on #efeff4 is 2.8:1),
  // and the app.css token each one feeds. --link-text is the link colour
  // used as text (in-page buttons of the Mini App; iOS #007aff on white is
  // 4.0:1); --link itself stays as Telegram sends it.
  var READABLE_TOKENS = { hint_color: '--hint', section_header_text_color: '--section-title',
    destructive_text_color: '--destructive', link_color: '--link-text' };
  var MIN_CONTRAST = 4.5;

  function hexToRgb(value) {
    if (typeof value !== 'string' || !/^#([0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})$/i.test(value)) {
      return null;
    }
    var h = value.slice(1);
    if (h.length < 6) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    return [0, 2, 4].map(function (i) { return parseInt(h.slice(i, i + 2), 16); });
  }

  function luminance(rgb) {
    var c = rgb.map(function (v) {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  }

  function contrast(a, b) {
    var x = luminance(a);
    var y = luminance(b);
    return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
  }

  /**
   * The colour to use for `value` so it reads at 4.5:1 on every ground: the
   * theme's own colour when it already does, else the same hue moved towards
   * `toward` (the text colour) just far enough. null = keep the theme's colour.
   */
  function readable(value, grounds, toward) {
    var rgb = hexToRgb(value);
    if (!rgb || !grounds.length || !toward) return null;
    for (var step = 0; step <= 20; step++) {
      var mixed = rgb.map(function (v, i) { return Math.round(v + (toward[i] - v) * step / 20); });
      var ok = grounds.every(function (g) { return contrast(mixed, g) >= MIN_CONTRAST; });
      if (ok) return step === 0 ? null : 'rgb(' + mixed.join(', ') + ')';
    }
    return null;
  }

  function applyTheme() {
    var root = document.documentElement;
    var theme = (tg && isObject(tg.themeParams)) ? tg.themeParams : {};
    THEME_KEYS.forEach(function (key) {
      var name = '--tg-theme-' + key.replace(/_/g, '-');
      var value = theme[key];
      if (typeof value === 'string' && /^#[0-9a-f]{3,8}$/i.test(value)) {
        root.style.setProperty(name, value);
      } else {
        // Unset, so the light/dark fallbacks in app.css apply.
        root.style.removeProperty(name);
      }
    });
    // Text sits on the page (secondary_bg), on list groups (section_bg) and
    // on bg where a client sends no section colour. The CSS fallbacks
    // already reach 4.5:1, so only Telegram's colours are adjusted.
    var grounds = [theme.bg_color, theme.secondary_bg_color, theme.section_bg_color].map(hexToRgb).filter(Boolean);
    var toward = hexToRgb(theme.text_color);
    Object.keys(READABLE_TOKENS).forEach(function (key) {
      var fixed = readable(theme[key], grounds, toward);
      if (fixed) root.style.setProperty(READABLE_TOKENS[key], fixed);
      else root.style.removeProperty(READABLE_TOKENS[key]);
    });
    root.setAttribute('data-theme', colorScheme());
  }

  function applyInsets() {
    var root = document.documentElement;
    function set(prefix, inset) {
      if (!isObject(inset)) return;
      ['top', 'right', 'bottom', 'left'].forEach(function (side) {
        var v = Number(inset[side]);
        if (isFinite(v)) root.style.setProperty(prefix + side, v + 'px');
      });
    }
    if (tg && atLeast('8.0')) {
      set('--sa-', tg.safeAreaInset);
      set('--csa-', tg.contentSafeAreaInset);
    }
  }

  function onEvent(name, handler) {
    if (tg && typeof tg.onEvent === 'function') safeCall(function () { tg.onEvent(name, handler); });
  }

  // ── feedback ──────────────────────────────────────────────────────────────

  function haptic(kind) {
    if (!tg || !atLeast('6.1') || !tg.HapticFeedback) return;
    safeCall(function () {
      var hf = tg.HapticFeedback;
      if (kind === 'select') hf.selectionChanged();
      else if (kind === 'light') hf.impactOccurred('light');
      else if (kind === 'success' || kind === 'error' || kind === 'warning') hf.notificationOccurred(kind);
    });
  }

  function showAlert(message) {
    if (tg && atLeast('6.2') && typeof tg.showAlert === 'function') {
      safeCall(function () { tg.showAlert(message); });
    } else {
      window.alert(message);
    }
  }

  var dirty = false;

  /** Ask before closing while the form holds unsent changes (6.2+). */
  function setDirty(value) {
    value = !!value;
    if (value === dirty) return;
    dirty = value;
    if (!tg || !atLeast('6.2')) return;
    safeCall(function () {
      if (dirty) tg.enableClosingConfirmation();
      else tg.disableClosingConfirmation();
    });
  }

  // ── buttons ───────────────────────────────────────────────────────────────

  var mainHandler = null;
  var backHandler = null;

  /**
   * Shows the MainButton with `text` calling `onClick`; text null hides it.
   * opts.enabled (default true). Returns nothing; call again to change it.
   */
  function mainButton(text, onClick, opts) {
    if (!tg || !tg.MainButton) return;
    var mb = tg.MainButton;
    safeCall(function () {
      if (mainHandler) mb.offClick(mainHandler);
      mainHandler = null;
      if (text == null) {
        mb.hide();
        return;
      }
      mb.setText(String(text).slice(0, 64));
      if (typeof onClick === 'function') {
        mainHandler = function () { onClick(); };
        mb.onClick(mainHandler);
      }
      if (opts && opts.enabled === false) mb.disable();
      else mb.enable();
      mb.show();
    });
  }

  function mainButtonProgress(on) {
    if (!tg || !tg.MainButton) return;
    safeCall(function () {
      if (on) tg.MainButton.showProgress(false);
      else tg.MainButton.hideProgress();
    });
  }

  /**
   * BackButton for sub-views: a handler shows it, null hides it (6.1+).
   * In api mode null shows the default Back instead (nav.back(), asking
   * first when the form holds unsent changes), except on the home page;
   * false always hides it.
   */
  function backButton(onClick) {
    if (!tg || !tg.BackButton || !atLeast('6.1')) return;
    if (typeof onClick !== 'function' && onClick !== false && apiMode && !isHomePage()) {
      onClick = defaultBack;
    }
    var bb = tg.BackButton;
    safeCall(function () {
      if (backHandler) bb.offClick(backHandler);
      backHandler = null;
      if (typeof onClick !== 'function') {
        bb.hide();
        return;
      }
      backHandler = function () { onClick(); };
      bb.onClick(backHandler);
      bb.show();
    });
  }

  // ── store ─────────────────────────────────────────────────────────────────

  function localGet(key) {
    try {
      return window.localStorage.getItem(STORE_PREFIX + key);
    } catch (e) {
      return null;
    }
  }

  function localSet(key, value) {
    try {
      window.localStorage.setItem(STORE_PREFIX + key, value);
    } catch (e) { /* private mode, quota */ }
  }

  function cloud() {
    return (tg && atLeast('6.9') && tg.CloudStorage) ? tg.CloudStorage : null;
  }

  /**
   * Small per-user values (strings). Telegram CloudStorage follows the user
   * across devices; localStorage is the fallback. get() never rejects.
   */
  var store = {
    get: function (key) {
      var cs = cloud();
      if (!cs) return Promise.resolve(localGet(key));
      return new Promise(function (resolve) {
        var done = false;
        function finish(value) {
          if (done) return;
          done = true;
          resolve(value);
        }
        // Some clients never call back; the local copy answers instead.
        var timer = setTimeout(function () { finish(localGet(key)); }, CLOUD_TIMEOUT_MS);
        try {
          cs.getItem(STORE_PREFIX + key, function (err, value) {
            clearTimeout(timer);
            finish(!err && typeof value === 'string' && value !== '' ? value : localGet(key));
          });
        } catch (e) {
          clearTimeout(timer);
          finish(localGet(key));
        }
      });
    },
    set: function (key, value) {
      value = String(value);
      localSet(key, value);
      var cs = cloud();
      if (!cs) return Promise.resolve();
      return new Promise(function (resolve) {
        try {
          cs.setItem(STORE_PREFIX + key, value, function () { resolve(); });
        } catch (e) {
          resolve();
        }
        setTimeout(resolve, CLOUD_TIMEOUT_MS);
      });
    }
  };

  // ── transport ─────────────────────────────────────────────────────────────

  function byteLength(text) {
    return new TextEncoder().encode(text).length;
  }

  /**
   * The chat transport: Telegram.WebApp.sendData, which delivers the JSON to
   * the bot as a web_app_data message and closes the page. A transport's
   * send(obj) returns {ok, reason?} (or a promise of it).
   */
  var sendDataTransport = {
    name: 'sendData',
    send: function (obj) {
      var json = JSON.stringify(obj);
      if (byteLength(json) > MAX_PAYLOAD_BYTES) {
        haptic('error');
        showAlert(t('too_long'));
        return { ok: false, reason: 'too_long' };
      }
      if (!tg || typeof tg.sendData !== 'function') {
        showAlert(t('send_failed'));
        return { ok: false, reason: 'unavailable' };
      }
      mainButtonProgress(true);
      // Off before sendData, which closes the page: a confirmation prompt would
      // stop that close. Restored below if the send is refused.
      var wasDirty = dirty;
      setDirty(false);
      haptic('success');
      try {
        tg.sendData(json);
      } catch (e) {
        // Not opened from a keyboard button (sendData is refused there). The
        // edits are still unsent, so closing must ask again.
        setDirty(wasDirty);
        mainButtonProgress(false);
        showAlert(t('send_failed'));
        return { ok: false, reason: 'refused' };
      }
      return { ok: true };
    }
  };

  var transport = sendDataTransport;

  function setTransport(next) {
    if (next && typeof next.send === 'function') transport = next;
  }

  /** Sends a page payload through the current transport; resolves {ok, reason?}. */
  function sendPayload(obj) {
    return Promise.resolve()
      .then(function () { return transport.send(obj); })
      .then(function (result) { return result || { ok: false, reason: 'unknown' }; },
        function () {
          mainButtonProgress(false);
          showAlert(t('send_failed'));
          return { ok: false, reason: 'error' };
        });
  }

  // ── api mode ──────────────────────────────────────────────────────────────
  //
  // Everything the Mini App pages under /tg/ share: the API client, page
  // navigation, the language switch, refresh-on-return and polling. The
  // chat's sendData pages never use these unless their link put them in api
  // mode, and then only through the transport.

  var initData = (tg && typeof tg.initData === 'string') ? tg.initData : '';
  var startParam = (function () {
    var value = tg && tg.initDataUnsafe && tg.initDataUnsafe.start_param;
    return typeof value === 'string' && /^[A-Za-z0-9_-]{1,64}$/.test(value) ? value : null;
  })();
  // Tells launches apart: the hash of the signed initData (each launch has
  // its own auth_date), else the raw string; '' without initData. The pages of
  // one launch share it, as Telegram keeps the launch data across them.
  var launchId = (function () {
    var m = /(?:^|&)hash=([^&]+)/.exec(initData);
    return m ? m[1] : initData;
  })();

  // Relative to the page, so /tg/<page>.html talks to /tg/api/v1/ and
  // initData only ever goes to this origin.
  var API_BASE = 'api/v1/';
  var SECOND = 1000;
  var API_TIMEOUT_MS = 15 * SECOND;
  // A write that carries an Idempotency-Key (POST /orders waits up to 20 s
  // for the job to start) must outlive the server's wait, or the retry only
  // replays 'starting' instead of the real outcome.
  var KEYED_WRITE_TIMEOUT_MS = 30 * SECOND;
  var UPLOAD_TIMEOUT_MS = 120 * SECOND;
  var READ_RETRIES = 2;
  var WRITE_RETRIES = 2;                 // only with an Idempotency-Key
  var RETRY_DELAYS_MS = [400, 1200];
  var KEY_PATTERN = /^[A-Za-z0-9_-]{8,64}$/;

  function wait(ms) {
    return new Promise(function (resolve) { setTimeout(resolve, ms); });
  }

  /** 'me' / '/drafts/x' -> 'api/v1/…'; null for anything that is not a plain API path. */
  function apiUrl(path) {
    var raw = String(path == null ? '' : path);
    var rel = raw.replace(/^\//, '');
    // Percent-encoded dots and slashes are dot segments to the URL parser
    // ('%2e%2e' == '..'): refused like the plain ones, so the tma header never
    // leaves api/v1/.
    if (!rel || rel.charAt(0) === '/' || /^[a-z][a-z0-9+.-]*:/i.test(rel) || rel.indexOf('..') >= 0 ||
        rel.indexOf('\\') >= 0 || rel.indexOf('#') >= 0 || /%(2e|2f|5c)/i.test(rel)) {
      return null;
    }
    return API_BASE + rel;
  }

  function apiResult(ok, status, data, code, retryAfter) {
    return {
      ok: !!ok,
      status: status,
      data: data === undefined ? null : data,
      code: code || null,
      retryAfter: retryAfter == null ? null : retryAfter
    };
  }

  /** The error body's code ({"error": {"code": …}}), else one from the status. */
  function errorCode(status, data) {
    if (isObject(data) && isObject(data.error) && typeof data.error.code === 'string' && data.error.code) {
      return data.error.code;
    }
    if (status === 401) return 'auth_invalid';
    if (status === 404) return 'not_found';
    if (status === 413) return 'too_large';
    if (status === 429) return 'rate_limited';
    if (status === 500) return 'internal';
    if (status > 500) return 'unavailable';
    return 'unknown';
  }

  function retryAfterOf(header, data) {
    var n = parseInt(header, 10);
    if (isFinite(n) && n >= 0) return n;
    if (isObject(data) && isObject(data.error)) {
      n = parseInt(data.error.retry_after, 10);
      if (isFinite(n) && n >= 0) return n;
    }
    return null;
  }

  function parseBody(text) {
    if (!text) return null;
    try {
      return JSON.parse(text);
    } catch (e) {
      return null;
    }
  }

  var authHandlers = [];

  /** fn(code) runs on every 401 instead of the default "open it again" notice. */
  function onAuthFailure(fn) {
    if (typeof fn === 'function') authHandlers.push(fn);
  }

  function authFailed(code) {
    if (authHandlers.length) {
      authHandlers.forEach(function (fn) { safeCall(function () { fn(code); }); });
      return;
    }
    showNotice(t('auth_title'), t('auth_text'));
  }

  function settle(res) {
    if (res.status === 401) authFailed(res.code);
    return res;
  }

  /** One fetch; resolves an apiResult, never rejects. */
  function attempt(method, url, headers, body, timeoutMs) {
    return new Promise(function (resolve) {
      var done = false;
      var controller = typeof AbortController === 'function' ? new AbortController() : null;
      function end(res) {
        if (done) return;
        done = true;
        clearTimeout(timer);
        resolve(res);
      }
      var timer = setTimeout(function () {
        end(apiResult(false, 0, null, 'timeout'));
        if (controller) safeCall(function () { controller.abort(); });
      }, timeoutMs);
      var init = { method: method, headers: headers, credentials: 'omit', cache: 'no-store',
        redirect: 'error' };
      if (body !== undefined) init.body = body;
      if (controller) init.signal = controller.signal;
      var pending;
      try {
        pending = window.fetch(url, init);
      } catch (e) {
        pending = Promise.reject(e);
      }
      pending.then(function (response) {
        return response.text().then(function (text) {
          var data = parseBody(text);
          var ok = response.status >= 200 && response.status < 300;
          end(apiResult(ok, response.status, data, ok ? null : errorCode(response.status, data),
            retryAfterOf(response.headers.get('Retry-After'), data)));
        });
      }).catch(function () {
        end(apiResult(false, 0, null, 'offline'));
      });
    });
  }

  function retryable(res, reading) {
    if (res.code === 'offline' || res.code === 'timeout') return true;
    return reading && (res.status === 502 || res.status === 503 || res.status === 504);
  }

  function retryDelay(n, res) {
    var ms = RETRY_DELAYS_MS[Math.min(n, RETRY_DELAYS_MS.length - 1)];
    if (res.retryAfter != null && res.retryAfter <= 3) ms = Math.max(ms, res.retryAfter * SECOND);
    return ms;
  }

  /**
   * MiniApp.api.request(method, path, {json, form, idempotencyKey, timeoutMs})
   * -> Promise<{ok, status, data, code, retryAfter}>. Never rejects: a
   * network problem gives status 0 and code 'offline' or 'timeout'. Reads
   * retry twice with backoff; writes retry (network problems only) when they
   * carry an Idempotency-Key, which then stays the same (their default
   * timeout is 30 s, reads and plain writes 15 s). A 401 runs the
   * onAuthFailure handlers (default: the "open it again" notice).
   */
  function request(method, path, opts) {
    opts = opts || {};
    method = String(method || 'GET').toUpperCase();
    var url = apiUrl(path);
    if (!url) return Promise.resolve(apiResult(false, 0, null, 'bad_request'));
    if (!initData) return Promise.resolve(settle(apiResult(false, 401, null, 'auth_missing')));
    var headers = { 'Authorization': 'tma ' + initData, 'Accept': 'application/json' };
    var body;
    if (opts.json !== undefined) {
      headers['Content-Type'] = 'application/json';
      body = JSON.stringify(opts.json);
    } else if (opts.form) {
      body = opts.form;
    }
    var key = opts.idempotencyKey;
    if (key != null) {
      if (!KEY_PATTERN.test(String(key))) {
        return Promise.resolve(apiResult(false, 0, null, 'missing_idempotency_key'));
      }
      headers['Idempotency-Key'] = String(key);
    }
    var reading = method === 'GET' || method === 'HEAD';
    var retries = reading ? READ_RETRIES : (key != null ? WRITE_RETRIES : 0);
    var timeoutMs = opts.timeoutMs > 0 ? opts.timeoutMs :
      (!reading && key != null ? KEYED_WRITE_TIMEOUT_MS : API_TIMEOUT_MS);
    function run(n) {
      return attempt(method, url, headers, body, timeoutMs).then(function (res) {
        if (n < retries && retryable(res, reading)) {
          return wait(retryDelay(n, res)).then(function () { return run(n + 1); });
        }
        return settle(res);
      });
    }
    return run(0);
  }

  /**
   * A multipart upload through XHR (for progress): upload(path, formData,
   * {idempotencyKey, onProgress(fraction), timeoutMs}). The browser sends
   * Content-Length itself. Not retried automatically: retry with the same key.
   */
  function upload(path, formData, opts) {
    opts = opts || {};
    var url = apiUrl(path);
    if (!url) return Promise.resolve(apiResult(false, 0, null, 'bad_request'));
    if (!initData) return Promise.resolve(settle(apiResult(false, 401, null, 'auth_missing')));
    var key = opts.idempotencyKey;
    if (key != null && !KEY_PATTERN.test(String(key))) {
      return Promise.resolve(apiResult(false, 0, null, 'missing_idempotency_key'));
    }
    return new Promise(function (resolve) {
      var xhr = new XMLHttpRequest();
      var done = false;
      function end(res) {
        if (done) return;
        done = true;
        resolve(settle(res));
      }
      try {
        xhr.open('POST', url, true);
        xhr.timeout = opts.timeoutMs > 0 ? opts.timeoutMs : UPLOAD_TIMEOUT_MS;
        xhr.withCredentials = false;
        xhr.setRequestHeader('Authorization', 'tma ' + initData);
        xhr.setRequestHeader('Accept', 'application/json');
        if (key != null) xhr.setRequestHeader('Idempotency-Key', String(key));
        if (typeof opts.onProgress === 'function' && xhr.upload) {
          xhr.upload.onprogress = function (event) {
            if (event.lengthComputable && event.total > 0) {
              safeCall(function () { opts.onProgress(event.loaded / event.total); });
            }
          };
        }
        xhr.onload = function () {
          var data = parseBody(xhr.responseText);
          var ok = xhr.status >= 200 && xhr.status < 300;
          end(apiResult(ok, xhr.status, data, ok ? null : errorCode(xhr.status, data),
            retryAfterOf(xhr.getResponseHeader('Retry-After'), data)));
        };
        xhr.onerror = function () { end(apiResult(false, 0, null, 'offline')); };
        xhr.onabort = function () { end(apiResult(false, 0, null, 'offline')); };
        xhr.ontimeout = function () { end(apiResult(false, 0, null, 'timeout')); };
        xhr.send(formData);
      } catch (e) {
        end(apiResult(false, 0, null, 'offline'));
      }
    });
  }

  /** A fresh Idempotency-Key: 32 hex characters. */
  function newKey() {
    var bytes = new Uint8Array(16);
    try {
      window.crypto.getRandomValues(bytes);
    } catch (e) {
      for (var i = 0; i < bytes.length; i++) bytes[i] = Math.floor(Math.random() * 256);
    }
    return Array.prototype.map.call(bytes, function (b) {
      return (b < 16 ? '0' : '') + b.toString(16);
    }).join('');
  }

  function withBody(method) {
    return function (path, json, opts) {
      var o = {};
      Object.keys(opts || {}).forEach(function (k) { o[k] = opts[k]; });
      if (json !== undefined) o.json = json;
      return request(method, path, o);
    };
  }

  var api = {
    base: API_BASE,
    request: request,
    get: function (path, opts) { return request('GET', path, opts); },
    post: withBody('POST'),
    put: withBody('PUT'),
    del: function (path, opts) { return request('DELETE', path, opts); },
    upload: upload,
    newKey: newKey
  };

  /** The user-facing text for an API error code (err.<code>, else a generic one). */
  function errorText(code) {
    var key = 'err.' + (code || 'unknown');
    return I18N.has && I18N.has(lang, key) ? t(key) : t('err.unknown');
  }

  // ── navigation (api mode) ─────────────────────────────────────────────────
  //
  // Pages are separate documents in one folder. The way back is a stack of
  // relative URLs in sessionStorage (it survives the page loads; Telegram's
  // script keeps initData there too). Every move replaces the document, so
  // the web view's own history never grows; Back is Telegram's BackButton.

  var HOME_PAGE = 'index.html';
  var NAV_KEY = STORE_PREFIX + 'nav';
  var NAV_MAX = 20;
  var PAGE_RE = /^[A-Za-z0-9_-]+\.html$/;
  var REL_RE = /^[A-Za-z0-9_-]+\.html(\?[^#]*)?$/;

  function isRel(rel) {
    return typeof rel === 'string' && REL_RE.test(rel);
  }

  function pageOf(rel) {
    return rel.split('?')[0];
  }

  function currentRel() {
    var path = window.location.pathname;
    var name = path.slice(path.lastIndexOf('/') + 1) || HOME_PAGE;
    return name + window.location.search;
  }

  function isHomePage() {
    return pageOf(currentRel()) === HOME_PAGE;
  }

  function readStack() {
    try {
      var list = JSON.parse(window.sessionStorage.getItem(NAV_KEY) || '[]');
      return Array.isArray(list) ? list.filter(isRel) : [];
    } catch (e) {
      return [];
    }
  }

  function writeStack(list) {
    try {
      window.sessionStorage.setItem(NAV_KEY, JSON.stringify(list.slice(-NAV_MAX)));
    } catch (e) { /* private mode */ }
  }

  /** rel with lang=<current language> in its query. */
  function withLang(rel) {
    var at = rel.indexOf('?');
    var query = readParams(at >= 0 ? rel.slice(at + 1) : '');
    query.lang = lang;
    var parts = Object.keys(query).map(function (k) {
      return encodeURIComponent(k) + '=' + encodeURIComponent(query[k]);
    });
    return pageOf(rel) + '?' + parts.join('&');
  }

  function navigate(rel) {
    // Leaving the page drops its closing confirmation: the next page starts clean.
    dirty = false;
    if (tg && atLeast('6.2')) safeCall(function () { tg.disableClosingConfirmation(); });
    window.location.replace(withLang(rel));
  }

  /**
   * Opens a relative page URL ("order.html?svc=presentation", as the API
   * hands them out). Going to a page already on the stack returns to it
   * (the stack is cut there), so order -> settings -> Save -> order does not
   * loop. opts.replace: the current page is not kept for Back.
   */
  function goUrl(rel, opts) {
    if (!isRel(rel)) return false;
    var stack = readStack();
    var target = pageOf(rel);
    for (var i = stack.length - 1; i >= 0; i--) {
      if (pageOf(stack[i]) === target) {
        writeStack(stack.slice(0, i));
        navigate(rel);
        return true;
      }
    }
    var here = currentRel();
    if (!(opts && opts.replace) && pageOf(here) !== target) stack.push(here);
    writeStack(stack);
    navigate(rel);
    return true;
  }

  /** go('order.html', {svc: 'referat'}): goUrl with the params as a query. */
  function go(page, query, opts) {
    if (typeof page !== 'string' || !PAGE_RE.test(page)) return false;
    var parts = [];
    Object.keys(query || {}).forEach(function (k) {
      var v = query[k];
      if (v != null && v !== false && k !== 'lang') {
        parts.push(encodeURIComponent(k) + '=' + encodeURIComponent(String(v)));
      }
    });
    return goUrl(page + (parts.length ? '?' + parts.join('&') : ''), opts);
  }

  /** The previous page on the stack, else home. */
  function back() {
    var stack = readStack();
    var previous = stack.pop();
    writeStack(stack);
    navigate(previous || HOME_PAGE);
  }

  function home() {
    writeStack([]);
    navigate(HOME_PAGE);
  }

  /** Empties the Back stack without leaving the page (a new launch). */
  function reset() {
    writeStack([]);
  }

  function defaultBack() {
    if (!dirty) {
      back();
      return;
    }
    confirmDialog(t('leave_confirm')).then(function (yes) {
      if (yes) back();
    });
  }

  var nav = {
    HOME: HOME_PAGE,
    go: go,
    goUrl: goUrl,
    back: back,
    home: home,
    reset: reset,
    stack: readStack,
    current: currentRel,
    isHome: isHomePage
  };

  /** A yes/no question: Telegram's popup (6.2+), else the browser's. Promise<bool>. */
  function confirmDialog(message) {
    return new Promise(function (resolve) {
      if (tg && atLeast('6.2') && typeof tg.showConfirm === 'function') {
        try {
          tg.showConfirm(String(message), function (ok) { resolve(!!ok); });
          return;
        } catch (e) { /* fall through */ }
      }
      var answer = false;
      try {
        answer = window.confirm(String(message));
      } catch (e) { /* no dialogs */ }
      resolve(!!answer);
    });
  }

  // ── language, resume, polling (api mode) ─────────────────────────────────

  /**
   * Switches the language of the page: t(), <html lang>, [data-i18n] nodes,
   * then a 'langchange' event (bubbling from document, detail {lang}) so the
   * page re-renders. Returns false for an unsupported code.
   */
  function setLang(code) {
    var next = I18N.normalize(code);
    if (!next) return false;
    var changed = next !== lang;
    lang = next;
    if (M) M.lang = next;
    document.documentElement.setAttribute('lang', next);
    if (changed) {
      applyI18n();
      var event;
      try {
        event = new CustomEvent('langchange', { bubbles: true, detail: { lang: next } });
      } catch (e) {
        event = document.createEvent('CustomEvent');
        event.initCustomEvent('langchange', true, false, { lang: next });
      }
      document.dispatchEvent(event);
    }
    return true;
  }

  /**
   * fn() when the user comes back to the page: a page shown from the
   * back/forward cache, the tab becoming visible again, or Telegram's
   * 'activated' event (8.0+). Calls closer than half a second apart merge.
   */
  function onResume(fn) {
    if (typeof fn !== 'function') return;
    var last = 0;
    function run() {
      var now = Date.now();
      if (now - last < 500) return;
      last = now;
      safeCall(fn);
    }
    window.addEventListener('pageshow', function (event) { if (event.persisted) run(); });
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'visible') run();
    });
    if (atLeast('8.0')) onEvent('activated', run);
  }

  /**
   * Runs task() (a promise; resolving false stops it) every opts.interval
   * ms (2 s), every opts.slowInterval ms (5 s) once opts.slowAfter ms (60 s)
   * have passed, and only while the page is visible. The first run comes
   * after one interval. Returns {stop(), now(), reset()}.
   */
  function poll(task, opts) {
    opts = opts || {};
    var interval = opts.interval > 0 ? opts.interval : 2 * SECOND;
    var slowAfter = opts.slowAfter > 0 ? opts.slowAfter : 60 * SECOND;
    var slowInterval = opts.slowInterval > 0 ? opts.slowInterval : 5 * SECOND;
    var started = Date.now();
    var timer = null;
    var stopped = false;
    var running = false;

    function schedule() {
      clearTimeout(timer);
      timer = null;
      if (stopped || document.visibilityState === 'hidden') return;
      timer = setTimeout(tick, Date.now() - started > slowAfter ? slowInterval : interval);
    }

    function tick() {
      timer = null;
      if (stopped || running) return;
      running = true;
      Promise.resolve().then(task).then(function (more) {
        running = false;
        if (more === false) stop();
        else schedule();
      }, function () {
        running = false;
        schedule();
      });
    }

    function onVisible() {
      if (!stopped && document.visibilityState === 'visible' && !timer && !running) tick();
    }

    function stop() {
      stopped = true;
      clearTimeout(timer);
      timer = null;
      document.removeEventListener('visibilitychange', onVisible);
    }

    document.addEventListener('visibilitychange', onVisible);
    schedule();
    return {
      stop: stop,
      now: function () {
        if (stopped || running) return;
        clearTimeout(timer);
        tick();
      },
      reset: function () { started = Date.now(); }
    };
  }

  /** Asks to let the bot write to the user (6.9+). Promise<bool>; false when unsupported. */
  function requestWriteAccess() {
    if (!tg || !atLeast('6.9') || typeof tg.requestWriteAccess !== 'function') {
      return Promise.resolve(false);
    }
    return new Promise(function (resolve) {
      try {
        tg.requestWriteAccess(function (granted) { resolve(!!granted); });
      } catch (e) {
        resolve(false);
      }
    });
  }

  /** Opens an https://t.me/… link in Telegram (the chat, a share sheet). */
  function openTelegramLink(url) {
    if (typeof url !== 'string' || !/^https:\/\/t\.me\/[^\s]*$/.test(url)) return false;
    if (tg && typeof tg.openTelegramLink === 'function') {
      safeCall(function () { tg.openTelegramLink(url); });
    } else {
      window.location.href = url;
    }
    return true;
  }

  function closeApp() {
    dirty = false;
    if (tg && typeof tg.close === 'function') safeCall(function () { tg.close(); });
  }

  // ── transport: api ────────────────────────────────────────────────────────

  var apiSending = false;

  /**
   * The api-mode transport of the chat's pages (settings.html, catalog.html):
   * the very payload sendData would carry goes to
   * POST drafts/<params.svc>/apply {payload, revision: null}; on success the
   * page moves to the `next` URL the server gives (the order page).
   */
  var apiTransport = {
    name: 'api',
    send: function (obj) {
      var svc = params.svc;
      if (typeof svc !== 'string' || !/^[a-z]{1,16}$/.test(svc)) {
        haptic('error');
        showAlert(t('bad_link'));
        return { ok: false, reason: 'bad_link' };
      }
      if (byteLength(JSON.stringify(obj)) > MAX_PAYLOAD_BYTES) {
        haptic('error');
        showAlert(t('too_long'));
        return { ok: false, reason: 'too_long' };
      }
      if (apiSending) return { ok: false, reason: 'busy' };
      apiSending = true;
      mainButtonProgress(true);
      return api.post('drafts/' + svc + '/apply', { payload: obj, revision: null }).then(function (res) {
        apiSending = false;
        if (res.ok) {
          haptic('success');
          var next = isObject(res.data) ? res.data.next : null;
          // a form that was just saved is not a Back target
          if (!goUrl(next, { replace: true })) back();
          return { ok: true };
        }
        mainButtonProgress(false);
        if (res.status !== 401) {
          haptic('error');
          showAlert(errorText(res.code));
        }
        return { ok: false, reason: res.code || 'error' };
      });
    }
  };

  // ── dom ───────────────────────────────────────────────────────────────────

  /**
   * el('div', {class: 'x', text: 'y', attrs: {...}, on: {click: fn}}, [children])
   * Text goes in as textContent, never as HTML.
   */
  function el(tag, props, children) {
    var node = document.createElement(tag);
    props = props || {};
    Object.keys(props).forEach(function (key) {
      var value = props[key];
      if (value == null || value === false) return;
      if (key === 'text') node.textContent = String(value);
      else if (key === 'class') node.className = value;
      else if (key === 'attrs') {
        Object.keys(value).forEach(function (name) {
          if (value[name] != null && value[name] !== false) node.setAttribute(name, String(value[name]));
        });
      } else if (key === 'on') {
        Object.keys(value).forEach(function (name) { node.addEventListener(name, value[name]); });
      } else {
        node[key] = value;
      }
    });
    (children || []).forEach(function (child) {
      if (child == null || child === false) return;
      node.appendChild(typeof child === 'string' ? document.createTextNode(child) : child);
    });
    return node;
  }

  /** Fills [data-i18n], [data-i18n-placeholder] and [data-i18n-aria-label]. */
  function applyI18n(rootNode) {
    var scope = rootNode || document;
    Array.prototype.forEach.call(scope.querySelectorAll('[data-i18n]'), function (node) {
      node.textContent = t(node.getAttribute('data-i18n'));
    });
    Array.prototype.forEach.call(scope.querySelectorAll('[data-i18n-placeholder]'), function (node) {
      node.setAttribute('placeholder', t(node.getAttribute('data-i18n-placeholder')));
    });
    Array.prototype.forEach.call(scope.querySelectorAll('[data-i18n-aria-label]'), function (node) {
      node.setAttribute('aria-label', t(node.getAttribute('data-i18n-aria-label')));
    });
  }

  /**
   * Arrow-key movement inside a group of [role=radio] or [role=tab] buttons
   * (roving tabindex). onPick(button) runs on arrow moves; clicks are the
   * page's own handlers.
   */
  function rovingGroup(container, selector, onPick) {
    function items() {
      return Array.prototype.filter.call(container.querySelectorAll(selector),
        function (node) { return !node.disabled && !node.hidden; });
    }
    function sync() {
      var list = items();
      var active = list.filter(function (node) {
        return node.getAttribute('aria-checked') === 'true' || node.getAttribute('aria-selected') === 'true';
      })[0] || list[0];
      list.forEach(function (node) { node.tabIndex = node === active ? 0 : -1; });
    }
    container.addEventListener('keydown', function (event) {
      var keys = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };
      if (!(event.key in keys) && event.key !== 'Home' && event.key !== 'End') return;
      var list = items();
      var index = list.indexOf(document.activeElement);
      if (index < 0) return;
      event.preventDefault();
      var next = event.key === 'Home' ? 0 : event.key === 'End' ? list.length - 1
        : (index + keys[event.key] + list.length) % list.length;
      list[next].focus();
      if (onPick) onPick(list[next]);
      sync();
    });
    sync();
    return { sync: sync };
  }

  /** Replaces the page with a single message (no MainButton, nothing to send). */
  function showNotice(title, text) {
    mainButton(null);
    backButton(false);
    setDirty(false);
    var main = document.getElementById('app') || document.body;
    main.textContent = '';
    main.hidden = false;
    main.appendChild(el('div', { class: 'notice', attrs: { role: 'status' } }, [
      el('h1', { class: 'notice-title', text: title }),
      el('p', { class: 'notice-text', text: text })
    ]));
  }

  // ── lifecycle ─────────────────────────────────────────────────────────────

  var themeWired = false;

  function wireTheme() {
    if (themeWired) return;
    themeWired = true;
    applyTheme();
    applyInsets();
    onEvent('themeChanged', applyTheme);
    onEvent('safeAreaChanged', applyInsets);
    onEvent('contentSafeAreaChanged', applyInsets);
    if (!tg || !tg.colorScheme) {
      try {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyTheme);
      } catch (e) { /* old engines */ }
    }
  }

  /**
   * First call of every page. Outside Telegram it shows only the
   * "open from the bot" notice and returns false; the page stops there.
   */
  function start() {
    wireTheme();
    // A keyboard-button launch carries no initData, so the API cannot be
    // used from it: api mode then shows the same notice (menu-button wording).
    if (inTelegram && !(apiMode && !initData)) {
      if (apiMode) {
        setTransport(apiTransport);
        mainButton(null);
        backButton(null);
      }
      return true;
    }
    showNotice(t('open_title'),
      BOT_USERNAME ? t('open_text', { bot: BOT_USERNAME }) : t('open_text_any'));
    return false;
  }

  /**
   * Call right after the page's DOM is built: ready(), expand(), colours,
   * and for forms no vertical swipe-to-close (7.7+), so scrolling a long
   * form never closes it.
   */
  function ready(opts) {
    var main = document.getElementById('app');
    if (main) main.hidden = false;
    if (!tg) return;
    safeCall(function () { tg.ready(); });
    safeCall(function () { tg.expand(); });
    if (atLeast('6.1')) {
      // The pages are grouped lists on secondary_bg_color, so Telegram's
      // header and overscroll match the page ground.
      safeCall(function () { tg.setHeaderColor('secondary_bg_color'); });
      safeCall(function () { tg.setBackgroundColor('secondary_bg_color'); });
    }
    if (opts && opts.form && atLeast('7.7')) {
      safeCall(function () { tg.disableVerticalSwipes(); });
    }
  }

  var M = window.MiniApp = {
    VERSION: '2',
    PAYLOAD_VERSION: PAYLOAD_VERSION,
    MAX_PAYLOAD_BYTES: MAX_PAYLOAD_BYTES,
    BOT_USERNAME: BOT_USERNAME,
    tg: tg,
    inTelegram: inTelegram,
    atLeast: atLeast,
    lang: lang,
    t: t,
    params: params,
    prices: prices,
    state: prefill,
    user: telegramUser(),
    fmtNumber: fmtNumber,
    fmtPrice: fmtPrice,
    pricing: {
      qualityKey: qualityKey,
      tiers: tiers,
      tierFor: tierFor,
      unitPrice: unitPrice,
      maxPaidImages: maxPaidImages,
      quote: quote
    },
    applyTheme: applyTheme,
    start: start,
    ready: ready,
    sendPayload: sendPayload,
    setTransport: setTransport,
    transports: { sendData: sendDataTransport, api: apiTransport },
    apiMode: apiMode,
    initData: initData,
    startParam: startParam,
    launchId: launchId,
    api: api,
    onAuthFailure: onAuthFailure,
    errorText: errorText,
    nav: nav,
    setLang: setLang,
    onResume: onResume,
    poll: poll,
    confirm: confirmDialog,
    requestWriteAccess: requestWriteAccess,
    openTelegramLink: openTelegramLink,
    close: closeApp,
    mainButton: mainButton,
    backButton: backButton,
    setDirty: setDirty,
    haptic: haptic,
    showAlert: showAlert,
    store: store,
    el: el,
    applyI18n: applyI18n,
    rovingGroup: rovingGroup,
    showNotice: showNotice,
    decodeParam: decodeParam,
    toInt: toInt,
    clamp: clamp,
    isObject: isObject
  };
})(window, document);
