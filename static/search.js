const qInput = document.getElementById("q");
const categorySelect = document.getElementById("category");
const minPriceInput = document.getElementById("minPrice");
const maxPriceInput = document.getElementById("maxPrice");
const autoClearInput = document.getElementById("autoClear");
const searchBtn = document.getElementById("searchBtn");
const statusEl = document.getElementById("status");
const errorEl = document.getElementById("error");
const resultsTable = document.getElementById("resultsTable");
const resultsBody = document.getElementById("resultsBody");

function renderRows(items) {
  resultsBody.innerHTML = "";
  items.forEach((item, idx) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${idx + 1}</td>
      <td>${item.product_name}</td>
      <td><span class="badge">${item.category}</span></td>
      <td><span class="qty">${item.quantity}</span></td>
      <td><span class="price">₹${item.price.toFixed(2)}</span></td>
    `;
    resultsBody.appendChild(tr);
  });
}

function showNoResults() {
  resultsTable.hidden = true;
  statusEl.textContent = "No results found.";
}

async function fetchResults() {
  errorEl.textContent = "";
  statusEl.textContent = "Loading...";

  const q = qInput.value.trim();
  const category = categorySelect.value;
  const minPrice = minPriceInput.value.trim();
  const maxPrice = maxPriceInput.value.trim();

  if (minPrice && maxPrice && Number(minPrice) > Number(maxPrice)) {
    statusEl.textContent = "";
    errorEl.textContent = "Invalid price range: min price cannot be greater than max price.";
    resultsTable.hidden = true;
    return;
  }

  const params = new URLSearchParams();
  if (q) params.append("q", q);
  if (category) params.append("category", category);
  if (minPrice) params.append("minPrice", minPrice);
  if (maxPrice) params.append("maxPrice", maxPrice);

  const res = await fetch(`/search?${params.toString()}`);
  const data = await res.json();

  if (!res.ok) {
    statusEl.textContent = "";
    errorEl.textContent = data.detail || "Failed to fetch results.";
    resultsTable.hidden = true;
    return;
  }

  if (!data.results.length) {
    showNoResults();
    if (autoClearInput.checked) {
      qInput.value = "";
    }
    return;
  }

  renderRows(data.results);
  resultsTable.hidden = false;
  statusEl.textContent = `${data.count} result(s) found.`;
  if (autoClearInput.checked) {
    qInput.value = "";
  }
}

async function loadCategories() {
  const res = await fetch("/search");
  const data = await res.json();
  const categories = [...new Set(data.results.map((item) => item.category))].sort();
  categories.forEach((cat) => {
    const option = document.createElement("option");
    option.value = cat;
    option.textContent = cat;
    categorySelect.appendChild(option);
  });
}

searchBtn.addEventListener("click", fetchResults);
qInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") fetchResults();
});
window.addEventListener("load", async () => {
  await loadCategories();
  await fetchResults();
});
