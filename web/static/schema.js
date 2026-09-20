const t = (key, fallback, values) => window.R3XAI18N?.t(key, fallback, values) || fallback;
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

const setGraphActionVisible = (element, visible) => {
  element?.classList.toggle("graph-action-hidden", !visible);
};

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

const jsonValueClass = (value) => {
  if (value === null) return "jv-light-rightNull";
  if (typeof value === "number") return "jv-light-rightNumber";
  if (typeof value === "boolean") return "jv-light-rightBoolean";
  return "jv-light-rightString";
};

const renderJsonViewer = (data, expand = false) => {
  treeEl.replaceChildren();
  const container = document.createElement("div");
  container.className = "jv-light-con";
  treeEl.appendChild(container);

  const renderEntry = (key, value, parent, depth) => {
    const row = document.createElement("div");
    row.className = "jv-light-current";
    row.style.paddingLeft = `${depth * 20 + 20}px`;
    const left = document.createElement("span");
    left.className = "jv-light-left";
    const isObject = value !== null && typeof value === "object";
    if (isObject) {
      const toggle = document.createElement("span");
      toggle.className = `jv-folder jv-light-folder${expand ? " rotate90" : ""}`;
      toggle.setAttribute("role", "button");
      toggle.setAttribute("tabindex", "0");
      toggle.setAttribute("aria-label", t("schema.toggle", `Toggle ${key}`, {key}));
      left.appendChild(toggle);
      const size = Array.isArray(value) ? value.length : Object.keys(value).length;
      left.appendChild(document.createTextNode(`${String(key)}  ${Array.isArray(value) ? `[${size}]` : `{${size}}`}`));
      row.appendChild(left);

      const children = document.createElement("div");
      children.className = `jv-light-rightObj${expand ? " add-height" : ""}`;
      const toggleChildren = () => {
        children.classList.toggle("add-height");
        toggle.classList.toggle("rotate90");
      };
      toggle.addEventListener("click", toggleChildren);
      toggle.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          toggleChildren();
        }
      });
      const entries = Array.isArray(value)
        ? value.map((entry, index) => [index, entry])
        : Object.entries(value);
      entries.forEach(([childKey, childValue]) => renderEntry(childKey, childValue, children, depth + 1));
      row.appendChild(children);
    } else {
      left.textContent = `${String(key)}: `;
      const right = document.createElement("span");
      right.className = jsonValueClass(value);
      right.textContent = JSON.stringify(value);
      row.appendChild(left);
      row.appendChild(right);
    }
    parent.appendChild(row);
  };

  renderEntry("$", data, container, 0);
};

const renderSummary = async () => {
  try {
    if (!cachedSummary) {
      cachedSummary = await window.R3XARuntime.loadSchemaSummary();
    }
    renderJsonViewer(cachedSummary, true);
  } catch {
    treeEl.textContent = t("schema.failed_summary", "Failed to load schema summary.");
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
      treeEl.textContent = t("schema.no_draft", "No draft found. Create one in the editor first.");
      return;
    }
    renderJsonViewer(buildDisplayDraft(payload), true);
  } catch {
    treeEl.textContent = t("schema.failed_draft", "Failed to load draft.");
  }
};

const sanitizeSvg = (content) => {
  const parsed = new DOMParser().parseFromString(content, "image/svg+xml");
  if (parsed.querySelector("parsererror") || parsed.documentElement?.nodeName.toLowerCase() !== "svg") {
    throw new Error("Graph response is not a valid SVG document.");
  }
  const allowedElements = new Set([
    "svg", "g", "path", "polygon", "polyline", "ellipse", "rect", "text", "tspan",
    "title", "desc", "line", "circle", "clipPath", "defs", "use", "marker",
  ]);
  const elements = [parsed.documentElement, ...parsed.querySelectorAll("*")];
  elements.forEach((element) => {
    if (!allowedElements.has(element.tagName)) {
      element.remove();
      return;
    }
    [...element.attributes].forEach((attribute) => {
      const name = attribute.name.toLowerCase();
      const value = attribute.value.trim().toLowerCase();
      const isLocalUseReference = element.tagName.toLowerCase() === "use"
        && (name === "href" || name.endsWith(":href"))
        && value.startsWith("#");
      if (name.startsWith("on") || name === "src"
        || ((name === "href" || name.endsWith(":href")) && !isLocalUseReference)
        || value.includes("javascript:") || value.includes("data:text/html")) {
        element.removeAttribute(attribute.name);
      }
    });
  });
  return document.importNode(parsed.documentElement, true);
};

