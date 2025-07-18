document.addEventListener('DOMContentLoaded', function () {
  // Auto-dismiss messages after 2 seconds
  setTimeout(function () {
    const messages = document.querySelectorAll('[role="alert"]');
    messages.forEach(function (message) {
      message.style.opacity = '0';
      message.style.transition = 'opacity 0.3s ease-in-out';
      setTimeout(function () {
        message.remove();
      }, 300);
    });
  }, 2000);

  // Confirmation dialog function
  window.showConfirmation = function (message, onConfirm) {
    const container = document.createElement('div');
    container.className = "fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50";
    container.setAttribute('role', 'dialog');

    const dialog = document.createElement('div');
    dialog.className = "bg-white rounded-lg p-6 max-w-sm mx-auto shadow-xl";

    const messageEl = document.createElement('div');
    messageEl.className = "mb-4 text-gray-700";
    messageEl.textContent = message;

    const buttonContainer = document.createElement('div');
    buttonContainer.className = "flex justify-end gap-3";

    const confirmButton = document.createElement('button');
    confirmButton.className = "px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors";
    confirmButton.textContent = "OK";
    confirmButton.onclick = () => {
      container.remove();
      if (onConfirm) onConfirm();
    };

    const cancelButton = document.createElement('button');
    cancelButton.className = "px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors";
    cancelButton.textContent = "Cancel";
    cancelButton.onclick = () => container.remove();

    buttonContainer.appendChild(cancelButton);
    buttonContainer.appendChild(confirmButton);

    dialog.appendChild(messageEl);
    dialog.appendChild(buttonContainer);
    container.appendChild(dialog);
    document.body.appendChild(container);

    confirmButton.focus();
  };
});