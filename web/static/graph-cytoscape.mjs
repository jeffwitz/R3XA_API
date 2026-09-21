import cytoscape from "cytoscape";
import {buildGraphModel, formatNodeLabel} from "./graph-core.mjs";
import {renderGraph as renderGraphviz} from "./graph-runtime.mjs";

const shapeForSection = {
  settings: "hexagon",
  data_sources: "ellipse",
  data_sets: "rectangle",
};

const parseNumber = (value, fallback = 0) => {
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const shapeBounds = (shape) => {
  if (!shape) return null;
  const tag = shape.tagName.toLowerCase();
  if (tag === "ellipse") {
    return {
      x: parseNumber(shape.getAttribute("cx")),
      y: parseNumber(shape.getAttribute("cy")),
      width: parseNumber(shape.getAttribute("rx")) * 2,
      height: parseNumber(shape.getAttribute("ry")) * 2,
    };
  }
  if (tag === "rect") {
    const width = parseNumber(shape.getAttribute("width"));
    const height = parseNumber(shape.getAttribute("height"));
    return {
      x: parseNumber(shape.getAttribute("x")) + width * 0.5,
      y: parseNumber(shape.getAttribute("y")) + height * 0.5,
      width,
      height,
    };
  }
  const points = String(shape.getAttribute("points") || "")
    .trim()
    .split(/\s+/)
    .map((point) => point.split(",").map((value) => Number.parseFloat(value)))
    .filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y));
  if (!points.length) return null;
  const xs = points.map(([x]) => x);
  const ys = points.map(([, y]) => y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  return {
    x: (minX + maxX) * 0.5,
    y: (minY + maxY) * 0.5,
    width: maxX - minX,
    height: maxY - minY,
  };
};

const readGraphvizLayout = (svgText) => {
  const parsed = new DOMParser().parseFromString(svgText, "image/svg+xml");
  if (parsed.querySelector("parsererror") || parsed.documentElement?.tagName.toLowerCase() !== "svg") {
    throw new Error("Graphviz returned an invalid SVG layout.");
  }
  const svg = parsed.documentElement;
  const viewBox = String(svg.getAttribute("viewBox") || "0 0 1200 800")
    .trim()
    .split(/\s+/)
    .map((value) => parseNumber(value));
  const nodes = new Map();
  parsed.querySelectorAll("g.node").forEach((group) => {
    const title = group.querySelector("title")?.textContent?.trim();
    const bounds = shapeBounds(group.querySelector("ellipse, polygon, rect"));
    if (title && bounds) nodes.set(title, bounds);
  });
  return {viewBox, nodes};
};

export const styleFor = (style = {}) => ({
  fill: style.fillcolor || style.color || "#d8dee8",
  border: style.color || style.fillcolor || "#3d4652",
  borderWidth: Math.max(1, parseNumber(style.penwidth, 1)),
  text: style.fontcolor || "#000000",
});

const nodeRecords = (payload, model, styles, includeDescription, layoutNodes) => {
  const records = [];
  const add = (section, item, style) => {
    if (!item?.id) return;
    const status = section === "data_sources"
      ? (model.intermediateSources.includes(item.id) ? "intermediate" : "initial")
      : section === "data_sets"
        ? (model.usedDatasets.includes(item.id) ? "intermediate" : "final")
        : "root";
    const colors = styleFor(style);
    const bounds = layoutNodes.get(item.id) || {width: 190, height: 64};
    const width = Math.max(120, bounds.width);
    const height = Math.max(56, bounds.height);
    records.push({
      data: {
        id: item.id,
        label: formatNodeLabel(item.title, item.description, includeDescription),
        shape: shapeForSection[section],
        fill: colors.fill,
        border: colors.border,
        borderWidth: colors.borderWidth,
        text: colors.text,
        width,
        height,
        textMaxWidth: Math.max(100, width - 18),
      },
      classes: `${section.replace("_", "-")} ${status}`,
    });
  };
  (payload.settings || []).forEach((item) => add("settings", item, styles.settings.root));
  (payload.data_sources || []).forEach((item) => {
    const status = model.intermediateSources.includes(item?.id) ? "intermediate" : "initial";
    add("data_sources", item, styles.data_sources[status]);
  });
  (payload.data_sets || []).forEach((item) => {
    const status = model.usedDatasets.includes(item?.id) ? "intermediate" : "final";
    add("data_sets", item, styles.data_sets[status]);
  });
  return records;
};

