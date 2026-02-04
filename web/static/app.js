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

const loadDraft = () => {
  const stored = localStorage.getItem("r3xaDraft");
  if (stored) return stored;
  return JSON.stringify(defaultPayload, null, 2);
};

const saveDraft = () => {
  localStorage.setItem("r3xaDraft", inputEl.value);
};

const ensureServerStart = () => {
  const appStart = document.body?.dataset?.appStart;
  if (!appStart) return;
  const stored = localStorage.getItem("r3xaAppStart");
  if (stored !== appStart) {
    localStorage.setItem("r3xaAppStart", appStart);
    localStorage.removeItem("r3xaDraft");
  }
};

const reset = () => {
  inputEl.value = JSON.stringify(defaultPayload, null, 2);
  outputEl.textContent = "";
  saveDraft();
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
    generic: (payload) => ({
      id: makeId(),
      kind: "data_sets/generic",
      title: "Generic data",
      description: "Data set description",
      data_sources: payload?.data_sources?.length ? [payload.data_sources[0].id] : [],
      file_type: "application/octet-stream",
      path: "data/",
    }),
    file: (payload) => ({
      id: makeId(),
      kind: "data_sets/file",
      title: "Data file",
      description: "Single file data set",
      data_sources: payload?.data_sources?.length ? [payload.data_sources[0].id] : [],
      time_reference: 0.0,
      timestamps: { kind: "data_set_file", filename: "timestamps.csv" },
      data: { kind: "data_set_file", filename: "data.csv" },
    }),
    list: (payload) => ({
      id: makeId(),
      kind: "data_sets/list",
      title: "Data list",
      description: "List of data files",
      file_type: "application/octet-stream",
      data_sources: payload?.data_sources?.length ? [payload.data_sources[0].id] : [],
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
      payload[key].push(factory(payload));
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

    const validateBtn = document.createElement("button");
    validateBtn.textContent = "Validate item";
    validateBtn.className = "ghost";
    validateBtn.type = "button";
    validateBtn.addEventListener("click", async () => {
      let payload;
      try {
        payload = JSON.parse(inputEl.value);
      } catch {
        return;
      }
      const itemTitle =
        payload[key][index]?.title || `${label} #${index + 1}`;
      const copy = {
        title: payload.title || "temp",
        description: payload.description || "temp",
        version: payload.version || "2024.7.1",
        authors: payload.authors || "temp",
        date: payload.date || "2024-01-01",
        settings: [],
        data_sources: [],
        data_sets: [],
      };
      copy[key] = [payload[key][index]];
      const response = await fetch("/api/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(copy),
      });
      const report = await response.json();
      if (report.valid) {
        window.alert(`${itemTitle}: Valid ✅`);
        return;
      }
      const lines = [`${itemTitle}: Invalid ❌`, ""];
      for (const error of report.errors || []) {
        lines.push(`- ${error.path || "<root>"}: ${error.message}`);
      }
      window.alert(lines.join("\n"));
    });

    header.appendChild(remove);
    header.appendChild(validateBtn);
    card.appendChild(header);

    const form = document.createElement("div");
    form.className = "array-item-form";

    const updateItem = (updater) => {
      let payload;
      try {
        payload = JSON.parse(inputEl.value);
      } catch {
        return;
      }
      payload[key] = payload[key] || [];
      const current = payload[key][index] || {};
      updater(current);
      payload[key][index] = current;
      inputEl.value = JSON.stringify(payload, null, 2);
      saveDraft();
    };

    const addField = (labelText, value, onChange, type = "text") => {
      const row = document.createElement("div");
      row.className = "form-row";

      const label = document.createElement("label");
      label.textContent = labelText;
      const input = document.createElement(type === "textarea" ? "textarea" : "input");
      if (type !== "textarea") input.type = type;
      input.value = value ?? "";
      input.addEventListener("input", () => onChange(input.value));
      row.appendChild(label);
      row.appendChild(input);
      form.appendChild(row);
      return input;
    };

    const addJsonField = (labelText, value, onValid) => {
      const row = document.createElement("div");
      row.className = "form-row";
      const label = document.createElement("label");
      label.textContent = labelText;
      const textarea = document.createElement("textarea");
      textarea.value = JSON.stringify(value ?? {}, null, 2);
      textarea.addEventListener("input", () => {
        try {
          const parsed = JSON.parse(textarea.value);
          onValid(parsed);
        } catch {
          return;
        }
      });
      row.appendChild(label);
      row.appendChild(textarea);
      form.appendChild(row);
    };

    const kind = item.kind || "";
    addField("id", item.id || "", (val) => updateItem((obj) => (obj.id = val)));
    addField("kind", kind, (val) => updateItem((obj) => (obj.kind = val)));
    addField("title", item.title || "", (val) => updateItem((obj) => (obj.title = val)));
    addField(
      "description",
      item.description || "",
      (val) => updateItem((obj) => (obj.description = val))
    );

    if (key === "settings" && kind === "settings/specimen") {
      addJsonField("sizes (JSON array)", item.sizes || [], (val) =>
        updateItem((obj) => (obj.sizes = val))
      );
    }

    if (key === "data_sources") {
      addField(
        "output_components",
        item.output_components ?? 1,
        (val) => updateItem((obj) => (obj.output_components = Number(val))),
        "number"
      );
      addField(
        "output_dimension",
        item.output_dimension || "surface",
        (val) => updateItem((obj) => (obj.output_dimension = val))
      );
      addJsonField("output_units (JSON array)", item.output_units || [], (val) =>
        updateItem((obj) => (obj.output_units = val))
      );
      addField(
        "manufacturer",
        item.manufacturer || "",
        (val) => updateItem((obj) => (obj.manufacturer = val))
      );
      addField("model", item.model || "", (val) => updateItem((obj) => (obj.model = val)));

      if (kind === "data_sources/camera") {
        addJsonField("image_size (JSON array)", item.image_size || [], (val) =>
          updateItem((obj) => (obj.image_size = val))
        );
      }
    }

    if (key === "data_sets") {
      const dsList = (item.data_sources || []).join(", ");
      addField("data_sources (comma)", dsList, (val) =>
        updateItem((obj) => (obj.data_sources = val.split(",").map((s) => s.trim()).filter(Boolean)))
      );

      if (kind === "data_sets/generic") {
        addField(
          "file_type",
          item.file_type || "application/octet-stream",
          (val) => updateItem((obj) => (obj.file_type = val))
        );
        addField("path", item.path || "data/", (val) => updateItem((obj) => (obj.path = val)));
      }

      if (kind === "data_sets/file") {
        addField(
          "time_reference",
          item.time_reference ?? 0,
          (val) => updateItem((obj) => (obj.time_reference = Number(val))),
          "number"
        );
        addField("data filename", item.data?.filename || "data.csv", (val) =>
          updateItem((obj) => (obj.data = { kind: "data_set_file", filename: val }))
        );
        addField(
          "timestamps filename",
          item.timestamps?.filename || "timestamps.csv",
          (val) => updateItem((obj) => (obj.timestamps = { kind: "data_set_file", filename: val }))
        );
      }

      if (kind === "data_sets/list") {
        addField(
          "file_type",
          item.file_type || "application/octet-stream",
          (val) => updateItem((obj) => (obj.file_type = val))
        );
        addField(
          "time_reference",
          item.time_reference ?? 0,
          (val) => updateItem((obj) => (obj.time_reference = Number(val))),
          "number"
        );
        addField(
          "timestamps (comma numbers)",
          (item.timestamps || []).join(", "),
          (val) =>
            updateItem((obj) => {
              obj.timestamps = val
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean)
                .map((n) => Number(n));
            })
        );
        addField(
          "data files (comma)",
          (item.data || []).join(", "),
          (val) =>
            updateItem((obj) => {
              obj.data = val.split(",").map((s) => s.trim()).filter(Boolean);
            })
        );
      }
    }

    card.appendChild(form);

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
  saveDraft();
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
  saveDraft();
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
inputEl.addEventListener("input", () => {
  saveDraft();
  syncFormFromJson();
});

ensureServerStart();
inputEl.value = loadDraft();
syncFormFromJson();
renderSummary();
