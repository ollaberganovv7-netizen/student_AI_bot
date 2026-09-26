/*
 * Mini App components: window.MiniAppUI (design C, "Polished native").
 *
 * Loaded after assets/app.js by the api-mode pages (index, order, wallet,
 * history, invite). Every builder returns a DOM node made with
 * MiniApp.el / createElementNS; text only ever goes in as textContent. The
 * classes are those of assets/app.css, so new pages look like settings.html
 * and catalog.html.
 *
 *   icon(name)                     <svg class="i"> from assets/icons.svg
 *   tile(name, tint)               the coloured rounded-square icon of a row
 *   group({title, foot, items, icons, id})       inset grouped list section
 *   cell({icon, tint, title, subtitle, value, onClick, chevron, external,
 *         id, ariaLabel, trailing, disabled})    one row
 *   toast(text, {kind, ms})        a short message at the bottom
 *   banner({kind, title, text, action: {label, onClick}, icon})
 *   confirm(message)               Promise<bool>
 *   popup({title, message, buttons: [{id, type, text}]})  Promise<id|null>
 *   progress(el)                   -> {el, set(pct|null, text)}
 *   priceLines(el, quote)          the server quote as price rows
 *   statusPill(status)             a coloured status label
 *   empty({icon, title, text, action})
 *   skeleton(rows)                 a loading placeholder
 *   copyField({label, value, id, onCopy, compact, wrap})
 *                                  a read-only value with a Copy button;
 *                                  compact: icon-only button (the aria-label
 *                                  still says "Copy: <label>"), so a long value
 *                                  keeps the room; wrap: the value breaks over
 *                                  as many lines as it needs instead of being
 *                                  cut with an ellipsis (a link)
 *   balanceCard({balance, pending, onClick})
 *   fileRow({icon, tint, title, meta, action: {label, icon, onClick}})
 *   button({text, onClick, kind, icon})
 *   formatDate(iso, lang, {time, year})
 *   clear(el)
 *
 * Amounts are formatted by MiniApp.fmtPrice; no amount is ever written here.
 */
