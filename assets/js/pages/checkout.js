// Checkout (demo): delivery → payment → confirmation. No data leaves the browser.
import * as store from '../store.js';
import { GUIDES } from '../data.js';
import { $, $$, esc, icon, img, wait, reducedMotion } from '../ui.js';

const root = $('[data-checkout]');
const steps = $$('[data-steps] li');
const formDelivery = $('[data-step="delivery"]');
const formPay = $('[data-step="payment"]');
const done = $('[data-step="done"]');
const summary = $('[data-co-summary]');
const body = $('[data-summary-body]');

let snapshot = store.lines();
const data = { method: 'standard' };

if (!snapshot.length) {
  root.innerHTML = `<div class="empty" style="grid-column:1/-1">
    <p class="eyebrow">Checkout</p>
    <h1 class="h3">There’s nothing to check out yet</h1>
    <p>Add a kit or a workshop seat to your cart first.</p>
    <div style="display:flex;gap:var(--s-3);flex-wrap:wrap"><a class="btn btn--solid" href="/shop">Browse kits</a><a class="btn btn--bone" href="/workshops">See workshops</a></div>
  </div>`;
} else {
  init();
}

function hasKits() { return snapshot.some((l) => l.kind === 'kit'); }

function setStep(name) {
  const order = ['delivery', 'payment', 'done'];
  const i = order.indexOf(name);
  steps.forEach((li, n) => {
    li.classList.toggle('is-current', n === i);
    li.classList.toggle('is-done', n < i);
    if (n === i) li.setAttribute('aria-current', 'step'); else li.removeAttribute('aria-current');
  });
  formDelivery.hidden = name !== 'delivery';
  formPay.hidden = name !== 'payment';
  done.hidden = name !== 'done';
  window.scrollTo({ top: 0, behavior: reducedMotion() ? 'auto' : 'smooth' });
  const heading = (name === 'delivery' ? formDelivery : name === 'payment' ? formPay : done).querySelector('h1');
  if (heading) { heading.tabIndex = -1; heading.focus({ preventScroll: true }); }
}

function renderSummary() {
  const t = store.totals(data.method, snapshot);
  $('[data-summary-total]').textContent = store.money(t.total);
  const shipLabel = !t.hasKits ? 'None needed' : t.shipping === 0 ? 'Free' : store.money(t.shipping);
  body.innerHTML = `
    <div class="mini-lines">${t.items.map((i) => `<div class="mini-line"><img src="${img(i.img)}" alt="" width="56" height="70"><div><strong>${esc(i.name)}</strong><span class="meta">${i.kind === 'ws' ? esc(i.detail) + ' · ' : ''}${i.label} ${i.qty}</span></div><span class="price" style="font-size:var(--small)">${store.money(i.unit * i.qty)}</span></div>`).join('')}</div>
    <dl class="summary__rows" style="padding-top:var(--s-4);border-top:1px solid var(--hair)">
      <div><dt>Subtotal</dt><dd>${store.money(t.subtotal)}</dd></div>
      <div><dt>Shipping${t.hasKits ? ` · ${esc(store.SHIP[data.method].label.toLowerCase())}` : ''}</dt><dd>${shipLabel}</dd></div>
      <div><dt>Tax (6%)</dt><dd>${store.money(t.tax)}</dd></div>
    </dl>
    <div class="summary__total"><span class="ink" style="font-weight:500">Total</span><span class="price">${store.money(t.total)}</span></div>`;
  const toggle = $('[data-summary-toggle]');
  toggle.querySelector('span').textContent = summary.dataset.collapsed === 'true' ? 'Show order summary' : 'Hide order summary';
  return t;
}

function shippingOptions() {
  const t = store.totals('standard', snapshot);
  const wrap = $('[data-ship-options]');
  wrap.innerHTML = Object.entries(store.SHIP).map(([key, m]) => {
    const p = m.price(t.kitSub);
    const note = key === 'standard' && t.kitSub < store.FREE_SHIP ? ` · free over ${store.money(store.FREE_SHIP)}` : '';
    return `<label class="option"><input type="radio" name="method" value="${key}"${key === data.method ? ' checked' : ''}><span class="session__dot"></span><span><span class="option__t">${m.label}</span><span class="option__d">${m.detail}${note}</span></span><span class="option__p">${p === 0 ? 'Free' : store.money(p)}</span></label>`;
  }).join('');
  wrap.addEventListener('change', (e) => {
    if (e.target.name !== 'method') return;
    data.method = e.target.value;
    renderSummary();
  });
}

// ---------- validation ----------
const MESSAGES = {
  email: 'Enter an email like name@example.com.',
  first: 'Enter your first name.',
  last: 'Enter your last name.',
  street: 'Enter a street address.',
  city: 'Enter a city.',
  zip: 'Enter a 5-digit ZIP code.',
  wfirst: 'Enter the first name for the guest list.',
  wlast: 'Enter the last name for the guest list.',
};
function fieldOf(input) { return input.closest('.field'); }
function setError(input, msg) {
  const field = fieldOf(input);
  let help = field.querySelector('.field__help');
  if (!help) { help = document.createElement('p'); help.className = 'field__help'; field.append(help); }
  if (!help.dataset.original) help.dataset.original = help.textContent || '';
  if (!help.id) help.id = `${input.id}-help`;
  input.setAttribute('aria-describedby', help.id);
  if (msg) {
    field.classList.add('is-invalid');
    input.setAttribute('aria-invalid', 'true');
    help.textContent = msg;
  } else {
    field.classList.remove('is-invalid');
    input.removeAttribute('aria-invalid');
    help.textContent = help.dataset.original;
  }
}
function validate(form) {
  const inputs = $$('input[required]', form).filter((i) => !i.closest('[hidden]'));
  let first = null;
  for (const input of inputs) {
    const ok = input.checkValidity() && input.value.trim() !== '';
    setError(input, ok ? '' : MESSAGES[input.name] || 'Fill in this field.');
    if (!ok && !first) first = input;
  }
  if (first) first.focus();
  return !first;
}

