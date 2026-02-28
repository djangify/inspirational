/**
 * Accordion functionality for profile sections
 */
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

  // Auto-expand saved prompts only if there are prompts
  const savedPanel = document.getElementById("saved-prompts-content");

  if (savedPanel) {
    const promptItems = savedPanel.querySelectorAll(".border.bg-white");
    if (promptItems.length > 0) {
      savedPanel.classList.remove("hidden");

      const icon = document.querySelector('[data-target="saved-prompts-content"] .accordion-icon');
      if (icon) icon.classList.add("rotate-180");
    }
  }

});