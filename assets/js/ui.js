// Small UI helpers shared by every page.
export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
export const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;
export const wait = (ms) => new Promise((r) => setTimeout(r, ms));

export function icon(name, cls = 'icon') {
  return `<svg class="${cls}" aria-hidden="true"><use href="#i-${name}"></use></svg>`;
}

export function esc(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}

export const img = (name) => `/assets/img/${name}-sm.webp`;

// Toasts: short confirmations with an optional action.
export function toast({ title, text = '', image = '', action = null, timeout = 4200 }) {
  const region = $('[data-toasts]');
  if (!region) return null;
  while (region.children.length > 2) region.firstElementChild.remove();
  const el = document.createElement('div');
  el.className = 'toast';
  el.setAttribute('role', 'status');
  const lead = image ? `<img src="${img(image)}" alt="" width="40" height="50">` : `<span class="toast__ic">${icon('check', 'icon icon--sm')}</span>`;
  let act = '';
  if (action && action.href) act = `<a href="${action.href}">${esc(action.label)}</a>`;
  else if (action) act = `<button type="button">${esc(action.label)}</button>`;
  el.innerHTML = `${lead}<div><strong>${esc(title)}</strong>${text ? `<span>${esc(text)}</span>` : ''}</div>${act}`;
  region.append(el);

  let timer;
  const leave = () => {
    clearTimeout(timer);
    if (el.classList.contains('is-leaving')) return;
    el.classList.add('is-leaving');
    el.addEventListener('animationend', () => el.remove(), { once: true });
    setTimeout(() => el.remove(), 400);
  };
  const arm = () => { clearTimeout(timer); timer = setTimeout(leave, timeout); };
  el.addEventListener('mouseenter', () => clearTimeout(timer));
  el.addEventListener('mouseleave', arm);
  el.addEventListener('focusin', () => clearTimeout(timer));
  el.addEventListener('focusout', arm);
  if (action && action.onClick) {
    el.querySelector('button').addEventListener('click', () => { action.onClick(); leave(); });
  }
  arm();
  return el;
}

// Button flow from the design system: Default → Loading → Confirmed → Default.
export async function confirmFlow(btn, { loading = 'Adding…', done = 'Added to cart', idle, hold = 1800, delay = 550 } = {}) {
  if (btn.classList.contains('is-loading')) return false;
  const label = btn.querySelector('[data-buy-label], [data-book-label]') || btn;
  const original = idle ?? label.textContent;
  const width = btn.offsetWidth;
  btn.style.minWidth = `${width}px`;
  btn.classList.add('is-loading');
  btn.setAttribute('aria-busy', 'true');
  label.innerHTML = `<span class="spinner" aria-hidden="true"></span> ${esc(loading)}`;
  await wait(reducedMotion() ? 150 : delay);
  btn.classList.remove('is-loading');
  btn.removeAttribute('aria-busy');
  btn.classList.add('is-confirmed');
  label.innerHTML = `${icon('check', 'icon icon--sm')} ${esc(done)}`;
  setTimeout(() => {
    btn.classList.remove('is-confirmed');
    const current = typeof idle === 'function' ? idle() : original;
    label.textContent = current;
    btn.style.minWidth = '';
  }, hold);
  return true;
}

// Steppers (.qty) with min/max.
export function stepper(root, { min = 1, max = 9, value = 1, onChange } = {}) {
  const out = root.querySelector('output, input');
  const [dec, inc] = root.querySelectorAll('button');
  const state = { value, min, max };
  const render = () => {
    out.value = state.value;
    out.textContent = state.value;
    dec.disabled = state.value <= state.min;
    inc.disabled = state.value >= state.max;
  };
  const set = (v, silent) => {
    const next = Math.max(state.min, Math.min(state.max, v));
    const changed = next !== state.value;
    state.value = next;
    render();
    if (changed && !silent && onChange) onChange(next);
  };
  dec.addEventListener('click', () => set(state.value - 1));
  inc.addEventListener('click', () => set(state.value + 1));
  render();
  return {
    get value() { return state.value; },
    set,
    setMax(m) { state.max = Math.max(state.min, m); set(Math.min(state.value, state.max), true); render(); },
  };
}

// Focus trap for dialogs that aren't native <dialog>.
export function trapFocus(container, e) {
  if (e.key !== 'Tab') return;
  const items = $$('a[href], button:not([disabled]), input:not([disabled]), select, [tabindex]:not([tabindex="-1"])', container)
    .filter((el) => el.offsetParent !== null);
  if (!items.length) return;
  const first = items[0];
  const last = items[items.length - 1];
  if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
  else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
}

export function pluralize(n, one, many = `${one}s`) { return `${n} ${n === 1 ? one : many}`; }
