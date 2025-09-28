// For prompt and writing api categories - see shop-filter.js for shop categories
document.addEventListener("DOMContentLoaded", function () {
  // Populate Writing Style dropdown
  fetch("/prompt/api/writing-styles/")
    .then((response) => response.json())
    .then((data) => {
      const styleSelect = document.getElementById("writingStyle");
      if (!styleSelect) return;

      styleSelect.querySelectorAll("option:not(:first-child)").forEach((opt) => opt.remove());

      data.forEach((style) => {
        const option = document.createElement("option");
        option.value = style.name;
        option.textContent = style.name;
        styleSelect.appendChild(option);
      });
    })
    .catch((error) => console.error("Failed to load writing styles:", error));

  // Populate Category dropdown
  fetch("/prompt/api/categories/")
    .then((response) => response.json())
    .then((data) => {
      const categorySelect = document.getElementById("category");
      if (!categorySelect) return;

      categorySelect.querySelectorAll("option:not(:first-child)").forEach((opt) => opt.remove());

      const categories = data.results || data;
      categories.forEach((cat) => {
        const option = document.createElement("option");
        option.value = cat.slug;
        option.textContent = cat.name;
        categorySelect.appendChild(option);
      });
    })
    .catch((error) => console.error("Failed to load categories:", error));
});
