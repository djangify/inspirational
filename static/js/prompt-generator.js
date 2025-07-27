document.addEventListener('DOMContentLoaded', function () {
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
  const currentPromptIdInput = document.getElementById('current-prompt-id') || (() => {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.id = 'current-prompt-id';
    document.body.appendChild(input);
    return input;
  })();

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + '=') {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.textContent = message;
    toast.className = `fixed top-4 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded shadow-md z-50 transition-all text-white text-sm
      ${type === "success" ? "bg-green-600" : type === "error" ? "bg-red-600" : "bg-blue-600"}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  }

  async function generatePrompt() {
    if (generateBtn) {
      generateBtn.disabled = true;
      generateBtn.textContent = "Generating...";
    }
    if (promptCard) {
      promptCard.classList.add("opacity-50");
    }

    const category = categorySelect?.value || "";
    const difficulty = difficultySelect?.value || "";
    const promptType = promptTypeSelect?.value || "";
    const currentPromptId = currentPromptIdInput?.value || "";

    let url = "/prompt/api/random-prompt/?";
    if (category) url += `category=${encodeURIComponent(category)}&`;
    if (difficulty) url += `difficulty=${encodeURIComponent(difficulty)}&`;
    if (promptType) url += `type=${encodeURIComponent(promptType)}&`;
    if (currentPromptId) url += `current_id=${encodeURIComponent(currentPromptId)}&`;

    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error("Error fetching prompt");
      const data = await response.json();

      if (data.no_prompts || data.no_more_prompts) {
        showToast(data.message || "No prompts found", "info");
        return;
      }

      if (promptText) promptText.textContent = data.text || "No prompt";
      if (promptCategory) promptCategory.textContent = data.category_name || "General";
      if (promptDifficulty) {
        const difficultyMap = {
          easy: "Quick (5–10 mins)",
          medium: "Medium (15–20 mins)",
          deep: "Deep Dive (30+ mins)"
        };
        promptDifficulty.textContent = difficultyMap[data.difficulty] || data.difficulty;
      }

      if (data.id) {
        currentPromptIdInput.value = data.id;
        if (favouriteBtn) {
          favouriteBtn.setAttribute("data-prompt-id", data.id);
          if (data.is_favourite) {
            favouriteBtn.classList.add("text-yellow-500");
            favouriteBtn.classList.remove("text-gray-400");
          } else {
            favouriteBtn.classList.remove("text-yellow-500");
            favouriteBtn.classList.add("text-gray-400");
          }
        }
      }

      if (promptCard) {
        promptCard.classList.remove("hidden");
        promptCard.classList.remove("opacity-50");
      }

    } catch (err) {
      console.error(err);
      showToast("Failed to load prompt", "error");
    } finally {
      if (generateBtn) {
        generateBtn.disabled = false;
        generateBtn.textContent = "Generate Prompt";
      }
    }
  }

  function waitForCategoryOptions(callback) {
    const interval = setInterval(() => {
      const categorySelect = document.getElementById("category");
      if (categorySelect && categorySelect.options.length > 1) {
        clearInterval(interval);
        callback();
      }
    }, 100);
  }

  function initPromptGenerator() {
    if (generateBtn) generateBtn.addEventListener("click", generatePrompt);
    if (newPromptBtn) newPromptBtn.addEventListener("click", generatePrompt);
    // Removed bindSaveButton(); because the function was deleted
    if (promptCard) promptCard.classList.add("hidden");
  }

  waitForCategoryOptions(initPromptGenerator);
});
