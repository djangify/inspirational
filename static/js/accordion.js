/**
 * Accordion functionality for profile sections
 */
document.addEventListener('DOMContentLoaded', function () {
  // Get all accordion headers
  const accordionHeaders = document.querySelectorAll('.accordion-header');

  // Add click event listener to each header
  accordionHeaders.forEach(header => {
    header.addEventListener('click', function () {
      // Get the target content element
      const targetId = this.getAttribute('data-target');
      const content = document.getElementById(targetId);

      if (!content) return; // Safety check in case element isn't found

      // Toggle the content visibility
      content.classList.toggle('hidden');

      // Toggle the icon rotation for the arrow
      const icon = this.querySelector('.accordion-icon');
      if (icon) {
        icon.classList.toggle('rotate-180');
      }
    });
  });

  document.addEventListener('DOMContentLoaded', function () {
    const accordionHeaders = document.querySelectorAll('.accordion-header');

    accordionHeaders.forEach(header => {
      header.addEventListener('click', function () {
        const targetId = this.getAttribute('data-target');
        const content = document.getElementById(targetId);
        if (!content) return;
        content.classList.toggle('hidden');
        const icon = this.querySelector('.accordion-icon');
        if (icon) {
          icon.classList.toggle('rotate-180');
        }
      });
    });

    // Auto-expand saved prompts only
    const savedPanel = document.getElementById("saved-prompts-content");
    if (savedPanel) {
      const items = savedPanel.querySelectorAll(".border.rounded-lg");
      if (items.length > 0) {
        savedPanel.classList.remove("hidden");
        const icon = document.querySelector('[data-target="saved-prompts-content"] .accordion-icon');
        if (icon) icon.classList.add("rotate-180");
      } else {
        savedPanel.classList.add("hidden");
      }
    }
  });
})
