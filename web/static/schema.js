const treeEl = document.getElementById("schema-tree");

const renderNode = (label, node) => {
  const li = document.createElement("li");
  const title = document.createElement("strong");
  title.textContent = label;
  li.appendChild(title);

  const meta = [];
  if (node.type) meta.push(node.type);
  if (node.required) meta.push(`required: ${node.required.length}`);
  if (node.enum) meta.push(`enum: ${node.enum.length}`);
  if (node.const) meta.push(`const: ${node.const}`);
  if (node.ref) meta.push(`ref: ${node.ref}`);
  if (meta.length) {
    const span = document.createElement("span");
    span.textContent = ` (${meta.join(", ")})`;
    span.className = "muted";
    li.appendChild(span);
  }

  if (node.description) {
    const desc = document.createElement("div");
    desc.textContent = node.description;
    desc.className = "muted";
    li.appendChild(desc);
  }

  if (node.properties) {
    const ul = document.createElement("ul");
    Object.entries(node.properties).forEach(([key, child]) => {
      ul.appendChild(renderNode(key, child));
    });
    li.appendChild(ul);
  }

  if (node.items) {
    const ul = document.createElement("ul");
    ul.appendChild(renderNode("items", node.items));
    li.appendChild(ul);
  }

  return li;
};

const renderSummary = async () => {
  try {
    const response = await fetch("/api/schema/summary");
    const summary = await response.json();
    const root = document.createElement("ul");
    const sections = summary.sections || {};
    Object.entries(sections).forEach(([section, node]) => {
      root.appendChild(renderNode(section, node));
    });
    treeEl.innerHTML = "";
    treeEl.appendChild(root);
  } catch (err) {
    treeEl.textContent = "Failed to load schema summary.";
  }
};

renderSummary();
