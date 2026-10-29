// Site chrome and interactions shared by every page.
import { KITS, WORKSHOPS, GUIDES, FIELDS } from './data.js';
import * as store from './store.js';
import { $, $$, icon, esc, img, toast, trapFocus, reducedMotion, pluralize } from './ui.js';

const PAGES = ['home', 'shop', 'product', 'cart', 'checkout', 'workshops', 'workshop', 'learn', 'guide'];

/* ---------- demo banner ---------- */
function initBanner() {
  const el = $('[data-banner]');
  if (!el || store.banner.dismissed()) return;
  el.hidden = false;
  const close = document.createElement('button');
  close.type = 'button';
  close.className = 'demo-banner__close';
  close.textContent = 'Dismiss';
  close.addEventListener('click', () => { store.banner.dismiss(); el.remove(); });
  el.append(close);
}

/* ---------- cart badge + card states ---------- */
let lastCount = null;
function syncCart() {
  const n = store.count();
  for (const c of $$('[data-cart-count]')) c.textContent = n;
  for (const link of $$('[data-cart-link]')) {
    link.setAttribute('aria-label', `Cart, ${pluralize(n, 'item')}`);
    if (lastCount !== null && n > lastCount && !reducedMotion()) {
      link.classList.remove('is-bumped');
      void link.offsetWidth;
      link.classList.add('is-bumped');
    }
  }
  lastCount = n;
  for (const card of $$('.kit-card[data-kit]')) {
    const q = store.qtyOf(card.dataset.kit);
    const status = card.querySelector('[data-status]');
    card.classList.toggle('is-in-cart', q > 0);
    if (status) status.textContent = q > 0 ? `In your cart${q > 1 ? ` · ${q}` : ''}` : status.dataset.default;
  }
}

/* ---------- quick add on kit cards ---------- */
function initQuickAdd() {
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-add]');
    if (!btn || btn.disabled) return;
    e.preventDefault();
    const slug = btn.dataset.add;
    const k = store.kitBySlug[slug];
    const added = store.addKit(slug, 1);
    if (!added) {
      toast({ title: `You already have ${store.KIT_MAX} in your cart`, text: 'That’s the most we ship in one order.' });
      return;
    }
    btn.classList.add('is-added');
    const label = btn.querySelector('.add__label');
    if (label) label.textContent = 'Added';
    btn.setAttribute('aria-label', `${k.name} added to cart`);
    clearTimeout(btn._t);
    btn._t = setTimeout(() => {
      btn.classList.remove('is-added');
      if (label) label.textContent = 'Add to cart';
      btn.setAttribute('aria-label', `Add ${k.name} to cart`);
    }, 1800);
    toast({ title: 'Added to cart', text: k.name, image: k.img, action: { label: 'View cart', href: '/cart' } });
  });
}

/* ---------- nav: hide on scroll down, show on scroll up ---------- */
function initNav() {
  const nav = $('[data-nav]');
  if (!nav) return;
  let lastY = window.scrollY;
  let ticking = false;
  window.addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      const y = window.scrollY;
      const menuOpen = $('[data-menu]')?.classList.contains('is-open');
      const hide = y > 240 && y > lastY + 4 && !menuOpen && !nav.contains(document.activeElement);
      if (hide) nav.classList.add('is-hidden');
      else if (y < lastY - 4 || y < 240) nav.classList.remove('is-hidden');
      lastY = y;
      ticking = false;
    });
  }, { passive: true });
  nav.addEventListener('focusin', () => nav.classList.remove('is-hidden'));
}

/* ---------- mobile menu ---------- */
function initMenu() {
  const btn = $('[data-menu-toggle]');
  const menu = $('[data-menu]');
  if (!btn || !menu) return;
  menu.inert = true;
  const set = (open) => {
    menu.classList.toggle('is-open', open);
    menu.inert = !open;
    btn.setAttribute('aria-expanded', String(open));
    btn.setAttribute('aria-label', open ? 'Close menu' : 'Menu');
    btn.innerHTML = icon(open ? 'close' : 'menu');
  };
  btn.addEventListener('click', () => set(!menu.classList.contains('is-open')));
  menu.addEventListener('click', (e) => { if (e.target.closest('a, [data-search-open]')) set(false); });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && menu.classList.contains('is-open')) { set(false); btn.focus(); }
  });
  window.matchMedia('(min-width: 1000px)').addEventListener('change', (m) => { if (m.matches) set(false); });
}

