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
const modeHelpEl = document.getElementById("mode-help");
const profileSelectEl = document.getElementById("profile-select");
const guidedStepsEl = document.getElementById("guided-steps");
const guidedPreviousEl = document.getElementById("guided-previous");
const guidedNextEl = document.getElementById("guided-next");
const guidedProgressEl = document.getElementById("guided-progress");
const modeButtons = document.querySelectorAll("[data-editor-mode]");

let schemaCatalog = null;
let uiCatalog = null;
let editorMode = localStorage.getItem("r3xaEditorMode") || "guided";
let selectedProfile = localStorage.getItem("r3xaProfile") || "generic";
let guidedStepIndex = Number(localStorage.getItem("r3xaGuidedStep")) || 0;
let syncing = false;

const loadDraft = () => {
  const stored = localStorage.getItem("r3xaDraft");
  if (stored) return stored;
  return JSON.stringify(defaultPayload, null, 2);
};

const saveDraft = () => {
  localStorage.setItem("r3xaDraft", inputEl.value);
  localStorage.setItem("r3xaDraftLast", inputEl.value);
};

const readPayload = () => {
  try {
    return JSON.parse(inputEl.value);
  } catch {
    return null;
  }
};

const setObjectField = (object, key, value, required) => {
  if (value === undefined || (value === "" && !required)) {
    delete object[key];
    return;
  }
  object[key] = value;
};

const fieldLevel = (key) => uiCatalog?.default?.fields?.[key]?.level || "basic";

const isFieldVisible = (key, required = false, forceVisible = false) => {
  const level = fieldLevel(key);
  if (required || forceVisible) return true;
  if (editorMode === "expert") return true;
  if (editorMode === "advanced") return level !== "expert";
  return level === "basic";
};

const isKindVisible = (kind) => {
  if (editorMode !== "guided") return true;
  const profile = uiCatalog?.profiles?.[selectedProfile];
  const recommended = profile?.recommended_kinds || [];
  return recommended.length === 0 || recommended.includes(kind);
};

const updateEditorMode = () => {
  document.body.dataset.editorMode = editorMode;
  modeButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.editorMode === editorMode);
    button.setAttribute("aria-selected", button.dataset.editorMode === editorMode ? "true" : "false");
  });
  const help = {
    guided: "Start from an experience profile. Common fields are shown first.",
    advanced: "Edit all user-facing fields while keeping technical identifiers hidden.",
    expert: "Inspect every field and edit the canonical JSON directly when needed.",
  };
  if (modeHelpEl) modeHelpEl.textContent = help[editorMode];
  if (profileSelectEl) profileSelectEl.disabled = editorMode !== "guided";
  if (schemaCatalog) {
    buildHeaderForm(schemaCatalog.sections?.header?.properties || {});
    syncFormFromJson();
  }
};

const populateProfiles = () => {
  if (!profileSelectEl || !uiCatalog) return;
  profileSelectEl.innerHTML = "";
  Object.entries(uiCatalog.profiles || {}).forEach(([profileId, profile]) => {
    const option = document.createElement("option");
    option.value = profileId;
    option.textContent = profile.title || profileId;
    option.title = profile.description || "";
    profileSelectEl.appendChild(option);
  });
  if (!uiCatalog.profiles?.[selectedProfile]) selectedProfile = "generic";
  profileSelectEl.value = selectedProfile;
};

const appendItem = (sectionName, kind) => {
  const payload = readPayload();
  const meta = schemaCatalog?.sections?.[sectionName]?.kinds?.[kind];
  if (!payload || !meta) return;
  payload[sectionName] = payload[sectionName] || [];
  payload[sectionName].push(createItem(kind, meta, payload));
  inputEl.value = JSON.stringify(payload, null, 2);
  saveDraft();
  syncFormFromJson();
};

const hasValue = (value) => {
  if (Array.isArray(value)) return value.length > 0;
  return value !== undefined && value !== null && value !== "";
};

const requiredFieldIsPresent = (item, key, meta) => {
  if (!(key in item) || item[key] === undefined || item[key] === null) return false;
  const value = item[key];
  const fieldMeta = meta.properties?.[key] || {};
  if (fieldMeta.type === "array") return value.length >= (fieldMeta.minItems || 0);
  if (fieldMeta.type === "string") return value.length >= (fieldMeta.minLength || 0);
  return true;
};

const itemIsComplete = (item, meta) => {
  return (meta.required || []).every((key) => requiredFieldIsPresent(item, key, meta));
};

const validationMessage = (error) => editorMode === "guided" ? error.user_message || error.message : error.message;

