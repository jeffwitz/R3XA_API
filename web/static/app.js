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

const reset = () => {
  inputEl.value = JSON.stringify(defaultPayload, null, 2);
  outputEl.textContent = "";
};

const renderSummary = async () => {
  try {
    const response = await fetch("/api/schema-summary");
    const summary = await response.json();
    const sections = Object.keys(summary.sections || {});
    summaryEl.textContent = `Schema version: ${summary.schema_version || "unknown"}\nSections: ${sections.join(", ")}`;
  } catch (err) {
    summaryEl.textContent = "Failed to load schema summary.";
  }
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

reset();
renderSummary();