/* ---------- account popover ---------- */
function initAccount() {
  const btn = $('[data-account]');
  const pop = btn && document.getElementById(btn.getAttribute('aria-controls'));
  if (!pop) return;
  const set = (open) => { pop.classList.toggle('is-open', open); btn.setAttribute('aria-expanded', String(open)); };
  btn.addEventListener('click', (e) => { e.stopPropagation(); set(!pop.classList.contains('is-open')); });
  document.addEventListener('click', (e) => { if (!pop.contains(e.target)) set(false); });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && pop.classList.contains('is-open')) { set(false); btn.focus(); }
  });
}

/* ---------- search ---------- */
function initSearch() {
  const root = $('[data-search]');
  if (!root) return;
  const input = $('[data-search-input]', root);
  const results = $('[data-search-results]', root);
  let opener = null;
  let active = -1;

  const index = [
    ...KITS.map((k) => ({ group: 'Kits', title: k.name, sub: `${k.fieldName} · ${store.cap(k.level)} · ${k.soldout ? 'Sold out' : store.money(k.price)}`, href: `/kits/${k.slug}`, img: k.img, text: `${k.name} ${k.fieldName} ${k.desc} ${k.level}` })),
    ...WORKSHOPS.map((w) => {
      const next = w.sessions.find((s) => s.seats > 0);
      return { group: 'Workshops', title: w.title, sub: next ? `Next: ${next.short} · ${store.money(w.price)}` : 'Fully booked', href: `/workshops/${w.slug}`, img: w.img, text: `${w.title} ${FIELDS[w.field]} workshop class` };
    }),
    ...GUIDES.map((g) => ({ group: 'Guides', title: g.title, sub: `${FIELDS[g.field]} · ${pluralize(g.lessons, 'lesson')}`, href: `/learn/${g.slug}`, img: g.img, text: `${g.title} ${FIELDS[g.field]} guide lesson learn` })),
  ];
  const suggestions = () => [
    index.find((i) => i.href === '/kits/countertop-grow-kit'),
    index.find((i) => i.href === '/kits/oyster-mushroom-lab'),
    index.find((i) => i.group === 'Workshops'),
    index.find((i) => i.group === 'Guides'),
  ].filter(Boolean);

  const render = () => {
    const q = input.value.trim().toLowerCase();
    const terms = q.split(/\s+/).filter(Boolean);
    const found = q ? index.filter((i) => terms.every((t) => i.text.toLowerCase().includes(t))) : suggestions();
    active = found.length ? 0 : -1;
    if (!found.length) {
      results.innerHTML = `<p class="search__empty">Nothing matches “${esc(input.value.trim())}”. Try “basil”, “mushroom” or “protein”.</p>`;
      input.removeAttribute('aria-activedescendant');
      return;
    }
    const groups = q ? ['Kits', 'Workshops', 'Guides'] : ['Suggested'];
    let html = '';
    let n = 0;
    for (const g of groups) {
      const items = q ? found.filter((i) => i.group === g) : found;
      if (!items.length) continue;
      html += `<p class="search__group eyebrow" role="presentation">${g}</p>`;
      for (const i of items) {
        html += `<a class="search__item" id="sr-${n}" role="option" aria-selected="${n === 0}" href="${i.href}"><img src="${img(i.img)}" alt="" width="44" height="54" loading="lazy"><span><strong>${esc(i.title)}</strong><span class="meta">${esc(i.sub)}</span></span></a>`;
        n += 1;
      }
    }
    results.innerHTML = html;
    input.setAttribute('aria-activedescendant', 'sr-0');
  };
  const move = (d) => {
    const items = $$('.search__item', results);
    if (!items.length) return;
    active = (active + d + items.length) % items.length;
    items.forEach((el, i) => el.setAttribute('aria-selected', String(i === active)));
    items[active].scrollIntoView({ block: 'nearest' });
    input.setAttribute('aria-activedescendant', items[active].id);
  };
  const open = (from) => {
    opener = from || document.activeElement;
    root.hidden = false;
    document.body.style.overflow = 'hidden';
    requestAnimationFrame(() => root.classList.add('is-open'));
    input.value = '';
    render();
    setTimeout(() => input.focus(), 30);
  };
  const close = () => {
    root.classList.remove('is-open');
    document.body.style.overflow = '';
    setTimeout(() => { if (!root.classList.contains('is-open')) root.hidden = true; }, 260);
    if (opener && opener.focus) opener.focus();
  };

  document.addEventListener('click', (e) => {
    const t = e.target.closest('[data-search-open]');
    if (t) { e.preventDefault(); open(t); }
  });
  root.addEventListener('click', (e) => { if (e.target === root) close(); });
  input.addEventListener('input', render);
  root.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { e.preventDefault(); close(); }
    else if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
    else if (e.key === 'Enter' && document.activeElement === input) {
      const el = $$('.search__item', results)[active];
      if (el) { e.preventDefault(); window.location.href = el.getAttribute('href'); }
    } else trapFocus(root, e);
  });
  document.addEventListener('keydown', (e) => {
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName) || document.activeElement?.isContentEditable;
    if (!root.hidden) return;
    if ((e.key === '/' && !typing) || (e.key.toLowerCase() === 'k' && (e.metaKey || e.ctrlKey))) { e.preventDefault(); open(); }
  });
}

