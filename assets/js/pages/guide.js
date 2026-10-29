// Guide: mark lessons as done; progress is kept in this browser.
import * as store from '../store.js';
import { $, $$, toast } from '../ui.js';

const article = $('.article[data-guide]');
if (article) {
  const slug = article.dataset.guide;
  const total = Number(article.dataset.lessons);
  const boxes = $$('[data-done]', article);
  const paint = () => {
    const done = new Set(store.progress(slug));
    boxes.forEach((b) => {
      const i = Number(b.dataset.done);
      b.checked = done.has(i);
      b.closest('.lesson').classList.toggle('is-done', done.has(i));
    });
    window.dispatchEvent(new CustomEvent('progress:change'));
  };
  for (const box of boxes) {
    box.addEventListener('change', () => {
      const list = store.setLesson(slug, Number(box.dataset.done), box.checked);
      paint();
      if (box.checked && list.length === total) {
        toast({ title: 'Guide complete', text: 'Nice work. Your next harvest is waiting.', action: { label: 'More guides', href: '/learn' } });
      }
    });
  }
  paint();
}