const stepIsComplete = (step, payload) => {
  if (step.section === "header") {
    const required = schemaCatalog?.sections?.header?.required || [];
    return required.every((key) => hasValue(payload[key]));
  }
  const items = payload[step.section] || [];
  if (!step.kind) return items.length > 0;
  const meta = schemaCatalog?.sections?.[step.section]?.kinds?.[step.kind];
  return Boolean(meta && items.some((item) => item.kind === step.kind && itemIsComplete(item, meta)));
};

const stepCanAdvance = (step, payload) => {
  if (!step) return false;
  const target = step.section === "header"
    ? payload
    : step.kind
      ? guidedItem(step, payload)
      : payload[step.section] || [];
  if (!target) return false;
  return (step.questions || [])
    .filter((question) => question.required && conditionMatches(question.when, payload))
    .every((question) => hasValue(target[question.field]));
};

const valueAtPath = (payload, path) => path.split(".").reduce((value, key) => value?.[key], payload);

const conditionMatches = (condition, payload) => {
  if (!condition) return true;
  if (condition.kind) {
    const exists = (payload[condition.section] || []).some((item) => item.kind === condition.kind);
    if (condition.exists !== undefined && exists !== condition.exists) return false;
  }
  if (condition.path) {
    const value = valueAtPath(payload, condition.path);
    if (condition.exists !== undefined && Boolean(value) !== condition.exists) return false;
    if (condition.equals !== undefined && value !== condition.equals) return false;
  }
  return true;
};

const guidedItem = (step, payload) => {
  if (!step.kind) return null;
  return (payload[step.section] || []).find((item) => item.kind === step.kind) || null;
};

const renderGuidedQuestions = (step, payload, container) => {
  (step.questions || []).forEach((question) => {
    if (!conditionMatches(question.when, payload)) return;
    const target = step.section === "header" ? payload : guidedItem(step, payload);
    if (!target || !question.field) return;
    const properties = step.section === "header"
      ? schemaCatalog.sections.header.properties
      : schemaCatalog.sections[step.section].kinds[step.kind]?.properties;
    const sourceMeta = properties?.[question.field];
    if (!sourceMeta) return;
    const required = question.required || (step.section === "header"
      ? (schemaCatalog.sections.header.required || []).includes(question.field)
      : (schemaCatalog.sections[step.section].kinds[step.kind]?.required || []).includes(question.field));
    const meta = {
      ...sourceMeta,
      title: question.title || sourceMeta.title,
      description: question.description || sourceMeta.description,
    };
    renderField(
      container,
      question.field,
      meta,
      target[question.field],
      (value) => {
        const currentPayload = readPayload();
        if (!currentPayload) return;
        const currentTarget = step.section === "header" ? currentPayload : guidedItem(step, currentPayload);
        if (!currentTarget) return;
        setObjectField(currentTarget, question.field, value, required);
        inputEl.value = JSON.stringify(currentPayload, null, 2);
        saveDraft();
        refreshGuidedNavigation();
      },
      {
        required,
        forceVisible: true,
        payload,
        id: `guided-${step.id}-${question.field}`,
        path: step.section === "header" ? question.field : `${step.section}/0/${question.field}`,
      }
    );
  });
};

const renderGuidedSteps = () => {
  if (!guidedStepsEl || !uiCatalog || !schemaCatalog) return;
  const profile = uiCatalog.profiles?.[selectedProfile];
  const steps = profile?.steps || [];
  guidedStepIndex = Math.min(Math.max(guidedStepIndex, 0), Math.max(steps.length - 1, 0));
  guidedStepsEl.innerHTML = "";
  guidedStepsEl.className = "guided-steps";
  const payload = readPayload() || {};
  if (guidedProgressEl) guidedProgressEl.textContent = steps.length ? `Step ${guidedStepIndex + 1} of ${steps.length}` : "";
  if (guidedPreviousEl) guidedPreviousEl.disabled = guidedStepIndex === 0;
  if (guidedNextEl) guidedNextEl.disabled = !steps.length || guidedStepIndex === steps.length - 1 || !stepCanAdvance(steps[guidedStepIndex], payload);
  steps.forEach((step, index) => {
    const block = document.createElement("div");
    block.className = "guided-step-block";
    const row = document.createElement("div");
    row.className = "guided-step";
    if (index === guidedStepIndex) row.classList.add("is-current");
    row.addEventListener("click", () => {
      guidedStepIndex = index;
      localStorage.setItem("r3xaGuidedStep", String(guidedStepIndex));
      renderGuidedSteps();
    });
    const complete = stepIsComplete(step, payload);
    if (complete) row.classList.add("is-complete");
    const label = document.createElement("div");
    label.className = "guided-step-label";
    label.textContent = `${complete ? "✓" : "○"} ${step.title || step.id}`;
    row.appendChild(label);
    if (step.section !== "header" && !complete) {
      const kinds = step.kind
        ? [[step.kind, schemaCatalog.sections[step.section].kinds[step.kind]]]
        : Object.entries(schemaCatalog.sections[step.section]?.kinds || {});
      kinds.forEach(([kind, meta]) => {
        const addButton = document.createElement("button");
        addButton.type = "button";
        addButton.className = "ghost";
        addButton.textContent = `Add ${meta.title || kind}`;
        addButton.addEventListener("click", (event) => event.stopPropagation());
        addButton.addEventListener("click", () => appendItem(step.section, kind));
        row.appendChild(addButton);
      });
    }
    block.appendChild(row);
    const questions = document.createElement("div");
    questions.className = "guided-questions";
    if (index === guidedStepIndex) renderGuidedQuestions(step, payload, questions);
    block.appendChild(questions);
    guidedStepsEl.appendChild(block);
  });
};

