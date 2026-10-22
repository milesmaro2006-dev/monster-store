(() => {
  const root = document.querySelector('[data-box-builder]');
  if (!root) return;
  const selected = [];
  const slots = [...root.querySelectorAll('[data-box-slot]')];
  const inputWrap = root.querySelector('[data-box-inputs]');
  const total = root.querySelector('[data-box-total]');
  const submit = root.querySelector('[data-box-submit]');
  const render = () => {
    slots.forEach((slot, index) => {
      slot.replaceChildren();
      const item = selected[index];
      if (!item) { slot.innerHTML = `<span>خانة ${index + 1}</span><span class="box-slot-empty">اختر منتجاً</span>`; return; }
      const img = document.createElement('img'); img.src = item.dataset.image; img.alt = '';
      const name = document.createElement('span'); name.textContent = item.dataset.name;
      const remove = document.createElement('button'); remove.type = 'button'; remove.textContent = '×'; remove.setAttribute('aria-label', 'إزالة');
      remove.addEventListener('click', () => { selected.splice(index, 1); render(); });
      slot.append(img, name, remove);
    });
    inputWrap.replaceChildren(...selected.map(item => { const input = document.createElement('input'); input.type = 'hidden'; input.name = 'product_ids'; input.value = item.dataset.id; return input; }));
    const amount = selected.reduce((sum, item) => sum + Number(item.dataset.price), 0);
    total.textContent = selected.length === 3 ? `${Math.max(0, amount - 40).toFixed(2)} ج.م` : '—';
    submit.disabled = selected.length !== 3;
    submit.textContent = selected.length === 3 ? 'إضافة البوكس المخصص للسلة (وفرت 40 ج.م)' : 'اختر 3 منتجات للمتابعة';
    root.querySelectorAll('[data-box-add]').forEach(button => { button.disabled = selected.length >= 3; });
  };
  root.querySelectorAll('[data-box-add]').forEach(button => button.addEventListener('click', () => {
    const card = button.closest('[data-box-product]');
    const count = selected.filter(item => item.dataset.id === card.dataset.id).length;
    if (selected.length < 3 && count < Number(card.dataset.stock)) { selected.push(card); render(); }
  }));
  render();
})();
