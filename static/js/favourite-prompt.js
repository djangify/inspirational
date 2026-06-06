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

          // Dynamically update the saved prompts list if it exists on the page
          updateSavedPromptsList(data);

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

  // Dynamically add or remove a prompt card in the saved prompts list
  function updateSavedPromptsList(data) {
    const list = document.getElementById('saved-prompts-list');
    const emptyState = document.getElementById('saved-prompts-empty');
    if (!list) return;

    if (data.is_favourite) {
      // Don't add if already in the list
      if (list.querySelector(`[data-prompt-id="${data.prompt_id}"]`)) return;

      const card = document.createElement('div');
      card.className = 'border bg-white rounded-md p-4 relative';
      card.setAttribute('data-prompt-id', data.prompt_id);
      card.innerHTML = `
        <div class="prose prose-lg">
          <p class="text-gray-900">${data.prompt_text}</p>
        </div>
        <div class="flex justify-between items-center mt-4">
          <div>
            <span class="text-sm font-medium text-teal-700">Category:</span>
            <span class="text-sm ml-1">${data.prompt_category}</span>
          </div>
          <div>
            <span class="text-sm font-medium text-teal-700">Time:</span>
            <span class="text-sm ml-1">${data.prompt_difficulty}</span>
          </div>
        </div>
        <a href="${data.remove_url}" class="absolute top-2 right-2 text-red-600 hover:text-red-800">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </a>`;

      list.prepend(card);
      list.classList.remove('hidden');
      if (emptyState) emptyState.classList.add('hidden');

    } else {
      // Remove the card if it exists
      const existing = list.querySelector(`[data-prompt-id="${data.prompt_id}"]`);
      if (existing) existing.remove();

      // Show empty state if list is now empty
      if (list.children.length === 0) {
        list.classList.add('hidden');
        if (emptyState) emptyState.classList.remove('hidden');
      }
    }
  }

  // Handle X (remove) buttons on saved prompt cards without page reload
  function initRemoveButtons() {
    document.addEventListener('click', function (e) {
      const removeLink = e.target.closest('#saved-prompts-list a[href*="favourite-prompt"]');
      if (!removeLink) return;

      e.preventDefault();

      const card = removeLink.closest('[data-prompt-id]');
      const url = removeLink.getAttribute('href');

      fetch(url, {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin'
      })
        .then(r => r.json())
        .then(data => {
          if (data.status === 'success' && !data.is_favourite) {
            if (card) card.remove();
            const list = document.getElementById('saved-prompts-list');
            const emptyState = document.getElementById('saved-prompts-empty');
            if (list && list.children.length === 0) {
              list.classList.add('hidden');
              if (emptyState) emptyState.classList.remove('hidden');
            }
          }
        })
        .catch(err => console.error('Error removing prompt:', err));
    });
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
  initRemoveButtons();

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
