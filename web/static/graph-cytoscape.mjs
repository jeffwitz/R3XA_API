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

const styleFor = (style = {}) => ({
  fill: style.fillcolor || style.color || "#d8dee8",
  border: style.color || style.fillcolor || "#3d4652",
  borderWidth: Math.max(1, parseNumber(style.penwidth, 1)),
  text: style.fontcolor || "#ffffff",
});

const nodeRecords = (payload, model, styles, includeDescription) => {
  const records = [];
  const add = (section, item, style) => {
    if (!item?.id) return;
    const status = section === "data_sources"
      ? (model.intermediateSources.includes(item.id) ? "intermediate" : "initial")
      : section === "data_sets"
        ? (model.usedDatasets.includes(item.id) ? "intermediate" : "final")
        : "root";
    const colors = styleFor(style);
    records.push({
      data: {
        id: item.id,
        label: formatNodeLabel(item.title, item.description, includeDescription),
        shape: shapeForSection[section],
        fill: colors.fill,
        border: colors.border,
        borderWidth: colors.borderWidth,
        text: colors.text,
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
      width: 190,
      height: 64,
      "background-color": "data(fill)",
      "border-color": "data(border)",
      "border-width": "data(borderWidth)",
      color: "data(text)",
      "font-size": 14,
      "font-family": "Arial, sans-serif",
      "text-wrap": "wrap",
      "text-max-width": 190,
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
    ...nodeRecords(payload, model, styles, includeDescription),
    ...edgeRecords(model, styles),
  ];
  const container = globalThis.document.createElement("div");
  container.className = "cytoscape-graph";
  container.dataset.nodeCount = String(model.nodeIds.length);
  container.dataset.edgeCount = String(model.edgeRecords.length);
  const width = layout.viewBox[2] || 1200;
  const height = layout.viewBox[3] || 800;
  container.style.aspectRatio = `${width} / ${height}`;
  const positions = Object.fromEntries(
    [...layout.nodes.entries()].map(([id, bounds]) => [id, {x: bounds.x, y: bounds.y}]),
  );
  const cy = cytoscape({
    container,
    elements,
    style: cytoscapeStyle,
    layout: {name: "preset", positions, fit: true, padding: 40},
    minZoom: 0.1,
    maxZoom: 4,
    wheelSensitivity: 0.2,
  });
  cy.on("tap", "node", (event) => {
    const neighborhood = event.target.closedNeighborhood();
    cy.elements().removeClass("faded highlighted");
    neighborhood.addClass("highlighted");
    cy.elements().difference(neighborhood).addClass("faded");
  });
  cy.on("tap", (event) => {
    if (event.target === cy) cy.elements().removeClass("faded highlighted");
  });
  return {element: container, dispose: () => cy.destroy()};
};
