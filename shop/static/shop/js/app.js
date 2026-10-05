const API = "/api";
const FALLBACK_IMAGE = "https://placehold.co/700x500?text=No+Image";

let products = [];
let categories = [];
let cart = {}; // productId:priceType -> quantity in the main sale unit
let currentCategory = "";

const $ = (selector) => document.querySelector(selector);

function normalizeSearch(value) {
  return String(value || "")
    .toLocaleLowerCase("ru-RU")
    .normalize("NFKC")
    .replace(/ё/g, "е")
    .replace(/й/g, "и")
    .replace(/[^\p{L}\p{N}.]+/gu, " ")
    .trim();
}

function searchWords(value) {
  return normalizeSearch(value).split(/\s+/).filter(Boolean);
}

async function readResponse(response) {
  const text = await response.text();
  if (!text) return {};

  try {
    return JSON.parse(text);
  } catch {
    const clean = text.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
    throw new Error(
      response.status === 403
        ? "Сессия устарела. Обновите страницу и попробуйте ещё раз."
        : `Сервер вернул ошибку (${response.status}). ${clean.slice(0, 180)}`
    );
  }
}

async function loadCategories() {
  const response = await fetch(`${API}/categories/`, { credentials: "same-origin" });
  const data = await readResponse(response);
  if (!response.ok) throw new Error(data.detail || "Не удалось загрузить категории");

  categories = Array.isArray(data) ? data : [];
  const list = $("#categoryList");
  list.innerHTML = `<button class="category active" data-category="">Все товары</button>`;

  categories.forEach((category) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "category";
    button.dataset.category = category.slug || "";
    button.textContent = category.name;
    list.appendChild(button);
  });

  list.querySelectorAll(".category").forEach((button) => {
    button.addEventListener("click", () => {
      list.querySelectorAll(".category").forEach((x) => x.classList.remove("active"));
      button.classList.add("active");
      currentCategory = button.dataset.category || "";
      renderProducts();
    });
  });
}

async function loadProducts() {
  const response = await fetch(`${API}/products/`, { credentials: "same-origin" });
  const data = await readResponse(response);
  if (!response.ok) throw new Error(data.detail || "Не удалось загрузить товары");

  products = Array.isArray(data) ? data : [];
  renderProducts();
}

function getFilteredProducts() {
  const words = searchWords($("#searchInput")?.value);

  return products.filter((product) => {
    // Category filter and search are deliberately independent and work
    // identically for every category.
    const categoryOk = !currentCategory || String(product.category?.slug || "") === currentCategory;
    if (!categoryOk) return false;

    if (!words.length) return true;

    const searchable = normalizeSearch([
      product.name,
      product.description,
      product.category?.name,
      product.category?.slug,
      product.unit,
      product.package_type,
      product.package_label,
      product.package_quantity,
      product.retail_price,
      product.wholesale_price,
    ].join(" "));

    return words.every((word) => searchable.includes(word));
  });
}

function money(value) {
  return Number(value).toLocaleString("ru-RU") + " сом";
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (m) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[m]));
}

function cartKey(id, type) {
  return `${id}:${type}`;
}

function parseKey(key) {
  const [id, type] = key.split(":");
  return { id: Number(id), type: type || "retail" };
}

function getCartQtyForProduct(id) {
  return Object.entries(cart).reduce((sum, [key, quantity]) => {
    const parsed = parseKey(key);
    return parsed.id === Number(id) ? sum + Number(quantity) : sum;
  }, 0);
}

function formatQuantity(value) {
  const number = Number(value);
  if (Number.isInteger(number)) return String(number);
  return number.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
}

function formatStockLabel(product, baseQuantity) {
  const quantity = Number(baseQuantity);
  if (quantity <= 0) return "Нет в наличии";

  const packageSize = Number(product.package_quantity) || 1;
  if (!product.package_type || packageSize <= 1) {
    return `${formatQuantity(quantity)} ${product.unit}`;
  }

  const wholePackages = Math.floor(quantity / packageSize);
  const remainder = quantity - wholePackages * packageSize;

  if (remainder <= 0.000001) {
    return `${wholePackages} ${product.package_type}`;
  }

  const remainderText = `${formatQuantity(remainder)} ${product.unit}`;
  return wholePackages > 0
    ? `${wholePackages} ${product.package_type} + ${remainderText}`
    : remainderText;
}

