const treeEl = document.getElementById("schema-tree");
const filterEl = document.getElementById("schema-filter");
const clearBtn = document.getElementById("schema-clear");
const summaryToggle = document.getElementById("schema-summary-toggle");

let cachedSummary = null;
let cachedSchema = null;

const renderJsonViewer = (data) => {
  treeEl.innerHTML = "";
  const viewer = new JSONViewer();
  treeEl.appendChild(viewer.getContainer());
  viewer.showJSON(data, null, 2);
};

const renderSummary = async () => {
  try {
    if (!cachedSummary) {
      const response = await fetch("/api/schema/summary");
      cachedSummary = await response.json();
    }
    renderJsonViewer(cachedSummary);
  } catch {
    treeEl.textContent = "Failed to load schema summary.";
  }
};

const renderSchema = async () => {
  try {
    if (!cachedSchema) {
      const response = await fetch("/api/schema");
      cachedSchema = await response.json();
    }
    renderJsonViewer(cachedSchema);
  } catch {
    treeEl.textContent = "Failed to load schema.";
  }
};

const applyFilter = () => {
  const term = (filterEl?.value || "").trim().toLowerCase();
  if (!term) {
    treeEl.querySelectorAll("li").forEach((li) => {
      li.style.display = "";
    });
    return;
  }

  treeEl.querySelectorAll("li").forEach((li) => {
    const text = li.textContent.toLowerCase();
    li.style.display = text.includes(term) ? "" : "none";
  });
};

filterEl?.addEventListener("input", applyFilter);
clearBtn?.addEventListener("click", () => {
  if (filterEl) filterEl.value = "";
  applyFilter();
});

summaryToggle?.addEventListener("change", () => {
  if (summaryToggle.checked) {
    renderSummary();
  } else {
    renderSchema();
  }
});

renderSummary();