const refreshGuidedNavigation = () => {
  const steps = uiCatalog?.profiles?.[selectedProfile]?.steps || [];
  const payload = readPayload() || {};
  const currentStep = steps[guidedStepIndex];
  if (guidedPreviousEl) guidedPreviousEl.disabled = guidedStepIndex === 0;
  if (guidedNextEl) guidedNextEl.disabled = !steps.length || guidedStepIndex === steps.length - 1 || !stepCanAdvance(currentStep, payload);
  if (guidedProgressEl) guidedProgressEl.textContent = steps.length ? `Step ${guidedStepIndex + 1} of ${steps.length}` : "";
  guidedStepsEl?.querySelectorAll(".guided-step").forEach((row, index) => {
    const complete = stepIsComplete(steps[index], payload);
    row.classList.toggle("is-complete", complete);
    row.classList.toggle("is-current", index === guidedStepIndex);
    const label = row.querySelector(".guided-step-label");
    if (label) label.textContent = `${complete ? "✓" : "○"} ${steps[index].title || steps[index].id}`;
  });
};

const makeId = () => `id_${Math.random().toString(36).slice(2, 12)}`;

const defaultForField = (key, meta, payload) => {
  if (meta.const !== undefined) return meta.const;
  if (meta.default !== undefined) return meta.default;

  if (key === "id") return makeId();
  if (key === "title") return `New ${meta.title || "item"}`;
  if (key === "description") return "";
  if (key === "file_type") return "application/octet-stream";
  if (key === "path" || key === "folder") return "data/";
  if (key === "filename") return "data.csv";
  if (key === "output_components") return 1;
  if (key === "output_dimension") {
    return meta.enum?.includes("surface") ? "surface" : meta.enum?.[0] || "";
  }
  if (key === "data_sources") {
    const sourceId = payload?.data_sources?.[0]?.id;
    return sourceId ? [sourceId] : [];
  }
  if (key === "input_data_sets") {
    const dataSetId = payload?.data_sets?.[0]?.id;
    return dataSetId ? [dataSetId] : [];
  }

  if (meta.type === "string") return "";
  if (meta.type === "number" || meta.type === "integer") return 0;
  if (meta.type === "boolean") return false;
  if (meta.type === "array") return [];
  if (meta.type === "object") {
    const object = {};
    Object.entries(meta.properties || {}).forEach(([propertyKey, propertyMeta]) => {
      const propertyRequired = (meta.required || []).includes(propertyKey);
      if (propertyRequired || propertyMeta.const !== undefined) {
        object[propertyKey] = defaultForField(propertyKey, propertyMeta, payload);
      }
    });
    return object;
  }
  return "";
};

const createItem = (kind, meta, payload) => {
  const item = {};
  const properties = meta.properties || {};
  const required = new Set(meta.required || []);

  Object.entries(properties).forEach(([key, propertyMeta]) => {
    if (key === "id") {
      item[key] = makeId();
      return;
    }
    if (key === "kind") {
      item[key] = propertyMeta.const || kind;
      return;
    }
    if (required.has(key)) {
      item[key] = defaultForField(key, propertyMeta, payload);
    }
  });
  return item;
};

const fieldControlValue = (control, meta) => {
  if (meta.type === "boolean") return control.checked;
  if (meta.type === "number" || meta.type === "integer") {
    return control.value === "" ? undefined : Number(control.value);
  }
  return control.value;
};

const isUnitMeta = (meta) => meta?.ref === "#/$defs/types/unit";

const referenceSection = (meta, options) => {
  if (options.referenceSection) return options.referenceSection;
  if (meta?.ref?.endsWith("data_set_id")) return "data_sets";
  if (meta?.ref?.endsWith("data_source_id")) return "data_sources";
  return null;
};

