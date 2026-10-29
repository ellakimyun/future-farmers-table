// Workshop detail: pick a session, choose seats, book into the cart.
import * as store from '../store.js';
import { $, $$, toast, confirmFlow, stepper } from '../ui.js';

const panel = $('[data-booking]');
if (panel) {
  const price = Number(panel.dataset.price);
  const radios = $$('input[name="session"]', panel);
  const total = $('[data-ws-total]', panel);
  const book = $('[data-book]', panel);
  const label = $('[data-book-label]', panel);

  const selected = () => radios.find((r) => r.checked);
  const room = (r) => Math.max(0, Math.min(6, Number(r.dataset.seats)) - store.seatsInCart(r.value));

  const seats = stepper($('[data-seat-qty]', panel), { min: 1, max: 6, onChange: () => paint() });

  const bookLabel = () => {
    const r = selected();
    if (!r) return 'Choose a date';
    if (room(r) === 0) return store.seatsInCart(r.value) ? 'All open seats are in your cart' : 'Fully booked';
    return `Book ${seats.value} ${seats.value === 1 ? 'seat' : 'seats'}`;
  };

  function paint() {
    const r = selected();
    const left = r ? room(r) : 0;
    seats.setMax(Math.max(1, left));
    total.textContent = store.money(price * seats.value);
    book.disabled = !r || left === 0;
    if (!book.classList.contains('is-loading') && !book.classList.contains('is-confirmed')) label.textContent = bookLabel();
  }

  // Preselect from ?session= (links from the list and home page).
  const wanted = new URLSearchParams(location.search).get('session');
  const match = radios.find((r) => r.value === wanted && !r.disabled);
  if (match) match.checked = true;

  panel.addEventListener('change', (e) => { if (e.target.name === 'session') paint(); });

  book.addEventListener('click', async () => {
    const r = selected();
    if (!r) return;
    const n = seats.value;
    const started = confirmFlow(book, { loading: 'Holding seats…', done: n === 1 ? 'Seat added to cart' : `${n} seats added to cart`, idle: bookLabel });
    const added = store.addSession(r.value, n);
    if (!(await started)) return;
    const s = store.sessionById[r.value];
    toast({ title: added === 1 ? 'Seat added to cart' : `${added} seats added to cart`, text: s.label, image: s.workshop.img, action: { label: 'View cart', href: '/cart' } });
    seats.set(1, true);
    setTimeout(paint, 1900);
  });

  window.addEventListener('cart:change', paint);
  paint();
}
