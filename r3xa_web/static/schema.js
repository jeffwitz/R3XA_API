const t = (key, fallback, values) => window.R3XAI18N?.t(key, fallback, values) || fallback;
const treeEl = document.getElementById("schema-tree");
const filterEl = document.getElementById("schema-filter");
const clearBtn = document.getElementById("schema-clear");
const viewSelect = document.getElementById("schema-view");
const graphContainer = document.getElementById("graph-container");
const graphWorkspace = document.getElementById("graph-workspace");
const graphInspector = document.getElementById("graph-inspector");
const graphInspectorTitle = document.getElementById("graph-inspector-title");
const graphInspectorKind = document.getElementById("graph-inspector-kind");
const graphInspectorId = document.getElementById("graph-inspector-id");
const graphInspectorFields = document.getElementById("graph-inspector-fields");
const graphInspectorEditBtn = document.getElementById("graph-inspector-edit-btn");
const graphInspectorValidateBtn = document.getElementById("graph-inspector-validate-btn");
const graphInspectorCancelBtn = document.getElementById("graph-inspector-cancel-btn");
const graphInspectorStatus = document.getElementById("graph-inspector-status");
const saveGraphBtn = document.getElementById("save-graph-btn");
const fullscreenGraphBtn = document.getElementById("fullscreen-graph-btn");
const fitGraphBtn = document.getElementById("fit-graph-btn");
const zoomOutGraphBtn = document.getElementById("zoom-out-graph-btn");
const zoomInGraphBtn = document.getElementById("zoom-in-graph-btn");
const exportStandaloneBtn = document.getElementById("export-standalone-btn");
const graphNavigationHelp = document.querySelector(".graph-navigation-help");
const graphDescriptionToggle = document.getElementById("graph-show-description");
const graphPaletteSelect = document.getElementById("graph-palette");
const graphRelationSelect = document.getElementById("graph-relations");
const graphBackendSelect = document.getElementById("graph-backend");

let cachedSummary = null;
let cachedCatalog = null;
let currentGraph = null;
let inspectorRequest = 0;
let selectedGraphSelection = null;
let selectedGraphProperties = {};
let graphInspectorEditing = false;

const setGraphActionVisible = (element, visible) => {
  element?.classList.toggle("graph-action-hidden", !visible);
};

const setGraphNavigationHelpVisible = (visible) => {
  if (graphNavigationHelp) graphNavigationHelp.hidden = !visible;
};

const setGraphInspectorVisible = (visible) => {
  graphWorkspace?.classList.toggle("graph-workspace-interactive", visible);
  if (graphInspector) graphInspector.hidden = !visible;
};

const setGraphInspectorActions = (selection, editing) => {
  const hasSelection = Boolean(selection?.item);
  if (graphInspectorEditBtn) graphInspectorEditBtn.hidden = !hasSelection || editing;
  if (graphInspectorValidateBtn) graphInspectorValidateBtn.hidden = !hasSelection || !editing;
  if (graphInspectorCancelBtn) graphInspectorCancelBtn.hidden = !hasSelection || !editing;
};

const renderInspectorValue = (value) => {
  if (value === undefined) return "—";
  if (value === null) return "null";
  if (typeof value === "string") return value;
  return JSON.stringify(value, null, 2);
};

const propertyTypes = (property) => {
  if (Array.isArray(property?.type)) return property.type;
  if (property?.type) return [property.type];
  if (property?.properties) return ["object"];
  if (property?.items) return ["array"];
  return [];
};

const propertyEnum = (property) => {
  if (Array.isArray(property?.enum)) return property.enum;
  if (!Array.isArray(property?.oneOf)) return [];
  return property.oneOf
    .filter((variant) => Object.prototype.hasOwnProperty.call(variant || {}, "const"))
    .map((variant) => variant.const);
};

const editorValueType = (property, value) => {
  const types = propertyTypes(property);
  if (value === null && types.includes("null")) return "null";
  if (Array.isArray(value) || types.includes("array")) return "array";
  if (value !== null && typeof value === "object" || types.includes("object")) return "object";
  if (types.includes("boolean")) return "boolean";
  if (types.includes("number") || types.includes("integer")) return types.find((type) => type !== "null");
  return "string";
};

