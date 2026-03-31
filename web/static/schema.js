const treeEl = document.getElementById("schema-tree");
const filterEl = document.getElementById("schema-filter");
const clearBtn = document.getElementById("schema-clear");
const viewSelect = document.getElementById("schema-view");
const graphContainer = document.getElementById("graph-container");
const saveGraphBtn = document.getElementById("save-graph-btn");
const fullscreenGraphBtn = document.getElementById("fullscreen-graph-btn");
const exportStandaloneBtn = document.getElementById("export-standalone-btn");

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

const getStoredDraftText = () => {
  return localStorage.getItem("r3xaDraft") || localStorage.getItem("r3xaDraftLast");
};

const getStoredDraft = () => {
  const stored = getStoredDraftText();
  if (!stored) return null;
  return JSON.parse(stored);
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
      out[title] = item;
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
    const payload = getStoredDraft();
    if (!payload) {
      treeEl.textContent = "No draft found. Create one in the editor first.";
      return;
    }
    renderJsonViewer(buildDisplayDraft(payload), true);
  } catch {
    treeEl.textContent = "Failed to load draft.";
  }
};

const renderGraph = async () => {
  const stored = getStoredDraftText();
  if (!graphContainer) return false;
  graphContainer.textContent = "Generating graph…";
  if (!stored) {
    graphContainer.textContent = "No draft found. Create one in the editor first.";
    if (saveGraphBtn) saveGraphBtn.style.display = "none";
    if (fullscreenGraphBtn) fullscreenGraphBtn.style.display = "none";
    return false;
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
        // keep raw detail
      }
      graphContainer.textContent = `Graph error: ${detail}`;
      return false;
    }
    const svgText = await response.text();
    graphContainer.innerHTML = svgText;
    const svg = graphContainer.querySelector("svg");
    if (svg) {
      svg.removeAttribute("width");
      svg.removeAttribute("height");
      svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
    }
    if (saveGraphBtn) saveGraphBtn.style.display = svg ? "" : "none";
    if (fullscreenGraphBtn) fullscreenGraphBtn.style.display = svg ? "" : "none";
    localStorage.setItem("r3xaDraftLast", stored);
    return !!svg;
  } catch (err) {
    graphContainer.textContent = `Failed to generate graph: ${err.message || err}`;
    if (saveGraphBtn) saveGraphBtn.style.display = "none";
    if (fullscreenGraphBtn) fullscreenGraphBtn.style.display = "none";
    return false;
  }
};

const showFullscreenGraph = () => {
  const svg = graphContainer?.querySelector("svg");
  if (!svg) {
    if (graphContainer) graphContainer.textContent = "No graph available. Generate it first.";
    return;
  }

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
    if (w && h) clone.setAttribute("viewBox", `0 0 ${w} ${h}`);
  }
  inner.appendChild(clone);

  const closeBtn = document.createElement("button");
  closeBtn.className = "graph-overlay-close";
  closeBtn.textContent = "Close";
  closeBtn.addEventListener("click", () => overlay.remove());
  inner.appendChild(closeBtn);

  const zoomState = { scale: 1 };
  const applyZoom = () => {
    clone.style.transformOrigin = "0 0";
    clone.style.transform = `scale(${zoomState.scale})`;
    inner.style.overflow = "auto";
  };
  applyZoom();

  clone.addEventListener("click", (event) => {
    event.preventDefault();
    zoomState.scale = Math.min(4, zoomState.scale + 0.2);
    applyZoom();
  });

  clone.addEventListener("contextmenu", (event) => {
    event.preventDefault();
    zoomState.scale = Math.max(1, zoomState.scale - 0.2);
    applyZoom();
  });

  inner.addEventListener("mousemove", (event) => {
    if (zoomState.scale <= 1) return;
    const rect = inner.getBoundingClientRect();
    const x = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width));
    const y = Math.min(1, Math.max(0, (event.clientY - rect.top) / rect.height));
    const maxX = inner.scrollWidth - inner.clientWidth;
    const maxY = inner.scrollHeight - inner.clientHeight;
    inner.scrollLeft = maxX * x;
    inner.scrollTop = maxY * y;
  });

  overlay.appendChild(inner);
  document.body.appendChild(overlay);

  const onKey = (e) => {
    if (e.key === "Escape") {
      overlay.remove();
      document.removeEventListener("keydown", onKey);
    }
  };
  document.addEventListener("keydown", onKey);
};

