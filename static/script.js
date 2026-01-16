document.addEventListener("DOMContentLoaded", () => {
  // === CSRF ===
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let c of cookies) {
        c = c.trim();
        if (c.startsWith(name + "=")) {
          cookieValue = decodeURIComponent(c.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  window.CSRF_TOKEN = getCookie("csrftoken");

  // === DOM ===
  const modalContainer = document.getElementById("modal_container");
  const closeBtn = document.getElementById("close");

  const segSize = document.getElementById("segSize");
  const segBase = document.getElementById("segBase");
  const addonsGrid = document.getElementById("addonsGrid");

  const modalTitle = document.getElementById("modalTitle");
  const modalTotal = document.getElementById("modalTotal");
  const modalAddToCart = document.getElementById("modalAddToCart");

  // Быстрая проверка, чтобы не молчало
  const missing = [];
  if (!modalContainer) missing.push("modal_container");
  if (!segSize) missing.push("segSize");
  if (!segBase) missing.push("segBase");
  if (!addonsGrid) missing.push("addonsGrid");
  if (!modalTitle) missing.push("modalTitle");
  if (!modalTotal) missing.push("modalTotal");
  if (!modalAddToCart) missing.push("modalAddToCart");
  if (!closeBtn) missing.push("close");
  if (missing.length) {
    console.log("Missing modal nodes:", missing.join(", "));
    return;
  }

  // === STATE ===
  let productId = null;
  let selectedAddons = new Set();
  let selectedSizeId = 0;
  let selectedBaseId = 0;
  let lastCalc = null;
  let calcTimer = null;

  // === UI helpers ===
  function openModal() {
    modalContainer.classList.add("show");
    modalContainer.setAttribute("aria-hidden", "false");
    document.body.classList.add("no-scroll");
  }

  function closeModal() {
    modalContainer.classList.remove("show");
    modalContainer.setAttribute("aria-hidden", "true");
    document.body.classList.remove("no-scroll");
  }

  function setActive(groupEl, btn) {
    groupEl.querySelectorAll(".seg__btn").forEach(b => b.classList.remove("is-active"));
    btn.classList.add("is-active");
  }

  function syncFromUI() {
    selectedSizeId = Number(segSize.querySelector(".seg__btn.is-active")?.dataset.sizeId || 0);
    selectedBaseId = Number(segBase.querySelector(".seg__btn.is-active")?.dataset.baseId || 0);
  }

  function showToast(text) {
    const t = document.createElement("div");
    t.className = "toast-added";
    t.textContent = text;
    document.body.appendChild(t);
    requestAnimationFrame(() => t.classList.add("show"));
    setTimeout(() => {
      t.classList.remove("show");
      setTimeout(() => t.remove(), 250);
    }, 1200);
  }

  // === Название донера из админки (без правки HTML) ===
  async function fillModalProductTitle(productId) {
    if (!modalTitle) return;
    if (!productId) {
      modalTitle.textContent = "Донер";
      return;
    }

    try {
      // НУЖЕН эндпоинт: GET /api/products/<id>/ (я описывал ранее)
      const r = await fetch(`/api/products/${productId}/`, { method: "GET" });
      const data = await r.json().catch(() => ({}));

      if (r.ok && data.ok && data.product?.name) {
        modalTitle.textContent = data.product.name;
      } else {
        modalTitle.textContent = "Донер";
      }
    } catch (e) {
      modalTitle.textContent = "Донер";
    }
  }

  // === Server calc ===
  async function recalcOnServer() {
    syncFromUI();

    const payload = {
      product_id: productId,                 // важно (builder/services.py требует product_id)
      size_id: selectedSizeId,
      base_id: selectedBaseId,
      ingredient_ids: Array.from(selectedAddons),
      quantities: {}
    };

    // пока считаем — отключим кнопку
    modalAddToCart.disabled = true;
    modalAddToCart.textContent = "Считаю...";

    const r = await fetch("/api/builder/calculate/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": window.CSRF_TOKEN || ""
      },
      credentials: "same-origin",
      body: JSON.stringify(payload)
    });

    const data = await r.json().catch(() => ({}));

    if (!r.ok || !data.ok) {
      console.log("calculate error:", data);
      modalTotal.textContent = "Ошибка";
      modalAddToCart.textContent = "Нельзя";
      modalAddToCart.disabled = true;
      lastCalc = null;
      return null;
    }

    lastCalc = data;

    modalTotal.textContent = data.subtotal + " тг.";
    modalAddToCart.textContent = `В корзину за ${data.subtotal} тг.`;
    modalAddToCart.disabled = false;

    return data;
  }

  function recalcDebounced() {
    clearTimeout(calcTimer);
    calcTimer = setTimeout(() => recalcOnServer(), 120);
  }

  // === Open modal from card ===
  document.addEventListener("click", async (e) => {
    const btn = e.target.closest(".js-open-modal");
    if (!btn) return;

    productId = Number(btn.dataset.productId || 0);
    selectedAddons = new Set();
    lastCalc = null;

    // сброс выделения допов в UI
    addonsGrid.querySelectorAll(".addon-card").forEach(c => c.classList.remove("is-selected"));

    // выставим дефолт (первую активную кнопку) если вдруг ничего не активировано
    if (!segSize.querySelector(".seg__btn.is-active")) {
      const first = segSize.querySelector(".seg__btn");
      if (first) first.classList.add("is-active");
    }
    if (!segBase.querySelector(".seg__btn.is-active")) {
      const first = segBase.querySelector(".seg__btn");
      if (first) first.classList.add("is-active");
    }

    // 1) Заголовок из админки
    await fillModalProductTitle(productId);

    // 2) Открыть
    openModal();

    // 3) Сразу посчитать базовую цену (донер + выбранные опции)
    recalcDebounced();
  });

  // === Close handlers ===
  closeBtn.addEventListener("click", closeModal);

  modalContainer.addEventListener("click", (e) => {
    if (e.target === modalContainer) closeModal();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modalContainer.classList.contains("show")) closeModal();
  });

  // === Size / base select ===
  segSize.addEventListener("click", (e) => {
    const b = e.target.closest(".seg__btn");
    if (!b) return;
    setActive(segSize, b);
    recalcDebounced();
  });

  segBase.addEventListener("click", (e) => {
    const b = e.target.closest(".seg__btn");
    if (!b) return;
    setActive(segBase, b);
    recalcDebounced();
  });

  // === Addons select ===
  addonsGrid.addEventListener("click", (e) => {
    const card = e.target.closest(".addon-card");
    if (!card) return;

    const id = Number(card.dataset.addonId);
    if (!id) return;

    if (selectedAddons.has(id)) {
      selectedAddons.delete(id);
      card.classList.remove("is-selected");
    } else {
      selectedAddons.add(id);
      card.classList.add("is-selected");
    }

    recalcDebounced();
  });

  // === Add to cart ===
  modalAddToCart.addEventListener("click", async () => {
    // гарантируем актуальный snapshot
    if (!lastCalc?.snapshot) {
      const c = await recalcOnServer();
      if (!c?.snapshot) return;
    }

    const snap = lastCalc.snapshot;

    // product_id должен быть внутри payload
  const payload = {
    item_type: "BUILDER",
    quantity: 1,
    product_id: productId,   // важно
    size_id: snap.size.id,
    base_id: snap.base.id,
    ingredient_ids: snap.items.map(x => x.id),
    quantities: Object.fromEntries(snap.items.map(x => [String(x.id), x.qty]))
  };


    modalAddToCart.disabled = true;
    modalAddToCart.textContent = "Добавляю...";

    const r = await fetch("/api/cart/add/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": window.CSRF_TOKEN || ""
      },
      credentials: "same-origin",
      body: JSON.stringify(payload)
    });

    const data = await r.json().catch(() => ({}));
    if (!r.ok || !data.ok) {
      console.log("cart/add error:", data);
      modalAddToCart.disabled = false;
      modalAddToCart.textContent = "Не получилось";
      return;
    }

    showToast("Добавлено в корзину ✓");
    closeModal();

    window.location.href = "/cart/";
  });
});