const referenceSectionFor = (property) => {
  const reference = property?.ref || property?.items?.ref || property?.$ref || property?.items?.$ref;
  if (!reference) return null;
  if (String(reference).endsWith("setting_id")) return "settings";
  if (String(reference).endsWith("data_source_id")) return "data_sources";
  if (String(reference).endsWith("data_set_id")) return "data_sets";
  return null;
};

const inspectorReferenceCandidates = (section) => {
  const payload = getStoredDraft();
  return Array.isArray(payload?.[section])
    ? payload[section].filter((item) => item && typeof item === "object" && typeof item.id === "string" && item.id)
    : [];
};

const inspectorReferenceLabel = (item, section) => (
  `${item.title || t("schema.untitled_object", "Untitled object")} · ${item.kind || section} · ${item.id}`
);

const inspectorReferenceIds = (value) => (
  Array.isArray(value) ? value.filter((item) => typeof item === "string" && item) : typeof value === "string" && value ? [value] : []
);

const createInspectorReferenceEditor = (key, property, value, section) => {
  const currentIds = inspectorReferenceIds(value);
  const candidates = inspectorReferenceCandidates(section);
  const choices = new Map(candidates.map((item) => [item.id, inspectorReferenceLabel(item, section)]));
  currentIds.forEach((id) => {
    if (!choices.has(id)) choices.set(id, t("schema.missing_object", "Missing object · {id}", {id}));
  });
  const isArray = propertyTypes(property).includes("array");
  if (isArray) {
    const wrapper = document.createElement("div");
    wrapper.className = "reference-checklist graph-inspector-reference-checklist";
    wrapper.dataset.inspectorField = key;
    wrapper.dataset.inspectorType = "reference-array";
    wrapper.dataset.inspectorReferenceSection = section;
    wrapper.dataset.inspectorInitialCount = String(currentIds.length);
    const selectedIds = new Set(currentIds);
    choices.forEach((label, id) => {
      const option = document.createElement("label");
      option.className = "reference-option";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.value = id;
      checkbox.checked = selectedIds.has(id);
      option.append(checkbox, document.createTextNode(label));
      wrapper.appendChild(option);
    });
    if (!choices.size) {
      const empty = document.createElement("small");
      empty.className = "field-description";
      empty.textContent = t("field.no_compatible_objects", "No compatible objects have been created yet.");
      wrapper.appendChild(empty);
    }
    return wrapper;
  }
  const control = document.createElement("select");
  control.dataset.inspectorField = key;
  control.dataset.inspectorType = "reference";
  control.dataset.inspectorReferenceSection = section;
  const blank = document.createElement("option");
  blank.value = "";
  blank.textContent = t("field.select_object", "Select an object…");
  control.appendChild(blank);
  choices.forEach((label, id) => {
    const option = document.createElement("option");
    option.value = id;
    option.textContent = label;
    option.selected = currentIds.includes(id);
    control.appendChild(option);
  });
  if (!choices.size) control.disabled = true;
  return control;
};

const createInspectorEditor = (key, property, value) => {
  const referenceSection = referenceSectionFor(property);
  if (referenceSection) {
    return createInspectorReferenceEditor(key, property, value, referenceSection);
  }
  const enumValues = propertyEnum(property);
  const type = editorValueType(property, value);
  const isComplex = type === "array" || type === "object";
  let control;
  if (enumValues.length) {
    control = document.createElement("select");
    enumValues.forEach((optionValue) => {
      const option = document.createElement("option");
      option.value = String(optionValue);
      option.textContent = String(optionValue);
      control.appendChild(option);
    });
  } else if (type === "boolean") {
    control = document.createElement("input");
    control.type = "checkbox";
    control.checked = value === true;
  } else if (isComplex || key === "description" || key === "documentation" || String(value || "").length > 120) {
    control = document.createElement("textarea");
    control.rows = 4;
    control.value = value === undefined ? "" : isComplex ? JSON.stringify(value, null, 2) : String(value);
  } else {
    control = document.createElement("input");
    control.type = type === "number" || type === "integer" ? "number" : "text";
    if (type === "number" || type === "integer") control.step = type === "integer" ? "1" : "any";
    control.value = value === undefined || value === null ? "" : String(value);
  }
  control.dataset.inspectorField = key;
  control.dataset.inspectorType = type;
  control.className = "graph-inspector-control";
  if (key === "id" || key === "kind" || Object.prototype.hasOwnProperty.call(property || {}, "const")) {
    control.disabled = true;
  }
  return control;
};

