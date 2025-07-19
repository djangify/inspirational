// favourite-products.js
document.addEventListener('DOMContentLoaded', function () {
  // Handle favourite button clicks
  document.querySelectorAll('.favourite-btn').forEach(button => {
    button.addEventListener('click', function (e) {
      e.preventDefault();

      const productSlug = this.dataset.productSlug;
      const originalText = this.innerHTML;

      this.innerHTML = '⏳ Saving...';
      this.disabled = true;

      const formData = new FormData();
      formData.append("csrfmiddlewaretoken", this.dataset.csrf);

      fetch(this.dataset.actionUrl, {
        method: "POST",
        body: formData,
        headers: {
          "X-Requested-With": "XMLHttpRequest"
        }
      })

        .then(response => response.json())
        .then(data => {
          if (data.status === 'success') {
            // Update button text based on favourite status
            if (data.is_favourite) {
              this.innerHTML = '❤️ Remove from Wish List';
              this.classList.add('bg-red-50', 'border-red-300');
            } else {
              this.innerHTML = '🤍 Add to Wish List';
              this.classList.remove('bg-red-50', 'border-red-300');
            }
          } else {
            // Restore original text on error
            this.innerHTML = originalText;
            alert('Something went wrong. Please try again.');
          }
        })
        .catch(error => {
          console.error('Error:', error);
          this.innerHTML = originalText;
          alert('Something went wrong. Please try again.');
        })
        .finally(() => {
          this.disabled = false;
        });
    });
  });

  // Handle tab switching for saved products
  const savedProductsLink = document.querySelector('a[href="#saved-products"]');
  if (savedProductsLink) {
    savedProductsLink.addEventListener('click', function (e) {
      e.preventDefault();

      // Hide all tab contents
      document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = 'none';
      });

      // Show saved products tab
      const savedProductsTab = document.getElementById('saved-products');
      if (savedProductsTab) {
        savedProductsTab.style.display = 'block';
      }

      // Update active tab styling
      document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.classList.remove('text-teal-800', 'font-semibold');
        link.classList.add('text-teal-700');
      });
      this.classList.add('text-teal-800', 'font-semibold');
      this.classList.remove('text-teal-700');
    });
  }
});