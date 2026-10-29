// Shop: category, faceted filters with live counts, sort, URL state and the mobile sheet.
import { FIELDS } from '../data.js';
import { $, $$, esc, icon, reducedMotion } from '../ui.js';

const grid = $('[data-grid]');
const cards = $$('.kit-card', grid);
const GROUPS = { level: 'level', space: 'space', price: 'price', time: 'time' };
const LABELS = {
  level: { beginner: 'Beginner', intermediate: 'Intermediate' },
  space: { countertop: 'Countertop', 'shelf-wall': 'Shelf or wall', tabletop: 'Tabletop' },
  price: { 'under-50': 'Under $50', '50-100': '$50 – $100', 'over-100': 'Over $100' },
  time: { 'under-2': 'Under 2 weeks', '2-4': '2 – 4 weeks' },
};
const SORTS = {
  featured: (a, b) => a.dataset.order - b.dataset.order,
  'price-asc': (a, b) => a.dataset.cost - b.dataset.cost,
  'price-desc': (a, b) => b.dataset.cost - a.dataset.cost,
  harvest: (a, b) => a.dataset.days - b.dataset.days,
};
const forms = [$('[data-filters]'), $('[data-filters-m]')].filter(Boolean);
const sortSelect = $('[data-sort]');
const sheet = $('[data-sheet]');

// ---------- state ----------
const state = { cat: '', sort: 'featured', f: { level: new Set(), space: new Set(), price: new Set(), time: new Set() } };
function fromURL() {
  const p = new URLSearchParams(location.search);
  state.cat = FIELDS[p.get('category')] ? p.get('category') : '';
  state.sort = SORTS[p.get('sort')] ? p.get('sort') : 'featured';
  for (const g of Object.keys(GROUPS)) {
    state.f[g] = new Set((p.get(g) || '').split(',').filter((v) => LABELS[g][v]));
  }
}
function toURL() {
  const p = new URLSearchParams();
  if (state.cat) p.set('category', state.cat);
  for (const g of Object.keys(GROUPS)) if (state.f[g].size) p.set(g, [...state.f[g]].join(','));
  if (state.sort !== 'featured') p.set('sort', state.sort);
  const qs = p.toString();
  history.replaceState(null, '', qs ? `${location.pathname}?${qs}` : location.pathname);
}

const matches = (card, skip) => (!state.cat || card.dataset.field === state.cat)
  && Object.keys(GROUPS).every((g) => g === skip || !state.f[g].size || state.f[g].has(card.dataset[g]));

