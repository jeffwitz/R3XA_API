const defaultPayload = {
  title: "Minimal R3XA",
  description: "Quick validation example",
  version: "2024.7.1",
  authors: "R3XA Team",
  date: "2024-10-30",
  settings: [],
  data_sources: [],
  data_sets: [],
};

const inputEl = document.getElementById("json-input");
const outputEl = document.getElementById("validation-output");
const summaryEl = document.getElementById("schema-summary");
const formEl = document.getElementById("header-form");
const settingsEl = document.getElementById("settings-form");
const dataSourcesEl = document.getElementById("data-sources-form");
const dataSetsEl = document.getElementById("data-sets-form");

const reset = () => {
  inputEl.value = JSON.stringify(defaultPayload, null, 2);
  outputEl.textContent = "";
  syncFormFromJson();
};

const renderSummary = async () => {
  try {
    const response = await fetch("/api/schema/summary");
    const summary = await response.json();
    const sections = Object.keys(summary.sections || {});
    summaryEl.textContent = `Schema version: ${summary.schema_version || "unknown"}\nSections: ${sections.join(", ")}`;
    buildHeaderForm(summary.sections?.header?.properties || {});
  } catch (err) {
    summaryEl.textContent = "Failed to load schema summary.";
  }
};

let syncing = false;

const buildHeaderForm = (properties) => {
  if (!formEl) return;
  formEl.innerHTML = "";
  Object.entries(properties).forEach(([key, meta]) => {
    const wrapper = document.createElement("div");
    wrapper.className = "form-row";

    const label = document.createElement("label");
    label.textContent = meta.title || key;
    label.setAttribute("for", `field-${key}`);

    const input = document.createElement("input");
    input.type = "text";
    input.id = `field-${key}`;
    input.name = key;
    input.placeholder = meta.description || "";
    input.addEventListener("input", () => syncJsonFromForm());

    wrapper.appendChild(label);
    wrapper.appendChild(input);
    formEl.appendChild(wrapper);
  });
  syncFormFromJson();
};

const makeId = () => `id_${Math.random().toString(36).slice(2, 12)}`;

const templates = {
  settings: {
    generic: () => ({
      id: makeId(),
      kind: "settings/generic",
      title: "Generic setting",
      description: "Describe the setting",
    }),
    specimen: () => ({
      id: makeId(),
      kind: "settings/specimen",
      title: "Specimen",
      description: "Specimen description",
      sizes: [{ kind: "unit", unit: "mm", title: "length", value: 0, scale: 1 }],
    }),
  },
  data_sources: {
    generic: () => ({
      id: makeId(),
      kind: "data_sources/generic",
      title: "Generic source",
      description: "Source description",
      output_components: 1,
      output_dimension: "surface",
      output_units: [{ kind: "unit", unit: "unit", title: "value", value: 1, scale: 1 }],
      manufacturer: "Unknown",
      model: "Unknown",
    }),
    camera: () => ({
      id: makeId(),
      kind: "data_sources/camera",
      title: "Camera",
      description: "Camera description",
      output_components: 1,
      output_dimension: "surface",
      output_units: [{ kind: "unit", unit: "gl", title: "graylevel", value: 1, scale: 1 }],
      manufacturer: "Unknown",
      model: "Unknown",
      image_size: [
        { kind: "unit", unit: "px", title: "width", value: 0, scale: 1 },
        { kind: "unit", unit: "px", title: "height", value: 0, scale: 1 },
      ],
    }),
  },
  data_sets: {
    generic: () => ({
      id: makeId(),
      kind: "data_sets/generic",
      title: "Generic data",
      description: "Data set description",
      data_sources: [],
      file_type: "application/octet-stream",
      path: "data/",
    }),
    file: () => ({
      id: makeId(),
      kind: "data_sets/file",
      title: "Data file",
      description: "Single file data set",
      data_sources: [],
      time_reference: 0.0,
      timestamps: { kind: "data_set_file", filename: "timestamps.csv" },
      data: { kind: "data_set_file", filename: "data.csv" },
    }),
    list: () => ({
      id: makeId(),
      kind: "data_sets/list",
      title: "Data list",
      description: "List of data files",
      file_type: "application/octet-stream",
      data_sources: [],
      time_reference: 0.0,
      timestamps: [0.0],
      data: ["data_0001.tif"],
    }),
  },
};

