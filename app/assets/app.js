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
 *   transport - how a payload leaves the page; sendData today, an HTTPS API
 *               can be added later with setTransport() without touching pages
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
   * What the order would cost, from `p` alone:
   * {base, tierMax, paid, unit, images, total, payable, trial} or null.
   * `payable` is what the student pays: the free trial covers the base only.
   */
  function quote(table, opts) {
    var tier = tierFor(table, opts.quality, opts.n);
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
      trial: trial
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
  // and the app.css token each one feeds.
  var READABLE_TOKENS = { hint_color: '--hint', section_header_text_color: '--section-title',
    destructive_text_color: '--destructive' };
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
    // Text sits on the page (bg) and on cards (secondary_bg). The CSS
    // fallbacks already reach 4.5:1, so only Telegram's colours are adjusted.
    var grounds = [theme.bg_color, theme.secondary_bg_color].map(hexToRgb).filter(Boolean);
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

  /** BackButton for sub-views: a handler shows it, null hides it (6.1+). */
  function backButton(onClick) {
    if (!tg || !tg.BackButton || !atLeast('6.1')) return;
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
    backButton(null);
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
    if (inTelegram) return true;
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
      safeCall(function () { tg.setHeaderColor('bg_color'); });
      safeCall(function () { tg.setBackgroundColor('bg_color'); });
    }
    if (opts && opts.form && atLeast('7.7')) {
      safeCall(function () { tg.disableVerticalSwipes(); });
    }
  }

  window.MiniApp = {
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
      maxPaidImages: maxPaidImages,
      quote: quote
    },
    applyTheme: applyTheme,
    start: start,
    ready: ready,
    sendPayload: sendPayload,
    setTransport: setTransport,
    transports: { sendData: sendDataTransport },
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
    clamp: clamp
  };
})(window, document);
