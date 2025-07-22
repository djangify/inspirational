document.addEventListener("DOMContentLoaded", function () {
  // Category toggle logic (for visual filter grid, not dropdown)
  const filterToggle = document.querySelector('[data-collapse-toggle="categories-grid"]');
  const categoriesGrid = document.getElementById('categories-grid');
  const filterIcon = document.getElementById('filterIcon');

  if (filterToggle && categoriesGrid && filterIcon) {
    filterToggle.addEventListener('click', function () {
      categoriesGrid.classList.toggle('hidden');
      filterIcon.style.transform = categoriesGrid.classList.contains('hidden') ? 'rotate(0deg)' : 'rotate(180deg)';
    });

    function handleResize() {
      if (window.innerWidth >= 1024) {
        categoriesGrid.classList.remove('hidden');
      } else {
        categoriesGrid.classList.add('hidden');
      }
    }

    handleResize();
    window.addEventListener('resize', handleResize);
  }

  // Populate Writing Style dropdown
  fetch("/prompt/api/writing-styles/")
    .then(response => response.json())
    .then(data => {
      const styleSelect = document.getElementById("writingStyle");
      if (!styleSelect) return;

      // Remove existing dynamic options (keep only the first)
      styleSelect.querySelectorAll("option:not(:first-child)").forEach(opt => opt.remove());

      data.forEach(style => {
        const option = document.createElement("option");
        option.value = style.name;
        option.textContent = style.name;
        styleSelect.appendChild(option);
      });
    });

  // Populate Category dropdown
  fetch("/prompt/api/categories/")
    .then(response => response.json())
    .then(data => {
      const categorySelect = document.getElementById("category");
      if (!categorySelect) return;

      // Remove dynamic options except the first
      categorySelect.querySelectorAll("option:not(:first-child)").forEach(opt => opt.remove());

      const categories = data.results || data;
      categories.forEach(cat => {
        const option = document.createElement("option");
        option.value = cat.slug;
        option.textContent = cat.name;
        categorySelect.appendChild(option);
      });
    })
    .catch(error => {
      console.error("Failed to load categories:", error);
    });
});
