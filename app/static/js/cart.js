document.addEventListener('submit', async (e) => {
  const form = e.target.closest('.add-form');
  if (!form) return;
  e.preventDefault();
  const data = new FormData(form);
  try {
    const res = await fetch(form.action, {
      method: 'POST',
      body: data,
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    });
    const json = await res.json();
    const countEl = document.querySelector('.cart-count');
    if (countEl && json.count !== undefined) countEl.textContent = json.count;
    showToast(json.message || (json.ok ? 'تمت الإضافة.' : 'تعذر الإضافة.'), json.ok ? 'success' : 'danger');
  } catch (_err) {
    form.submit();
  }
});

function showToast(message, category) {
  let wrap = document.querySelector('.flash-wrap');
  if (!wrap) {
    wrap = document.createElement('div');
    wrap.className = 'flash-wrap';
    document.body.appendChild(wrap);
  }
  const el = document.createElement('div');
  el.className = 'flash flash-' + (category || 'info');
  el.textContent = message;
  wrap.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; }, 3500);
  setTimeout(() => { el.remove(); }, 4000);
}


document.addEventListener('submit', (event) => {
  const form = event.target.closest('[data-quantity-form]');
  if (!form) return;
  if (form.dataset.submitting === 'true') {
    event.preventDefault();
    return;
  }
  form.dataset.submitting = 'true';
  form.setAttribute('aria-busy', 'true');
  form.classList.add('is-pending');
});
