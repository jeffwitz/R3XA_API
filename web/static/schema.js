const treeEl = document.getElementById("schema-tree");
const filterEl = document.getElementById("schema-filter");
const clearBtn = document.getElementById("schema-clear");
const viewSelect = document.getElementById("schema-view");
const graphContainer = document.getElementById("graph-container");
const saveGraphBtn = document.getElementById("save-graph-btn");
const fullscreenGraphBtn = document.getElementById("fullscreen-graph-btn");
const exportStandaloneBtn = document.getElementById("export-standalone-btn");
const graphDescriptionToggle = document.getElementById("graph-show-description");
const graphPaletteSelect = document.getElementById("graph-palette");
const graphBackendSelect = document.getElementById("graph-backend");

let cachedSummary = null;
let currentGraph = null;
let graphObjectUrl = null;

const ensureServerStart = () => {
  const appStart = document.body?.dataset?.appStart;
  if (!appStart) return;
  const stored = localStorage.getItem("r3xaAppStart");
  if (stored !== appStart) {
    localStorage.setItem("r3xaAppStart", appStart);
  }
};

const getStoredDraftText = () => {
  return localStorage.getItem("r3xaDraft") || localStorage.getItem("r3xaDraftLast");
};

const getStoredDraft = () => {
  const stored = getStoredDraftText();
  if (!stored) return null;
  try {
    const parsed = JSON.parse(stored);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : null;
  } catch {
    return null;
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
      cachedSummary = await window.R3XARuntime.loadSchemaSummary();
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
  currentGraph = null;
  if (graphObjectUrl) {
    URL.revokeObjectURL(graphObjectUrl);
    graphObjectUrl = null;
  }
  if (!stored) {
    graphContainer.textContent = "No draft found. Create one in the editor first.";
    if (saveGraphBtn) saveGraphBtn.style.display = "none";
    if (fullscreenGraphBtn) fullscreenGraphBtn.style.display = "none";
    return false;
  }
  try {
    const payload = JSON.parse(stored);
    const backend = graphBackendSelect ? graphBackendSelect.value : "graphviz";
    const showDescription = graphDescriptionToggle ? graphDescriptionToggle.checked : true;
    const palette = graphPaletteSelect ? graphPaletteSelect.value : "document";
    const response = await window.R3XARuntime.renderGraph(payload, {
      showDescription,
      palette,
      backend,
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
    if (backend === "matplotlib") {
      const blob = await response.blob();
      graphObjectUrl = URL.createObjectURL(blob);
      const image = document.createElement("img");
      image.className = "graph-image";
      image.src = graphObjectUrl;
      image.alt = "R3XA graph rendered with Matplotlib";
      graphContainer.replaceChildren(image);
      currentGraph = {backend, data: blob, extension: "png", mediaType: "image/png"};
    } else {
      const content = await response.text();
      currentGraph = {
        backend,
        data: content,
        extension: backend === "pyvis" ? "html" : "svg",
        mediaType: backend === "pyvis" ? "text/html" : "image/svg+xml",
      };
      if (backend === "pyvis") {
        const frame = document.createElement("iframe");
        frame.className = "graph-frame";
        frame.title = "Interactive R3XA graph";
        frame.srcdoc = content;
        graphContainer.replaceChildren(frame);
      } else {
        graphContainer.innerHTML = content;
        const svg = graphContainer.querySelector("svg");
        if (svg) {
          svg.removeAttribute("width");
          svg.removeAttribute("height");
          svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
        }
      }
    }
    if (saveGraphBtn) saveGraphBtn.style.display = currentGraph ? "" : "none";
    if (fullscreenGraphBtn) fullscreenGraphBtn.style.display = currentGraph ? "" : "none";
    if (exportStandaloneBtn) exportStandaloneBtn.style.display = backend === "graphviz" ? "" : "none";
    localStorage.setItem("r3xaDraftLast", stored);
    return !!currentGraph;
  } catch (err) {
    graphContainer.textContent = `Failed to generate graph: ${err.message || err}`;
    currentGraph = null;
    if (saveGraphBtn) saveGraphBtn.style.display = "none";
    if (fullscreenGraphBtn) fullscreenGraphBtn.style.display = "none";
    if (exportStandaloneBtn) exportStandaloneBtn.style.display = "none";
    return false;
  }
};

const showFullscreenGraph = () => {
  const svg = graphContainer?.querySelector("svg");
  const visual = svg || graphContainer?.querySelector("img, iframe");
  if (!visual) {
    if (graphContainer) graphContainer.textContent = "No graph available. Generate it first.";
    return;
  }

  if (!svg) {
    const overlay = document.createElement("div");
    overlay.className = "graph-overlay";
    overlay.addEventListener("click", () => overlay.remove());
    const inner = document.createElement("div");
    inner.className = "graph-overlay-inner graph-overlay-media";
    inner.addEventListener("click", (event) => event.stopPropagation());
    inner.appendChild(visual.cloneNode(true));
    const closeBtn = document.createElement("button");
    closeBtn.className = "graph-overlay-close";
    closeBtn.textContent = "Close";
    closeBtn.addEventListener("click", () => overlay.remove());
    inner.appendChild(closeBtn);
    overlay.appendChild(inner);
    document.body.appendChild(overlay);
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
  if (!currentGraph) return;
  const blob = currentGraph.data instanceof Blob
    ? currentGraph.data
    : new Blob([currentGraph.data], {type: currentGraph.mediaType});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `r3xa-graph.${currentGraph.extension}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
};

const openFullscreenGraph = async () => {
  if (!currentGraph) {
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
  graphPaletteSelect?.addEventListener("change", renderGraph);
  graphBackendSelect?.addEventListener("change", renderGraph);
  document.getElementById("generate-graph-btn")?.addEventListener("click", renderGraph);
  saveGraphBtn?.addEventListener("click", saveGraph);
  fullscreenGraphBtn?.addEventListener("click", openFullscreenGraph);
  exportStandaloneBtn?.addEventListener("click", exportStandaloneHtml);
  graphContainer?.addEventListener("click", () => {
    if (graphContainer.querySelector("svg")) showFullscreenGraph();
  });
};

const configureGraphBackends = () => {
  if (!graphBackendSelect || !Array.isArray(window.R3XARuntime?.graphBackends)) return;
  const supported = new Set(window.R3XARuntime.graphBackends);
  const graphvizOption = graphBackendSelect.querySelector('option[value="graphviz"]');
  if (graphvizOption && window.R3XARuntime.mode === "static") {
    graphvizOption.textContent = "Graphviz WebAssembly · SVG · browser";
  }
  Array.from(graphBackendSelect.options).forEach((option) => {
    const enabled = supported.has(option.value);
    option.hidden = !enabled;
    option.disabled = !enabled;
  });
  if (!supported.has(graphBackendSelect.value)) {
    graphBackendSelect.value = window.R3XARuntime.graphBackends[0] || "graphviz";
  }
};

window.renderGraph = renderGraph;
window.showFullscreenGraph = showFullscreenGraph;

ensureServerStart();
configureGraphBackends();
bindEvents();
if (getStoredDraft() && viewSelect) {
  viewSelect.value = "draft";
}
if (viewSelect?.value === "draft") renderDraft();
else renderSummary();
