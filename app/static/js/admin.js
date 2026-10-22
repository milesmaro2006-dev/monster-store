// Admin JS
// Admin JS - mobile sidebar toggle
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.mobile-toggle');
  const sidebar = document.querySelector('.sidebar');
  if (toggle && sidebar) {
    const close = () => {
      sidebar.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
    };
    toggle.addEventListener('click', () => {
      const open = sidebar.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
      if (open) sidebar.querySelector('a')?.focus();
    });
    sidebar.addEventListener('click', (event) => {
      if (event.target.closest('a')) close();
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && sidebar.classList.contains('open')) {
        close();
        toggle.focus();
      }
    });
  }

  document.querySelectorAll('.order-status-form').forEach((form) => {
    const select = form.querySelector('select[name="status"]');
    const submit = form.querySelector('button[type="submit"]');
    const feedback = form.querySelector('.order-status-feedback');
    if (!select || !submit || !feedback) return;

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const previousStatus = form.dataset.currentStatus;
      const requestedStatus = select.value;
      if (requestedStatus === previousStatus) return;
      select.disabled = true;
      submit.disabled = true;
      feedback.textContent = 'جارٍ الحفظ…';
      try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
          || form.querySelector('input[name="csrf_token"]')?.value;
        if (!csrfToken) throw new Error('انتهت صلاحية التحقق الأمني. حدّث الصفحة وحاول مرة أخرى.');
        const response = await fetch(form.action, {
          method: 'POST',
          body: JSON.stringify({ status: requestedStatus }),
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
          },
          credentials: 'same-origin',
        });
        const result = await response.json();
        if (!response.ok || result.success === false) throw new Error(result.error || 'تعذر تحديث الحالة.');
        form.dataset.currentStatus = result.status;
        const deliveredCount = document.querySelector('[data-delivered-count]');
        if (deliveredCount && Number.isFinite(Number(result.delivered))) {
          deliveredCount.textContent = result.delivered;
        }
        const badge = form.closest('tr')?.querySelector('.order-status-badge');
        if (badge) {
          badge.classList.remove('status-pending', 'status-confirmed', 'status-shipped',
            'status-preparing', 'status-out_for_delivery', 'status-delivered', 'status-cancelled');
          badge.classList.add(`status-${result.status}`);
          badge.textContent = result.label;
        }
        feedback.textContent = result.message || 'تم تحديث الحالة بنجاح';
      } catch (error) {
        select.value = previousStatus;
        feedback.textContent = error.message || 'تعذر تحديث الحالة.';
      } finally {
        select.disabled = false;
        submit.disabled = false;
      }
    });
  });

  const categoryModal = document.querySelector('[data-category-modal]');
  const categoryTrigger = document.querySelector('[data-open-category-modal]');
  const categorySelect = document.querySelector('[data-category-select]');
  const categoryForm = document.querySelector('[data-category-quick-add]');
  if (categoryModal && categoryTrigger && categorySelect && categoryForm) {
    const feedback = categoryForm.querySelector('.category-modal-feedback');
    const closeCategoryModal = () => {
      categoryModal.hidden = true;
      categoryTrigger.focus();
    };
    categoryTrigger.addEventListener('click', () => {
      categoryModal.hidden = false;
      categoryForm.reset();
      if (feedback) feedback.textContent = '';
      categoryForm.querySelector('[name="name_ar"]')?.focus();
    });
    categoryModal.querySelectorAll('[data-close-category-modal]').forEach((button) => {
      button.addEventListener('click', closeCategoryModal);
    });
    categoryModal.addEventListener('click', (event) => {
      if (event.target === categoryModal) closeCategoryModal();
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && !categoryModal.hidden) closeCategoryModal();
    });
    categoryForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const submit = categoryForm.querySelector('[type="submit"]');
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content
        || categoryForm.querySelector('[name="csrf_token"]')?.value;
      if (!csrfToken) {
        if (feedback) feedback.textContent = 'انتهت صلاحية التحقق الأمني. حدّث الصفحة وحاول مرة أخرى.';
        return;
      }
      submit.disabled = true;
      if (feedback) feedback.textContent = 'جارٍ إضافة القسم…';
      try {
        const response = await fetch(categoryForm.action, {
          method: 'POST',
          credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
          body: JSON.stringify({
            name_ar: categoryForm.elements.name_ar.value,
            name_en: categoryForm.elements.name_en.value,
          }),
        });
        const result = await response.json();
        if (!response.ok || !result.success) throw new Error(result.error || 'تعذر إضافة القسم.');
        let option = Array.from(categorySelect.options).find((item) => item.value === String(result.id));
        if (!option) {
          option = new Option(result.name_en ? `${result.name_ar} — ${result.name_en}` : result.name_ar, result.id);
          categorySelect.add(option);
        }
        categorySelect.value = String(result.id);
        closeCategoryModal();
      } catch (error) {
        if (feedback) feedback.textContent = error.message || 'تعذر إضافة القسم.';
      } finally {
        submit.disabled = false;
      }
    });
  }

  document.querySelectorAll('.product-quick-form').forEach((form) => {
    form.addEventListener('submit', () => {
      const button = form.querySelector('button[type="submit"]');
      if (button) {
        button.disabled = true;
        button.textContent = 'جارٍ الحفظ…';
      }
    });
  });

  document.querySelectorAll('.inventory-update-form').forEach((form) => {
    form.addEventListener('submit', () => {
      const button = document.querySelector(`button[form="${form.id}"][type="submit"]`);
      if (button) {
        button.disabled = true;
        button.textContent = 'جارٍ الحفظ…';
      }
    });
  });

  const flavorTagWidget = document.querySelector('[data-flavor-tag-quick-add]');
  if (flavorTagWidget) {
    const tagList = document.querySelector('[data-flavor-tag-list]');
    const feedback = flavorTagWidget.querySelector('[data-tag-feedback]');
    const addButton = flavorTagWidget.querySelector('[data-add-flavor-tag]');
    const inputs = flavorTagWidget.querySelectorAll('input[name="name_ar"], input[name="name_en"]');
    const emptyMessage = document.querySelector('[data-tag-empty]');
    const count = document.querySelector('[data-tag-count]');
    const updateCount = () => {
      const selectedCount = tagList.querySelectorAll('input[name="tag_ids"]:checked').length;
      if (count) count.textContent = `${selectedCount} محدد`;
    };
    tagList.addEventListener('change', (event) => {
      if (event.target.matches('input[name="tag_ids"]')) updateCount();
    });
    updateCount();
    addButton.addEventListener('click', async () => {
      const nameAr = flavorTagWidget.querySelector('[name="name_ar"]').value.trim();
      const nameEn = flavorTagWidget.querySelector('[name="name_en"]').value.trim();
      const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content
        || document.querySelector('input[name="csrf_token"]')?.value;
      if (!nameAr) { feedback.textContent = 'أدخل اسم الوسم بالعربية أولاً.'; return; }
      if (!csrfToken) { feedback.textContent = 'انتهت صلاحية التحقق الأمني. حدّث الصفحة وحاول مرة أخرى.'; return; }
      addButton.disabled = true;
      feedback.textContent = 'جارٍ إضافة الوسم…';
      try {
        const response = await fetch(flavorTagWidget.dataset.url, {
          method: 'POST', credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
          body: JSON.stringify({ name_ar: nameAr, name_en: nameEn }),
        });
        const result = await response.json();
        if (!response.ok || !result.success) throw new Error(result.error || 'تعذر إضافة الوسم.');
        let checkbox = tagList.querySelector(`input[name="tag_ids"][value="${result.id}"]`);
        if (!checkbox) {
          const label = document.createElement('label'); label.className = 'flavor-admin-chip';
          checkbox = document.createElement('input'); checkbox.type = 'checkbox'; checkbox.name = 'tag_ids'; checkbox.value = result.id;
          const caption = document.createElement('span'); caption.append(document.createTextNode(result.name_ar));
          const translation = document.createElement('small'); translation.textContent = result.name_en; caption.append(translation);
          label.append(checkbox, caption); tagList.append(label);
        }
        checkbox.checked = true;
        if (emptyMessage) emptyMessage.hidden = true;
        inputs.forEach((input) => { input.value = ''; });
        feedback.textContent = 'تمت إضافة الوسم واختياره.';
        updateCount();
      } catch (error) {
        feedback.textContent = error.message || 'تعذر إضافة الوسم.';
      } finally { addButton.disabled = false; }
    });
  }
});