const renderReferenceField = (container, key, meta, value, onChange, options) => {
  const wrapper = document.createElement("div");
  wrapper.className = "form-row";
  wrapper.dataset.fieldLevel = fieldLevel(key);
  if (options.path) wrapper.dataset.jsonPath = options.path;
  if (options.id) wrapper.id = options.id;
  const label = document.createElement("label");
  label.textContent = `${meta.title || key}${options.required ? " *" : ""}`;
  const fieldId = options.id || `field-${key}`;
  label.setAttribute("for", fieldId);
  wrapper.appendChild(label);

  const control = document.createElement("select");
  control.id = fieldId;
  control.name = key;
  control.multiple = meta.type === "array";
  if (control.multiple) control.size = 3;
  const section = referenceSection(meta, options);
  const known = options.payload?.[section] || [];
  const current = Array.isArray(value) ? value : value ? [value] : [];
  const choices = new Map(known.map((item) => [item.id, item.title || item.kind || item.id]));
  current.forEach((id) => {
    if (!choices.has(id)) choices.set(id, `${id} (not loaded)`);
  });
  if (!control.multiple && !current.length) {
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = "Select an object…";
    control.appendChild(blank);
  }
  choices.forEach((title, id) => {
    if (!id) return;
    const option = document.createElement("option");
    option.value = id;
    option.textContent = title;
    option.selected = current.includes(id);
    control.appendChild(option);
  });
  control.addEventListener("change", () => {
    const selected = Array.from(control.selectedOptions).map((option) => option.value).filter(Boolean);
    onChange(meta.type === "array" ? selected : selected[0]);
  });
  wrapper.appendChild(control);
  if (meta.description) {
    const description = document.createElement("small");
    description.className = "field-description";
    description.textContent = meta.description;
    wrapper.appendChild(description);
  }
  container.appendChild(wrapper);
  return control;
};

const renderUnitField = (container, key, meta, value, onChange, options) => {
  const wrapper = document.createElement("div");
  wrapper.className = "form-row unit-field";
  wrapper.dataset.fieldLevel = fieldLevel(key);
  if (options.path) wrapper.dataset.jsonPath = options.path;
  if (options.id) wrapper.id = options.id;
  const label = document.createElement("label");
  label.textContent = `${meta.title || key}${options.required ? " *" : ""}`;
  wrapper.appendChild(label);
  const fields = document.createElement("div");
  fields.className = "unit-editor";
  let unitValue = { ...(value || {}), kind: "unit" };
  const properties = meta.properties || {};
  Object.entries(properties).forEach(([part, partMeta]) => {
    if (part === "kind") return;
    const partWrapper = document.createElement("label");
    partWrapper.className = "unit-part";
    partWrapper.textContent = partMeta.title || part;
    const control = document.createElement("input");
    control.type = partMeta.type === "number" || partMeta.type === "integer" ? "number" : "text";
    control.step = partMeta.type === "number" ? "any" : "1";
    control.value = unitValue[part] ?? "";
    control.addEventListener("input", () => {
      const next = { ...unitValue, kind: "unit" };
      const nextValue = control.type === "number" && control.value !== "" ? Number(control.value) : control.value;
      if (nextValue === "" && !(meta.required || []).includes(part)) delete next[part];
      else next[part] = nextValue;
      unitValue = next;
      onChange(next);
    });
    partWrapper.appendChild(control);
    fields.appendChild(partWrapper);
  });
  wrapper.appendChild(fields);
  if (meta.description) {
    const description = document.createElement("small");
    description.className = "field-description";
    description.textContent = meta.description;
    wrapper.appendChild(description);
  }
  container.appendChild(wrapper);
  return wrapper;
};

const renderUnitArrayField = (container, key, meta, value, onChange, options) => {
  const wrapper = document.createElement("div");
  wrapper.className = "form-row unit-array-field";
  wrapper.dataset.fieldLevel = fieldLevel(key);
  if (options.path) wrapper.dataset.jsonPath = options.path;
  if (options.id) wrapper.id = options.id;
  const label = document.createElement("label");
  label.textContent = `${meta.title || key}${options.required ? " *" : ""}`;
  wrapper.appendChild(label);
  const list = document.createElement("div");
  list.className = "unit-array-list";
  let values = Array.isArray(value) ? [...value] : [];
  values.forEach((unitValue, index) => {
    const row = document.createElement("div");
    row.className = "unit-array-row";
    renderUnitField(row, `${key}-${index}`, meta.items, unitValue, (next) => {
      const nextValues = [...values];
      nextValues[index] = next;
      values = nextValues;
      onChange(nextValues);
    }, {required: false, id: `${options.id || key}-${index}`});
    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.className = "ghost";
    removeButton.textContent = "Remove";
    removeButton.addEventListener("click", () => {
      values = values.filter((_, itemIndex) => itemIndex !== index);
      onChange(values);
      options.refresh?.();
    });
    row.appendChild(removeButton);
    list.appendChild(row);
  });
  wrapper.appendChild(list);
  const addButton = document.createElement("button");
  addButton.type = "button";
  addButton.className = "ghost";
  addButton.textContent = "Add unit";
  addButton.addEventListener("click", () => {
    values = [...values, {kind: "unit", unit: ""}];
    onChange(values);
    options.refresh?.();
  });
  wrapper.appendChild(addButton);
  if (meta.description) {
    const description = document.createElement("small");
    description.className = "field-description";
    description.textContent = meta.description;
    wrapper.appendChild(description);
  }
  container.appendChild(wrapper);
  return wrapper;
};

