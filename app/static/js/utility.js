(() => {
  const tip = document.querySelector('[data-chat-tip]');
  if (!tip) return;
  const hideKey = 'id-chat-tip-dismissed';
  try { if (window.sessionStorage.getItem(hideKey) === '1') return; } catch (_) { /* storage may be disabled */ }
  const timer = window.setTimeout(() => tip.classList.add('is-visible'), 3000);
  tip.querySelector('[data-chat-tip-close]')?.addEventListener('click', () => {
    window.clearTimeout(timer);
    tip.classList.remove('is-visible');
    try { window.sessionStorage.setItem(hideKey, '1'); } catch (_) { /* dismissal still applies for this page */ }
  });
})();
