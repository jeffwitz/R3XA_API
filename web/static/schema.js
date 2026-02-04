const treeEl = document.getElementById("schema-tree");
const filterEl = document.getElementById("schema-filter");
const clearBtn = document.getElementById("schema-clear");
const summaryToggle = document.getElementById("schema-summary-toggle");

let cachedSummary = null;
let cachedSchema = null;

const renderJsonViewer = (data) => {
  treeEl.innerHTML = "";
  const container = document.createElement("div");
  treeEl.appendChild(container);
  new JSONViewer({
    container,
    data: JSON.stringify(data, null, 2),
    theme: "light",
    expand: false,
  });
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
  const nodes = Array.from(
    treeEl.querySelectorAll(".jv-light-current, .jv-dark-current")
  );
  if (!nodes.length) return;

  if (!term) {
    nodes.forEach((node) => {
      node.style.display = "";
    });
    return;
  }

  nodes.forEach((node) => {
    const text = node.textContent.toLowerCase();
    node.style.display = text.includes(term) ? "" : "none";
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
