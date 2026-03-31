const defaultRegistryItem = {
  id: "item_example",
  kind: "data_sources/generic",
  title: "Generic source",
  description: "Example registry item",
  output_components: 1,
  output_dimension: "surface",
  output_units: [{ kind: "unit", title: "value", value: 1.0, unit: "unit", scale: 1.0 }],
  manufacturer: "Unknown",
  model: "Unknown",
};

const inputEl = document.getElementById("registry-json-input");
const outputEl = document.getElementById("registry-validation-output");
const kindEl = document.getElementById("registry-kind");

const ensureServerStart = () => {
  const appStart = document.body?.dataset?.appStart;
  if (!appStart) return;
  const stored = localStorage.getItem("r3xaRegistryAppStart");
  if (stored !== appStart) {
    localStorage.setItem("r3xaRegistryAppStart", appStart);
    localStorage.removeItem("r3xaRegistryDraft");
  }
};

const loadDraft = () => {
  const stored = localStorage.getItem("r3xaRegistryDraft");
  if (stored) {
    return stored;
  }
  return JSON.stringify(defaultRegistryItem, null, 2);
};

const saveDraft = () => {
  localStorage.setItem("r3xaRegistryDraft", inputEl.value);
  localStorage.setItem("r3xaRegistryKind", kindEl.value.trim());
};

const reset = () => {
  inputEl.value = JSON.stringify(defaultRegistryItem, null, 2);
  kindEl.value = "";
  outputEl.textContent = "";
  saveDraft();
};

const validateItem = async () => {
  outputEl.textContent = "";
  let item;
  try {
    item = JSON.parse(inputEl.value);
  } catch (err) {
    outputEl.textContent = `Parse error: ${err.message}`;
    return;
  }

  const payload = { item };
  const kind = kindEl.value.trim();
  if (kind) {
    payload.kind = kind;
  }

  const response = await fetch("/api/registry/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const report = await response.json();
  if (report.valid) {
    outputEl.textContent = "Valid registry item ✅";
    saveDraft();
    return;
  }
  const lines = ["Invalid registry item ❌", ""];
  for (const error of report.errors || []) {
    lines.push(`- ${error}`);
  }
  outputEl.textContent = lines.join("\n");
};

const downloadJson = () => {
  try {
    JSON.parse(inputEl.value);
  } catch (err) {
    outputEl.textContent = `Parse error: ${err.message}`;
    return;
  }
  const blob = new Blob([inputEl.value], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "registry-item.json";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
};

const saveWithDialog = async () => {
  try {
    JSON.parse(inputEl.value);
  } catch (err) {
    outputEl.textContent = `Parse error: ${err.message}`;
    return;
  }

  if (window.showSaveFilePicker) {
    try {
      const handle = await window.showSaveFilePicker({
        suggestedName: "registry-item.json",
        types: [
          {
            description: "JSON",
            accept: { "application/json": [".json"] },
          },
        ],
      });
      const writable = await handle.createWritable();
      await writable.write(inputEl.value);
      await writable.close();
      return;
    } catch (err) {
      if (err && err.name === "AbortError") return;
    }
  }

  downloadJson();
};

const loadJsonFile = (file) => {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    const text = reader.result;
    try {
      JSON.parse(text);
    } catch (err) {
      outputEl.textContent = `Parse error: ${err.message}`;
      return;
    }
    inputEl.value = text;
    outputEl.textContent = "";
    saveDraft();
  };
  reader.readAsText(file);
};

document.getElementById("registry-validate-btn").addEventListener("click", validateItem);
document.getElementById("registry-reset-btn").addEventListener("click", reset);
document.getElementById("registry-save-btn").addEventListener("click", saveWithDialog);
document.getElementById("registry-load-input").addEventListener("change", (event) => {
  loadJsonFile(event.target.files?.[0]);
  event.target.value = "";
});
inputEl.addEventListener("input", saveDraft);
kindEl.addEventListener("input", saveDraft);

ensureServerStart();
inputEl.value = loadDraft();
kindEl.value = localStorage.getItem("r3xaRegistryKind") || "";
