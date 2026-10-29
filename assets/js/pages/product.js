// Product detail: gallery, quantity, add to cart, save for later, harvest timeline.
import * as store from '../store.js';
import { $, $$, toast, confirmFlow, stepper, reducedMotion } from '../ui.js';

/* gallery */
const main = $('[data-main]');
for (const thumb of $$('[data-thumb]')) {
  thumb.addEventListener('click', () => {
    const name = thumb.dataset.thumb;
    if (main.dataset.current === name) return;
    main.dataset.current = name;
    $$('[data-thumb]').forEach((t) => t.removeAttribute('aria-current'));
    thumb.setAttribute('aria-current', 'true');
    const source = thumb.querySelector('img');
    const swap = () => {
      main.srcset = source.srcset;
      main.src = source.getAttribute('src');
    };
    if (reducedMotion()) { swap(); return; }
    main.style.opacity = '0';
    setTimeout(() => {
      swap();
      const show = () => { main.style.opacity = ''; };
      if (main.complete) requestAnimationFrame(show); else main.addEventListener('load', show, { once: true });
      setTimeout(show, 600);
    }, 180);
  });
}

/* buy */
const buy = $('[data-buy]');
const qtyEl = $('[data-qty]');
const qty = qtyEl ? stepper(qtyEl, { min: 1, max: store.KIT_MAX }) : null;
if (buy) {
  const slug = buy.dataset.buy;
  const k = store.kitBySlug[slug];
  const idle = () => (store.qtyOf(slug) ? 'Add another' : 'Add to cart');
  $('[data-buy-label]').textContent = idle();
  buy.addEventListener('click', async () => {
    const want = qty ? qty.value : 1;
    if (store.qtyOf(slug) >= store.KIT_MAX) {
      toast({ title: `You already have ${store.KIT_MAX} in your cart`, text: 'That’s the most we ship in one order.', action: { label: 'View cart', href: '/cart' } });
      return;
    }
    const started = confirmFlow(buy, { idle, done: 'Added to cart' });
    const added = store.addKit(slug, want);
    if (!(await started)) return;
    toast({ title: added > 1 ? `${added} added to cart` : 'Added to cart', text: k.name, image: k.img, action: { label: 'View cart', href: '/cart' } });
    qty?.set(1, true);
  });

  const save = $('[data-save]');
  const paint = () => {
    const on = store.isSaved(slug);
    save.setAttribute('aria-pressed', String(on));
    save.textContent = on ? 'Saved for later' : 'Save for later';
  };
  save.addEventListener('click', () => {
    const on = store.toggleSaved(slug, !store.isSaved(slug));
    paint();
    toast(on
      ? { title: 'Saved for later', text: 'You’ll find it under your cart.', image: k.img, action: { label: 'View', href: '/cart#saved' } }
      : { title: 'Removed from saved', text: k.name });
  });
  paint();
}

/* sold out */
const notify = $('[data-notify]');
if (notify) {
  notify.addEventListener('click', () => {
    notify.classList.add('is-confirmed');
    notify.textContent = 'We’ll let you know';
    notify.disabled = true;
    toast({ title: 'Reminder set', text: 'Demo only: no email is collected or sent.' });
  });
}

/* harvest timeline */
const harvest = $('[data-harvest]');
if (harvest) {
  const range = $('[data-day]', harvest);
  const fill = $('[data-fill]', harvest);
  const knob = $('[data-knob]', harvest);
  const stages = $$('.stage', harvest);
  const ticks = $$('.harvest__ticks span', harvest);
  const max = Number(range.max) || 1;
  const set = (i) => {
    const pct = (i / max) * 100;
    fill.style.width = `${pct}%`;
    knob.style.left = `${pct}%`;
    stages.forEach((s, n) => { s.classList.toggle('is-active', n === i); s.classList.toggle('is-done', n < i); });
    ticks.forEach((t, n) => t.classList.toggle('is-active', n <= i));
    const st = stages[i];
    range.setAttribute('aria-valuetext', `Day ${st.dataset.stage}: ${st.querySelector('h3').textContent}`);
  };
  range.addEventListener('input', () => set(Number(range.value)));
  stages.forEach((s, i) => s.addEventListener('click', () => { range.value = i; set(i); }));
  set(0);
}