/* ---------- newsletter (nothing is sent) ---------- */
function initNewsletter() {
  for (const form of $$('[data-newsletter]')) {
    const msg = $('[data-newsletter-msg]', form);
    const input = form.querySelector('input');
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      if (!input.checkValidity()) {
        msg.textContent = 'Enter an email like name@example.com.';
        input.setAttribute('aria-invalid', 'true');
        input.focus();
        return;
      }
      input.removeAttribute('aria-invalid');
      msg.textContent = 'You’re on the list. (Demo only: your email isn’t stored or sent.)';
      form.reset();
    });
  }
}

/* ---------- hero: the one orchestrated reveal ---------- */
function initReveal() {
  const els = $$('[data-reveal]');
  if (!els.length) return;
  if (reducedMotion()) { els.forEach((el) => el.classList.add('is-in')); return; }
  const rises = els.filter((el) => el.classList.contains('rise'));
  const tiles = els.filter((el) => el.classList.contains('grow'));
  rises.forEach((el, i) => { el.style.transitionDelay = `${i * 70}ms`; });
  const go = () => requestAnimationFrame(() => requestAnimationFrame(() => {
    rises.forEach((el) => el.classList.add('is-in'));
    tiles.forEach((el, i) => {
      el.style.transitionDelay = `${180 + i * 130}ms`;
      const im = el.querySelector('img');
      if (im) im.style.transitionDelay = `${180 + i * 130}ms`;
      el.classList.add('is-in');
    });
  }));
  const first = tiles.map((t) => t.querySelector('img')).filter(Boolean).slice(0, 2);
  Promise.race([
    Promise.all(first.map((im) => (im.complete ? Promise.resolve() : im.decode().catch(() => {})))),
    new Promise((r) => setTimeout(r, 700)),
  ]).then(go);
}

/* ---------- guide progress on cards ---------- */
function paintProgress(root = document) {
  for (const el of $$('[data-guide][data-lessons]', root)) {
    const total = Number(el.dataset.lessons);
    const done = store.progress(el.dataset.guide).length;
    const bar = $('.progress__bar span', el);
    const label = $('[data-progress-label]', el);
    if (bar) bar.style.width = `${Math.round((done / total) * 100)}%`;
    if (label) label.textContent = done === 0 ? (el.classList.contains('guide-card') ? 'Not started' : `0 of ${total}`) : done >= total ? 'Complete' : `${done} of ${total} lessons`;
  }
}

/* ---------- boot ---------- */
initBanner();
initNav();
initMenu();
initAccount();
initSearch();
initNewsletter();
initQuickAdd();
initReveal();
syncCart();
paintProgress();
window.addEventListener('cart:change', syncCart);
window.addEventListener('progress:change', () => paintProgress());
window.addEventListener('pageshow', (e) => { if (e.persisted) { syncCart(); paintProgress(); } });

const page = document.body.dataset.page;
if (PAGES.includes(page)) {
  import(`./pages/${page}.js`).catch((err) => console.error(`[fft] ${page} failed to load`, err));
}
