document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.flash').forEach((el) => {
    setTimeout(() => { el.style.opacity = '0'; }, 4000);
    setTimeout(() => { el.remove(); }, 4500);
  });

  const toggle = document.querySelector('[data-nav-toggle]');
  const nav = document.querySelector('[data-site-nav]');
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    nav.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => {
        nav.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  document.querySelectorAll('[data-quantity-step]').forEach((button) => {
    button.addEventListener('click', () => {
      const input = button.closest('.quantity-picker')?.querySelector('input[type="number"]');
      if (!input) return;
      const min = Number(input.min || 1);
      const max = Number(input.max || Number.MAX_SAFE_INTEGER);
      const value = Number(input.value || min);
      input.value = String(Math.min(max, Math.max(min, value + Number(button.dataset.quantityStep))));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    });
  });

  const placeholder = document.querySelector('img[data-fallback]');
  const fallbackSrc = placeholder ? placeholder.getAttribute('data-fallback') : '';
  document.querySelectorAll('img[data-fallback]').forEach((img) => {
    img.addEventListener('error', function onErr() {
      const src = img.getAttribute('data-fallback') || fallbackSrc;
      if (!src || img.dataset.fallbackApplied === '1') return;
      img.dataset.fallbackApplied = '1';
      const picture = img.closest('picture');
      if (picture) picture.querySelectorAll('source').forEach((source) => source.remove());
      img.src = src;
    });
  });

  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!reduce && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    document.querySelectorAll('.reveal').forEach((el) => io.observe(el));
  } else {
    document.querySelectorAll('.reveal').forEach((el) => el.classList.add('visible'));
  }

  document.querySelectorAll('[data-submit-once]').forEach((btn) => {
    const form = btn.closest('form');
    if (!form) return;
    form.addEventListener('submit', () => {
      btn.disabled = true;
    });
  });

  const paymentRadios = document.querySelectorAll('input[name="payment_method"]');
  const paymentPanels = document.querySelectorAll('[data-payment-info]');
  const updatePaymentPanel = () => {
    const value = document.querySelector('input[name="payment_method"]:checked')?.value;
    paymentPanels.forEach((panel) => { panel.hidden = panel.dataset.paymentInfo !== value; });
  };
  paymentRadios.forEach((radio) => radio.addEventListener('change', updatePaymentPanel));
  updatePaymentPanel();
  document.querySelectorAll('[data-copy]').forEach((button) => button.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(button.dataset.copy); }
    catch (_) {
      const field = document.createElement('textarea'); field.value = button.dataset.copy;
      field.style.position = 'fixed'; field.style.opacity = '0'; document.body.append(field);
      field.select(); document.execCommand('copy'); field.remove();
    }
    const original = button.textContent; button.textContent = 'تم النسخ';
    window.setTimeout(() => { button.textContent = original; }, 1400);
  }));
  document.querySelectorAll('.faq-trigger').forEach((button) => button.addEventListener('click', () => {
    const panel = button.nextElementSibling;
    const expanded = button.getAttribute('aria-expanded') === 'true';
    button.setAttribute('aria-expanded', String(!expanded));
    if (panel) panel.hidden = expanded;
  }));
});
