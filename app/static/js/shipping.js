(function () {
  'use strict';
  const language = document.documentElement.lang;
  const currency = language === 'en' ? 'EGP' : 'جنيه';
  const requestError = language === 'en'
    ? 'Could not update the delivery method. Please try again.'
    : 'تعذر تحديث طريقة التوصيل. حاول مرة أخرى.';

  function cents(value) {
    const [whole = '0', fraction = ''] = String(value || '0').split('.');
    return (Number.parseInt(whole, 10) || 0) * 100
      + Number.parseInt((fraction + '00').slice(0, 2), 10);
  }

  function money(amount) {
    const whole = Math.floor(amount / 100);
    const fraction = String(amount % 100).padStart(2, '0');
    return `${whole}.${fraction} ${currency}`;
  }

  function feeFor(method, summary) {
    return cents(method === 'metro_pickup' ? summary?.dataset.metroFee : summary?.dataset.homeFee);
  }

  function updateSummary(method, summary, authoritative) {
    if (!summary) return;
    const feeNode = summary.querySelector('[data-shipping-fee]');
    const totalNode = summary.querySelector('[data-total]');
    const subtotalNode = summary.querySelector('[data-subtotal]');
    const fee = authoritative ? cents(authoritative.delivery_fee) : feeFor(method, summary);
    const subtotal = subtotalNode ? cents(subtotalNode.dataset.subtotal) : 0;
    const total = authoritative ? cents(authoritative.total) : subtotal + fee;
    if (feeNode) feeNode.textContent = money(fee);
    if (totalNode) totalNode.textContent = money(total);
  }

  const cartForm = document.querySelector('[data-shipping-form]');
  const cartSummary = document.querySelector('[data-cart-summary][data-shipping-url]');
  let confirmedMethod = cartForm?.querySelector('[data-shipping-choice]:checked')?.value || 'home_delivery';
  let requestQueue = Promise.resolve();
  let requestSequence = 0;

  function saveCartMethod(method) {
    if (!cartForm || !cartSummary) return;
    const sequence = ++requestSequence;
    const formData = new FormData(cartForm);
    formData.set('delivery_method', method);
    const status = cartSummary.querySelector('[data-shipping-status]');
    if (status) status.textContent = '';
    updateSummary(method, cartSummary);

    requestQueue = requestQueue.then(async () => {
      const response = await fetch(cartSummary.dataset.shippingUrl, {
        method: 'POST', body: formData, credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error('Shipping update failed');
      confirmedMethod = method;
      if (sequence === requestSequence) updateSummary(method, cartSummary, result);
    }).catch(() => {
      if (sequence !== requestSequence) return;
      const previous = cartForm.querySelector(`input[value="${confirmedMethod}"]`);
      if (previous) previous.checked = true;
      updateSummary(confirmedMethod, cartSummary);
      if (status) status.textContent = requestError;
    });
  }

  cartForm?.querySelectorAll('[data-shipping-choice]').forEach((radio) => {
    radio.addEventListener('change', () => saveCartMethod(radio.value));
  });

  const checkoutForm = document.querySelector('[data-checkout-form]');
  if (!checkoutForm) return;
  const checkoutSummary = document.querySelector('.order-preview[data-cart-summary]');
  const radios = checkoutForm.querySelectorAll('input[name="delivery_method"]');
  const wrappers = checkoutForm.querySelectorAll('[data-delivery-fields]');

  function applyCheckoutMethod() {
    const method = checkoutForm.querySelector('input[name="delivery_method"]:checked')?.value || 'home_delivery';
    wrappers.forEach((wrapper) => {
      const active = wrapper.dataset.deliveryFields === method;
      wrapper.hidden = false;
      wrapper.inert = !active;
      wrapper.setAttribute('aria-hidden', String(!active));
      wrapper.classList.toggle('is-active', active);
      wrapper.querySelectorAll('input, select, textarea').forEach((field) => {
        field.disabled = !active;
        field.required = active;
      });
    });
    updateSummary(method, checkoutSummary);
  }

  radios.forEach((radio) => radio.addEventListener('change', applyCheckoutMethod));
  applyCheckoutMethod();
})();