function availableQuantity(product) {
  return Math.max(0, Number(product.stock_quantity) - getCartQtyForProduct(product.id));
}

function imageWithFallback(img, url) {
  if (!img) return;
  img.onerror = () => {
    img.onerror = null;
    img.src = FALLBACK_IMAGE;
  };
  img.src = url || FALLBACK_IMAGE;
}

function renderProducts() {
  const visible = getFilteredProducts();
  const container = $("#products");
  container.innerHTML = "";
  $("#productsCount").textContent = `${visible.length} товаров`;

  visible.forEach((product, index) => {
    const available = availableQuantity(product);
    const out = available <= 0;
    const inCart = getCartQtyForProduct(product.id);
    const card = document.createElement("div");
    card.className = "product";
    card.style.animationDelay = `${index * 0.04}s`;

    card.addEventListener("click", (event) => {
      if (!event.target.closest("button")) openProductModal(product.id);
    });

    card.innerHTML = `
      <div class="product-image">
        ${out ? "<div class='product-tag'>Нет в наличии</div>" : ""}
        <img src="${escapeHtml(product.image_url || FALLBACK_IMAGE)}" alt="${escapeHtml(product.name)}" loading="lazy">
      </div>
      <div class="product-info">
        <div class="product-category">${escapeHtml(product.category?.name || "")}</div>
        <div class="product-name">${escapeHtml(product.name)}</div>
        <div class="price-row"><div class="retail-price">${money(product.retail_price)}</div></div>
        <div class="unit">за ${escapeHtml(product.unit)}</div>
        <div class="stock-note">${out ? "Нет в наличии" : `В наличии: ${escapeHtml(formatStockLabel(product, available))}`}</div>
        <div class="product-bottom">
          <div class="card-cart-controls">
            ${out
              ? `<span class="out-of-stock">Нет в наличии</span>`
              : `<button class="add-btn" type="button" title="Выбрать цену">+</button>${inCart ? `<span class="in-cart-count">В корзине: ${inCart} ${escapeHtml(product.unit)}</span>` : ""}`}
          </div>
        </div>
      </div>`;

    const addButton = card.querySelector(".add-btn");
    if (addButton) {
      addButton.addEventListener("click", (event) => {
        event.stopPropagation();
        openProductModal(product.id);
      });
    }

    const image = card.querySelector("img");
    imageWithFallback(image, product.image_url);
    container.appendChild(card);
  });

  if (!visible.length) {
    const query = $("#searchInput")?.value?.trim();
    container.innerHTML = `
      <div class="empty-search">
        <strong>Товары не найдены</strong>
        <p>${query ? `По запросу «${escapeHtml(query)}» ничего не найдено.` : "В этой категории пока нет товаров."}</p>
      </div>`;
  }
}

function openProductModal(id) {
  const product = products.find((x) => x.id === Number(id));
  if (!product || availableQuantity(product) <= 0) return;

  $("#productModalTitle").textContent = product.name;
  $("#retailChoice").textContent = `Розница — ${money(product.retail_price)} / ${product.unit}`;
  $("#wholesaleChoice").textContent = `Опт — ${money(product.wholesale_price)} / ${product.unit}`;
  $("#productModal").dataset.productId = product.id;
  $("#productModalQty").value = 1;
  $("#productModalError").textContent = "";
  $("#retailRadio").checked = true;
  imageWithFallback($("#productModalImage"), product.image_url);

  const packageInfo = $("#packageInfo");
  if (product.package_type && Number(product.package_quantity) > 1) {
    packageInfo.textContent = `Упаковка: ${product.package_type} — ${product.package_quantity} ${product.unit}`;
    packageInfo.style.display = "block";
  } else {
    packageInfo.style.display = "none";
  }

  $("#productModal").classList.add("active");
}

