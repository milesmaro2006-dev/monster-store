// Dark/light theme
// Dark/Light theme toggle
(function () {
  const saved = localStorage.getItem('theme') || 'dark';
  if (saved === 'light') document.body.classList.add('theme-light');
})();