(function (window, document) {
  'use strict';

  var M = window.MiniApp;
  var el = M.el;
  var SVG_NS = 'http://www.w3.org/2000/svg';
  var SPRITE = 'assets/icons.svg';
  var TINTS = ['blue', 'indigo', 'green', 'orange', 'pink', 'purple', 'teal', 'red', 'grey', 'yellow'];
  var NAME_RE = /^[a-z0-9-]{1,32}$/;
  var SECOND = 1000;
  var counter = 0;

  function t(key, vars) {
    return M.t(key, vars);
  }

  function uid(prefix) {
    counter += 1;
    return 'ui-' + prefix + '-' + counter;
  }

  function clear(node) {
    while (node && node.firstChild) node.removeChild(node.firstChild);
    return node;
  }

  function icon(name, cls) {
    var svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('class', cls || 'i');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('focusable', 'false');
    var use = document.createElementNS(SVG_NS, 'use');
    use.setAttribute('href', SPRITE + '#i-' + (NAME_RE.test(name) ? name : 'info'));
    svg.appendChild(use);
    return svg;
  }

  function tile(name, tint) {
    var colour = TINTS.indexOf(tint) >= 0 ? tint : 'grey';
    return el('span', { class: 'ic ic-' + colour, attrs: { 'aria-hidden': 'true' } }, [icon(name)]);
  }

  // ── lists ─────────────────────────────────────────────────────────────────

  /**
   * An inset grouped list: <section class="group"> with an optional title
   * (it labels the section) and foot note. items: nodes (cells). icons:
   * false when the rows carry no icon tile (separators then start at the
   * text).
   */
  function group(opts) {
    opts = opts || {};
    var titleId = opts.title ? uid('group') : null;
    var list = el('div', { class: opts.icons === false ? 'list' : 'list icons' });
    (opts.items || []).forEach(function (item) {
      if (item) list.appendChild(item);
    });
    return el('section', { class: 'group', attrs: { id: opts.id, 'aria-labelledby': titleId } }, [
      opts.title ? el('h2', { class: 'group-title', text: opts.title, attrs: { id: titleId } }) : null,
      list,
      opts.foot ? el('p', { class: 'group-foot', text: opts.foot }) : null
    ]);
  }

  /**
   * One row. With onClick it is a <button> (44 px, chevron by default);
   * external: true marks a row that leaves the app (to the chat) with an
   * arrow icon and a spoken hint. value: short text on the right.
   * trailing: a node placed last (e.g. a pill).
   */
  function cell(opts) {
    opts = opts || {};
    var clickable = typeof opts.onClick === 'function';
    var chevron = clickable && opts.chevron !== false && !opts.external;
    var text = el('span', { class: 'cell-text' }, [
      el('span', { class: 'cell-label', text: opts.title }),
      opts.subtitle ? el('span', { class: 'cell-sub', text: opts.subtitle }) : null
    ]);
    var children = [
      opts.icon ? tile(opts.icon, opts.tint) : null,
      text,
      opts.value != null && opts.value !== '' ? el('span', { class: 'cell-value', text: opts.value }) : null,
      opts.trailing || null,
      opts.external ? el('span', { class: 'visually-hidden', text: '(' + t('opens_chat') + ')' }) : null,
      opts.external ? icon('external', 'i ext') : null,
      chevron ? chev() : null
    ];
    var cls = 'cell' + (opts.icon ? ' has-icon' : '') + (clickable ? ' cell-link' : '') +
      (opts.className ? ' ' + opts.className : '');
    var node = el(clickable ? 'button' : 'div', {
      class: cls,
      attrs: {
        id: opts.id,
        type: clickable ? 'button' : null,
        'aria-label': opts.ariaLabel,
        disabled: clickable && opts.disabled ? 'disabled' : null
      },
      on: clickable ? { click: function (event) { opts.onClick(event); } } : null
    }, children);
    return node;
  }

  function chev() {
    var svg = icon('chev', 'chev i');
    return svg;
  }

  /** An in-page button: kind 'primary' | 'plain' (default) | 'destructive'. */
  function button(opts) {
    opts = opts || {};
    var kind = ['primary', 'plain', 'destructive'].indexOf(opts.kind) >= 0 ? opts.kind : 'plain';
    return el('button', {
      class: 'btn btn-' + kind + (opts.className ? ' ' + opts.className : ''),
      attrs: { type: 'button', id: opts.id, 'aria-label': opts.ariaLabel },
      on: typeof opts.onClick === 'function' ? { click: function (event) { opts.onClick(event); } } : null
    }, [opts.icon ? icon(opts.icon) : null, el('span', { text: opts.text })]);
  }

  // ── feedback ──────────────────────────────────────────────────────────────

  var toastRegion = null;

  function toastHost() {
    if (toastRegion && toastRegion.parentNode) return toastRegion;
    toastRegion = el('div', { class: 'toasts', attrs: { role: 'status', 'aria-live': 'polite' } });
    document.body.appendChild(toastRegion);
    return toastRegion;
  }

  /** A short message near the bottom; kind 'info' | 'success' | 'error'. */
  function toast(text, opts) {
    opts = opts || {};
    var kind = ['success', 'error'].indexOf(opts.kind) >= 0 ? opts.kind : 'info';
    var host = toastHost();
    var node = el('div', { class: 'toast toast-' + kind }, [
      icon(kind === 'success' ? 'check-circle' : kind === 'error' ? 'alert' : 'info'),
      el('span', { text: text })
    ]);
    host.appendChild(node);
    while (host.children.length > 2) host.removeChild(host.firstChild);
    setTimeout(function () {
      if (node.parentNode) node.parentNode.removeChild(node);
    }, opts.ms > 0 ? opts.ms : 3 * SECOND);
    if (kind === 'error') M.haptic('error');
    else if (kind === 'success') M.haptic('success');
    return node;
  }

  var BANNER_ICONS = { info: 'info', success: 'check-circle', warn: 'alert', error: 'alert' };
  var BANNER_TINTS = { info: 'blue', success: 'green', warn: 'orange', error: 'red' };

  /**
   * A message block inside the page (a pending top-up, a running order, an
   * error): kind 'info' | 'success' | 'warn' | 'error'. Errors are role=alert,
   * the rest role=status. action: {label, onClick} adds a link-styled button.
   */
  function banner(opts) {
    opts = opts || {};
    var kind = BANNER_ICONS[opts.kind] ? opts.kind : 'info';
    var body = el('div', { class: 'banner-body' }, [
      opts.title ? el('strong', { class: 'banner-title', text: opts.title }) : null,
      opts.text ? el('span', { class: 'banner-text', text: opts.text }) : null,
      opts.action && typeof opts.action.onClick === 'function'
        ? el('button', {
          class: 'banner-action',
          attrs: { type: 'button' },
          text: opts.action.label,
          on: { click: function (event) { opts.action.onClick(event); } }
        })
        : null
    ]);
    return el('div', {
      class: 'banner banner-' + kind,
      attrs: { role: kind === 'error' ? 'alert' : 'status', id: opts.id }
    }, [tile(opts.icon || BANNER_ICONS[kind], BANNER_TINTS[kind]), body]);
  }

  function confirm(message) {
    return M.confirm(message);
  }

  /**
   * Telegram's popup (6.2+) with up to three buttons; resolves the pressed
   * button's id, or null when dismissed. Older clients get the browser's
   * confirm: OK = the first button that is not 'cancel'.
   */
  function popup(opts) {
    opts = opts || {};
    var buttons = (opts.buttons && opts.buttons.length ? opts.buttons : [{ id: 'ok', type: 'ok' }]).slice(0, 3);
    var tg = M.tg;
    return new Promise(function (resolve) {
      if (tg && M.atLeast('6.2') && typeof tg.showPopup === 'function') {
        try {
          tg.showPopup({
            title: opts.title ? String(opts.title).slice(0, 64) : undefined,
            message: String(opts.message || '').slice(0, 256),
            buttons: buttons.map(function (b) {
              var out = { id: String(b.id || ''), type: b.type || 'default' };
              if (b.text) out.text = String(b.text).slice(0, 64);
              return out;
            })
          }, function (id) { resolve(id ? String(id) : null); });
          return;
        } catch (e) { /* fall through */ }
      }
      var primary = buttons.filter(function (b) { return b.type !== 'cancel'; })[0] || buttons[0];
      var ok = false;
      try {
        ok = buttons.length > 1 ? window.confirm(String(opts.message || '')) : (window.alert(String(opts.message || '')), true);
      } catch (e) { ok = false; }
      resolve(ok ? String(primary.id || '') : null);
    });
  }

  /**
   * Turns `node` into a progress bar (role=progressbar). set(pct, text): a
   * number 0..100 fills the bar; null shows an indeterminate bar. The text
   * is shown under it and read as the value.
   */
  function progress(node) {
    clear(node);
    node.classList.add('progress');
    var bar = el('span', { class: 'progress-bar' });
    var track = el('span', { class: 'progress-track' }, [bar]);
    var label = el('span', { class: 'progress-text' });
    node.setAttribute('role', 'progressbar');
    node.setAttribute('aria-valuemin', '0');
    node.setAttribute('aria-valuemax', '100');
    if (!node.getAttribute('aria-label') && !node.getAttribute('aria-labelledby')) {
      node.setAttribute('aria-label', t('ui.progress'));
    }
    node.appendChild(track);
    node.appendChild(label);
    function set(pct, text) {
      var known = typeof pct === 'number' && isFinite(pct);
      var value = known ? Math.max(0, Math.min(100, Math.round(pct))) : null;
      node.classList.toggle('indeterminate', !known);
      bar.style.width = known ? value + '%' : '';
      if (known) node.setAttribute('aria-valuenow', String(value));
      else node.removeAttribute('aria-valuenow');
      var words = text ? String(text) : '';
      label.textContent = words;
      var spoken = known ? (words ? words + ' · ' : '') + value + '%' : words;
      if (spoken) node.setAttribute('aria-valuetext', spoken);
      else node.removeAttribute('aria-valuetext');
    }
    set(null, '');
    return { el: node, set: set };
  }

  // ── money ─────────────────────────────────────────────────────────────────

  function num(v) {
    var n = Number(v);
    return isFinite(n) ? Math.round(n) : 0;
  }

  function priceRow(label, amount, cls) {
    return el('div', { class: 'cell ' + (cls || 'price-line') }, [
      el('span', { class: 'cell-label', text: label }),
      amount
    ]);
  }

  /**
   * The price rows of a server quote (GET /drafts: {units, unit, unit_price,
   * base, paid_images, image_price, total, payable, admin, trial}) into
   * `node` (emptied first; aria-live). Nothing is computed here but the
   * picture subtotal the server priced per picture; the total shown is the
   * server's payable.
   */
  function priceLines(node, quote) {
    clear(node);
    node.classList.add('list', 'prices');
    node.setAttribute('aria-live', 'polite');
    if (!quote || typeof quote !== 'object') return node;
    var units = num(quote.units);
    var baseKey = quote.unit === 'page' ? 'ui.price_pages' : 'ui.price_slides';
    var base = el('span', { class: 'amt' });
    if (quote.trial || quote.admin) {
      base.appendChild(el('s', { text: M.fmtPrice(num(quote.base)) }));
      base.appendChild(el('span', { class: 'free-tag', text: t('free') }));
    } else {
      base.textContent = M.fmtPrice(num(quote.base));
    }
    node.appendChild(priceRow(t(baseKey, { n: units, unit: M.fmtPrice(num(quote.unit_price)) }), base));
    var paid = num(quote.paid_images);
    if (paid > 0) {
      node.appendChild(priceRow(t('ui.price_images', { n: paid, unit: M.fmtPrice(num(quote.image_price)) }),
        el('span', { class: 'amt', text: M.fmtPrice(paid * num(quote.image_price)) })));
    }
    if (quote.trial || quote.admin) {
      node.appendChild(priceRow(t(quote.admin ? 'ui.price_admin' : 'ui.price_trial'),
        el('span', { class: 'amt' }, [el('span', { class: 'free-tag', text: t('free') })])));
    }
    var payable = num(quote.payable);
    var total = el('span', { class: 'amt', text: payable ? M.fmtPrice(payable) : t('free') });
    total.setAttribute('data-amount', String(payable));
    node.appendChild(priceRow(t('ui.price_pay'), total, 'price-total'));
    return node;
  }

  /**
   * The balance card: the amount large, "⏳ N receipts being checked" under
   * it when some are pending. With onClick it is a button (to the wallet).
   */
  function balanceCard(opts) {
    opts = opts || {};
    var clickable = typeof opts.onClick === 'function';
    var pending = num(opts.pending);
    var amount = el('span', { class: 'balance-amount', text: M.fmtPrice(num(opts.balance)) });
    amount.setAttribute('data-amount', String(num(opts.balance)));
    return el(clickable ? 'button' : 'div', {
      class: 'balance-card' + (clickable ? ' cell-link' : ''),
      attrs: { type: clickable ? 'button' : null, id: opts.id, 'aria-live': 'polite' },
      on: clickable ? { click: function (event) { opts.onClick(event); } } : null
    }, [
      el('span', { class: 'balance-text' }, [
        el('span', { class: 'balance-label', text: opts.label || t('ui.balance') }),
        amount,
        pending > 0 ? el('span', { class: 'balance-pending', text: t('ui.pending_receipts', { n: pending }) }) : null
      ]),
      tile('wallet', 'green'),
      clickable ? chev() : null
    ]);
  }

  // ── status and states ─────────────────────────────────────────────────────

  var PILL_TONES = {
    starting: 'info', queued: 'info', building: 'info', sending: 'info',
    delivered: 'good', approved: 'good',
    pending: 'warn',
    failed: 'bad', rejected: 'bad',
    cancelled: 'neutral', refused: 'neutral'
  };

  /** A job or payment status as a small coloured label (status.<name>). */
  function statusPill(status) {
    var name = PILL_TONES[status] ? status : null;
    var tone = name ? PILL_TONES[name] : 'neutral';
    return el('span', { class: 'pill pill-' + tone, text: name ? t('status.' + name) : String(status || '') });
  }

  /** An empty state: icon, title, text and an optional button. */
  function empty(opts) {
    opts = opts || {};
    return el('div', { class: 'empty-state', attrs: { role: 'status' } }, [
      tile(opts.icon || 'info', opts.tint || 'grey'),
      opts.title ? el('p', { class: 'empty-title', text: opts.title }) : null,
      opts.text ? el('p', { class: 'empty-text', text: opts.text }) : null,
      opts.action && typeof opts.action.onClick === 'function'
        ? button({ text: opts.action.label, onClick: opts.action.onClick, kind: 'plain' })
        : null
    ]);
  }

  /** A grey placeholder list while data loads (aria-busy, "Loading…" for readers). */
  function skeleton(rows) {
    var n = Math.max(1, Math.min(8, num(rows) || 3));
    var list = el('div', { class: 'list skeleton', attrs: { 'aria-busy': 'true' } }, [
      el('span', { class: 'visually-hidden', text: t('loading') })
    ]);
    for (var i = 0; i < n; i++) {
      list.appendChild(el('div', { class: 'cell has-icon', attrs: { 'aria-hidden': 'true' } }, [
        el('span', { class: 'sk sk-tile' }),
        el('span', { class: 'sk-lines' }, [el('span', { class: 'sk sk-line' }),
          el('span', { class: 'sk sk-line short' })])
      ]));
    }
    return list;
  }

  // ── copy ──────────────────────────────────────────────────────────────────

  function selectText(input) {
    try {
      input.focus();
      input.select();
      input.setSelectionRange(0, input.value.length);
    } catch (e) { /* not selectable */ }
  }

  /** Copies text; Promise<bool>. Falls back to execCommand on a selection. */
  function copyText(text, input) {
    return new Promise(function (resolve) {
      function fallback() {
        var ok = false;
        if (input) {
          selectText(input);
          try {
            ok = document.execCommand('copy');
          } catch (e) { ok = false; }
        }
        resolve(!!ok);
      }
      try {
        if (window.navigator.clipboard && typeof window.navigator.clipboard.writeText === 'function') {
          window.navigator.clipboard.writeText(String(text)).then(function () { resolve(true); }, fallback);
          return;
        }
      } catch (e) { /* no clipboard API */ }
      fallback();
    });
  }

  // A wrapping copy value is a read-only <textarea>; app.css styles only
  // `input.copy-input`, so the box's look is set here (CSSOM, not markup).
  var WRAP_STYLE = {
    flex: '1 1 auto', minWidth: '0', width: 'auto', minHeight: 'var(--target, 44px)', height: 'auto',
    margin: '0', padding: '10px 12px', border: '0', borderRadius: 'var(--radius-sm)',
    background: 'var(--fill)', color: 'var(--text)', fontSize: '16px', lineHeight: '1.35',
    resize: 'none', overflow: 'hidden', overflowWrap: 'anywhere', wordBreak: 'break-all',
    whiteSpace: 'pre-wrap'
  };

  function sizesItself() {
    try {
      return !!(window.CSS && window.CSS.supports && window.CSS.supports('field-sizing', 'content'));
    } catch (e) { return false; }
  }

  /** A textarea as tall as its text, also where CSS field-sizing is missing. */
  function fitHeight(area) {
    if (sizesItself()) {
      area.style.fieldSizing = 'content';
      return;
    }
    var tries = 0;
    var attached = false;
    function connected() {
      return typeof area.isConnected === 'boolean' ? area.isConnected
        : document.documentElement.contains(area);
    }
    function fit() {
      if (!connected()) {
        if (attached) window.removeEventListener('resize', fit);
        else if (tries++ < 10) later(fit);
        return;
      }
      attached = true;
      area.style.height = 'auto';
      // 0 while an ancestor is hidden: measure again a little later.
      if (area.scrollHeight > 0) area.style.height = area.scrollHeight + 'px';
      else if (tries++ < 10) later(fit);
    }
    function later(fn) {
      if (window.requestAnimationFrame) window.requestAnimationFrame(fn);
      else window.setTimeout(fn, 16);
    }
    window.addEventListener('resize', fit);
    later(fit);
  }

  /**
   * A labelled read-only field with a Copy button (a card number, the
   * referral link). On copy: a toast; when copying is refused, the text is
   * selected so the user can copy it by hand.
   *
   * opts.compact: the button shows only its icon; its aria-label keeps the
   *   spoken "Copy: <label>". Use it when the value must stay whole on a
   *   phone (card numbers, links).
   * opts.wrap: the value wraps onto more lines (a read-only textarea, as tall
   *   as its text) instead of being cut; for values longer than a phone line.
   */
  function copyField(opts) {
    opts = opts || {};
    var id = opts.id || uid('copy');
    var text = String(opts.value == null ? '' : opts.value);
    var input;
    if (opts.wrap) {
      input = el('textarea', {
        class: 'copy-input copy-input-wrap',
        attrs: { id: id, readonly: 'readonly', rows: '1', spellcheck: 'false', autocapitalize: 'off',
          autocorrect: 'off' }
      });
      Object.keys(WRAP_STYLE).forEach(function (name) { input.style[name] = WRAP_STYLE[name]; });
      input.value = text;
      fitHeight(input);
    } else {
      input = el('input', {
        class: 'copy-input',
        attrs: { id: id, type: 'text', readonly: 'readonly', value: text,
          spellcheck: 'false', autocomplete: 'off' }
      });
      input.value = text;
    }
    var copy = el('button', {
      class: 'copy-button',
      attrs: { type: 'button', 'aria-label': t('copy') + (opts.label ? ': ' + opts.label : '') },
      on: {
        click: function () {
          copyText(input.value, input).then(function (ok) {
            if (ok) {
              toast(t('copied'), { kind: 'success' });
            } else {
              selectText(input);
              toast(t('copy_failed'));
            }
            if (typeof opts.onCopy === 'function') opts.onCopy(ok);
          });
        }
      }
    }, [icon('copy'), opts.compact ? null : el('span', { class: 'copy-word', text: t('copy') })]);
    return el('div', { class: 'copy-field' + (opts.compact ? ' copy-compact' : '') }, [
      el('label', { class: 'copy-label', attrs: { for: id }, text: opts.label || '' }),
      el('div', { class: 'copy-row' }, [input, copy])
    ]);
  }

  // ── rows of files ─────────────────────────────────────────────────────────

  /**
   * A delivered file: icon, title (two lines at most), meta line, and an
   * optional 44 px trailing action ({label, icon, onClick}).
   */
  function fileRow(opts) {
    opts = opts || {};
    var action = opts.action && typeof opts.action.onClick === 'function'
      ? el('button', {
        class: 'file-action',
        attrs: { type: 'button', 'aria-label': opts.action.label, title: opts.action.label },
        on: { click: function (event) { opts.action.onClick(event); } }
      }, [icon(opts.action.icon || 'resend')])
      : null;
    return el('div', { class: 'cell has-icon file-row', attrs: { id: opts.id } }, [
      tile(opts.icon || 'page', opts.tint || 'blue'),
      el('span', { class: 'cell-text' }, [
        el('span', { class: 'file-title', text: opts.title }),
        opts.meta ? el('span', { class: 'cell-sub', text: opts.meta }) : null
      ]),
      opts.trailing || null,
      action
    ]);
  }

  // ── dates ─────────────────────────────────────────────────────────────────

  function pad(n) {
    return (n < 10 ? '0' : '') + n;
  }

  /**
   * An ISO-8601 time as the bot writes dates: "25.09" this year, else
   * "25.09.2025"; opts.time adds " 14:05"; opts.year always adds the year.
   * Local time of the device. '' for anything unparsable.
   */
  function formatDate(iso, lang, opts) {
    opts = opts || {};
    var d = new Date(typeof iso === 'string' ? iso : NaN);
    if (!isFinite(d.getTime())) return '';
    var now = new Date();
    var text = pad(d.getDate()) + '.' + pad(d.getMonth() + 1);
    if (opts.year || d.getFullYear() !== now.getFullYear()) text += '.' + d.getFullYear();
    if (opts.time) text += ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
    return text;
  }

  window.MiniAppUI = {
    icon: icon,
    tile: tile,
    group: group,
    cell: cell,
    button: button,
    toast: toast,
    banner: banner,
    confirm: confirm,
    popup: popup,
    progress: progress,
    priceLines: priceLines,
    balanceCard: balanceCard,
    statusPill: statusPill,
    empty: empty,
    skeleton: skeleton,
    copyField: copyField,
    copyText: copyText,
    fileRow: fileRow,
    formatDate: formatDate,
    clear: clear
  };
})(window, document);
