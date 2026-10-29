// Home: the fit finder answers "which kit fits my space, skill and budget?"
import { KITS } from '../data.js';
import { $, img, reducedMotion } from '../ui.js';

const root = $('[data-finder]');
if (root) {
  // Each answer is a ceiling: a bigger space still fits smaller kits, a bigger budget still allows cheaper ones.
  const RULES = {
    space: { countertop: ['countertop'], 'shelf-wall': ['countertop', 'shelf-wall'], tabletop: ['countertop', 'tabletop'] },
    level: { beginner: ['beginner'], intermediate: ['beginner', 'intermediate'] },
    price: { 'under-50': ['under-50'], '50-100': ['under-50', '50-100'], 'over-100': null, any: null },
    time: { 'under-2': ['under-2'], '2-4': ['under-2', '2-4'], any: null },
  };
  const KEY = { space: 'space', level: 'level', price: 'price_bucket', time: 'time_bucket' };
  const selects = [...root.querySelectorAll('select')];
  const count = $('[data-finder-count]', root);
  const link = $('[data-finder-link]', root);
  const thumbs = $('[data-finder-thumbs]', root);
  let shown = '';

  const update = () => {
    const allowed = Object.fromEntries(selects.map((s) => [s.name, RULES[s.name][s.value]]));
    const fits = KITS.filter((k) => Object.entries(allowed).every(([name, list]) => !list || list.includes(k[KEY[name]])));
    const n = fits.length;
    count.textContent = n === 0 ? 'No kits fit yet' : `${n} ${n === 1 ? 'kit fits' : 'kits fit'}`;

    const params = new URLSearchParams();
    for (const [name, list] of Object.entries(allowed)) if (list) params.set(name, list.join(','));
    link.href = n ? `/shop?${params}` : '/shop';
    link.textContent = n ? `Show ${n} ${n === 1 ? 'kit' : 'kits'}` : 'Browse all kits';

    const key = fits.map((k) => k.slug).join();
    if (key === shown) return;
    shown = key;
    const pick = fits.filter((k) => !k.soldout).slice(0, 4);
    thumbs.innerHTML = pick.map((k, i) => `<img src="${img(k.img)}" alt="" width="44" height="56" style="opacity:0;transform:translateY(6px);transition-delay:${i * 50}ms">`).join('')
      + (fits.length > pick.length && pick.length ? `<span class="meta">+${fits.length - pick.length}</span>` : '');
    requestAnimationFrame(() => requestAnimationFrame(() => {
      for (const im of thumbs.querySelectorAll('img')) { im.style.opacity = ''; im.style.transform = ''; }
    }));
    if (reducedMotion()) for (const im of thumbs.querySelectorAll('img')) { im.style.opacity = ''; im.style.transform = ''; }
  };

  // Keep each select only as wide as its current answer, so the sentence reads naturally.
  const sentence = root.querySelector('.finder__sentence');
  const measure = document.createElement('span');
  measure.style.cssText = 'position:absolute;left:0;top:0;visibility:hidden;white-space:pre;font:inherit;pointer-events:none';
  const size = (s) => {
    measure.textContent = s.options[s.selectedIndex].text;
    sentence.append(measure);
    s.style.width = `calc(${measure.offsetWidth}px + 1.2em)`;
    measure.remove();
  };
  const native = window.CSS?.supports?.('field-sizing', 'content');
  const sizeAll = () => { if (!native) selects.forEach(size); };
  if (!native) {
    document.fonts?.load('400 1em Syne').then(sizeAll).catch(() => {});
    document.fonts?.addEventListener?.('loadingdone', sizeAll);
    window.addEventListener('resize', sizeAll);
  }

  for (const s of selects) s.addEventListener('change', () => { if (!native) size(s); update(); });
  sizeAll();
  update();
}