const renderInspectorFields = (selection, properties, editing) => {
  if (!graphInspectorFields) return;
  const keys = [...Object.keys(properties), ...Object.keys(selection.item).filter((key) => !(key in properties))];
  graphInspectorFields.replaceChildren();
  keys.forEach((key) => {
    const property = properties[key] || {};
    const field = document.createElement("section");
    field.className = "graph-inspector-field";
    const label = document.createElement("h4");
    label.textContent = property.title || key;
    const name = document.createElement("code");
    name.textContent = key;
    label.append(" ", name);
    field.appendChild(label);
    if (property.description) {
      const description = document.createElement("p");
      description.className = "muted";
      description.textContent = property.description;
      field.appendChild(description);
    }
    if (editing) {
      field.appendChild(createInspectorEditor(key, property, selection.item[key]));
    } else {
      const value = document.createElement("pre");
      value.textContent = renderInspectorValue(selection.item[key]);
      field.appendChild(value);
    }
    graphInspectorFields.appendChild(field);
  });
};

const renderGraphInspector = async (selection) => {
  const request = ++inspectorRequest;
  selectedGraphSelection = selection;
  graphInspectorEditing = false;
  selectedGraphProperties = {};
  setGraphInspectorActions(selection, false);
  if (graphInspectorStatus) graphInspectorStatus.textContent = "";
  if (!selection?.item) {
    if (graphInspectorTitle) graphInspectorTitle.textContent = t("schema.graph_select_node", "Select an object");
    if (graphInspectorKind) graphInspectorKind.textContent = t("schema.graph_select_node_help", "Click a graph node to inspect its fields.");
    if (graphInspectorId) graphInspectorId.textContent = "";
    graphInspectorFields?.replaceChildren();
    return;
  }
  if (graphInspectorTitle) graphInspectorTitle.textContent = selection.item.title || selection.kind || selection.id;
  if (graphInspectorKind) graphInspectorKind.textContent = selection.kind || selection.section || "";
  if (graphInspectorId) graphInspectorId.textContent = `ID: ${selection.id}`;
  if (!graphInspectorFields) return;
  graphInspectorFields.textContent = t("schema.loading_fields", "Loading fields…");
  try {
    cachedCatalog ||= await window.R3XARuntime.loadSchemaCatalog();
    if (request !== inspectorRequest) return;
    const kindSchema = cachedCatalog?.sections?.[selection.section]?.kinds?.[selection.kind] || {};
    const properties = kindSchema.properties || {};
    selectedGraphProperties = properties;
    renderInspectorFields(selection, properties, false);
  } catch (error) {
    if (request === inspectorRequest) {
      graphInspectorFields.textContent = t("schema.failed_fields", "Failed to load fields: {message}", {message: error.message || error});
    }
  }
};

const startGraphInspectorEdit = () => {
  if (!selectedGraphSelection?.item) return;
  graphInspectorEditing = true;
  renderInspectorFields(selectedGraphSelection, selectedGraphProperties, true);
  setGraphInspectorActions(selectedGraphSelection, true);
  if (graphInspectorStatus) graphInspectorStatus.textContent = "";
};

const cancelGraphInspectorEdit = () => {
  if (!selectedGraphSelection?.item) return;
  graphInspectorEditing = false;
  renderInspectorFields(selectedGraphSelection, selectedGraphProperties, false);
  setGraphInspectorActions(selectedGraphSelection, false);
  if (graphInspectorStatus) graphInspectorStatus.textContent = "";
};