const renderGraph = async () => {
  const stored = getStoredDraftText();
  if (!graphContainer) return false;
  graphContainer.textContent = t("schema.generating", "Generating graph…");
  currentGraph = null;
  if (!stored) {
    graphContainer.textContent = t("schema.no_draft", "No draft found. Create one in the editor first.");
    setGraphActionVisible(saveGraphBtn, false);
    setGraphActionVisible(fullscreenGraphBtn, false);
    return false;
  }
  try {
    const payload = JSON.parse(stored);
    const backend = graphBackendSelect
      ? graphBackendSelect.value
      : (window.R3XARuntime?.graphBackends?.[0] || "graphviz");
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
      graphContainer.textContent = t("schema.graph_error", "Graph error: {message}", {message: detail});
      return false;
    }
    const content = await response.text();
    const isPyvis = backend === "pyvis";
    currentGraph = {
      backend,
      data: content,
      extension: isPyvis ? "html" : "svg",
      mediaType: isPyvis ? "text/html" : "image/svg+xml",
    };
    if (isPyvis) {
      const frame = document.createElement("iframe");
      frame.className = "graph-frame";
      frame.title = t("schema.interactive_graph", "Interactive R3XA graph");
      frame.sandbox.add("allow-scripts");
      frame.srcdoc = content;
      graphContainer.replaceChildren(frame);
    } else {
      const svg = sanitizeSvg(content);
      graphContainer.replaceChildren(svg);
      if (svg) {
        svg.removeAttribute("width");
        svg.removeAttribute("height");
        svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
      }
    }
    setGraphActionVisible(saveGraphBtn, !!currentGraph);
    setGraphActionVisible(fullscreenGraphBtn, !!currentGraph);
    setGraphActionVisible(exportStandaloneBtn, backend === "graphviz");
    localStorage.setItem("r3xaDraftLast", stored);
    return !!currentGraph;
  } catch (err) {
    graphContainer.textContent = t("schema.failed_graph", "Failed to generate graph: {message}", {message: err.message || err});
    currentGraph = null;
    setGraphActionVisible(saveGraphBtn, false);
    setGraphActionVisible(fullscreenGraphBtn, false);
    setGraphActionVisible(exportStandaloneBtn, false);
    return false;
  }
};

const showFullscreenGraph = () => {
  const svg = graphContainer?.querySelector("svg");
  const visual = svg || graphContainer?.querySelector("img, iframe");
  if (!visual) {
    if (graphContainer) graphContainer.textContent = t("schema.no_graph", "No graph available. Generate it first.");
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
    closeBtn.textContent = t("schema.close", "Close");
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
  closeBtn.textContent = t("schema.close", "Close");
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
    if (graphContainer) graphContainer.textContent = t("schema.no_draft", "No draft found. Create one in the editor first.");
    return;
  }

  const hasSvg = graphContainer?.querySelector("svg");
  if (!hasSvg) {
    const ok = await renderGraph();
    if (!ok) return;
  }

  const svg = graphContainer?.querySelector("svg");
  const svgMarkup = svg ? svg.outerHTML : `<p>${t("schema.no_graph", "No graph available. Generate it first.")}</p>`;
  const prettyJson = escapeHtml(JSON.stringify(payload, null, 2));
  const generatedAt = new Date().toISOString();

  const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>${t("schema.standalone_title", "R3XA Standalone Export")}</title>
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
    <h1>${t("schema.standalone_title", "R3XA Standalone Export")}</h1>
    <p class="muted">${t("schema.standalone_help", "Generated at {date}. This file is self-contained and does not require a server.", {date: generatedAt})}</p>
    <section class="panel graph">
      <h2>${t("schema.standalone_graph", "Graph (SVG)")}</h2>
      ${svgMarkup}
    </section>
    <section class="panel">
      <h2>${t("schema.standalone_json", "R3XA Draft JSON")}</h2>
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
  if (graphvizOption) {
    const graphvizLabel = window.R3XARuntime.mode === "static"
      ? ["schema.graphviz_browser", "Graphviz WebAssembly · SVG · browser"]
      : ["schema.graphviz_native", "Graphviz · SVG · system dot"];
    graphvizOption.dataset.i18n = graphvizLabel[0];
    graphvizOption.textContent = t(graphvizLabel[0], graphvizLabel[1]);
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
