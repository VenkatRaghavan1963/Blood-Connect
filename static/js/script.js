document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('input[type="date"]').forEach((input) => {
    if (!input.max) input.max = new Date().toISOString().split('T')[0];
  });
});