const edgeRecords = (model, styles) => model.edgeRecords.map((edge, index) => {
  const style = styles.edges[edge.styleKey] || styles.edges.reference || styles.edges.setting || {};
  return {
    data: {
      id: `edge-${index}`,
      source: edge.src,
      target: edge.dst,
      label: edge.label || "",
      color: style.color || "#555555",
      lineStyle: style.style === "dashed" ? "dashed" : "solid",
    },
    classes: edge.role === "context" ? "context" : "dataflow",
  };
});

const cytoscapeStyle = [
  {
    selector: "node",
    style: {
      label: "data(label)",
      shape: "data(shape)",
      width: "data(width)",
      height: "data(height)",
      "background-color": "data(fill)",
      "border-color": "data(border)",
      "border-width": "data(borderWidth)",
      color: "data(text)",
      "font-size": 14,
      "font-family": "Arial, sans-serif",
      "text-wrap": "wrap",
      "text-max-width": "data(textMaxWidth)",
      "text-valign": "center",
      "text-halign": "center",
      "overlay-opacity": 0,
    },
  },
  {
    selector: "edge",
    style: {
      width: 1.5,
      label: "data(label)",
      "line-color": "data(color)",
      "target-arrow-color": "data(color)",
      "target-arrow-shape": "triangle",
      "curve-style": "bezier",
      "line-style": "data(lineStyle)",
      color: "#555555",
      "font-size": 11,
      "text-background-color": "#ffffff",
      "text-background-opacity": 0.85,
      "text-rotation": "autorotate",
    },
  },
  {selector: ".faded", style: {opacity: 0.18}},
  {selector: ".highlighted", style: {"border-width": 4, "z-index": 10}},
];

export const renderCytoscapeGraph = async (
  payload,
  {includeDescription = true, palette = "document", relations = "all"} = {},
  palettes,
  relationCatalog,
) => {
  const svg = await renderGraphviz(payload, {includeDescription, palette, relations}, palettes, relationCatalog);
  const layout = readGraphvizLayout(svg);
  const model = buildGraphModel(payload, {relations}, relationCatalog);
  const styles = palettes[palette] || palettes.document || palettes;
  const elements = [
    ...nodeRecords(payload, model, styles, includeDescription, layout.nodes),
    ...edgeRecords(model, styles),
  ];
  const container = globalThis.document.createElement("div");
  container.className = "cytoscape-graph";
  container.dataset.nodeCount = String(model.nodeIds.length);
  container.dataset.edgeCount = String(model.edgeRecords.length);
  const width = layout.viewBox[2] || 1200;
  const height = layout.viewBox[3] || 800;
  container.style.aspectRatio = `${width} / ${height}`;
  const layoutBounds = [...layout.nodes.values()];
  const minX = layoutBounds.length ? Math.min(...layoutBounds.map((bounds) => bounds.x)) : 0;
  const minY = layoutBounds.length ? Math.min(...layoutBounds.map((bounds) => bounds.y)) : 0;
  const positions = Object.fromEntries(
    [...layout.nodes.entries()].map(([id, bounds]) => [id, {
      x: bounds.x - minX,
      y: bounds.y - minY,
    }]),
  );
  const cy = cytoscape({
    container,
    elements,
    style: cytoscapeStyle,
    layout: {name: "preset", positions, fit: true, padding: 40},
    minZoom: 0.1,
    maxZoom: 4,
    wheelSensitivity: 0.12,
    panningEnabled: true,
    userPanningEnabled: true,
    userZoomingEnabled: true,
    boxSelectionEnabled: false,
    autolock: false,
    autoungrabify: true,
  });
  const fit = () => {
    if (cy.destroyed()) return;
    cy.resize();
    cy.fit(cy.elements(), 40);
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
  globalThis.requestAnimationFrame?.(fit);
  setTimeout(fit, 0);
  cy.on("tap", "node", (event) => {
    const neighborhood = event.target.closedNeighborhood();
    cy.elements().removeClass("faded highlighted");
    neighborhood.addClass("highlighted");
    cy.elements().difference(neighborhood).addClass("faded");
  });
  cy.on("tap", (event) => {
    if (event.target === cy) cy.elements().removeClass("faded highlighted");
  });
  return {
    element: container,
    fit,
    zoomIn: () => zoomAtCenter(1.25),
    zoomOut: () => zoomAtCenter(0.8),
    dispose: () => {
      resizeObserver?.disconnect();
      cy.destroy();
    },
  };
};