const renderObjectArrayField = (container, key, meta, value, onChange, options) => {
  const wrapper = document.createElement("div");
  wrapper.className = "form-row object-array-field";
  wrapper.dataset.fieldLevel = fieldLevel(key);
  if (options.path) wrapper.dataset.jsonPath = options.path;
  if (options.id) wrapper.id = options.id;
  const label = document.createElement("label");
  label.textContent = `${meta.title || key}${options.required ? " *" : ""}`;
  wrapper.appendChild(label);
  let values = Array.isArray(value) ? [...value] : [];
  const list = document.createElement("div");
  list.className = "object-array-list";
  values.forEach((item, index) => {
    const row = document.createElement("div");
    row.className = "object-array-row";
    const control = document.createElement("textarea");
    control.value = JSON.stringify(item, null, 2);
    control.className = "json-field";
    control.addEventListener("input", () => {
      try {
        values[index] = JSON.parse(control.value);
        control.setCustomValidity("");
        onChange(values);
      } catch {
        control.setCustomValidity("Enter valid JSON");
      }
    });
    row.appendChild(control);
    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.className = "ghost";
    removeButton.textContent = "Remove";
    removeButton.addEventListener("click", () => {
      values = values.filter((_, itemIndex) => itemIndex !== index);
      onChange(values);
      options.refresh?.();
    });
    row.appendChild(removeButton);
    list.appendChild(row);
  });
  wrapper.appendChild(list);
  const addButton = document.createElement("button");
  addButton.type = "button";
  addButton.className = "ghost";
  addButton.textContent = "Add object";
  addButton.addEventListener("click", () => {
    values = [...values, {}];
    onChange(values);
    options.refresh?.();
  });
  wrapper.appendChild(addButton);
  if (meta.description) {
    const description = document.createElement("small");
    description.className = "field-description";
    description.textContent = meta.description;
    wrapper.appendChild(description);
  }
  container.appendChild(wrapper);
  return wrapper;
};