function init() {
  const kits = hasKits();
  for (const b of $$('[data-ship-block]')) b.hidden = !kits;
  const ws = $('[data-ws-block]');
  ws.hidden = kits;
  for (const i of $$('input', ws)) i.required = !kits;
  if (!kits) data.method = 'pickup';
  if (kits) shippingOptions();
  formDelivery.querySelector('[type="submit"]').textContent = 'Continue to payment';
  renderSummary();

  $('[data-summary-toggle]').addEventListener('click', (e) => {
    const collapsed = summary.dataset.collapsed === 'true';
    summary.dataset.collapsed = String(!collapsed);
    e.currentTarget.setAttribute('aria-expanded', String(collapsed));
    renderSummary();
  });

  formDelivery.addEventListener('input', (e) => { if (fieldOf(e.target)?.classList.contains('is-invalid')) setError(e.target, ''); });
  formDelivery.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!validate(formDelivery)) return;
    const f = new FormData(formDelivery);
    Object.assign(data, Object.fromEntries(f.entries()));
    if (!kits) { data.first = data.wfirst; data.last = data.wlast; }
    review();
    setStep('payment');
  });

  formPay.addEventListener('click', (e) => {
    if (e.target.closest('[data-back], [data-change]')) setStep('delivery');
  });
  formPay.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = $('[data-place]');
    btn.classList.add('is-loading');
    btn.setAttribute('aria-busy', 'true');
    btn.style.minWidth = `${btn.offsetWidth}px`;
    btn.innerHTML = '<span class="spinner" aria-hidden="true"></span> Placing order…';
    await wait(reducedMotion() ? 200 : 1100);
    place();
  });
}

function review() {
  const kits = hasKits();
  const m = store.SHIP[data.method];
  const addr = kits && data.method !== 'pickup'
    ? `${esc(data.first)} ${esc(data.last)}, ${esc(data.street)}, ${esc(data.city)}, ${esc(data.state)} ${esc(data.zip)}`
    : data.method === 'pickup' && kits ? 'Pick up at The Greenhouse Studio, Ann Arbor' : 'No delivery: workshop seats only';
  $('[data-review]').innerHTML = `
    <div class="review__row"><span class="meta">Contact</span><span class="ink" style="text-align:right">${esc(data.email)}</span></div>
    <div class="review__row"><span class="meta">${kits ? 'Ship to' : 'Guest'}</span><span class="ink" style="text-align:right">${kits ? addr : `${esc(data.first)} ${esc(data.last)}`}</span></div>
    ${kits ? `<div class="review__row"><span class="meta">Method</span><span class="ink">${esc(m.label)} · ${esc(m.detail)}</span></div>` : ''}
    <button class="btn btn--link" type="button" data-change style="justify-self:start;font-size:var(--small)">Change details</button>`;
}

function place() {
  const t = renderSummary();
  const number = `FFT-${String(Math.floor(10000 + Math.random() * 90000))}`;
  const kitLines = t.items.filter((i) => i.kind === 'kit');
  const wsLines = t.items.filter((i) => i.kind === 'ws');
  const firstKit = kitLines[0] && store.kitBySlug[kitLines[0].slug];
  const guide = firstKit && GUIDES.find((g) => g.slug === firstKit.guide);
  store.lastOrder.set({ number, total: t.total, at: Date.now() });
  store.clear();

  const next = [];
  if (kitLines.length) {
    next.push([data.method === 'pickup' ? 'Pick up tomorrow' : 'Watch for your kit', data.method === 'pickup' ? 'We’ll have it ready at the greenhouse after 10am.' : `It ships in 2–3 business days by ${store.SHIP[data.method].label.toLowerCase()} delivery.`]);
    next.push(['Read lesson one while you wait', 'Your guided lessons are open now in Learn, and your progress saves as you go.']);
    next.push(['Plan your first harvest', 'Most beginner kits are ready to eat in about two weeks. If nothing sprouts in 21 days, we’ll replace it.']);
  }
  if (wsLines.length) {
    next.push(['Come to the greenhouse', `${wsLines.map((w) => `${esc(w.name)}: ${esc(w.detail)}`).join('; ')}. Wear closed shoes; everything else is provided.`]);
  }

  done.innerHTML = `
    <div class="confirm-mark">${icon('check', 'icon')}</div>
    <p class="eyebrow" style="margin-top:var(--s-6)">Order ${number}</p>
    <h1 class="h3" style="margin-top:var(--s-2)">Thank you, ${esc(data.first || 'grower')}. Your order is in.</h1>
    <p class="lead" style="margin-top:var(--s-3)">This is a demo, so nothing was charged and no email was sent to ${esc(data.email)}. Here’s what would happen next.</p>
    <ol class="next-steps">${next.map(([a, b], i) => `<li><span>${String(i + 1).padStart(2, '0')}</span><div><strong>${a}</strong><p class="small">${b}</p></div></li>`).join('')}</ol>
    <div class="co-actions" style="border-top:0;padding-top:var(--s-7);justify-content:start">
      ${guide ? `<a class="btn btn--solid" href="/learn/${guide.slug}">Start lesson one</a>` : '<a class="btn btn--solid" href="/learn">Browse grow guides</a>'}
      <a class="btn btn--bone" href="/shop">Keep shopping</a>
    </div>`;
  snapshot = [];
  setStep('done');
}