function closeProductModal() {
  $("#productModal").classList.remove("active");
}

function changeModalQty(delta) {
  const input = $("#productModalQty");
  const product = products.find((x) => x.id === Number($("#productModal").dataset.productId));
  if (!product) return;

  const maxAvailable = availableQuantity(product);
  if (maxAvailable <= 0) {
    input.value = 1;
    return;
  }

  const current = Math.max(1, Number(input.value) || 1);
  input.value = Math.max(1, Math.min(maxAvailable, current + delta));
}

function addSelectedToCart() {
  const modal = $("#productModal");
  const id = Number(modal.dataset.productId);
  const product = products.find((x) => x.id === id);
  if (!product) return;

  const type = document.querySelector("input[name='priceType']:checked")?.value || "retail";
  const quantity = Math.max(1, Number($("#productModalQty").value) || 1);
  const already = getCartQtyForProduct(id);
  const available = Number(product.stock_quantity) - already;

  if (type === "wholesale" && quantity < Number(product.min_wholesale_quantity)) {
    $("#productModalError").textContent = `Для оптовой цены нужно минимум ${product.min_wholesale_quantity} ${product.unit}.`;
    return;
  }

  if (quantity > available) {
    $("#productModalError").textContent = `Доступно только ${formatQuantity(Math.max(0, available))} ${product.unit}.`;
    return;
  }

  const key = cartKey(id, type);
  cart[key] = Number(cart[key] || 0) + quantity;

  closeProductModal();
  renderProducts();
  renderCart();
  flyToCart(product.image_url);
  showToast(`${product.name} добавлен в корзину`);
}

function changeQuantityByKey(key, amount) {
  const { id } = parseKey(key);
  const product = products.find((x) => x.id === id);
  if (!product) return;

  const current = Number(cart[key] || 0);
  const next = current + amount;
  const other = getCartQtyForProduct(id) - current;

  if (next > 0 && other + next > Number(product.stock_quantity)) {
    showToast("Больше этого товара нет в наличии");
    return;
  }

  if (next <= 0) delete cart[key];
  else cart[key] = next;

  renderProducts();
  renderCart();
}

function renderCart() {
  const ids = Object.keys(cart).filter((key) => Number(cart[key]) > 0);
  let count = 0;
  let total = 0;

  ids.forEach((key) => {
    const { id, type } = parseKey(key);
    const product = products.find((x) => x.id === id);
    if (!product) return;

    const quantity = Number(cart[key]);
    count += quantity;
    total += (type === "wholesale" ? Number(product.wholesale_price) : Number(product.retail_price)) * quantity;
  });

  $("#cartCount").textContent = count;
  $("#total").textContent = money(total);
  $("#orderBtn").disabled = !ids.length;

  if (!ids.length) {
    $("#cartItems").innerHTML = `<div class="empty-cart"><div><div class="empty-icon">🛒</div><strong>Корзина пока пустая</strong><p style="margin-top:8px;">Добавьте товары из каталога, чтобы оформить заказ.</p></div></div>`;
    return;
  }

  $("#cartItems").innerHTML = "";
  ids.forEach((key) => {
    const { id, type } = parseKey(key);
    const product = products.find((x) => x.id === id);
    if (!product) return;

    const quantity = Number(cart[key]);
    const price = type === "wholesale" ? Number(product.wholesale_price) : Number(product.retail_price);
    const item = document.createElement("div");
    item.className = "cart-item";
    item.innerHTML = `
      <div class="cart-item-image"><img src="${escapeHtml(product.image_url || FALLBACK_IMAGE)}" alt=""></div>
      <div class="cart-item-info">
        <div class="cart-item-name">${escapeHtml(product.name)}</div>
        <div class="cart-item-price">${type === "wholesale" ? "Опт" : "Розница"}: ${quantity} ${escapeHtml(product.unit)} × ${money(price)}</div>
        <div class="cart-item-controls">
          <button type="button" class="cart-minus">−</button>
          <strong>${quantity}</strong>
          <button type="button" class="cart-plus">+</button>
        </div>
      </div>`;

    item.querySelector(".cart-minus").addEventListener("click", () => changeQuantityByKey(key, -1));
    item.querySelector(".cart-plus").addEventListener("click", () => changeQuantityByKey(key, 1));
    imageWithFallback(item.querySelector("img"), product.image_url);
    $("#cartItems").appendChild(item);
  });
}

