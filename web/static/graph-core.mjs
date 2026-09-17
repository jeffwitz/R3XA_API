const SECTION_NAMES = ["settings", "data_sources", "data_sets"];

const asItems = (document, section) => (
  Array.isArray(document?.[section]) ? document[section] : []
);

const nonEmptyReferences = (value) => {
  if (!value) return [];
  if (Array.isArray(value)) return value.filter(Boolean);
  if (typeof value === "object") return Object.values(value).filter(Boolean);
  return [value];
};

const getInputDataSets = (source) => nonEmptyReferences(source?.input_data_sets);
const getDataSources = (dataset) => nonEmptyReferences(dataset?.parent_data_sources);
const getAttachedDataSources = (setting) => nonEmptyReferences(setting?.attached_data_sources);

const computeUsedDatasets = (document) => {
  const used = new Set();
  asItems(document, "data_sources").forEach((source) => {
    getInputDataSets(source).forEach((datasetId) => used.add(datasetId));
  });
  return used;
};

const computeLevels = (nodes, edges) => {
  const orderedNodes = [...new Set(nodes)];
  const adjacency = new Map(orderedNodes.map((nodeId) => [nodeId, []]));
  const indegree = new Map(orderedNodes.map((nodeId) => [nodeId, 0]));

  edges.forEach(([source, target]) => {
    if (!adjacency.has(source)) {
      adjacency.set(source, []);
      indegree.set(source, 0);
      orderedNodes.push(source);
    }
    if (!adjacency.has(target)) {
      adjacency.set(target, []);
      indegree.set(target, 0);
      orderedNodes.push(target);
    }
    adjacency.get(source).push(target);
    indegree.set(target, indegree.get(target) + 1);
  });

  const levels = Object.fromEntries(orderedNodes.map((nodeId) => [nodeId, 0]));
  const queue = orderedNodes.filter((nodeId) => indegree.get(nodeId) === 0);
  while (queue.length) {
    const current = queue.shift();
    adjacency.get(current).forEach((child) => {
      levels[child] = Math.max(levels[child], levels[current] + 1);
      indegree.set(child, indegree.get(child) - 1);
      if (indegree.get(child) === 0) queue.push(child);
    });
  }
  return levels;
};

export const buildGraphModel = (document) => {
  const settings = asItems(document, "settings");
  const sources = asItems(document, "data_sources");
  const datasets = asItems(document, "data_sets");
  const settingIds = settings.map((item) => item?.id).filter(Boolean);
  const sourceIds = sources.map((item) => item?.id).filter(Boolean);
  const datasetIds = datasets.map((item) => item?.id).filter(Boolean);
  const nodeIds = [...settingIds, ...sourceIds, ...datasetIds];
  const usedDatasets = computeUsedDatasets(document);
  const intermediateSources = new Set(
    sources
      .filter((source) => getInputDataSets(source).length > 0)
      .map((source) => source?.id)
      .filter(Boolean),
  );
  const edgeRecords = [];

  settings.forEach((setting) => {
    if (!setting?.id) return;
    getAttachedDataSources(setting).forEach((sourceId) => {
      edgeRecords.push({src: setting.id, dst: sourceId, styleKey: "setting"});
    });
  });
  sources.forEach((source) => {
    if (!source?.id) return;
    getInputDataSets(source).forEach((datasetId) => {
      edgeRecords.push({src: datasetId, dst: source.id, styleKey: "input"});
    });
  });
  datasets.forEach((dataset) => {
    if (!dataset?.id) return;
    getDataSources(dataset).forEach((sourceId) => {
      edgeRecords.push({
        src: sourceId,
        dst: dataset.id,
        styleKey: intermediateSources.has(sourceId) ? "data" : "data_initial",
      });
    });
  });

  return {
    settingIds,
    sourceIds,
    dataSetIds: datasetIds,
    nodeIds,
    usedDatasets: [...usedDatasets],
    intermediateSources: [...intermediateSources],
    edgeRecords,
    levels: computeLevels(nodeIds, edgeRecords.map((edge) => [edge.src, edge.dst])),
  };
};

const wrapLine = (line, maxChars) => {
  const words = line.trim().split(/\s+/).filter(Boolean);
  if (!words.length) return [""];
  const lines = [];
  let current = "";
  words.forEach((word) => {
    const candidate = current ? `${current} ${word}` : word;
    if (current && candidate.length > maxChars) {
      lines.push(current);
      current = word;
    } else {
      current = candidate;
    }
  });
  if (current) lines.push(current);
  return lines;
};

export const wrapLabelText = (value, maxChars) => {
  if (value === null || value === undefined) return "";
  const text = String(value).trim();
  if (!text) return "";
  return text.split(/\r?\n/).flatMap((line) => wrapLine(line, maxChars)).join("\n");
};

export const formatNodeLabel = (title, description, includeDescription = true) => {
  const titleText = wrapLabelText(title, 34);
  if (!includeDescription) return titleText;
  const descriptionText = wrapLabelText(description, 44);
  return descriptionText ? `${titleText}\n(${descriptionText})` : titleText;
};

const dotQuote = (value) => `"${String(value ?? "")
  .replaceAll("\\", "\\\\")
  .replaceAll('"', '\\"')
  .replace(/\r?\n/g, "\\n")}"`;

const dotAttributes = (attributes) => Object.entries(attributes)
  .filter(([, value]) => value !== undefined && value !== null)
  .map(([key, value]) => `${key}=${dotQuote(value)}`)
  .join(", ");

const nodeAttributes = (style, label) => ({...style, label});

export const buildDot = (document, {includeDescription = true} = {}, styles) => {
  if (!styles) throw new Error("Graph palette styles are required.");
  const model = buildGraphModel(document);
  const lines = [
    "digraph \"R3XA graph\" {",
    "  graph [rankdir=TB, bgcolor=transparent];",
    '  node [margin="0.2,0.1"];',
  ];
  const addNode = (id, label, style) => {
    lines.push(`  ${dotQuote(id)} [${dotAttributes(nodeAttributes(style, label))}];`);
  };

  asItems(document, "settings").forEach((setting) => {
    if (!setting?.id) return;
    addNode(
      setting.id,
      formatNodeLabel(setting.title, setting.description, includeDescription),
      styles.settings.root,
    );
  });
  asItems(document, "data_sources").forEach((source) => {
    if (!source?.id) return;
    const status = model.intermediateSources.includes(source.id) ? "intermediate" : "initial";
    addNode(
      source.id,
      formatNodeLabel(source.title, source.description, includeDescription),
      styles.data_sources[status],
    );
  });
  asItems(document, "data_sets").forEach((dataset) => {
    if (!dataset?.id) return;
    const status = model.usedDatasets.includes(dataset.id) ? "intermediate" : "final";
    addNode(
      dataset.id,
      formatNodeLabel(dataset.title, dataset.description, includeDescription),
      styles.data_sets[status],
    );
  });
  model.edgeRecords.forEach((edge) => {
    const style = styles.edges[edge.styleKey] || {};
    lines.push(`  ${dotQuote(edge.src)} -> ${dotQuote(edge.dst)} [${dotAttributes(style)}];`);
  });
  lines.push("}");
  return lines.join("\n");
};

export {SECTION_NAMES};
