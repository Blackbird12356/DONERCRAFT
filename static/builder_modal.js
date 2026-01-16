document.addEventListener("DOMContentLoaded", () => {
  const modalContainer = document.getElementById("modal_container");
  const closeBtn = document.getElementById("close");
  const modalTitle = document.getElementById("modalTitle");

  function openModal(title) {
    if (modalTitle) modalTitle.textContent = title || "Донер";
    modalContainer.classList.add("show");
    modalContainer.setAttribute("aria-hidden", "false");
    document.body.classList.add("no-scroll");
  }

  function closeModal() {
    modalContainer.classList.remove("show");
    modalContainer.setAttribute("aria-hidden", "true");
    document.body.classList.remove("no-scroll");
  }

  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".js-open-modal");
    if (!btn) return;
    openModal(btn.dataset.productName);
  });

  closeBtn?.addEventListener("click", closeModal);

  modalContainer?.addEventListener("click", (e) => {
    if (e.target === modalContainer) closeModal();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modalContainer.classList.contains("show")) closeModal();
  });
});