const renderField = (container, key, meta, value, onChange, options = {}) => {
  if (!isFieldVisible(key, options.required)) return null;
  if (isUnitMeta(meta)) return renderUnitField(container, key, meta, value, onChange, options);
  if (meta.type === "array" && isUnitMeta(meta.items)) {
    return renderUnitArrayField(container, key, meta, value, onChange, options);
  }
  if (meta.type === "array" && meta.items && (meta.items.type === "object" || meta.items.properties || meta.items.anyOf || meta.items.oneOf)) {
    return renderObjectArrayField(container, key, meta, value, onChange, options);
  }
  if (meta.ref?.endsWith("data_set_id") || meta.ref?.endsWith("data_source_id")) {
    return renderReferenceField(container, key, meta, value, onChange, options);
  }
  if (meta.type === "array" && (meta.items?.ref?.endsWith("data_set_id") || meta.items?.ref?.endsWith("data_source_id"))) {
    return renderReferenceField(container, key, meta, value, onChange, options);
  }
  const wrapper = document.createElement("div");
  wrapper.className = "form-row";
  wrapper.dataset.fieldLevel = fieldLevel(key);
  if (options.path) wrapper.dataset.jsonPath = options.path;

  const label = document.createElement("label");
  label.textContent = `${meta.title || key}${options.required ? " *" : ""}`;
  const fieldId = options.id || `field-${key}`;
  label.setAttribute("for", fieldId);
  wrapper.appendChild(label);

  let control;
  const complex = meta.type === "object" || meta.type === "array";
  const primitiveArray = meta.type === "array" && meta.items && meta.items.type !== "object";

  if (meta.enum) {
    control = document.createElement("select");
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = "Select…";
    control.appendChild(blank);
    meta.enum.forEach((choice) => {
      const option = document.createElement("option");
      option.value = choice;
      option.textContent = choice;
      control.appendChild(option);
    });
    control.value = value ?? "";
  } else if (meta.const !== undefined) {
    control = document.createElement("input");
    control.type = "text";
    control.value = meta.const;
    control.readOnly = true;
  } else if (meta.type === "boolean") {
    control = document.createElement("input");
    control.type = "checkbox";
    control.checked = Boolean(value);
  } else if (meta.type === "number" || meta.type === "integer") {
    control = document.createElement("input");
    control.type = "number";
    control.step = meta.type === "integer" ? "1" : "any";
    control.value = value ?? "";
  } else if (primitiveArray) {
    control = document.createElement("input");
    control.type = "text";
    control.value = Array.isArray(value) ? value.join(", ") : "";
    control.placeholder = "Comma-separated values";
  } else if (complex) {
    control = document.createElement("textarea");
    control.value = JSON.stringify(value ?? defaultForField(key, meta), null, 2);
    control.className = "json-field";
  } else {
    control = document.createElement(key === "description" ? "textarea" : "input");
    if (control.tagName === "INPUT") control.type = "text";
    control.value = value ?? "";
  }

  control.id = fieldId;
  control.name = key;
  control.dataset.fieldKey = key;
  control.title = meta.description || "";

  const update = () => {
    if (meta.const !== undefined) return;
    if (primitiveArray) {
      const parts = control.value.split(",").map((part) => part.trim()).filter(Boolean);
      onChange(meta.items.type === "number" ? parts.map(Number) : parts);
      return;
    }
    if (complex) {
      try {
        onChange(JSON.parse(control.value));
        control.setCustomValidity("");
      } catch {
        control.setCustomValidity("Enter valid JSON");
      }
      return;
    }
    onChange(fieldControlValue(control, meta));
  };

  control.addEventListener(meta.type === "boolean" || meta.enum ? "change" : "input", update);
  wrapper.appendChild(control);

  if (meta.description) {
    const description = document.createElement("small");
    description.className = "field-description";
    description.textContent = meta.description;
    wrapper.appendChild(description);
  }
  container.appendChild(wrapper);
  return control;
};

const syncHeaderControls = (payload) => {
  formEl.querySelectorAll("[data-field-key]").forEach((control) => {
    const key = control.dataset.fieldKey;
    const meta = schemaCatalog?.sections?.header?.properties?.[key];
    if (!meta) return;
    const value = payload[key];
    if (meta.type === "boolean") {
      control.checked = Boolean(value);
    } else if (meta.type === "object" || meta.type === "array") {
      control.value = JSON.stringify(value ?? defaultForField(key, meta), null, 2);
    } else {
      control.value = value ?? meta.const ?? "";
    }
  });
};

const buildHeaderForm = (properties) => {
  if (!formEl) return;
  formEl.innerHTML = "";
  const payload = readPayload() || {};
  const required = new Set(schemaCatalog.sections.header.required || []);
  Object.entries(properties).forEach(([key, meta]) => {
    renderField(
      formEl,
      key,
      meta,
      payload[key],
      (value) => {
        const currentPayload = readPayload();
        if (!currentPayload) return;
        setObjectField(currentPayload, key, value, required.has(key));
        inputEl.value = JSON.stringify(currentPayload, null, 2);
        saveDraft();
        refreshGuidedNavigation();
      },
      { required: required.has(key), payload, path: key, id: `field-${key}` }
    );
  });
};

const validateItem = async (section, item, index) => {
  const payload = readPayload();
  if (!payload) return;
  const copy = {
    title: payload.title || "temp",
    description: payload.description || "temp",
    version: payload.version || schemaCatalog.schema_version,
    authors: payload.authors || "temp",
    date: payload.date || "2024-01-01",
    settings: [],
    data_sources: [],
    data_sets: [],
  };
  copy[section] = [item];
  const response = await fetch("/api/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(copy),
  });
  const report = await response.json();
  const itemTitle = item.title || `${section} #${index + 1}`;
  if (report.valid) {
    window.alert(`${itemTitle}: Valid ✅`);
    return;
  }
  const lines = [`${itemTitle}: Invalid ❌`, ""];
  for (const error of report.errors || []) {
    lines.push(`- ${error.path || "<root>"}: ${validationMessage(error)}`);
  }
  window.alert(lines.join("\n"));
};

const validationTarget = (path) => {
  if (!path) return null;
  const parts = path.split("/");
  const candidates = [
    `field-${parts.join("-")}`,
    parts.length >= 3 ? `field-${parts.slice(0, 3).join("-")}` : null,
    parts.length === 1 ? `field-${parts[0]}` : null,
  ].filter(Boolean);
  for (const id of candidates) {
    const target = document.getElementById(id);
    if (target) return target;
  }
  return Array.from(document.querySelectorAll("[data-json-path]"))
    .find((element) => element.dataset.jsonPath === path || path.startsWith(`${element.dataset.jsonPath}/`));
};

