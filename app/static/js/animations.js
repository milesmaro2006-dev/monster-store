// Scroll reveal animation - IntersectionObserver
document.addEventListener('DOMContentLoaded', () => {
  const reveals = document.querySelectorAll('.reveal');

  if ('IntersectionObserver' in window && reveals.length > 0) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px',
    });

    reveals.forEach(el => observer.observe(el));
  } else {
    // Fallback للمتصفحات القديمة
    reveals.forEach(el => el.classList.add('visible'));
  }
});