import cytoscape from "cytoscape";
import {buildCytoscapeStateFromSvg} from "./graph-cytoscape-model.mjs";

const displayValue = (value) => {
  if (value === undefined) return "—";
  if (typeof value === "string") return value;
  const serialized = JSON.stringify(value, null, 2);
  return serialized === undefined ? String(value) : serialized;
};

const renderFields = (fieldsElement, item, properties) => {
  fieldsElement.replaceChildren();
  const keys = [...Object.keys(properties || {}), ...Object.keys(item || {}).filter((key) => !(key in (properties || {})))];
  keys.forEach((key) => {
    const field = document.createElement("section");
    field.className = "field";
    const heading = document.createElement("h3");
    heading.append(document.createTextNode(properties?.[key]?.title || key));
    const keyLabel = document.createElement("code");
    keyLabel.textContent = key;
    heading.append(" ", keyLabel);
    field.appendChild(heading);
    if (properties?.[key]?.description) {
      const description = document.createElement("p");
      description.className = "muted";
      description.textContent = properties[key].description;
      field.appendChild(description);
    }
    const value = document.createElement("pre");
    value.textContent = displayValue(item?.[key]);
    field.appendChild(value);
    fieldsElement.appendChild(field);
  });
};

export const mount = (graphElement, inspector, state, controls = {}) => {
  if (state.layoutSvg) {
    const graphState = buildCytoscapeStateFromSvg(
      state.payload,
      state.layoutSvg,
      state.options,
      state.palettes,
      state.relationCatalog,
    );
    state = {
      ...state,
      elements: graphState.elements.map((element) => ({
        ...element,
        position: graphState.positions[element.data.id],
      })),
      style: graphState.style,
    };
  }
  const style = [
    ...(state.style || []),
    {selector: ".standalone-selected", style: {"border-width": 4, "border-style": "dashed", "border-color": "#111111", "z-index": 10}},
  ];
  const cy = cytoscape({
    container: graphElement,
    elements: state.elements || [],
    style,
    layout: {name: "preset", fit: true, padding: 40},
    minZoom: 0.1,
    maxZoom: 4,
    wheelSensitivity: 0.3,
    panningEnabled: true,
    userPanningEnabled: true,
    userZoomingEnabled: true,
    boxSelectionEnabled: false,
    autolock: false,
    autoungrabify: true,
  });
  graphElement.style.position = "relative";
  const nodeHitLayer = document.createElement("div");
  nodeHitLayer.style.cssText = "position:absolute;inset:0;z-index:1;pointer-events:none";
  const nodeHitAreas = new Map();
  cy.nodes().forEach((node) => {
    const hitArea = document.createElement("button");
    hitArea.type = "button";
    hitArea.className = "standalone-node-hit-area";
    hitArea.dataset.nodeId = node.id();
    hitArea.setAttribute("aria-label", node.data("label") || node.id());
    hitArea.style.cssText = "position:absolute;margin:0;padding:0;border:0;background:transparent;cursor:pointer;pointer-events:auto";
    hitArea.addEventListener("click", () => selectNode({target: node}));
    hitArea.addEventListener("dblclick", (event) => {
      event.preventDefault();
      zoomToDataNode(node);
    });
    nodeHitAreas.set(node.id(), hitArea);
    nodeHitLayer.appendChild(hitArea);
  });
  graphElement.appendChild(nodeHitLayer);

  const clearInspector = () => {
    inspector.title.textContent = state.labels.selectTitle;
    inspector.kind.textContent = state.labels.selectHelp;
    inspector.id.textContent = "";
    inspector.fields.replaceChildren();
  };

  const selectNode = (event) => {
    const nodeData = event.target.data();
    const record = state.items?.[nodeData.id];
    if (!record?.item) return;
    inspector.title.textContent = record.item.title || nodeData.kind || nodeData.id;
    inspector.kind.textContent = nodeData.kind || nodeData.section || "";
    inspector.id.textContent = `${state.labels.id}: ${nodeData.id}`;
    renderFields(inspector.fields, record.item, record.properties || {});
    const neighborhood = event.target.closedNeighborhood();
    cy.elements().removeClass("faded highlighted standalone-selected");
    neighborhood.addClass("highlighted");
    cy.elements().difference(neighborhood).addClass("faded");
    event.target.addClass("standalone-selected");
  };

  cy.on("tap", "node", selectNode);
  cy.on("tap", (event) => {
    if (event.target !== cy) return;
    cy.elements().removeClass("faded highlighted standalone-selected");
    clearInspector();
  });

  const fit = () => {
    if (!cy.destroyed()) {
      cy.resize();
      cy.fit(cy.elements(), 40);
      syncNodeHitAreas();
    }
  };
  const syncNodeHitAreas = () => {
    if (cy.destroyed()) return;
    cy.nodes().forEach((node) => {
      const hitArea = nodeHitAreas.get(node.id());
      if (!hitArea) return;
      const bounds = node.renderedBoundingBox();
      hitArea.style.left = `${bounds.x1}px`;
      hitArea.style.top = `${bounds.y1}px`;
      hitArea.style.width = `${bounds.w}px`;
      hitArea.style.height = `${bounds.h}px`;
    });
  };
  const zoomAtCenter = (factor) => {
    if (cy.destroyed()) return;
    const level = Math.min(cy.maxZoom(), Math.max(cy.minZoom(), cy.zoom() * factor));
    cy.zoom({
      level,
      renderedPosition: {
        x: graphElement.clientWidth * 0.5,
        y: graphElement.clientHeight * 0.5,
      },
    });
  };
  const zoomToDataNode = (node) => {
    if (cy.destroyed() || !node || node.empty()) return;
    const section = node.data("section");
    if (section !== "data_sources" && section !== "data_sets") return;
    cy.animate({fit: {eles: node.closedNeighborhood(), padding: 56}}, {duration: 250});
  };
  cy.on("render zoom pan resize", syncNodeHitAreas);
  const zoomIn = () => zoomAtCenter(1.5);
  const zoomOut = () => zoomAtCenter(1 / 1.5);
  controls.zoomIn?.addEventListener("click", zoomIn);
  controls.zoomOut?.addEventListener("click", zoomOut);
  controls.fit?.addEventListener("click", fit);
  const resizeObserver = typeof ResizeObserver === "function" ? new ResizeObserver(fit) : null;
  resizeObserver?.observe(graphElement);
  requestAnimationFrame(fit);
  window.addEventListener("resize", fit);

  return {
    fit,
    dispose: () => {
      resizeObserver?.disconnect();
      window.removeEventListener("resize", fit);
      nodeHitLayer.remove();
      controls.zoomIn?.removeEventListener("click", zoomIn);
      controls.zoomOut?.removeEventListener("click", zoomOut);
      controls.fit?.removeEventListener("click", fit);
      cy.destroy();
    },
  };
};
