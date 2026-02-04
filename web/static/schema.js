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
  if (typeof JSONViewer === "undefined") {
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(data, null, 2);
    container.appendChild(pre);
    return;
  }
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
    const stored =
      localStorage.getItem("r3xaDraft") ||
      localStorage.getItem("r3xaDraftLast");
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

const renderGraph = async () => {
  const stored =
    localStorage.getItem("r3xaDraft") ||
    localStorage.getItem("r3xaDraftLast");
  const container = document.getElementById("graph-container");
  const saveBtn = document.getElementById("save-graph-btn");
  const fullscreenBtn = document.getElementById("fullscreen-graph-btn");
  if (!container) return;
  container.textContent = "Generating graph…";
  if (!stored) {
    container.textContent = "No draft found. Create one in the editor first.";
    if (saveBtn) saveBtn.style.display = "none";
    if (fullscreenBtn) fullscreenBtn.style.display = "none";
    return;
  }
  try {
    const payload = JSON.parse(stored);
    const response = await fetch("/api/graph", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      let detail = await response.text();
      try {
        const parsed = JSON.parse(detail);
        detail = parsed.detail || detail;
      } catch {
        // keep text
      }
      container.textContent = `Graph error: ${detail}`;
      return;
    }
    const svgText = await response.text();
    container.innerHTML = svgText;
    const svg = container.querySelector("svg");
    if (svg) {
      svg.removeAttribute("width");
      svg.removeAttribute("height");
      svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    }
    if (saveBtn) saveBtn.style.display = svg ? "" : "none";
    if (fullscreenBtn) fullscreenBtn.style.display = svg ? "" : "none";
    localStorage.setItem("r3xaDraftLast", stored);
  } catch (err) {
    container.textContent = `Failed to generate graph: ${err.message || err}`;
    if (saveBtn) saveBtn.style.display = "none";
    if (fullscreenBtn) fullscreenBtn.style.display = "none";
  }
};

const showFullscreenGraph = () => {
  const container = document.getElementById("graph-container");
  const svg = container?.querySelector("svg");
  if (!svg) return;

  const overlay = document.createElement("div");
  overlay.className = "graph-overlay";
  overlay.addEventListener("click", () => overlay.remove());

  const inner = document.createElement("div");
  inner.className = "graph-overlay-inner";
  inner.addEventListener("click", (event) => event.stopPropagation());
  const clone = svg.cloneNode(true);
  if (!clone.getAttribute("viewBox")) {
    const w = svg.viewBox?.baseVal?.width || svg.getAttribute("width") || 0;
    const h = svg.viewBox?.baseVal?.height || svg.getAttribute("height") || 0;
    if (w && h) {
      clone.setAttribute("viewBox", `0 0 ${w} ${h}`);
    }
  }
  inner.appendChild(clone);

  const closeBtn = document.createElement("button");
  closeBtn.className = "graph-overlay-close";
  closeBtn.textContent = "Close";
  closeBtn.addEventListener("click", () => overlay.remove());
  inner.appendChild(closeBtn);

  overlay.appendChild(inner);
  document.body.appendChild(overlay);
};

window.showFullscreenGraph = showFullscreenGraph;

const saveGraph = () => {
  const container = document.getElementById("graph-container");
  const svg = container?.querySelector("svg");
  if (!svg) return;
  const serializer = new XMLSerializer();
  const svgText = serializer.serializeToString(svg);
  const blob = new Blob([svgText], { type: "image/svg+xml" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "r3xa-graph.svg";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
};

document.getElementById("save-graph-btn")?.addEventListener("click", saveGraph);

window.renderGraph = renderGraph;

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

const bindGraphButton = () => {
  const btn = document.getElementById("generate-graph-btn");
  if (!btn) return false;
  btn.addEventListener("click", () => {
    const container = document.getElementById("graph-container");
    if (container) container.textContent = "Click received…";
    renderGraph();
  });
  return true;
};

if (!bindGraphButton()) {
  document.addEventListener("DOMContentLoaded", bindGraphButton);
}

const bindGraphContainer = () => {
  const container = document.getElementById("graph-container");
  if (!container) return false;
  container.addEventListener("click", () => {
    showFullscreenGraph();
  });
  return true;
};

if (!bindGraphContainer()) {
  document.addEventListener("DOMContentLoaded", bindGraphContainer);
}
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
