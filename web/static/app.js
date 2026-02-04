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