function openCart() {
  renderCart();
  $("#cartOverlay").classList.add("active");
  document.body.style.overflow = "hidden";
}

function closeCart() {
  $("#cartOverlay").classList.remove("active");
  document.body.style.overflow = "";
}

function overlayClick(event) {
  if (event.target === $("#cartOverlay")) closeCart();
}

function orderWhatsApp() {
  if (Object.keys(cart).length) $("#checkoutOverlay").classList.add("active");
}

function closeCheckout() {
  $("#checkoutOverlay").classList.remove("active");
}

function getCookie(name) {
  const prefix = `${name}=`;
  return document.cookie.split(";").map((x) => x.trim()).find((x) => x.startsWith(prefix))?.slice(prefix.length) || "";
}

$("#checkoutForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const error = $("#checkoutError");
  error.textContent = "";

  const form = event.target;
  const fd = new FormData(form);
  const items = Object.entries(cart).map(([key, quantity]) => {
    const { id, type } = parseKey(key);
    return { product_id: id, quantity: Number(quantity), price_type: type };
  });

  if (!items.length) {
    error.textContent = "Корзина пуста.";
    return;
  }

  try {
    const csrf = getCookie("csrftoken") || form.querySelector("input[name='csrfmiddlewaretoken']")?.value || "";
    const response = await fetch(`${API}/orders/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf,
        "Accept": "application/json",
      },
      credentials: "same-origin",
      body: JSON.stringify({
        customer_name: fd.get("customer_name"),
        phone: fd.get("phone"),
        address: fd.get("address"),
        comment: fd.get("comment"),
        items,
      }),
    });

    const data = await readResponse(response);
    if (!response.ok) throw new Error(data.detail || "Не удалось создать заказ");

    cart = {};
    await loadProducts();
    renderCart();
    closeCheckout();
    closeCart();
    form.reset();

    if (data.whatsapp_url) {
      window.open(data.whatsapp_url, "_blank", "noopener");
    }
    showToast(`Заказ #${data.order_id} создан`);
  } catch (errorObject) {
    error.textContent = errorObject.message || "Не удалось оформить заказ";
  }
});

let searchTimer;
function handleSearchInput() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(renderProducts, 80);
}
$("#searchInput").addEventListener("input", handleSearchInput);
$("#searchInput").addEventListener("search", handleSearchInput);

let toastTimeout;
function showToast(text) {
  const toast = $("#toast");
  toast.textContent = text;
  toast.classList.add("show");
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => toast.classList.remove("show"), 2200);
}

function flyToCart(image) {
  const button = $(".cart-button");
  if (!button || !image) return;

  const img = document.createElement("img");
  img.src = image;
  img.className = "flying-product";
  img.onerror = () => img.remove();
  document.body.appendChild(img);

  const start = button.getBoundingClientRect();
  img.style.left = `${start.left}px`;
  img.style.top = `${start.top}px`;

  requestAnimationFrame(() => {
    img.style.left = `${start.left + start.width / 2}px`;
    img.style.top = `${start.top + start.height / 2}px`;
    img.style.width = "15px";
    img.style.height = "15px";
    img.style.opacity = "0";
    img.style.transform = "rotate(360deg) scale(.5)";
  });

  setTimeout(() => img.remove(), 750);
}

async function init() {
  try {
    await loadCategories();
    await loadProducts();
  } catch (errorObject) {
    showToast(errorObject.message || "Не удалось загрузить каталог");
  }
  renderCart();
}

init();