const buildArrayEditor = (container, key, label, templateSet) => {
  if (!container) return;
  container.innerHTML = "";

  const actions = document.createElement("div");
  actions.className = "array-actions";

  Object.entries(templateSet).forEach(([templateKey, factory]) => {
    const addBtn = document.createElement("button");
    addBtn.textContent = `Add ${label} (${templateKey})`;
    addBtn.className = "ghost";
    addBtn.type = "button";
    addBtn.addEventListener("click", () => {
      let payload;
      try {
        payload = JSON.parse(inputEl.value);
      } catch {
        return;
      }
      payload[key] = payload[key] || [];
      payload[key].push(factory());
      inputEl.value = JSON.stringify(payload, null, 2);
      syncFormFromJson();
    });
    actions.appendChild(addBtn);
  });

  container.appendChild(actions);

  const list = document.createElement("div");
  list.className = "array-list";
  container.appendChild(list);

  let payload;
  try {
    payload = JSON.parse(inputEl.value);
  } catch {
    return;
  }
  const items = payload[key] || [];

  items.forEach((item, index) => {
    const card = document.createElement("div");
    card.className = "array-item";

    const header = document.createElement("div");
    header.className = "array-item-header";
    header.textContent = `${label} #${index + 1}`;

    const remove = document.createElement("button");
    remove.textContent = "Remove";
    remove.className = "ghost";
    remove.type = "button";
    remove.addEventListener("click", () => {
      let payload;
      try {
        payload = JSON.parse(inputEl.value);
      } catch {
        return;
      }
      payload[key] = payload[key] || [];
      payload[key].splice(index, 1);
      inputEl.value = JSON.stringify(payload, null, 2);
      syncFormFromJson();
    });

    header.appendChild(remove);
    card.appendChild(header);

    const textarea = document.createElement("textarea");
    textarea.spellcheck = false;
    textarea.value = JSON.stringify(item, null, 2);
    textarea.addEventListener("input", () => {
      let payload;
      try {
        payload = JSON.parse(inputEl.value);
      } catch {
        return;
      }
      try {
        payload[key][index] = JSON.parse(textarea.value);
      } catch {
        return;
      }
      inputEl.value = JSON.stringify(payload, null, 2);
    });
    card.appendChild(textarea);

    list.appendChild(card);
  });
};

const syncJsonFromForm = () => {
  if (syncing) return;
  syncing = true;
  let payload;
  try {
    payload = JSON.parse(inputEl.value);
  } catch (err) {
    syncing = false;
    return;
  }
  const inputs = formEl.querySelectorAll("input");
  inputs.forEach((input) => {
    if (input.value !== "") {
      payload[input.name] = input.value;
    }
  });
  inputEl.value = JSON.stringify(payload, null, 2);
  syncing = false;
};

const syncFormFromJson = () => {
  if (!formEl) return;
  if (syncing) return;
  syncing = true;
  let payload;
  try {
    payload = JSON.parse(inputEl.value);
  } catch (err) {
    syncing = false;
    return;
  }
  const inputs = formEl.querySelectorAll("input");
  inputs.forEach((input) => {
    input.value = payload[input.name] ?? "";
  });
  buildArrayEditor(settingsEl, "settings", "Setting", templates.settings);
  buildArrayEditor(dataSourcesEl, "data_sources", "Data source", templates.data_sources);
  buildArrayEditor(dataSetsEl, "data_sets", "Data set", templates.data_sets);
  syncing = false;
};

const validate = async () => {
  outputEl.textContent = "";
  let payload;
  try {
    payload = JSON.parse(inputEl.value);
  } catch (err) {
    outputEl.textContent = `Parse error: ${err.message}`;
    return;
  }

  const response = await fetch("/api/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const report = await response.json();
  if (report.valid) {
    outputEl.textContent = "Valid ✅";
    return;
  }

  const lines = ["Invalid ❌", ""];
  for (const error of report.errors || []) {
    lines.push(`- ${error.path || "<root>"}: ${error.message}`);
  }
  outputEl.textContent = lines.join("\n");
};

document.getElementById("validate-btn").addEventListener("click", validate);
document.getElementById("reset-btn").addEventListener("click", reset);
inputEl.addEventListener("input", () => syncFormFromJson());

reset();
renderSummary();