const saveGraph = () => {
  const svg = graphContainer?.querySelector("svg");
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

const openFullscreenGraph = async () => {
  const hasSvg = graphContainer?.querySelector("svg");
  if (!hasSvg) {
    const ok = await renderGraph();
    if (!ok) return;
  }
  showFullscreenGraph();
};

const escapeHtml = (text) => {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
};

const exportStandaloneHtml = async () => {
  const payload = getStoredDraft();
  if (!payload) {
    if (graphContainer) graphContainer.textContent = "No draft found. Create one in the editor first.";
    return;
  }

  const hasSvg = graphContainer?.querySelector("svg");
  if (!hasSvg) {
    const ok = await renderGraph();
    if (!ok) return;
  }

  const svg = graphContainer?.querySelector("svg");
  const svgMarkup = svg ? svg.outerHTML : "<p>No graph available.</p>";
  const prettyJson = escapeHtml(JSON.stringify(payload, null, 2));
  const generatedAt = new Date().toISOString();

  const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>R3XA Standalone Export</title>
  <style>
    body { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; margin: 0; background: #f5f7fa; color: #17202a; }
    main { max-width: 1100px; margin: 0 auto; padding: 1.5rem; }
    .panel { background: #fff; border: 1px solid #e4e8ee; border-radius: 8px; padding: 1rem; margin-top: 1rem; }
    .muted { color: #5b6673; }
    pre { background: #0b0b0b; color: #e8e8e8; border-radius: 6px; padding: 0.75rem; overflow: auto; }
    .graph svg { width: 100%; height: auto; max-height: 75vh; border: 1px solid #e4e8ee; border-radius: 6px; background: #fff; }
  </style>
</head>
<body>
  <main>
    <h1>R3XA Standalone Export</h1>
    <p class="muted">Generated at ${generatedAt}. This file is self-contained and does not require a server.</p>
    <section class="panel graph">
      <h2>Graph (SVG)</h2>
      ${svgMarkup}
    </section>
    <section class="panel">
      <h2>R3XA Draft JSON</h2>
      <pre>${prettyJson}</pre>
    </section>
  </main>
</body>
</html>`;

  const blob = new Blob([html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "r3xa-standalone.html";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
};

const applyFilter = () => {
  const term = (filterEl?.value || "").trim().toLowerCase();
  const nodes = Array.from(treeEl.querySelectorAll(".jv-light-current, .jv-dark-current"));
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

const bindEvents = () => {
  filterEl?.addEventListener("input", applyFilter);
  clearBtn?.addEventListener("click", () => {
    if (filterEl) filterEl.value = "";
    applyFilter();
  });
  viewSelect?.addEventListener("change", () => {
    if (viewSelect.value === "draft") renderDraft();
    else renderSummary();
  });
  document.getElementById("generate-graph-btn")?.addEventListener("click", renderGraph);
  saveGraphBtn?.addEventListener("click", saveGraph);
  fullscreenGraphBtn?.addEventListener("click", openFullscreenGraph);
  exportStandaloneBtn?.addEventListener("click", exportStandaloneHtml);
  graphContainer?.addEventListener("click", () => {
    if (graphContainer.querySelector("svg")) showFullscreenGraph();
  });
};

window.renderGraph = renderGraph;
window.showFullscreenGraph = showFullscreenGraph;

ensureServerStart();
bindEvents();
if (getStoredDraft() && viewSelect) {
  viewSelect.value = "draft";
}
if (viewSelect?.value === "draft") renderDraft();
else renderSummary();