const readInspectorValue = (control) => {
  if (control.dataset.inspectorType === "reference-array") {
    const selected = [...control.querySelectorAll("input[type=checkbox]:checked")].map((checkbox) => checkbox.value);
    if (!selected.length && control.dataset.inspectorInitialCount === "0") return undefined;
    return selected;
  }
  if (control.dataset.inspectorType === "reference") return control.value.trim() || undefined;
  if (control.type === "checkbox") return control.checked;
  const raw = control.value.trim();
  if (!raw) return undefined;
  if (control.dataset.inspectorType === "array" || control.dataset.inspectorType === "object") {
    try {
      return JSON.parse(raw);
    } catch {
      throw new Error(`${control.dataset.inspectorField}: enter valid JSON`);
    }
  }
  if (control.dataset.inspectorType === "number" || control.dataset.inspectorType === "integer") {
    const value = Number(raw);
    if (!Number.isFinite(value)) throw new Error(`${control.dataset.inspectorField}: enter a valid number`);
    return value;
  }
  return control.value;
};

const readInspectorItem = () => {
  const candidate = JSON.parse(JSON.stringify(selectedGraphSelection.item));
  graphInspectorFields?.querySelectorAll("[data-inspector-field]").forEach((control) => {
    if (control.disabled) return;
    const key = control.dataset.inspectorField;
    const value = readInspectorValue(control);
    if (value === undefined && !Object.prototype.hasOwnProperty.call(selectedGraphSelection.item, key)) {
      delete candidate[key];
    } else {
      candidate[key] = value;
    }
  });
  return candidate;
};

const inspectorReportText = (report) => {
  if (report.valid) return t("schema.valid_item", "Valid item ✅");
  const errors = (report.errors || []).map((error) => (
    `- ${error.path || "<root>"}: ${error.user_message || error.message || t("schema.validation_failed", "Validation failed.")}`
  ));
  return [t("schema.invalid_item", "Invalid item ❌"), "", ...errors].join("\n");
};

const validateGraphInspectorItem = async () => {
  if (!selectedGraphSelection?.item || !graphInspectorEditing) return;
  try {
    const candidate = readInspectorItem();
    const response = await window.R3XARuntime.validateItem(candidate, candidate.kind || "");
    if (!response.ok) throw new Error(`Validation request failed (${response.status})`);
    const report = await response.json();
    if (!report.valid) {
      if (graphInspectorStatus) graphInspectorStatus.textContent = inspectorReportText(report);
      return;
    }
    const payload = getStoredDraft();
    const sectionItems = payload?.[selectedGraphSelection.section];
    const index = Array.isArray(sectionItems)
      ? sectionItems.findIndex((item) => item?.id === selectedGraphSelection.id)
      : -1;
    if (!payload || index < 0) throw new Error("The selected item is no longer present in the draft.");
    sectionItems[index] = candidate;
    const serialized = JSON.stringify(payload);
    await window.R3XADraftStorage.save(serialized);
    storedDraftText = serialized;
    if (graphInspectorStatus) graphInspectorStatus.textContent = inspectorReportText(report);
    await renderGraph({section: selectedGraphSelection.section, id: candidate.id});
    await new Promise((resolve) => window.setTimeout(resolve, 0));
    if (graphInspectorStatus) graphInspectorStatus.textContent = inspectorReportText(report);
  } catch (error) {
    if (graphInspectorStatus) graphInspectorStatus.textContent = t(
      "schema.validation_failed",
      "Validation failed: {message}",
      {message: error.message || error},
    );
  }
};

const ensureServerStart = () => {
  const appStart = document.body?.dataset?.appStart;
  if (!appStart) return;
  const stored = localStorage.getItem("r3xaAppStart");
  if (stored !== appStart) {
    localStorage.setItem("r3xaAppStart", appStart);
  }
};