// ---------- render ----------
function render({ animate = true } = {}) {
  const visible = cards.filter((c) => matches(c));
  const n = visible.length;

  // order, then show/hide
  const sorted = [...cards].sort((a, b) => {
    const s = SORTS[state.sort](a, b);
    return s || a.dataset.order - b.dataset.order;
  });
  sorted.forEach((c) => grid.append(c));
  for (const c of cards) c.hidden = !visible.includes(c);
  if (animate && !reducedMotion()) {
    grid.classList.remove('is-updating');
    void grid.offsetWidth;
    grid.classList.add('is-updating');
  }

  // counts
  const label = `${n} of ${cards.length} kits`;
  $('[data-result-count]').textContent = label;
  $('[data-result-count-m]').textContent = `${n} ${n === 1 ? 'kit' : 'kits'}`;
  $('[data-empty]').hidden = n > 0;
  grid.hidden = n === 0;
  const apply = $('[data-sheet-apply]');
  if (apply) apply.textContent = n ? `Show ${n} ${n === 1 ? 'kit' : 'kits'}` : 'No kits match';

  // facet counts: how many kits you'd see if you also ticked this box
  for (const g of Object.keys(GROUPS)) {
    for (const v of Object.keys(LABELS[g])) {
      const c = cards.filter((card) => matches(card, g) && card.dataset[g] === v).length;
      for (const el of $$(`[data-count="${g}:${v}"]`)) {
        el.textContent = c;
        el.closest('.check').classList.toggle('is-empty', c === 0);
      }
    }
  }

  // inputs mirror state
  for (const form of forms) {
    for (const input of $$('input[type="checkbox"]', form)) input.checked = state.f[input.name].has(input.value);
  }
  sortSelect.value = state.sort;
  for (const b of $$('[data-sheet-sort]')) b.setAttribute('aria-pressed', String(b.dataset.sheetSort === state.sort));

  // categories
  for (const a of $$('[data-cat]')) {
    if (a.dataset.cat === state.cat) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current');
  }
  for (const c of $$('[data-cat-chip]')) {
    const on = c.dataset.catChip === state.cat;
    c.classList.toggle('is-active', on);
    c.setAttribute('aria-pressed', String(on));
  }
  $('[data-shop-title]').textContent = state.cat ? FIELDS[state.cat] : 'All kits';
  document.title = `${state.cat ? FIELDS[state.cat] : 'All kits'} · The Future Farmer's Table`;

  // active filter chips
  const active = Object.keys(GROUPS).flatMap((g) => [...state.f[g]].map((v) => ({ g, v })));
  const bar = $('[data-active-filters]');
  if (!active.length) {
    bar.innerHTML = `<span class="meta">${state.cat ? `Showing every ${esc(FIELDS[state.cat].toLowerCase())} kit` : 'Showing every kit'}</span>`;
  } else {
    bar.innerHTML = active.map(({ g, v }) => `<button class="chip chip--removable" type="button" data-remove="${g}:${v}" aria-label="Remove filter: ${esc(LABELS[g][v])}">${esc(LABELS[g][v])}${icon('close', 'icon')}</button>`).join('')
      + '<button class="btn btn--link" type="button" data-clear style="font-size:var(--small)">Clear all</button>';
  }
  const badge = $('[data-filter-badge]');
  if (badge) badge.textContent = active.length ? ` · ${active.length}` : '';
}

function update(opts) { toURL(); render(opts); }

// ---------- events ----------
for (const form of forms) {
  form.addEventListener('change', (e) => {
    const input = e.target;
    if (input.type !== 'checkbox') return;
    if (input.checked) state.f[input.name].add(input.value); else state.f[input.name].delete(input.value);
    update();
  });
}
sortSelect.addEventListener('change', () => { state.sort = sortSelect.value; update(); });

document.addEventListener('click', (e) => {
  const cat = e.target.closest('[data-cat], [data-cat-chip]');
  if (cat) {
    e.preventDefault();
    state.cat = cat.dataset.cat ?? cat.dataset.catChip;
    update();
    if (cat.matches('[data-cat-chip]')) cat.scrollIntoView({ inline: 'nearest', block: 'nearest', behavior: reducedMotion() ? 'auto' : 'smooth' });
    return;
  }
  const rm = e.target.closest('[data-remove]');
  if (rm) {
    const [g, v] = rm.dataset.remove.split(':');
    state.f[g].delete(v);
    update();
    ($('[data-remove]') || $('[data-result-count]')).focus?.();
    return;
  }
  if (e.target.closest('[data-clear]')) {
    for (const g of Object.keys(GROUPS)) state.f[g].clear();
    if (e.target.closest('[data-empty]')) state.cat = '';
    update();
    return;
  }
  const s = e.target.closest('[data-sheet-sort]');
  if (s) { state.sort = s.dataset.sheetSort; update(); }
});

// mobile sheet
if (sheet) {
  $('[data-sheet-open]').addEventListener('click', () => sheet.showModal());
  for (const b of $$('[data-sheet-close]', sheet)) b.addEventListener('click', () => sheet.close());
  sheet.addEventListener('click', (e) => { if (e.target === sheet) sheet.close(); });
}

window.addEventListener('popstate', () => { fromURL(); render(); });
fromURL();
render({ animate: false });
