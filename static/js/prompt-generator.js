/**
 * Prompt Generator JavaScript
 * Handles prompt generation functionality for Inspirational Guidance
 */

document.addEventListener('DOMContentLoaded', function () {
  // Elements
  const generateBtn = document.getElementById('generateBtn');
  const newPromptBtn = document.getElementById('newPromptBtn');
  const categorySelect = document.getElementById('category');
  const difficultySelect = document.getElementById('difficulty');
  const promptTypeSelect = document.getElementById('promptType');
  const promptCard = document.getElementById('promptCard');
  const promptText = document.getElementById('promptText');
  const promptCategory = document.getElementById('promptCategory');
  const promptDifficulty = document.getElementById('promptDifficulty');
  const favouriteBtn = document.getElementById('favouriteBtn');
  const currentPromptIdInput = document.getElementById('current-prompt-id') || document.createElement('input');

  // Ensure we have a hidden input for the current prompt ID
  if (!document.getElementById('current-prompt-id')) {
    currentPromptIdInput.type = 'hidden';
    currentPromptIdInput.id = 'current-prompt-id';
    document.body.appendChild(currentPromptIdInput);
  }

  console.log('Prompt generator script loaded'); // Debug logging

  /**
   * Fetch categories from the API
   */
  async function fetchCategories() {
    try {
      console.log('Fetching categories...');
      // Update the URL to match your Django URL configuration
      const response = await fetch('/prompt/api/categories/');

      if (!response.ok) {
        throw new Error(`Failed to fetch categories: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Categories data:', data);

      // Extract categories from the response (handle both paginated and non-paginated)
      const categories = data.results || data;

      if (!categories || !Array.isArray(categories)) {
        console.error('Invalid categories format:', data);
        return;
      }

      console.log('Categories extracted:', categories);

      // Make sure we have the select element
      if (!categorySelect) {
        console.error('Category select element not found');
        return;
      }

      // Clear existing options (except the default)
      while (categorySelect.options.length > 1) {
        categorySelect.remove(1);
      }

      // Add new options
      categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category.slug;
        option.textContent = category.name;
        categorySelect.appendChild(option);
      });

      console.log('Categories added to dropdown');
    } catch (error) {
      console.error('Error fetching categories:', error);
      showMessage('Failed to load categories. Please refresh the page.', 'error');
    }
  }

  /**
   * Generate a new prompt based on selected filters
   */
  async function generatePrompt() {
    // Show loading state
    if (promptCard) {
      promptCard.classList.add('opacity-50');
    }

    if (generateBtn) {
      generateBtn.disabled = true;
      generateBtn.innerHTML = '<span class="inline-block">Generating...</span>';
    }

    // Get filter values
    const category = categorySelect ? categorySelect.value : '';
    const difficulty = difficultySelect ? difficultySelect.value : '';
    const promptType = promptTypeSelect ? promptTypeSelect.value : '';

    // Get current prompt ID if available (for "Get Another Prompt")
    const currentPromptId = document.getElementById('current-prompt-id') ?
      document.getElementById('current-prompt-id').value : '';

    // Log the filter values for debugging
    console.log('Generating prompt with filters:', {
      category,
      difficulty,
      promptType,
      currentPromptId
    });

    // Build URL with query parameters
    let url = '/prompt/api/random-prompt/?';
    if (category) url += `category=${encodeURIComponent(category)}&`;
    if (difficulty) url += `difficulty=${encodeURIComponent(difficulty)}&`;
    if (promptType) url += `type=${encodeURIComponent(promptType)}&`;
    if (currentPromptId) url += `current_id=${encodeURIComponent(currentPromptId)}&`;

    console.log('Fetching from URL:', url);

    try {
      const response = await fetch(url);
      console.log('Response status:', response.status);

      if (!response.ok) {
        throw new Error(`Failed to fetch prompt: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Prompt data received:', data);

      // Check if we got a message about no prompts
      if (data.no_more_prompts || data.no_prompts) {
        console.log('No prompts available:', data.message);

        // Show message to the user
        showMessage(data.message || 'No prompts available with these filters. Try different options.', 'info');

        // If we have a prompt displayed already, keep it visible
        if (promptCard && !promptCard.classList.contains('hidden')) {
          promptCard.classList.remove('opacity-50');
        } else {
          // If no prompt is currently displayed, show a placeholder
          if (promptCard) {
            promptCard.classList.remove('hidden');
            promptCard.classList.remove('opacity-50');

            if (promptText) {
              promptText.textContent = "No prompts available with the current filters. Please try different options.";
            }

            if (promptCategory) {
              promptCategory.textContent = "N/A";
            }

            if (promptDifficulty) {
              promptDifficulty.textContent = "N/A";
            }
          }
        }

        return;
      }

      // Update the UI with the new prompt
      if (promptText) {
        promptText.textContent = data.text || "No prompt text available";
      }

      if (promptCategory) {
        promptCategory.textContent = data.category_name || "General";
      }

      // Map difficulty to user-friendly text
      const difficultyText = {
        'easy': 'Quick (5-10 minutes)',
        'medium': 'Medium (15-20 minutes)',
        'deep': 'Deep Dive (30+ minutes)'
      };

      if (promptDifficulty) {
        promptDifficulty.textContent = difficultyText[data.difficulty] || data.difficulty || "Medium";
      }

      // Store the current prompt ID for "Get Another Prompt"
      if (data.id) {
        console.log('Setting current prompt ID:', data.id);
        const idInput = document.getElementById('current-prompt-id');
        if (idInput) {
          idInput.value = data.id;
        }

        // If we have a favourite button, update it with the prompt ID
        if (favouriteBtn) {
          favouriteBtn.setAttribute('data-prompt-id', data.id);

          // Use the favourite handler from favourite-prompt.js if available
          if (window.favouritePrompts && window.favouritePrompts.resetButton) {
            window.favouritePrompts.resetButton(data.is_favourite);
          } else {
            // Fallback if the favouritePrompts API is not available
            if (data.is_favourite) {
              favouriteBtn.classList.remove('text-gray-400');
              favouriteBtn.classList.add('text-yellow-500');
              favouriteBtn.querySelector('svg').setAttribute('fill', 'currentColor');
            } else {
              favouriteBtn.classList.remove('text-yellow-500');
              favouriteBtn.classList.add('text-gray-400');
              favouriteBtn.querySelector('svg').setAttribute('fill', 'none');
            }
          }
        }
      } else {
        console.log('No prompt ID in response');
      }

      // Show the prompt card
      if (promptCard) {
        promptCard.classList.remove('hidden');
        promptCard.classList.remove('opacity-50');
      }

    } catch (error) {
      console.error('Error generating prompt:', error);
      showMessage('Error generating prompt. Please try again.', 'error');

      // Hide prompt card if there's an error and it's not already displaying a prompt
      if (promptCard && !promptText.textContent.trim()) {
        promptCard.classList.add('hidden');
      } else if (promptCard) {
        promptCard.classList.remove('opacity-50');
      }
    } finally {
      // Reset loading state
      if (generateBtn) {
        generateBtn.disabled = false;
        generateBtn.innerHTML = 'Generate Prompt';
      }
    }
  }

  /**
   * Display a message to the user
   * @param {string} message - The message to display
   * @param {string} type - The type of message (success, error, info)
   */
  function showMessage(message, type = 'info') {
    console.log(`Showing message (${type}): ${message}`);

    // Create message element
    const messageContainer = document.createElement('div');
    messageContainer.className = 'fixed top-1/4 left-1/2 transform -translate-x-1/2 z-50';
    messageContainer.id = 'prompt-message-container';

    const messageElement = document.createElement('div');

    // Set appropriate styling based on message type
    if (type === 'success') {
      messageElement.className = 'bg-green-100 border-green-600 text-green-700 border px-4 py-3 rounded relative shadow-lg mb-4';
    } else if (type === 'error') {
      messageElement.className = 'bg-red-100 border-red-800 text-red-900 border px-4 py-3 rounded relative shadow-lg mb-4';
    } else {
      messageElement.className = 'bg-blue-100 border-blue-600 text-blue-700 border px-4 py-3 rounded relative shadow-lg mb-4';
    }

    messageElement.setAttribute('role', 'alert');

    // Add message content
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

    // Automatically remove after 5 seconds
    setTimeout(() => {
      messageElement.style.opacity = '0';
      messageElement.style.transition = 'opacity 0.3s ease-in-out';
      setTimeout(() => {
        messageContainer.remove();
      }, 300);
    }, 5000);
  }

  // Initialize the prompt generator
  function initPromptGenerator() {
    // Fetch categories when page loads
    fetchCategories();

    // Set up event listeners
    if (generateBtn) {
      generateBtn.addEventListener('click', generatePrompt);
      console.log('Added event listener to Generate button');
    }

    if (newPromptBtn) {
      newPromptBtn.addEventListener('click', function () {
        // Scroll back to filter area if needed
        const filterArea = document.querySelector('.bg-white.shadow-md.rounded-lg');
        if (filterArea) {
          filterArea.scrollIntoView({ behavior: 'smooth' });
        }

        // Generate a new prompt
        generatePrompt();
      });
      console.log('Added event listener to New Prompt button');
    }

    // Log for debugging
    console.log('Prompt generator initialized');

    // Make sure the prompt card is hidden initially
    if (promptCard) {
      promptCard.classList.add('hidden');
    }
  }

  // Start initialization
  initPromptGenerator();

  /**
 * Prompt Generator and Writing Tracker integration
 * Allows recording a writing session directly after using a prompt
 */

  document.addEventListener('DOMContentLoaded', function () {
    // Check if we're on the home page with the prompt generator
    const promptCard = document.getElementById('promptCard');
    if (!promptCard) return;

    // Add "Record Session" button to the prompt card
    const addSessionButton = document.createElement('button');
    addSessionButton.id = 'record-session-btn';
    addSessionButton.className = 'mt-4 bg-green-600 hover:bg-green-700 text-white text-sm font-medium py-2 px-4 rounded-md transition duration-200';
    addSessionButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 inline-block mr-1" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v3.586L7.707 9.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 10.586V7z" clip-rule="evenodd" /></svg> Record Session Using This Prompt';

    // Add the button to the prompt card
    const promptButtons = document.querySelector('#promptCard .flex.justify-center');
    if (promptButtons) {
      promptButtons.appendChild(addSessionButton);
    }

    // Handle button click
    addSessionButton.addEventListener('click', function () {
      // Get current prompt ID
      const currentPromptId = document.getElementById('current-prompt-id')?.value;
      if (!currentPromptId) {
        console.error('No current prompt ID found');
        return;
      }

      // Redirect to writing tracker page with the prompt ID
      window.location.href = `/prompt/writing-progress/?prompt_id=${currentPromptId}`;
    });

    // Handle pre-filling prompt from URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const promptIdParam = urlParams.get('prompt_id');

    if (promptIdParam && document.getElementById('id_prompt_used')) {
      // Set the prompt ID in the session form
      const promptSelect = document.getElementById('id_prompt_used');

      // Check if the option exists
      let optionExists = false;
      for (let i = 0; i < promptSelect.options.length; i++) {
        if (promptSelect.options[i].value === promptIdParam) {
          promptSelect.selectedIndex = i;
          optionExists = true;
          break;
        }
      }

      // If the option doesn't exist, we need to fetch the prompt details and add it
      if (!optionExists) {
        fetch(`/prompt/api/prompts/${promptIdParam}/`)
          .then(response => {
            if (!response.ok) {
              throw new Error('Failed to fetch prompt');
            }
            return response.json();
          })
          .then(data => {
            // Create and add the option
            const option = document.createElement('option');
            option.value = data.id;
            option.textContent = data.text.substring(0, 60) + (data.text.length > 60 ? '...' : '');
            option.selected = true;
            promptSelect.appendChild(option);
          })
          .catch(error => {
            console.error('Error fetching prompt:', error);
          });
      }

      // Scroll to the session form
      document.querySelector('.bg-white.rounded-lg.shadow-md.p-6.mb-6.sticky').scrollIntoView({
        behavior: 'smooth'
      });
    }
  });
});