let storedDraftText = localStorage.getItem("r3xaDraft") || localStorage.getItem("r3xaDraftLast");
const draftReady = window.R3XADraftStorage.load().then((text) => {
  storedDraftText = text;
  return text;
});

const getStoredDraftText = () => localStorage.getItem("r3xaDraft") || storedDraftText || localStorage.getItem("r3xaDraftLast");

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

const jsonScalarText = (value) => {
  if (typeof value !== "string") return JSON.stringify(value);
  return `"${value.replaceAll("\\", "\\\\").replaceAll('"', '\\"')}"`;
};

const renderJsonViewer = (data, expandDepth = 1) => {
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
      const expanded = depth < expandDepth;
      const toggle = document.createElement("span");
      toggle.className = `jv-folder jv-light-folder${expanded ? " rotate90" : ""}`;
      toggle.setAttribute("role", "button");
      toggle.setAttribute("tabindex", "0");
      toggle.setAttribute("aria-label", t("schema.toggle", `Toggle ${key}`, {key}));
      left.appendChild(toggle);
      const size = Array.isArray(value) ? value.length : Object.keys(value).length;
      left.appendChild(document.createTextNode(`${String(key)}  ${Array.isArray(value) ? `[${size}]` : `{${size}}`}`));
      row.appendChild(left);

      const children = document.createElement("div");
      children.className = `jv-light-rightObj${expanded ? " add-height" : ""}`;
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
      right.textContent = jsonScalarText(value);
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
    renderJsonViewer(cachedSummary, 1);
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
    renderJsonViewer(buildDisplayDraft(payload), 1);
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

const renderGraph = async (selectionToRestore = null) => {
  await draftReady.catch(() => {});
  const stored = getStoredDraftText();
  if (!graphContainer) return false;
  currentGraph?.dispose?.();
  currentGraph = null;
  graphContainer.classList.remove("graph-container-interactive");
  setGraphInspectorVisible(false);
  renderGraphInspector(null);
  setGraphNavigationHelpVisible(false);
  setGraphActionVisible(fitGraphBtn, false);
  setGraphActionVisible(zoomOutGraphBtn, false);
  setGraphActionVisible(zoomInGraphBtn, false);
  graphContainer.textContent = t("schema.generating", "Generating graph…");
  if (!stored) {
    graphContainer.textContent = t("schema.no_draft", "No draft found. Create one in the editor first.");
    setGraphActionVisible(saveGraphBtn, false);
    setGraphActionVisible(fullscreenGraphBtn, false);
    setGraphActionVisible(fitGraphBtn, false);
    return false;
  }
  try {
    const payload = JSON.parse(stored);
    const backend = graphBackendSelect
      ? graphBackendSelect.value
      : (window.R3XARuntime?.graphBackends?.[0] || "graphviz");
    const showDescription = graphDescriptionToggle ? graphDescriptionToggle.checked : true;
    const palette = graphPaletteSelect ? graphPaletteSelect.value : "document";
    const relations = graphRelationSelect ? graphRelationSelect.value : "all";
    const response = await window.R3XARuntime.renderGraph(payload, {
      showDescription,
      palette,
      backend,
      relations,
      onNodeSelect: renderGraphInspector,
    });
    if (response?.element && response?.interactive !== false) {
      currentGraph = {
        backend,
        interactive: true,
        dispose: response.dispose,
        fit: response.fit,
        zoomIn: response.zoomIn,
        zoomOut: response.zoomOut,
        exportState: response.exportState,
        payload,
      };
      graphContainer.replaceChildren(response.element);
      graphContainer.classList.add("graph-container-interactive");
      setGraphInspectorVisible(true);
      renderGraphInspector(null);
      setGraphNavigationHelpVisible(true);
      setGraphActionVisible(saveGraphBtn, false);
      setGraphActionVisible(fullscreenGraphBtn, true);
      setGraphActionVisible(fitGraphBtn, true);
      setGraphActionVisible(zoomOutGraphBtn, true);
      setGraphActionVisible(zoomInGraphBtn, true);
      setGraphActionVisible(
        exportStandaloneBtn,
        backend === "cytoscape" && typeof window.R3XARuntime.loadStandaloneGraphBundle === "function",
      );
      if (selectionToRestore?.id) {
        const hitArea = Array.from(graphContainer.querySelectorAll("[data-node-id]")).find(
          (element) => element.dataset.nodeId === selectionToRestore.id,
        );
        hitArea?.click();
      }
      return true;
    }
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
    setGraphActionVisible(fitGraphBtn, false);
    setGraphActionVisible(zoomOutGraphBtn, false);
    setGraphActionVisible(zoomInGraphBtn, false);
    setGraphActionVisible(exportStandaloneBtn, backend === "graphviz");
    return !!currentGraph;
  } catch (err) {
    graphContainer.textContent = t("schema.failed_graph", "Failed to generate graph: {message}", {message: err.message || err});
    graphContainer.classList.remove("graph-container-interactive");
    setGraphNavigationHelpVisible(false);
    currentGraph = null;
    setGraphActionVisible(saveGraphBtn, false);
    setGraphActionVisible(fullscreenGraphBtn, false);
    setGraphActionVisible(fitGraphBtn, false);
    setGraphActionVisible(zoomOutGraphBtn, false);
    setGraphActionVisible(zoomInGraphBtn, false);
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

const updateFullscreenButton = () => {
  if (!fullscreenGraphBtn) return;
  const active = document.fullscreenElement === graphWorkspace
    || graphWorkspace?.classList.contains("graph-workspace-fullscreen-fallback");
  fullscreenGraphBtn.textContent = t(
    active ? "schema.exit_fullscreen" : "schema.fullscreen",
    active ? "Exit fullscreen" : "Fullscreen",
  );
};

const toggleWorkspaceFullscreen = async () => {
  if (!graphWorkspace) return;
  try {
    if (document.fullscreenElement === graphWorkspace) {
      await document.exitFullscreen();
    } else if (graphWorkspace.classList.contains("graph-workspace-fullscreen-fallback")) {
      graphWorkspace.classList.remove("graph-workspace-fullscreen-fallback");
    } else if (document.fullscreenEnabled && graphWorkspace.requestFullscreen) {
      await graphWorkspace.requestFullscreen();
    } else {
      graphWorkspace.classList.toggle("graph-workspace-fullscreen-fallback");
    }
  } catch (error) {
    graphWorkspace.classList.toggle("graph-workspace-fullscreen-fallback");
  }
  updateFullscreenButton();
};

const openFullscreenGraph = async () => {
  if (!currentGraph) {
    const ok = await renderGraph();
    if (!ok) return;
  }
  if (currentGraph.interactive) {
    await toggleWorkspaceFullscreen();
    return;
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

  if (currentGraph?.backend === "cytoscape" && currentGraph.exportState) {
    try {
      cachedCatalog ||= await window.R3XARuntime.loadSchemaCatalog();
      const bundle = await window.R3XARuntime.loadStandaloneGraphBundle();
      const graphItems = {};
      ["settings", "data_sources", "data_sets"].forEach((section) => {
        (currentGraph.payload?.[section] || []).forEach((item) => {
          if (!item?.id) return;
          const kind = item.kind || "";
          const properties = cachedCatalog?.sections?.[section]?.kinds?.[kind]?.properties || {};
          graphItems[item.id] = {item, properties};
        });
      });
      const standaloneState = {
        ...currentGraph.exportState(),
        items: graphItems,
        labels: {
          eyebrow: t("schema.graph_inspector", "Selected object"),
          selectTitle: t("schema.graph_select_node", "Select an object"),
          selectHelp: t("schema.graph_select_node_help", "Click a graph node to inspect its fields."),
          id: t("common.id", "ID"),
          generatedAt: t("schema.standalone_help", "Generated at {date}.", {date: new Date().toISOString()}),
          navigationHelp: t("schema.cytoscape_navigation", "Double-click a data source or data set to frame all directly connected objects."),
          fieldsTitle: t("schema.standalone_fields", "Object fields"),
          jsonTitle: t("schema.standalone_json", "R3XA Draft JSON"),
          title: t("schema.standalone_title", "R3XA Standalone Export"),
          zoomIn: t("schema.zoom_in_graph", "Zoom in"),
          zoomOut: t("schema.zoom_out_graph", "Zoom out"),
          fitGraph: t("schema.fit_graph", "Recenter graph"),
        },
      };
      const safeState = JSON.stringify(standaloneState).replace(/</g, "\\u003c");
      const safePayload = escapeHtml(JSON.stringify(currentGraph.payload || payload, null, 2));
      const safeTitle = escapeHtml(String((currentGraph.payload || payload).title || "R3XA"));
      const safeBundle = bundle.replace(/<\/script/gi, "<\\/script");
      const html = `<!doctype html>
<html lang="${document.documentElement.lang || "en"}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>${safeTitle} — R3XA</title>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; background: #f5f7fa; color: #17202a; font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
    main { max-width: 1500px; margin: 0 auto; padding: 1.25rem; }
    header, .panel, .graph, .inspector { border: 1px solid #e1e7ee; border-radius: 10px; background: #fff; }
    header { padding: 1.25rem; }
    h1, h2, h3, p { margin-top: 0; }
    .muted { color: #5b6673; }
    .workspace { display: grid; grid-template-columns: minmax(0, 1.7fr) minmax(280px, .9fr); gap: 1rem; margin-top: 1rem; align-items: start; }
    .graph-panel { position: relative; min-width: 0; }
    .graph-controls { position: absolute; z-index: 2; top: .75rem; right: .75rem; display: flex; gap: .4rem; }
    .graph-controls button { min-width: 2.5rem; min-height: 2.5rem; border: 1px solid #b8c4d1; border-radius: 6px; background: #fff; color: #17202a; font: inherit; font-weight: 700; cursor: pointer; box-shadow: 0 1px 4px #17202a22; }
    .graph-controls button:hover { background: #eef5fb; }
    .graph { min-width: 0; height: min(78vh, 960px); min-height: 520px; overflow: hidden; }
    .inspector { min-width: 0; max-height: min(78vh, 960px); overflow: auto; }
    .inspector-header { padding: 1rem; background: #eef5fb; border-bottom: 1px solid #e1e7ee; }
    .eyebrow { display: block; margin-bottom: .35rem; color: #5b6673; font-size: .8rem; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; }
    .inspector-header h2 { margin-bottom: .25rem; }
    .inspector-header p { margin-bottom: .4rem; }
    .inspector-fields { padding: .5rem 1rem; }
    .field { padding: .75rem 0; border-bottom: 1px solid #e1e7ee; }
    .field:last-child { border-bottom: 0; }
    .field h3 { margin: 0; font-size: .95rem; }
    .field h3 code { color: #5b6673; font-size: .78rem; font-weight: 400; }
    .field p { margin: .3rem 0; font-size: .85rem; }
    pre { margin: .45rem 0 0; padding: .55rem; overflow: auto; border-radius: 5px; background: #f5f7fa; color: #17202a; font: .82rem/1.4 ui-monospace, SFMono-Regular, Consolas, monospace; white-space: pre-wrap; overflow-wrap: anywhere; }
    details { margin-top: 1rem; }
    details pre { max-height: 55vh; background: #0b0b0b; color: #e8e8e8; }
    .cytoscape-graph { width: 100%; height: 100%; background: #fff; touch-action: none; }
    @media (max-width: 900px) { main { padding: .75rem; } .workspace { display: block; } .graph { height: 65vh; min-height: 420px; } .inspector { margin-top: 1rem; max-height: none; } }
  </style>
</head>
<body>
  <main>
    <header><h1>${safeTitle}</h1><p class="muted">${escapeHtml(standaloneState.labels.generatedAt)}</p><p class="muted">${escapeHtml(standaloneState.labels.navigationHelp)}</p></header>
    <section class="workspace" aria-label="Interactive R3XA graph and selected object fields">
      <div class="graph-panel">
        <div class="graph-controls" role="group" aria-label="Graph navigation">
          <button id="graph-zoom-in" type="button" title="${escapeHtml(standaloneState.labels.zoomIn)}" aria-label="${escapeHtml(standaloneState.labels.zoomIn)}">+</button>
          <button id="graph-zoom-out" type="button" title="${escapeHtml(standaloneState.labels.zoomOut)}" aria-label="${escapeHtml(standaloneState.labels.zoomOut)}">−</button>
          <button id="graph-fit" type="button" title="${escapeHtml(standaloneState.labels.fitGraph)}" aria-label="${escapeHtml(standaloneState.labels.fitGraph)}">↔</button>
        </div>
        <div id="graph" class="graph" aria-label="Interactive R3XA graph"></div>
      </div>
      <aside class="inspector" aria-live="polite">
        <div class="inspector-header">
          <span class="eyebrow">${escapeHtml(standaloneState.labels.eyebrow)}</span>
          <h2 id="selected-title">${escapeHtml(standaloneState.labels.selectTitle)}</h2>
          <p id="selected-kind" class="muted">${escapeHtml(standaloneState.labels.selectHelp)}</p>
          <code id="selected-id"></code>
        </div>
        <div id="selected-fields" class="inspector-fields"></div>
      </aside>
    </section>
    <details class="panel"><summary>${escapeHtml(standaloneState.labels.jsonTitle)}</summary><pre>${safePayload}</pre></details>
  </main>
  <script type="application/json" id="graph-state">${safeState}</script>
  <script>${safeBundle}</script>
  <script>
    const graphState = JSON.parse(document.getElementById("graph-state").textContent);
    window.R3XAStandaloneGraph.mount(
      document.getElementById("graph"),
      {
        title: document.getElementById("selected-title"),
        kind: document.getElementById("selected-kind"),
        id: document.getElementById("selected-id"),
        fields: document.getElementById("selected-fields"),
      },
      graphState,
      {
        zoomIn: document.getElementById("graph-zoom-in"),
        zoomOut: document.getElementById("graph-zoom-out"),
        fit: document.getElementById("graph-fit"),
      },
    );
  </script>
</body>
</html>`;
      const blob = new Blob([html], {type: "text/html"});
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "r3xa-standalone.html";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (error) {
      graphContainer.textContent = t("schema.failed_graph", "Failed to generate graph: {message}", {message: error.message || error});
    }
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
  graphRelationSelect?.addEventListener("change", renderGraph);
  graphBackendSelect?.addEventListener("change", renderGraph);
  document.getElementById("generate-graph-btn")?.addEventListener("click", renderGraph);
  saveGraphBtn?.addEventListener("click", saveGraph);
  fullscreenGraphBtn?.addEventListener("click", openFullscreenGraph);
  fitGraphBtn?.addEventListener("click", () => currentGraph?.fit?.());
  zoomOutGraphBtn?.addEventListener("click", () => currentGraph?.zoomOut?.());
  zoomInGraphBtn?.addEventListener("click", () => currentGraph?.zoomIn?.());
  exportStandaloneBtn?.addEventListener("click", exportStandaloneHtml);
  graphInspectorEditBtn?.addEventListener("click", startGraphInspectorEdit);
  graphInspectorValidateBtn?.addEventListener("click", validateGraphInspectorItem);
  graphInspectorCancelBtn?.addEventListener("click", cancelGraphInspectorEdit);
  document.addEventListener("fullscreenchange", updateFullscreenButton);
  graphContainer?.addEventListener("click", () => {
    if (graphContainer.querySelector("svg")) showFullscreenGraph();
  });
  updateFullscreenButton();
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
draftReady.then(() => {
  if (getStoredDraft() && viewSelect) {
    viewSelect.value = "draft";
  }
  if (viewSelect?.value === "draft") renderDraft();
  else renderSummary();
}).catch((error) => {
  if (treeEl) treeEl.textContent = t("schema.failed_draft", "Failed to load draft: {message}", {message: error.message || error});
});
