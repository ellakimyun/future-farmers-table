// Cart, saved items and lesson progress. Everything lives in this browser only.
import { KITS, WORKSHOPS } from './data.js';

const KEYS = { cart: 'fft.cart.v1', saved: 'fft.saved.v1', guides: 'fft.guides.v1', banner: 'fft.banner.v1', order: 'fft.lastOrder.v1' };
const memory = {};

function read(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return key in memory ? memory[key] : fallback;
  }
}
function write(key, value) {
  memory[key] = value;
  try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* private mode: keep in memory */ }
}

export const kitBySlug = Object.fromEntries(KITS.map((k) => [k.slug, k]));
export const sessionById = {};
for (const w of WORKSHOPS) for (const s of w.sessions) sessionById[s.id] = { ...s, workshop: w };

const emit = () => window.dispatchEvent(new CustomEvent('cart:change'));
window.addEventListener('storage', (e) => { if (e.key === KEYS.cart || e.key === KEYS.saved) emit(); });

// ---------- cart ----------
export function lines() {
  const raw = read(KEYS.cart, []);
  return Array.isArray(raw) ? raw.filter((l) => (l.kind === 'kit' ? kitBySlug[l.slug] : sessionById[l.session])) : [];
}
function save(next) { write(KEYS.cart, next); emit(); }

export const KIT_MAX = 9;
export function seatMax(sessionId) {
  const s = sessionById[sessionId];
  return s ? Math.min(6, s.seats) : 0;
}

export function addKit(slug, qty = 1) {
  const k = kitBySlug[slug];
  if (!k || k.soldout) return 0;
  const all = lines();
  const line = all.find((l) => l.kind === 'kit' && l.slug === slug);
  const before = line ? line.qty : 0;
  const after = Math.min(KIT_MAX, before + qty);
  if (line) line.qty = after; else all.push({ id: `kit:${slug}`, kind: 'kit', slug, qty: after });
  save(all);
  return after - before;
}

export function addSession(sessionId, qty = 1) {
  const s = sessionById[sessionId];
  if (!s || s.seats < 1) return 0;
  const all = lines();
  const line = all.find((l) => l.kind === 'ws' && l.session === sessionId);
  const before = line ? line.qty : 0;
  const after = Math.min(seatMax(sessionId), before + qty);
  if (line) line.qty = after; else all.push({ id: `ws:${sessionId}`, kind: 'ws', session: sessionId, qty: after });
  save(all);
  return after - before;
}

export function setQty(id, qty) {
  const all = lines();
  const line = all.find((l) => l.id === id);
  if (!line) return;
  const max = line.kind === 'kit' ? KIT_MAX : seatMax(line.session);
  line.qty = Math.max(1, Math.min(max, qty));
  save(all);
}

export function remove(id) {
  const all = lines();
  const index = all.findIndex((l) => l.id === id);
  if (index < 0) return null;
  const [removed] = all.splice(index, 1);
  save(all);
  return { line: removed, index };
}

export function restore({ line, index }) {
  const all = lines();
  if (all.some((l) => l.id === line.id)) return;
  all.splice(Math.min(index, all.length), 0, line);
  save(all);
}

export function clear() { save([]); }

export function count() { return lines().reduce((n, l) => n + l.qty, 0); }
export function qtyOf(slug) {
  const l = lines().find((x) => x.kind === 'kit' && x.slug === slug);
  return l ? l.qty : 0;
}
export function seatsInCart(sessionId) {
  const l = lines().find((x) => x.kind === 'ws' && x.session === sessionId);
  return l ? l.qty : 0;
}

// Describe a line for rendering.
export function describe(l) {
  if (l.kind === 'kit') {
    const k = kitBySlug[l.slug];
    return { ...l, name: k.name, img: k.img, unit: k.price, href: `/kits/${k.slug}`, detail: `${k.fieldName} · ${cap(k.level)}`, max: KIT_MAX, label: 'Quantity' };
  }
  const s = sessionById[l.session];
  return { ...l, name: s.workshop.title, img: s.workshop.img, unit: s.workshop.price, href: `/workshops/${s.workshop.slug}?session=${encodeURIComponent(s.id)}`, detail: s.label, max: seatMax(s.id), label: 'Seats' };
}

// ---------- money ----------
export const SHIP = {
  standard: { label: 'Standard', detail: '3–5 business days', price: (sub) => (sub >= 75 ? 0 : 8) },
  express: { label: 'Express', detail: '1–2 business days', price: () => 14 },
  pickup: { label: 'Pick up at the greenhouse', detail: 'Ready tomorrow in Ann Arbor', price: () => 0 },
};
export const FREE_SHIP = 75;
export const TAX = 0.06;

export function totals(method = 'standard', list = lines()) {
  const items = list.map(describe);
  const kitSub = items.filter((i) => i.kind === 'kit').reduce((n, i) => n + i.unit * i.qty, 0);
  const wsSub = items.filter((i) => i.kind === 'ws').reduce((n, i) => n + i.unit * i.qty, 0);
  const subtotal = kitSub + wsSub;
  const hasKits = kitSub > 0;
  const shipping = hasKits ? SHIP[method].price(kitSub) : 0;
  const tax = Math.round(subtotal * TAX * 100) / 100;
  return { items, kitSub, wsSub, subtotal, hasKits, shipping, tax, total: subtotal + shipping + tax };
}

const fmt = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
export const money = (n) => fmt.format(n);
export const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);

// ---------- saved for later ----------
export function saved() { const s = read(KEYS.saved, []); return Array.isArray(s) ? s.filter((x) => kitBySlug[x]) : []; }
export function isSaved(slug) { return saved().includes(slug); }
export function toggleSaved(slug, on) {
  const list = saved().filter((s) => s !== slug);
  if (on) list.unshift(slug);
  write(KEYS.saved, list);
  emit();
  return on;
}

// ---------- lesson progress ----------
export function progress(slug) { const all = read(KEYS.guides, {}); return Array.isArray(all[slug]) ? all[slug] : []; }
export function setLesson(slug, index, done) {
  const all = read(KEYS.guides, {});
  const set = new Set(Array.isArray(all[slug]) ? all[slug] : []);
  if (done) set.add(index); else set.delete(index);
  all[slug] = [...set].sort((a, b) => a - b);
  write(KEYS.guides, all);
  return all[slug];
}

// ---------- misc ----------
export const banner = { dismissed: () => read(KEYS.banner, false), dismiss: () => write(KEYS.banner, true) };
export const lastOrder = { get: () => read(KEYS.order, null), set: (o) => write(KEYS.order, o) };
