import cytoscape from "cytoscape";
import {buildCytoscapeStateFromSvg, cytoscapeStyle} from "./graph-cytoscape-model.mjs";
import {renderGraph as renderGraphviz} from "./graph-runtime.mjs";

export {buildCytoscapeStateFromSvg, resolveNodeOverlaps, styleFor} from "./graph-cytoscape-model.mjs";

export const renderCytoscapeGraph = async (
  payload,
  {includeDescription = true, palette = "document", relations = "all", onNodeSelect} = {},
  palettes,
  relationCatalog,
) => {
  const svg = await renderGraphviz(payload, {includeDescription, palette, relations}, palettes, relationCatalog);
  const {elements, style, positions, viewBox, model} = buildCytoscapeStateFromSvg(
    payload, svg, {includeDescription, palette, relations}, palettes, relationCatalog,
  );
  const container = globalThis.document.createElement("div");
  container.className = "cytoscape-graph";
  container.dataset.nodeCount = String(model.nodeIds.length);
  container.dataset.edgeCount = String(model.edgeRecords.length);
  const width = viewBox[2] || 1200;
  const height = viewBox[3] || 800;
  container.style.aspectRatio = `${width} / ${height}`;
  const cy = cytoscape({
    container,
    elements,
    style,
    layout: {name: "preset", positions, fit: true, padding: 40},
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
  const nodeHitLayer = globalThis.document.createElement("div");
  nodeHitLayer.className = "cytoscape-node-hit-layer";
  const nodeHitAreas = new Map();
  cy.nodes().forEach((node) => {
    const nodeData = node.data();
    const hitArea = globalThis.document.createElement("button");
    hitArea.type = "button";
    hitArea.className = "cytoscape-node-hit-area";
    hitArea.dataset.nodeId = nodeData.id;
    hitArea.setAttribute("aria-label", nodeData.label || nodeData.id);
    hitArea.addEventListener("click", () => selectNode({target: node}));
    hitArea.addEventListener("dblclick", () => zoomToDataNode(node));
    nodeHitAreas.set(nodeData.id, hitArea);
    nodeHitLayer.appendChild(hitArea);
  });
  container.appendChild(nodeHitLayer);
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
  const fit = () => {
    if (cy.destroyed()) return;
    cy.resize();
    cy.fit(cy.elements(), 40);
    syncNodeHitAreas();
  };
  const zoomToDataNode = (node) => {
    if (cy.destroyed() || !node || node.empty()) return;
    const section = node.data("section");
    if (section !== "data_sources" && section !== "data_sets") return;
    cy.animate({fit: {eles: node.closedNeighborhood(), padding: 56}}, {duration: 250});
  };
  const zoomAtCenter = (factor) => {
    if (cy.destroyed()) return;
    const level = Math.min(cy.maxZoom(), Math.max(cy.minZoom(), cy.zoom() * factor));
    cy.zoom({
      level,
      renderedPosition: {
        x: container.clientWidth * 0.5,
        y: container.clientHeight * 0.5,
      },
    });
  };
  const resizeObserver = typeof ResizeObserver === "function"
    ? new ResizeObserver(fit)
    : null;
  resizeObserver?.observe(container);
  cy.on("render zoom pan resize", syncNodeHitAreas);
  globalThis.requestAnimationFrame?.(fit);
  setTimeout(fit, 0);
  const selectNode = (event) => {
    const nodeData = event.target.data();
    const item = (payload[nodeData.section] || []).find((candidate) => candidate?.id === nodeData.id);
    nodeHitAreas.forEach((hitArea) => hitArea.classList.remove("graph-node-selected"));
    nodeHitAreas.get(nodeData.id)?.classList.add("graph-node-selected");
    onNodeSelect?.({
      id: nodeData.id,
      kind: nodeData.kind,
      section: nodeData.section,
      item,
    });
    const neighborhood = event.target.closedNeighborhood();
    cy.elements().removeClass("faded highlighted");
    neighborhood.addClass("highlighted");
    cy.elements().difference(neighborhood).addClass("faded");
  };
  const clearSelection = (event) => {
    if (event.target === cy) {
      nodeHitAreas.forEach((hitArea) => hitArea.classList.remove("graph-node-selected"));
      cy.elements().removeClass("faded highlighted");
      onNodeSelect?.(null);
    }
  };
  cy.on("tap", "node", selectNode);
  cy.on("click", "node", selectNode);
  cy.on("tap", clearSelection);
  cy.on("click", clearSelection);
  return {
    element: container,
    fit,
    zoomIn: () => zoomAtCenter(1.5),
    zoomOut: () => zoomAtCenter(1 / 1.5),
    exportState: () => ({
      elements: cy.elements().map((element) => {
        const record = element.json();
        record.classes = String(record.classes || "")
          .split(/\s+/)
          .filter((className) => className && className !== "faded" && className !== "highlighted")
          .join(" ");
        return record;
      }),
      style: cytoscapeStyle,
    }),
    dispose: () => {
      resizeObserver?.disconnect();
      nodeHitLayer.remove();
      cy.destroy();
    },
  };
};