const focusValidationTarget = (path) => {
  const target = validationTarget(path);
  if (!target) return;
  const focusable = target.matches?.("input, select, textarea, button")
    ? target
    : target.querySelector("input, select, textarea, button");
  (focusable || target).scrollIntoView({behavior: "smooth", block: "center"});
  focusable?.focus();
};

const renderValidationReport = (report) => {
  outputEl.innerHTML = "";
  if (report.valid) {
    outputEl.textContent = "Valid ✅";
    return;
  }
  const heading = document.createElement("strong");
  heading.textContent = "Invalid ❌";
  outputEl.appendChild(heading);
  const list = document.createElement("ul");
  list.className = "validation-list";
  for (const error of report.errors || []) {
    const item = document.createElement("li");
    const target = validationTarget(error.path);
    const message = `${error.path || "<root>"}: ${validationMessage(error)}`;
    if (target) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "validation-error";
      button.textContent = message;
      button.addEventListener("click", () => focusValidationTarget(error.path));
      item.appendChild(button);
    } else {
      item.textContent = message;
    }
    list.appendChild(item);
  }
  outputEl.appendChild(list);
};

const buildArrayEditor = (container, sectionName) => {
  if (!container || !schemaCatalog) return;
  container.innerHTML = "";
  const section = schemaCatalog.sections[sectionName];
  const actions = document.createElement("div");
  actions.className = "array-actions";

  Object.entries(section.kinds || {}).forEach(([kind, meta]) => {
    if (!isKindVisible(kind)) return;
    const addButton = document.createElement("button");
    addButton.textContent = `Add ${meta.title || kind}`;
    addButton.className = "ghost";
    addButton.type = "button";
    addButton.addEventListener("click", () => appendItem(sectionName, kind));
    actions.appendChild(addButton);
  });
  container.appendChild(actions);

  const list = document.createElement("div");
  list.className = "array-list";
  container.appendChild(list);
  const payload = readPayload();
  if (!payload) return;

  (payload[sectionName] || []).forEach((item, index) => {
    const card = document.createElement("div");
    card.className = "array-item";
    const header = document.createElement("div");
    header.className = "array-item-header";
    header.textContent = `${item.title || item.kind || sectionName} #${index + 1}`;

    const actionsRow = document.createElement("div");
    actionsRow.className = "actions";
    const removeButton = document.createElement("button");
    removeButton.textContent = "Remove";
    removeButton.className = "ghost";
    removeButton.type = "button";
    removeButton.addEventListener("click", () => {
      const currentPayload = readPayload();
      if (!currentPayload) return;
      currentPayload[sectionName].splice(index, 1);
      inputEl.value = JSON.stringify(currentPayload, null, 2);
      syncFormFromJson();
    });
    const validateButton = document.createElement("button");
    validateButton.textContent = "Validate item";
    validateButton.className = "ghost";
    validateButton.type = "button";
    validateButton.addEventListener("click", () => validateItem(sectionName, readPayload()?.[sectionName]?.[index] || item, index));
    actionsRow.appendChild(removeButton);
    actionsRow.appendChild(validateButton);
    header.appendChild(actionsRow);
    card.appendChild(header);

    const form = document.createElement("div");
    form.className = "array-item-form";
    const meta = section.kinds?.[item.kind];
    if (!meta) {
      const unknown = document.createElement("p");
      unknown.className = "muted";
      unknown.textContent = `No schema catalogue entry is available for ${item.kind || "this item"}.`;
      form.appendChild(unknown);
    } else {
      const required = new Set(meta.required || []);
      Object.entries(meta.properties || {}).forEach(([key, propertyMeta]) => {
        renderField(
          form,
          key,
          propertyMeta,
          item[key],
          (value) => {
            const currentPayload = readPayload();
            if (!currentPayload) return;
            const currentItem = currentPayload[sectionName]?.[index];
            if (!currentItem) return;
            setObjectField(currentItem, key, value, required.has(key));
            inputEl.value = JSON.stringify(currentPayload, null, 2);
            saveDraft();
            refreshGuidedNavigation();
          },
          {
            required: required.has(key),
            id: `field-${sectionName}-${index}-${key}`,
            payload: readPayload(),
            refresh: syncFormFromJson,
            path: `${sectionName}/${index}/${key}`,
          }
        );
      });
    }
    card.appendChild(form);
    list.appendChild(card);
  });
};

