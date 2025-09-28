document.addEventListener("DOMContentLoaded", function () {
  const filterToggle = document.querySelector('[data-collapse-toggle="categories-grid"]');
  const categoriesGrid = document.getElementById("categories-grid");
  const filterIcon = document.getElementById("filterIcon");

  if (filterToggle && categoriesGrid && filterIcon) {
    filterToggle.addEventListener("click", function () {
      categoriesGrid.classList.toggle("hidden");
      filterIcon.style.transform = categoriesGrid.classList.contains("hidden")
        ? "rotate(0deg)"
        : "rotate(180deg)";
    });

    function handleResize() {
      if (window.innerWidth >= 1024) {
        categoriesGrid.classList.remove("hidden");
      } else {
        categoriesGrid.classList.add("hidden");
      }
    }

    handleResize();
    window.addEventListener("resize", handleResize);
  }
});
