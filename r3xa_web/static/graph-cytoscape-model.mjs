import {buildGraphModel, formatNodeLabel} from "./graph-core.mjs";

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
const rectanglesOverlap = (first, second, gap) => {
  const horizontalDistance = Math.abs(first.x - second.x);
  const verticalDistance = Math.abs(first.y - second.y);
  return horizontalDistance < (first.width + second.width) * 0.5 + gap
    && verticalDistance < (first.height + second.height) * 0.5 + gap;
};

export const resolveNodeOverlaps = (nodes, positions, gap = 12) => {
  const resolved = new Map(
    Object.entries(positions).map(([id, position]) => [id, {...position}]),
  );
  const placedNodes = nodes.filter((node) => resolved.has(node.id));
  for (let pass = 0; pass < placedNodes.length; pass += 1) {
    let changed = false;
    for (let firstIndex = 0; firstIndex < placedNodes.length; firstIndex += 1) {
      const firstNode = placedNodes[firstIndex];
      const firstPosition = resolved.get(firstNode.id);
      for (let secondIndex = firstIndex + 1; secondIndex < placedNodes.length; secondIndex += 1) {
        const secondNode = placedNodes[secondIndex];
        const secondPosition = resolved.get(secondNode.id);
        const firstBounds = {...firstPosition, width: firstNode.width, height: firstNode.height};
        const secondBounds = {...secondPosition, width: secondNode.width, height: secondNode.height};
        if (!rectanglesOverlap(firstBounds, secondBounds, gap)) continue;

        const horizontalOverlap = (firstNode.width + secondNode.width) * 0.5
          + gap - Math.abs(firstPosition.x - secondPosition.x);
        const verticalOverlap = (firstNode.height + secondNode.height) * 0.5
          + gap - Math.abs(firstPosition.y - secondPosition.y);
        if (horizontalOverlap <= verticalOverlap) {
          const direction = secondPosition.x >= firstPosition.x ? 1 : -1;
          const shift = horizontalOverlap * 0.5;
          firstPosition.x -= direction * shift;
          secondPosition.x += direction * shift;
        } else {
          const direction = secondPosition.y >= firstPosition.y ? 1 : -1;
          const shift = verticalOverlap * 0.5;
          firstPosition.y -= direction * shift;
          secondPosition.y += direction * shift;
        }
        changed = true;
      }
    }
    if (!changed) break;
  }
  return Object.fromEntries(resolved);
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
    const width = Math.max(72, bounds.width);
    const height = Math.max(42, bounds.height);
    records.push({
      data: {
        id: item.id,
        section,
        kind: item.kind || "",
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

export const cytoscapeStyle = [
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

export const buildCytoscapeStateFromSvg = (
  payload,
  svg,
  {includeDescription = true, palette = "document", relations = "all"} = {},
  palettes,
  relationCatalog,
) => {
  const layout = readGraphvizLayout(svg);
  const model = buildGraphModel(payload, {relations}, relationCatalog);
  const styles = palettes[palette] || palettes.document || palettes;
  const elements = [
    ...nodeRecords(payload, model, styles, includeDescription, layout.nodes),
    ...edgeRecords(model, styles),
  ];
  const layoutBounds = [...layout.nodes.values()];
  const minX = layoutBounds.length ? Math.min(...layoutBounds.map((bounds) => bounds.x)) : 0;
  const minY = layoutBounds.length ? Math.min(...layoutBounds.map((bounds) => bounds.y)) : 0;
  const positions = Object.fromEntries(
    [...layout.nodes.entries()].map(([id, bounds]) => [id, {
      x: bounds.x - minX,
      y: bounds.y - minY,
    }]),
  );
  return {
    elements,
    style: cytoscapeStyle,
    positions: resolveNodeOverlaps(
      elements
        .filter((element) => element.data?.width && element.data?.height)
        .map((element) => ({
          id: element.data.id,
          width: element.data.width,
          height: element.data.height,
        })),
      positions,
    ),
    viewBox: layout.viewBox,
    model,
  };
};