const syncFormFromJson = () => {
  if (syncing || !schemaCatalog) return;
  syncing = true;
  const payload = readPayload();
  if (payload) {
    syncHeaderControls(payload);
    buildArrayEditor(settingsEl, "settings");
    buildArrayEditor(dataSourcesEl, "data_sources");
    buildArrayEditor(dataSetsEl, "data_sets");
    renderGuidedSteps();
    saveDraft();
  }
  syncing = false;
};

const renderSummary = async () => {
  try {
    const [schemaResponse, uiResponse] = await Promise.all([
      fetch("/api/schema/catalog"),
      fetch("/api/ui"),
    ]);
    if (!schemaResponse.ok || !uiResponse.ok) throw new Error("Unable to load editor metadata");
    schemaCatalog = await schemaResponse.json();
    uiCatalog = await uiResponse.json();
    populateProfiles();
    updateEditorMode();
    const sections = Object.entries(schemaCatalog.sections || {})
      .map(([name, section]) => `${name}: ${Object.keys(section.kinds || {}).length || "header"}`)
      .join(" · ");
    summaryEl.textContent = `Schema catalogue version: ${schemaCatalog.schema_version || "unknown"}\n${sections}`;
    buildHeaderForm(schemaCatalog.sections?.header?.properties || {});
    syncFormFromJson();
  } catch {
    summaryEl.textContent = "Failed to load schema catalogue.";
  }
};

const reset = () => {
  inputEl.value = JSON.stringify(defaultPayload, null, 2);
  outputEl.textContent = "";
  saveDraft();
  syncFormFromJson();
};

const validate = async () => {
  outputEl.textContent = "";
  const payload = readPayload();
  if (!payload) {
    outputEl.textContent = "Parse error: invalid JSON";
    return;
  }

  const response = await fetch("/api/validate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const report = await response.json();
  renderValidationReport(report);
};

const downloadJson = () => {
  if (!readPayload()) {
    outputEl.textContent = "Parse error: invalid JSON";
    return;
  }
  const blob = new Blob([inputEl.value], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "r3xa.json";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
};

const saveWithDialog = async () => {
  if (!readPayload()) {
    outputEl.textContent = "Parse error: invalid JSON";
    return;
  }

  if (window.showSaveFilePicker) {
    try {
      const handle = await window.showSaveFilePicker({
        suggestedName: "r3xa.json",
        types: [{ description: "JSON", accept: { "application/json": [".json"] } }],
      });
      const writable = await handle.createWritable();
      await writable.write(inputEl.value);
      await writable.close();
      return;
    } catch (error) {
      if (error && error.name === "AbortError") return;
    }
  }
  downloadJson();
};

const loadJsonFile = (file) => {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      JSON.parse(reader.result);
    } catch (error) {
      outputEl.textContent = `Parse error: ${error.message}`;
      return;
    }
    inputEl.value = reader.result;
    saveDraft();
    syncFormFromJson();
  };
  reader.readAsText(file);
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

document.getElementById("validate-btn").addEventListener("click", validate);
document.getElementById("reset-btn").addEventListener("click", reset);
document.getElementById("save-json-btn").addEventListener("click", saveWithDialog);
document.getElementById("load-json-input").addEventListener("change", (event) => {
  loadJsonFile(event.target.files?.[0]);
  event.target.value = "";
});
modeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    editorMode = button.dataset.editorMode;
    localStorage.setItem("r3xaEditorMode", editorMode);
    updateEditorMode();
  });
});
if (profileSelectEl) {
  profileSelectEl.addEventListener("change", () => {
    selectedProfile = profileSelectEl.value;
    guidedStepIndex = 0;
    localStorage.setItem("r3xaProfile", selectedProfile);
    localStorage.setItem("r3xaGuidedStep", "0");
    syncFormFromJson();
  });
}
if (guidedPreviousEl) {
  guidedPreviousEl.addEventListener("click", () => {
    guidedStepIndex = Math.max(guidedStepIndex - 1, 0);
    localStorage.setItem("r3xaGuidedStep", String(guidedStepIndex));
    renderGuidedSteps();
  });
}
if (guidedNextEl) {
  guidedNextEl.addEventListener("click", () => {
    const steps = uiCatalog?.profiles?.[selectedProfile]?.steps || [];
    guidedStepIndex = Math.min(guidedStepIndex + 1, Math.max(steps.length - 1, 0));
    localStorage.setItem("r3xaGuidedStep", String(guidedStepIndex));
    renderGuidedSteps();
  });
}
inputEl.addEventListener("input", () => {
  saveDraft();
  syncFormFromJson();
});

ensureServerStart();
updateEditorMode();
inputEl.value = loadDraft();
renderSummary();
