/**
 * Favourite Prompt Functionality
 * Handles saving and removing writing prompts from user favourites
 */

document.addEventListener('DOMContentLoaded', function () {
  // References to key elements
  const favouriteBtn = document.getElementById('favouriteBtn');

  // Only proceed if we have the favorite button (user is logged in)
  if (!favouriteBtn) return;

  // Function to update the favorite button appearance based on its state
  function updateFavouriteButtonAppearance(isFavourite) {
    console.log('Updating favourite button appearance:', isFavourite);
    if (isFavourite) {
      favouriteBtn.classList.remove('text-gray-400');
      favouriteBtn.classList.add('text-yellow-500');
      favouriteBtn.querySelector('svg').setAttribute('fill', 'currentColor');
    } else {
      favouriteBtn.classList.remove('text-yellow-500');
      favouriteBtn.classList.add('text-gray-400');
      favouriteBtn.querySelector('svg').setAttribute('fill', 'none');
    }
  }

  // Toggle favourite status function with visual feedback
  function toggleFavourite(event) {
    event.preventDefault();

    const promptId = this.getAttribute('data-prompt-id');
    if (!promptId) {
      console.error('No prompt ID available');
      return;
    }

    // Visual feedback while the request is being processed
    this.classList.add('animate-pulse');

    fetch(`/accounts/favourite-prompt/${promptId}/`, {
      method: 'GET',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json'
      },
      credentials: 'same-origin'
    })
      .then(response => response.json())
      .then(data => {
        // Remove loading animation
        this.classList.remove('animate-pulse');
        console.log('Favourite toggle response:', data);

        if (data.status === 'success') {
          // Update button appearance based on favorite status
          updateFavouriteButtonAppearance(data.is_favourite);

          // Show a message
          showMessage(data.message || (data.is_favourite ?
            'Prompt added to your profile!' :
            'Prompt removed from your profile.'), 'success');
        }
      })
      .catch(error => {
        // Remove loading animation
        this.classList.remove('animate-pulse');

        console.error('Error toggling favourite:', error);
        showMessage('Error saving favourite. Please try again.', 'error');
      });
  }

  // When a new prompt is loaded, check its favourite status
  function resetFavouriteButton(isFavourite) {
    console.log('Resetting favourite button with status:', isFavourite);
    if (favouriteBtn) {
      updateFavouriteButtonAppearance(isFavourite);

      // Make sure the data-prompt-id attribute is set correctly
      const currentPromptId = document.getElementById('current-prompt-id');
      if (currentPromptId && currentPromptId.value) {
        favouriteBtn.setAttribute('data-prompt-id', currentPromptId.value);
      }
    }
  }

  // Initialize favorite button functionality
  function initFavouriteButton() {
    console.log('Initializing favourite button');

    // Remove any existing event listeners to prevent duplicates
    favouriteBtn.removeEventListener('click', toggleFavourite);

    // Add the event listener
    favouriteBtn.addEventListener('click', toggleFavourite);
  }

  // Public API for integration with prompt-generator.js
  window.favouritePrompts = {
    updateButtonAppearance: updateFavouriteButtonAppearance,
    resetButton: resetFavouriteButton
  };

  // Initialize
  initFavouriteButton();

  /**
   * Display a message to the user using Tailwind classes
   * @param {string} message - The message to display
   * @param {string} type - The type of message (success, error, info)
   */
  function showMessage(message, type = 'info') {
    console.log(`Showing message (${type}): ${message}`);

    // Create message container with Tailwind classes
    const messageContainer = document.createElement('div');
    messageContainer.className = 'fixed top-1/4 left-1/2 transform -translate-x-1/2 z-50';
    messageContainer.id = 'prompt-message-container';

    const messageElement = document.createElement('div');

    // Set appropriate Tailwind styling based on message type
    if (type === 'success') {
      messageElement.className = 'bg-green-100 border-green-600 text-green-700 border px-4 py-3 rounded-lg shadow-lg mb-4';
    } else if (type === 'error') {
      messageElement.className = 'bg-red-100 border-red-800 text-red-900 border px-4 py-3 rounded-lg shadow-lg mb-4';
    } else {
      messageElement.className = 'bg-blue-100 border-blue-600 text-blue-700 border px-4 py-3 rounded-lg shadow-lg mb-4';
    }

    messageElement.setAttribute('role', 'alert');

    // Add message content with Tailwind typography classes
    const titleElement = document.createElement('strong');
    titleElement.className = 'font-bold';
    titleElement.textContent = type === 'success' ? 'Success!' : type === 'error' ? 'Error!' : 'Notice';

    const textElement = document.createElement('span');
    textElement.className = 'block sm:inline ml-2';
    textElement.textContent = message;

    messageElement.appendChild(titleElement);
    messageElement.appendChild(textElement);
    messageContainer.appendChild(messageElement);

    // Remove any existing messages
    const existingMessages = document.querySelectorAll('#prompt-message-container');
    existingMessages.forEach(msg => msg.remove());

    // Add to the DOM
    document.body.appendChild(messageContainer);

    // Automatically remove after 5 seconds with a fade effect
    setTimeout(() => {
      messageElement.style.opacity = '0';
      messageElement.style.transition = 'opacity 0.3s ease-in-out';
      setTimeout(() => {
        messageContainer.remove();
      }, 300);
    }, 5000);
  }
});
