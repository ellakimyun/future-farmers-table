// Learn: filter guides by field. Progress bars are painted by main.js.
import { $$, reducedMotion } from '../ui.js';

const chips = $$('[data-guide-filter]');
const cards = $$('[data-guide-grid] .guide-card');
for (const chip of chips) {
  chip.setAttribute('aria-pressed', String(chip.classList.contains('is-active')));
  chip.addEventListener('click', () => {
    const f = chip.dataset.guideFilter;
    chips.forEach((c) => { const on = c === chip; c.classList.toggle('is-active', on); c.setAttribute('aria-pressed', String(on)); });
    for (const card of cards) {
      const show = !f || card.dataset.field === f;
      card.hidden = !show;
      if (show && !reducedMotion()) { card.style.animation = 'none'; void card.offsetWidth; card.style.animation = 'settle 360ms var(--ease) both'; }
    }
  });
}
