// Cart: lines, steppers, remove with undo, free-shipping progress, saved for later.
import * as store from '../store.js';
import { $, $$, esc, icon, img, toast, pluralize } from '../ui.js';

const root = $('[data-cart-root]');
const eyebrow = $('[data-cart-eyebrow]');

function lineHTML(i) {
  const unitNote = i.qty > 1 ? `<span class="meta">${store.money(i.unit)} each</span>` : '';
  return `<article class="line" data-line="${esc(i.id)}">
    <a class="line__img" href="${i.href}" tabindex="-1" aria-hidden="true"><img src="${img(i.img)}" alt="" width="112" height="140" loading="lazy"></a>
    <div class="line__body">
      <p class="eyebrow">${i.kind === 'kit' ? 'Kit' : 'Workshop'}</p>
      <h2 class="line__name"><a href="${i.href}">${esc(i.name)}</a></h2>
      <p class="meta">${esc(i.detail)}</p>
      <div class="line__actions">
        <div class="qty qty--sm" data-line-qty role="group" aria-label="${i.label} for ${esc(i.name)}">
          <button type="button" data-step="-1" aria-label="Decrease ${i.label.toLowerCase()}"${i.qty <= 1 ? ' disabled' : ''}>${icon('minus', 'icon icon--sm')}</button>
          <output aria-live="polite">${i.qty}</output>
          <button type="button" data-step="1" aria-label="Increase ${i.label.toLowerCase()}"${i.qty >= i.max ? ' disabled' : ''}>${icon('plus', 'icon icon--sm')}</button>
        </div>
        <button class="btn btn--link" type="button" data-remove-line style="font-size:var(--small)">Remove</button>
      </div>
      ${i.kind === 'ws' && i.qty >= i.max ? `<p class="meta">That’s every seat left for this session.</p>` : ''}
    </div>
    <div class="line__price"><span class="price">${store.money(i.unit * i.qty)}</span>${unitNote}</div>
  </article>`;
}

function savedHTML() {
  const list = store.saved();
  if (!list.length) return '';
  return `<section class="saved" id="saved" aria-labelledby="saved-title">
    <div class="section-head" style="margin-bottom:0"><h2 class="h5" id="saved-title">Saved for later</h2></div>
    ${list.map((slug) => {
      const k = store.kitBySlug[slug];
      return `<article class="line" data-saved="${slug}">
        <a class="line__img" href="/kits/${slug}" tabindex="-1" aria-hidden="true"><img src="${img(k.img)}" alt="" width="64" height="80" loading="lazy"></a>
        <div class="line__body"><p class="line__name" style="font-size:1.0625rem"><a href="/kits/${slug}">${esc(k.name)}</a></p><p class="meta">${k.soldout ? 'Sold out' : store.money(k.price)}</p></div>
        <div style="display:flex;gap:var(--s-2);flex-wrap:wrap;justify-content:end">
          ${k.soldout ? '' : `<button class="btn btn--metal btn--sm" type="button" data-move="${slug}">Move to cart</button>`}
          <button class="btn btn--link" type="button" data-unsave="${slug}" style="font-size:var(--small)">Remove</button>
        </div>
      </article>`;
    }).join('')}
  </section>`;
}

function summaryHTML(t) {
  let ship = '';
  if (t.hasKits) {
    const left = store.FREE_SHIP - t.kitSub;
    const pct = Math.min(100, Math.round((t.kitSub / store.FREE_SHIP) * 100));
    ship = `<div class="free-ship">
      <span>${left > 0 ? `Add ${store.money(left)} more in kits for free shipping` : 'Your kits ship free'}</span>
      <div class="free-ship__bar"><span style="width:${pct}%"></span></div>
    </div>`;
  }
  return `<aside class="summary" aria-labelledby="sum-title">
    <h2 class="h5" id="sum-title">Order summary</h2>
    ${ship}
    <dl class="summary__rows">
      <div><dt>Subtotal · ${pluralize(t.items.reduce((n, i) => n + i.qty, 0), 'item')}</dt><dd>${store.money(t.subtotal)}</dd></div>
      <div><dt>Shipping</dt><dd>${t.hasKits ? (t.shipping === 0 ? 'Free' : `${store.money(t.shipping)} standard`) : 'None needed'}</dd></div>
      <div><dt>Estimated tax</dt><dd>${store.money(t.tax)}</dd></div>
    </dl>
    <div class="summary__total"><span class="ink" style="font-weight:500">Total</span><span class="price">${store.money(t.total)}</span></div>
    <a class="btn btn--solid btn--lg btn--block" href="/checkout">Check out</a>
    <p class="summary__note">${icon('lock', 'icon icon--sm')} Demo checkout: no payment is taken and nothing ships.</p>
    ${t.items.some((i) => i.kind === 'ws') ? '<p class="summary__note">Workshop seats can be cancelled for free up to 48 hours before.</p>' : ''}
  </aside>`;
}

function render() {
  const t = store.totals('standard');
  const n = t.items.reduce((s, i) => s + i.qty, 0);
  eyebrow.textContent = n ? `Cart · ${pluralize(n, 'item')}` : 'Cart';
  if (!t.items.length) {
    root.innerHTML = `<div class="empty" style="grid-column:1/-1">
      <h2 class="h4">Your cart is empty</h2>
      <p class="measure">Not sure where to start? Our beginner kits fit on a countertop and harvest in about two weeks.</p>
      <div style="display:flex;gap:var(--s-3);flex-wrap:wrap"><a class="btn btn--solid" href="/shop?level=beginner">See beginner kits</a><a class="btn btn--bone" href="/workshops">Book a workshop</a></div>
      ${savedHTML()}
    </div>`;
    return;
  }
  root.innerHTML = `<div><div class="lines">${t.items.map(lineHTML).join('')}</div>${savedHTML()}</div>${summaryHTML(t)}`;
}

root.addEventListener('click', (e) => {
  const lineEl = e.target.closest('[data-line]');
  const step = e.target.closest('[data-step]');
  if (step && lineEl) {
    const id = lineEl.dataset.line;
    const line = store.lines().find((l) => l.id === id);
    if (line) {
      store.setQty(id, line.qty + Number(step.dataset.step));
      requestAnimationFrame(() => $(`[data-line="${CSS.escape(id)}"] [data-step="${step.dataset.step}"]`)?.focus());
    }
    return;
  }
  if (e.target.closest('[data-remove-line]') && lineEl) {
    const id = lineEl.dataset.line;
    const name = $('.line__name', lineEl).textContent;
    lineEl.classList.add('is-leaving');
    setTimeout(() => {
      const removed = store.remove(id);
      if (!removed) return;
      toast({ title: 'Removed from cart', text: name, action: { label: 'Undo', onClick: () => store.restore(removed) }, timeout: 6000 });
      ($('[data-remove-line]') || $('h1')).focus?.();
    }, 240);
    return;
  }
  const move = e.target.closest('[data-move]');
  if (move) {
    store.addKit(move.dataset.move, 1);
    store.toggleSaved(move.dataset.move, false);
    toast({ title: 'Moved to cart', text: store.kitBySlug[move.dataset.move].name, image: store.kitBySlug[move.dataset.move].img });
    return;
  }
  const unsave = e.target.closest('[data-unsave]');
  if (unsave) store.toggleSaved(unsave.dataset.unsave, false);
});

window.addEventListener('cart:change', render);
render();
if (location.hash === '#saved') requestAnimationFrame(() => document.getElementById('saved')?.scrollIntoView());
