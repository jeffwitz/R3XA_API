const treeEl = document.getElementById("schema-tree");
const filterEl = document.getElementById("schema-filter");
const clearBtn = document.getElementById("schema-clear");
const viewSelect = document.getElementById("schema-view");

let cachedSummary = null;

const ensureServerStart = () => {
  const appStart = document.body?.dataset?.appStart;
  if (!appStart) return;
  const stored = localStorage.getItem("r3xaAppStart");
  if (stored !== appStart) {
    localStorage.setItem("r3xaAppStart", appStart);
    localStorage.removeItem("r3xaDraft");
  }
};

const renderJsonViewer = (data, expand = false) => {
  treeEl.innerHTML = "";
  const container = document.createElement("div");
  treeEl.appendChild(container);
  new JSONViewer({
    container,
    data: JSON.stringify(data, null, 2),
    theme: "light",
    expand,
  });
};

const renderSummary = async () => {
  try {
    if (!cachedSummary) {
      const response = await fetch("/api/schema/summary");
      cachedSummary = await response.json();
    }
    renderJsonViewer(cachedSummary, true);
  } catch {
    treeEl.textContent = "Failed to load schema summary.";
  }
};

const buildDisplayDraft = (payload) => {
  const clone = JSON.parse(JSON.stringify(payload));
  const mapArray = (items) => {
    const out = {};
    (items || []).forEach((item, index) => {
      const title = item?.title || item?.id || `item_${index + 1}`;
      const key = `${title}`;
      out[key] = item;
    });
    return out;
  };
  clone.settings = mapArray(clone.settings);
  clone.data_sources = mapArray(clone.data_sources);
  clone.data_sets = mapArray(clone.data_sets);
  return clone;
};

const renderDraft = () => {
  try {
    const stored = localStorage.getItem("r3xaDraft");
    if (!stored) {
      treeEl.textContent = "No draft found. Create one in the editor first.";
      return;
    }
    const payload = JSON.parse(stored);
    renderJsonViewer(buildDisplayDraft(payload), true);
  } catch {
    treeEl.textContent = "Failed to load draft.";
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

viewSelect?.addEventListener("change", () => {
  const view = viewSelect.value;
  if (view === "draft") {
    renderDraft();
  } else {
    renderSummary();
  }
});

ensureServerStart();
const hasDraft = !!localStorage.getItem("r3xaDraft");
if (hasDraft && viewSelect) {
  viewSelect.value = "draft";
}
if (viewSelect?.value === "draft") {
  renderDraft();
} else {
  renderSummary();
}
