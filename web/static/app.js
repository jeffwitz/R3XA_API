const defaultPayload = {
  title: "",
  description: "",
  version: "",
  authors: [],
  date: "",
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
const guidedPrefillEl = document.getElementById("guided-prefill");
const modeButtons = document.querySelectorAll("[data-editor-mode]");
const launchParams = new URLSearchParams(window.location.search);
const t = (key, fallback, values) => window.R3XAI18N?.t(key, fallback, values) || fallback;

let schemaCatalog = null;
let uiCatalog = null;
let editorMode = localStorage.getItem("r3xaEditorMode") || "guided";
let selectedProfile = launchParams.get("profile") || localStorage.getItem("r3xaProfile") || "generic";
let guidedStepIndex = Number(localStorage.getItem("r3xaGuidedStep")) || 0;
let guidedStepItems = {};
let pendingTemplateReview = new Set();
let syncing = false;
let prefillRequested = launchParams.get("prefill") === "1";
let newDocumentRequested = launchParams.get("new") === "1";

const guidedStepItemsStorageKey = () => `r3xaGuidedStepItems:${selectedProfile}`;

const loadGuidedStepItems = () => {
  try {
    const value = JSON.parse(localStorage.getItem(guidedStepItemsStorageKey()) || "{}");
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
  } catch {
    return {};
  }
};

const saveGuidedStepItems = () => {
  localStorage.setItem(guidedStepItemsStorageKey(), JSON.stringify(guidedStepItems));
};

const pendingTemplateReviewStorageKey = () => `r3xaPendingTemplateReview:${selectedProfile}`;

const loadPendingTemplateReview = () => {
  try {
    const value = JSON.parse(localStorage.getItem(pendingTemplateReviewStorageKey()) || "[]");
    return new Set(Array.isArray(value) ? value : []);
  } catch {
    return new Set();
  }
};

const savePendingTemplateReview = () => {
  localStorage.setItem(pendingTemplateReviewStorageKey(), JSON.stringify([...pendingTemplateReview]));
};

const clearAllTemplateReviews = () => {
  Object.keys(localStorage)
    .filter((key) => key.startsWith("r3xaPendingTemplateReview:"))
    .forEach((key) => localStorage.removeItem(key));
  pendingTemplateReview = new Set();
};

pendingTemplateReview = loadPendingTemplateReview();

const guidedTemplateFieldKey = (step, target, field) => `${step.id}:${target?.id || "header"}:${field}`;

const clearTemplateReviewField = (step, target, field) => {
  const key = guidedTemplateFieldKey(step, target, field);
  pendingTemplateReview.delete(key);
  savePendingTemplateReview();
  document.querySelectorAll("[data-template-review-key]").forEach((control) => {
    if (control.dataset.templateReviewKey === key) control.remove();
  });
};

const templateDefaultFields = (step) => Object.keys(step.defaults || {})
  .filter((field) => !["id", "kind", "version"].includes(field));

const markStepDefaultsForReview = (step, target) => {
  templateDefaultFields(step).forEach((field) => {
    pendingTemplateReview.add(guidedTemplateFieldKey(step, target, field));
  });
  savePendingTemplateReview();
};

const markProfileDefaultsForReview = (profile, payload) => {
  pendingTemplateReview = new Set();
  (profile?.steps || []).forEach((step) => {
    const target = step.section === "header" ? payload : profileStepItem(step, payload);
    if (target) markStepDefaultsForReview(step, target);
  });
  savePendingTemplateReview();
};

const templateReviewComplete = () => pendingTemplateReview.size === 0;

const templateFieldNeedsReview = (step, target, field) =>
  pendingTemplateReview.has(guidedTemplateFieldKey(step, target, field));

const requireTemplateReview = () => {
  if (templateReviewComplete()) return true;
  outputEl.textContent = t("guided.review_before_save", "Review the {count} listed template value(s) in Guided mode before saving.", {count: pendingTemplateReview.size});
  return false;
};

const selectGuidedStepItem = (stepId, itemId) => {
  if (itemId) guidedStepItems[stepId] = itemId;
  else delete guidedStepItems[stepId];
  saveGuidedStepItems();
};

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

const cloneJsonValue = (value) => JSON.parse(JSON.stringify(value));

const fieldLevel = (key) => uiCatalog?.default?.fields?.[key]?.level || "basic";

const isReferenceMeta = (meta) => {
  const reference = meta?.ref || meta?.items?.ref;
  return reference?.endsWith("data_set_id") || reference?.endsWith("data_source_id");
};

const isFieldVisible = (key, required = false, forceVisible = false, meta = null) => {
  const level = fieldLevel(key);
  if (required || forceVisible || isReferenceMeta(meta)) return true;
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
    guided: t("editor.mode_guided_help", "Start from an experience profile. Common fields are shown first."),
    advanced: t("editor.mode_advanced_help", "Edit all user-facing fields while keeping technical identifiers hidden."),
    expert: t("editor.mode_expert_help", "Inspect every field and edit the canonical JSON directly when needed."),
  };
  if (modeHelpEl) {
    modeHelpEl.textContent = editorMode === "guided" && selectedProfile === "generic"
      ? t("editor.generic_help", "This is a free-form schema-driven workflow. Add the settings, data sources, and data sets that describe your experiment; no example values are inserted.")
      : help[editorMode];
  }
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
    option.textContent = t(`profile.${profileId}.title`, profile.title || profileId);
    option.title = t(`profile.${profileId}.description`, profile.description || "");
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

const profileStepItem = (step, payload) => {
  if (!step.kind) return null;
  const candidates = (payload[step.section] || []).filter((item) => item.kind === step.kind);
  const rememberedId = guidedStepItems[step.id];
  if (rememberedId) {
    const remembered = candidates.find((item) => item.id === rememberedId);
    if (remembered) return remembered;
  }
  if (candidates.length !== 1) return null;
  selectGuidedStepItem(step.id, candidates[0].id);
  return candidates[0];
};

const referenceIds = (value) => Array.isArray(value) ? value : value ? [value] : [];

const restoreGuidedStepItems = (profile, payload) => {
  if (!profile || !payload) return;
  const steps = profile.steps || [];
  let changed = false;
  const assign = (step, item) => {
    if (guidedStepItems[step.id] === item.id) return;
    guidedStepItems[step.id] = item.id;
    changed = true;
  };
  const candidatesFor = (step) => (payload[step.section] || [])
    .filter((item) => item.kind === step.kind);

  steps.filter((step) => step.kind).forEach((step) => {
    const candidates = candidatesFor(step);
    const remembered = candidates.find((item) => item.id === guidedStepItems[step.id]);
    if (remembered) return;
    if (candidates.length === 1) assign(step, candidates[0]);
  });

  for (let pass = 0; pass < steps.length; pass += 1) {
    let resolvedOnPass = false;
    steps.filter((step) => step.kind && !guidedStepItems[step.id]).forEach((step) => {
      const matches = candidatesFor(step).filter((candidate) => {
        const inbound = (profile.links || []).some((link) => {
          if (link.to_step !== step.id) return false;
          const sourceId = guidedStepItems[link.from_step];
          return sourceId && referenceIds(candidate[link.to_field]).includes(sourceId);
        });
        const outbound = (profile.links || []).some((link) => {
          if (link.from_step !== step.id) return false;
          const targetStep = steps.find((entry) => entry.id === link.to_step);
          const targetId = targetStep && guidedStepItems[targetStep.id];
          const target = targetStep && candidatesFor(targetStep).find((item) => item.id === targetId);
          return target && referenceIds(target[link.to_field]).includes(candidate.id);
        });
        return inbound || outbound;
      });
      if (matches.length === 1) {
        assign(step, matches[0]);
        resolvedOnPass = true;
      }
    });
    if (!resolvedOnPass) break;
  }

  steps.filter((step) => step.kind && !guidedStepItems[step.id]).forEach((step) => {
    const expectedTitle = step.defaults?.title;
    const matches = expectedTitle
      ? candidatesFor(step).filter((item) => item.title === expectedTitle)
      : [];
    if (matches.length === 1) assign(step, matches[0]);
  });
  if (changed) saveGuidedStepItems();
};

const stepProperties = (step) => step.section === "header"
  ? schemaCatalog?.sections?.header?.properties || {}
  : schemaCatalog?.sections?.[step.section]?.kinds?.[step.kind]?.properties || {};

const applyStepDefaults = (step, target, payload) => {
  Object.entries(step.defaults || {}).forEach(([key, value]) => {
    target[key] = cloneJsonValue(value);
  });
  Object.entries(stepProperties(step)).forEach(([key, meta]) => {
    const isGuidedQuestion = (step.questions || []).some((question) => question.field === key);
    if (!isGuidedQuestion || Object.prototype.hasOwnProperty.call(target, key)) return;
    target[key] = defaultForField(key, meta, payload, step.kind);
  });
};

const applyProfileLinks = (profile, payload, options = {}) => {
  const updates = new Map();
  (profile?.links || []).forEach((link) => {
    const fromStep = profile.steps?.find((step) => step.id === link.from_step);
    const toStep = profile.steps?.find((step) => step.id === link.to_step);
    if (!fromStep || !toStep || !fromStep.kind || !toStep.kind) return;
    const fromItem = profileStepItem(fromStep, payload);
    const toItem = profileStepItem(toStep, payload);
    if (!fromItem?.id || !toItem || !link.to_field) return;
    const fields = updates.get(toItem) || new Map();
    const update = fields.get(link.to_field) || {ids: [], many: false};
    update.ids.push(fromItem.id);
    update.many = update.many || link.to_many !== false || Array.isArray(toItem[link.to_field]);
    fields.set(link.to_field, update);
    updates.set(toItem, fields);
  });
  updates.forEach((fields, item) => {
    fields.forEach((update, field) => {
      const ids = [...new Set(update.ids)];
      if (!options.overwrite && Object.prototype.hasOwnProperty.call(item, field)) return;
      item[field] = update.many ? ids : ids[0];
    });
  });
};

const guidedFieldPath = (step, payload, target, field) => {
  if (step.section === "header") return field;
  const index = (payload[step.section] || []).findIndex((item) => item === target);
  return `${step.section}/${Math.max(index, 0)}/${field}`;
};

const appendGuidedItem = (step, selectedKind = step.kind) => {
  const payload = readPayload();
  const meta = schemaCatalog?.sections?.[step.section]?.kinds?.[selectedKind];
  const profile = uiCatalog?.profiles?.[selectedProfile];
  if (!payload || !meta || !profile) return;
  payload[step.section] = payload[step.section] || [];
  const item = createItem(selectedKind, meta, payload);
  applyStepDefaults(step, item, payload);
  payload[step.section].push(item);
  selectGuidedStepItem(step.id, item.id);
  markStepDefaultsForReview(step, item);
  applyProfileLinks(profile, payload);
  inputEl.value = JSON.stringify(payload, null, 2);
  saveDraft();
  syncFormFromJson();
};

const profileHasPrefilledWorkflow = (profile) => Boolean(
  profile?.steps?.some((step) => step.kind) && profile?.steps?.some(
    (step) => Object.keys(step.defaults || {}).length > 0,
  ),
);

const createPrefilledWorkflow = () => {
  const profile = uiCatalog?.profiles?.[selectedProfile];
  if (!profile || !profileHasPrefilledWorkflow(profile)) return;
  const current = readPayload();
  const hasItems = ["settings", "data_sources", "data_sets"].some((section) => current?.[section]?.length);
  if (hasItems && !window.confirm(t("guided.replace_prefilled", "Replace the current document with the prefilled workflow?"))) return;

  const payload = cloneJsonValue(defaultPayload);
  guidedStepItems = {};
  clearAllTemplateReviews();
  profile.steps.forEach((step) => {
    if (step.section === "header") {
      applyStepDefaults(step, payload, payload);
      return;
    }
    if (!step.kind) return;
    const meta = schemaCatalog?.sections?.[step.section]?.kinds?.[step.kind];
    if (!meta) return;
    const item = createItem(step.kind, meta, payload);
    applyStepDefaults(step, item, payload);
    payload[step.section] = payload[step.section] || [];
    payload[step.section].push(item);
    selectGuidedStepItem(step.id, item.id);
  });
  payload.version = schemaCatalog?.schema_version || payload.version;
  applyProfileLinks(profile, payload, {overwrite: true});
  markProfileDefaultsForReview(profile, payload);
  guidedStepIndex = 0;
  localStorage.setItem("r3xaGuidedStep", "0");
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
  const item = profileStepItem(step, payload);
  return Boolean(meta && item && itemIsComplete(item, meta));
};

const stepCanAdvance = (step, payload) => {
  if (!step) return false;
  const target = step.section === "header"
    ? payload
    : step.kind
      ? profileStepItem(step, payload)
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

const appendTemplateReviewControl = (rendered, step, target, field) => {
  if (!templateFieldNeedsReview(step, target, field)) return;
  const wrapper = rendered?.classList?.contains("form-row")
    ? rendered
    : rendered?.closest?.(".form-row");
  if (!wrapper) return;
  const key = guidedTemplateFieldKey(step, target, field);
  const acknowledgement = document.createElement("label");
  acknowledgement.className = "template-review-control";
  acknowledgement.dataset.templateReviewKey = key;
  const checkbox = document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.addEventListener("change", () => {
    if (checkbox.checked) clearTemplateReviewField(step, target, field);
  });
  const text = document.createElement("span");
  text.textContent = t("guided.confirm_template", "I confirm this value for this experiment.");
  acknowledgement.append(checkbox, text);
  wrapper.appendChild(acknowledgement);
};

const renderGuidedCollectionItems = (step, payload, container) => {
  const items = payload[step.section] || [];
  if (!items.length) {
    const help = document.createElement("small");
    help.className = "field-description";
    help.textContent = t("guided.add_object_help", "Add an object above to start describing this part of the experiment.");
    container.appendChild(help);
    return;
  }
  items.forEach((item, itemIndex) => {
    const meta = schemaCatalog.sections[step.section]?.kinds?.[item.kind];
    const card = document.createElement("div");
    card.className = "array-item";
    const heading = document.createElement("strong");
    heading.textContent = `${item.title || item.kind || t("guided.object", "Object")} #${itemIndex + 1}`;
    card.appendChild(heading);
    if (!meta) {
      const missing = document.createElement("small");
      missing.className = "field-description";
      missing.textContent = t("guided.unknown_object", "No schema catalogue entry is available for {object}.", {object: item.kind || t("guided.object", "this object")});
      card.appendChild(missing);
      container.appendChild(card);
      return;
    }
    Object.entries(meta.properties || {}).forEach(([key, propertyMeta]) => {
      if (["id", "kind"].includes(key)) return;
      renderField(
        card,
        key,
        propertyMeta,
        item[key],
        (value) => {
          const currentPayload = readPayload();
          const currentItem = currentPayload?.[step.section]?.[itemIndex];
          if (!currentItem) return;
          setObjectField(currentItem, key, value, (meta.required || []).includes(key));
          inputEl.value = JSON.stringify(currentPayload, null, 2);
          saveDraft();
          refreshGuidedNavigation();
        },
        {
          required: (meta.required || []).includes(key),
          forceVisible: true,
          payload,
          refresh: syncFormFromJson,
          id: `guided-${step.id}-${itemIndex}-${key}`,
          path: `${step.section}/${itemIndex}/${key}`,
        }
      );
    });
    container.appendChild(card);
  });
};

const renderGuidedQuestions = (step, payload, container) => {
  const questionFields = new Set();
  (step.questions || []).forEach((question) => {
    if (!conditionMatches(question.when, payload)) return;
    const target = step.section === "header" ? payload : profileStepItem(step, payload);
    if (!target || !question.field) return;
    questionFields.add(question.field);
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
    const rendered = renderField(
      container,
      question.field,
      meta,
      target[question.field],
      (value) => {
        const currentPayload = readPayload();
        if (!currentPayload) return;
        const currentTarget = step.section === "header" ? currentPayload : profileStepItem(step, currentPayload);
        if (!currentTarget) return;
        setObjectField(currentTarget, question.field, value, required);
        clearTemplateReviewField(step, currentTarget, question.field);
        inputEl.value = JSON.stringify(currentPayload, null, 2);
        saveDraft();
        refreshGuidedNavigation();
      },
      {
        required,
        forceVisible: true,
        payload,
        refresh: syncFormFromJson,
        id: `guided-${step.id}-${question.field}`,
        path: guidedFieldPath(step, payload, target, question.field),
      }
    );
    appendTemplateReviewControl(rendered, step, target, question.field);
  });
  if (!step.kind) {
    renderGuidedCollectionItems(step, payload, container);
    return;
  }
  const target = step.section === "header" ? payload : profileStepItem(step, payload);
  const properties = step.section === "header"
    ? schemaCatalog.sections.header.properties
    : schemaCatalog.sections[step.section]?.kinds?.[step.kind]?.properties;
  if (!target || !properties) return;
  const relationshipEntries = Object.entries(properties).filter(([, meta]) => isReferenceMeta(meta));
  if (relationshipEntries.length) {
    const heading = document.createElement("strong");
    heading.className = "relationship-heading";
    heading.textContent = t("guided.relationships", "Optional relationships (pre-filled when possible)");
    container.appendChild(heading);
    const help = document.createElement("small");
    help.className = "field-description relationship-help";
    help.textContent = t("guided.relationship_help", "Select existing data sources or data sets. Leave empty when there is no dependency.");
    container.appendChild(help);
  }
  relationshipEntries.forEach(([key, meta]) => {
    if (questionFields.has(key) || !isReferenceMeta(meta)) return;
    const rendered = renderField(
      container,
      key,
      meta,
      target[key],
      (value) => {
        const currentPayload = readPayload();
        if (!currentPayload) return;
        const currentTarget = step.section === "header" ? currentPayload : profileStepItem(step, currentPayload);
        if (!currentTarget) return;
        setObjectField(currentTarget, key, value, false);
        clearTemplateReviewField(step, currentTarget, key);
        inputEl.value = JSON.stringify(currentPayload, null, 2);
        saveDraft();
        refreshGuidedNavigation();
      },
      {
        required: false,
        forceVisible: true,
        payload,
        refresh: syncFormFromJson,
        id: `guided-${step.id}-${key}`,
        path: guidedFieldPath(step, payload, target, key),
      }
    );
    appendTemplateReviewControl(rendered, step, target, key);
  });

  const templateFields = Object.keys(step.defaults || {}).filter((key) =>
    !questionFields.has(key)
    && !["id", "kind", "version"].includes(key)
    && properties[key]
    && !isReferenceMeta(properties[key])
  );
  if (templateFields.length) {
    const heading = document.createElement("strong");
    heading.className = "template-review-heading";
    heading.textContent = t("guided.template_values", "Additional template values (review before saving)");
    container.appendChild(heading);
    const help = document.createElement("small");
    help.className = "field-description template-review-help";
    help.textContent = t("guided.template_help", "These values come from the example profile. Check that paths, files, dimensions, and experimental parameters match your experiment.");
    container.appendChild(help);
    templateFields.forEach((key) => {
      const rendered = renderField(
        container,
        key,
        properties[key],
        target[key],
        (value) => {
          const currentPayload = readPayload();
          if (!currentPayload) return;
          const currentTarget = step.section === "header" ? currentPayload : profileStepItem(step, currentPayload);
          if (!currentTarget) return;
          setObjectField(currentTarget, key, value, false);
          clearTemplateReviewField(step, currentTarget, key);
          inputEl.value = JSON.stringify(currentPayload, null, 2);
          saveDraft();
          refreshGuidedNavigation();
        },
        {
          required: false,
          forceVisible: true,
          payload,
          refresh: syncFormFromJson,
          id: `guided-${step.id}-template-${key}`,
          path: guidedFieldPath(step, payload, target, key),
        }
      );
      appendTemplateReviewControl(rendered, step, target, key);
    });
  }
};

const renderGuidedSteps = () => {
  if (!guidedStepsEl || !uiCatalog || !schemaCatalog) return;
  const profile = uiCatalog.profiles?.[selectedProfile];
  const steps = profile?.steps || [];
  if (guidedPrefillEl) guidedPrefillEl.hidden = !profileHasPrefilledWorkflow(profile);
  guidedStepIndex = Math.min(Math.max(guidedStepIndex, 0), Math.max(steps.length - 1, 0));
  guidedStepsEl.innerHTML = "";
  guidedStepsEl.className = "guided-steps";
  const payload = readPayload() || {};
  if (guidedProgressEl) guidedProgressEl.textContent = steps.length ? t("guided.step_progress", "Step {current} of {total}", {current: guidedStepIndex + 1, total: steps.length}) : "";
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
    if (step.kind) {
      const candidates = (payload[step.section] || []).filter((item) => item.kind === step.kind);
      if (candidates.length) {
        const picker = document.createElement("select");
        picker.className = "guided-item-picker";
        picker.setAttribute("aria-label", `Select ${step.title || step.id}`);
        const activeItem = profileStepItem(step, payload);
        if (!activeItem) {
          const help = document.createElement("small");
          help.className = "guided-role-help";
          help.textContent = t("guided.choose_role", "Several items match this kind. Choose the item that represents {step}.", {step: step.title || step.id});
          block.appendChild(help);
          const placeholder = document.createElement("option");
          placeholder.value = "";
          placeholder.textContent = t("guided.choose_existing", "Choose an existing item…");
          picker.appendChild(placeholder);
        }
        candidates.forEach((item) => {
          const option = document.createElement("option");
          option.value = item.id;
          option.textContent = item.title || item.id;
          option.selected = item.id === activeItem?.id;
          picker.appendChild(option);
        });
        picker.addEventListener("click", (event) => event.stopPropagation());
        picker.addEventListener("change", (event) => {
          event.stopPropagation();
          selectGuidedStepItem(step.id, picker.value);
          renderGuidedSteps();
        });
        row.appendChild(picker);
      }
    }
    const candidates = step.kind
      ? (payload[step.section] || []).filter((item) => item.kind === step.kind)
      : [];
    if (step.section !== "header" && !complete && !candidates.length) {
      const kinds = step.kind
        ? [[step.kind, schemaCatalog.sections[step.section].kinds[step.kind]]]
        : Object.entries(schemaCatalog.sections[step.section]?.kinds || {});
      kinds.forEach(([kind, meta]) => {
        const addButton = document.createElement("button");
        addButton.type = "button";
        addButton.className = "ghost";
        addButton.textContent = t("guided.add", "Add {item}", {item: meta.title || kind});
        addButton.addEventListener("click", (event) => event.stopPropagation());
        addButton.addEventListener("click", () => appendGuidedItem(step, kind));
        row.appendChild(addButton);
      });
    }
    loadLocalRegistryItems()
      .filter((item) => registrySectionForKind(item.kind) === step.section)
      .filter((item) => !step.kind || item.kind === step.kind)
      .forEach((item) => {
        const addButton = document.createElement("button");
        addButton.type = "button";
        addButton.className = "ghost local-registry-add";
        addButton.textContent = t("guided.add_local", "Use local {item}", {item: item.title || item.kind});
        addButton.addEventListener("click", (event) => event.stopPropagation());
        addButton.addEventListener("click", () => appendLocalRegistryItem(step.section, item, step));
        row.appendChild(addButton);
      });
    const incomingLinks = (profile.links || []).filter((link) => link.to_step === step.id);
    if (incomingLinks.length) {
      const dependency = document.createElement("small");
      dependency.className = "guided-dependency";
      dependency.textContent = t("guided.uses", "Uses: {items}", {items: incomingLinks.map((link) => {
        const sourceStep = steps.find((candidate) => candidate.id === link.from_step);
        return sourceStep?.title || link.from_step;
      }).join(", ")});
      block.appendChild(dependency);
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
  if (guidedProgressEl) guidedProgressEl.textContent = steps.length ? t("guided.step_progress", "Step {current} of {total}", {current: guidedStepIndex + 1, total: steps.length}) : "";
  guidedStepsEl?.querySelectorAll(".guided-step").forEach((row, index) => {
    const complete = stepIsComplete(steps[index], payload);
    row.classList.toggle("is-complete", complete);
    row.classList.toggle("is-current", index === guidedStepIndex);
    const label = row.querySelector(".guided-step-label");
    if (label) label.textContent = `${complete ? "✓" : "○"} ${steps[index].title || steps[index].id}`;
  });
};

const {
  hasCanonicalId,
  makeId,
  normalizeDocumentIds,
  prefixForKind: idPrefixForKind,
  relationshipFields,
} = window.R3XAIdUtils;

const loadLocalRegistryItems = () => {
  const stored = window.R3XARegistryStorage.read();
  if (stored.corrupt) {
    outputEl.textContent = stored.error;
    return [];
  }
  const normalized = window.R3XAIdUtils.normalizeLocalRegistryItems(
    stored.items.filter((item) => item && typeof item === "object" && item.kind),
  );
  if (normalized.conflicts.length) {
    outputEl.textContent = t(
      "registry.duplicate_ids",
      "Local Registry migration was not applied because these IDs are duplicated: {ids}. Export or edit the affected items before continuing.",
      {ids: normalized.conflicts.join(", ")},
    );
    return normalized.items;
  }
  if (stored.migrated || normalized.changed) {
    window.R3XARegistryStorage.write(normalized.items, schemaCatalog?.schema_version);
  }
  return normalized.items;
};

const registrySectionForKind = (kind) => kind?.split("/", 1)[0] || "";

const cloneLocalRegistryClosure = (rootItem, payload) => {
  const localItems = loadLocalRegistryItems();
  const localById = new Map();
  const ambiguousLocalIds = new Set();
  localItems.forEach((item) => {
    if (!item.id) return;
    if (localById.has(item.id)) ambiguousLocalIds.add(item.id);
    else localById.set(item.id, item);
  });

  const existingDocumentIds = new Set([
    ...(payload.settings || []),
    ...(payload.data_sources || []),
    ...(payload.data_sets || []),
  ].map((item) => item.id).filter(Boolean));
  const state = new Map();
  const ordered = [];
  const missing = new Set();
  const cycles = new Set();

  const visit = (item) => {
    if (!item?.id) {
      missing.add("<item without id>");
      return;
    }
    if (ambiguousLocalIds.has(item.id)) {
      missing.add(`${item.id} (ambiguous local dependency)`);
      return;
    }
    if (state.get(item.id) === "visiting") {
      cycles.add(item.id);
      return;
    }
    if (state.get(item.id) === "visited") return;
    state.set(item.id, "visiting");
    relationshipFields.forEach((field) => {
      (item[field] || []).forEach((reference) => {
        const dependency = localById.get(reference);
        if (dependency) visit(dependency);
        else if (!existingDocumentIds.has(reference)) missing.add(reference);
      });
    });
    state.set(item.id, "visited");
    ordered.push(item);
  };

  visit(rootItem);
  if (missing.size || cycles.size) {
    const details = [
      missing.size ? `missing: ${[...missing].join(", ")}` : "",
      cycles.size ? `cycle: ${[...cycles].join(", ")}` : "",
    ].filter(Boolean).join("; ");
    return {error: details, items: [], rootId: null};
  }

  const used = new Set([
    ...(payload.settings || []),
    ...(payload.data_sources || []),
    ...(payload.data_sets || []),
  ].map((item) => item.id).filter(Boolean));
  const replacements = new Map();
  ordered.forEach((item) => replacements.set(item.id, makeId(item.kind, used)));
  const clones = ordered.map((item) => {
    const clone = cloneJsonValue(item);
    clone.id = replacements.get(item.id);
    relationshipFields.forEach((field) => {
      if (Array.isArray(clone[field])) {
        clone[field] = clone[field].map((reference) => replacements.get(reference) || reference);
      }
    });
    return clone;
  });
  return {error: "", items: clones, rootId: replacements.get(rootItem.id)};
};

const appendLocalRegistryItem = (sectionName, item, step = null) => {
  const payload = readPayload();
  if (!payload || registrySectionForKind(item.kind) !== sectionName) return;
  const closure = cloneLocalRegistryClosure(item, payload);
  if (closure.error) {
    outputEl.textContent = t(
      "guided.local_dependency_error",
      "Cannot use local Registry item: {details}",
      {details: closure.error},
    );
    return;
  }
  if (closure.items.length > 1 && !window.confirm(t(
    "guided.local_dependency_preview",
    "This local template will add {count} objects, including its dependencies. Continue?",
    {count: closure.items.length},
  ))) return;
  closure.items.forEach((clone) => {
    const section = registrySectionForKind(clone.kind);
    payload[section] = payload[section] || [];
    payload[section].push(clone);
  });
  if (step) selectGuidedStepItem(step.id, closure.rootId);
  const profile = uiCatalog?.profiles?.[selectedProfile];
  if (step && profile) applyProfileLinks(profile, payload);
  inputEl.value = JSON.stringify(payload, null, 2);
  saveDraft();
  syncFormFromJson();
};

const defaultForField = (key, meta, payload, kind = "") => {
  if (meta.const !== undefined) return meta.const;
  if (meta.default !== undefined) return meta.default;

  if (key === "id") return makeId(kind);
  if (key === "title" || key === "description") return "";
  if (key === "file_type" || key === "path" || key === "folder" || key === "filename") return "";
  if (key === "output_components") return undefined;
  if (key === "output_dimension") {
    return meta.enum?.includes("surface") ? "surface" : meta.enum?.[0] || "";
  }
  if (key === "parent_data_sources" || key === "attached_data_sources") {
    const sourceId = payload?.data_sources?.[0]?.id;
    return sourceId ? [sourceId] : [];
  }
  if (key === "input_data_sets") {
    const dataSetId = payload?.data_sets?.[0]?.id;
    return dataSetId ? [dataSetId] : [];
  }

  if (meta.type === "string") return "";
  if (meta.type === "number" || meta.type === "integer") return undefined;
  if (meta.type === "boolean") return false;
  if (meta.type === "array") return [];
  if (meta.type === "object") {
    const object = {};
    Object.entries(meta.properties || {}).forEach(([propertyKey, propertyMeta]) => {
      const propertyRequired = (meta.required || []).includes(propertyKey);
      if (propertyRequired || propertyMeta.const !== undefined) {
        object[propertyKey] = defaultForField(propertyKey, propertyMeta, payload, kind);
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
      item[key] = makeId(kind);
      return;
    }
    if (key === "kind") {
      item[key] = propertyMeta.const || kind;
      return;
    }
    if (required.has(key)) {
      item[key] = defaultForField(key, propertyMeta, payload, kind);
    }
  });
  return item;
};

const fieldTypes = (meta) => {
  const declared = Array.isArray(meta?.type) ? meta.type : [meta?.type];
  const alternatives = [...(meta?.oneOf || []), ...(meta?.anyOf || [])]
    .flatMap((option) => Array.isArray(option.type) ? option.type : [option.type]);
  return new Set([...declared, ...alternatives].filter(Boolean));
};

const fieldControlValue = (control, meta) => {
  const types = fieldTypes(meta);
  if (types.has("boolean") && types.size === 1) return control.checked;
  if ((types.has("number") || types.has("integer")) && types.size === 1) {
    return control.value === "" ? undefined : Number(control.value);
  }
  if (types.has("integer") && /^[-+]?\d+$/.test(control.value.trim())) {
    return Number(control.value);
  }
  if (types.has("number") && control.value !== "" && Number.isFinite(Number(control.value))) {
    return Number(control.value);
  }
  return control.value;
};

const primitiveValue = (value, meta) => {
  const types = fieldTypes(meta);
  if (value === "null" && types.has("null")) return null;
  if (types.has("integer") && /^[-+]?\d+$/.test(value)) return Number(value);
  if (types.has("number") && value !== "" && Number.isFinite(Number(value))) return Number(value);
  return value;
};

const isUnitMeta = (meta) => meta?.ref === "#/$defs/types/unit";

const referenceSection = (meta, options) => {
  if (options.referenceSection) return options.referenceSection;
  const reference = meta?.ref || meta?.items?.ref;
  if (reference?.endsWith("data_set_id")) return "data_sets";
  if (reference?.endsWith("data_source_id")) return "data_sources";
  return null;
};

const renderReferenceField = (container, key, meta, value, onChange, options) => {
  const wrapper = document.createElement("div");
  wrapper.className = "form-row";
  wrapper.dataset.fieldLevel = fieldLevel(key);
  if (options.path) wrapper.dataset.jsonPath = options.path;
  if (options.id) wrapper.id = options.id;
  const label = document.createElement("label");
  const labels = {
    parent_data_sources: t("field.parent_data_sources", "Parent data sources"),
    input_data_sets: t("field.input_data_sets", "Input data sets"),
    attached_data_sources: t("field.attached_data_sources", "Attached data sources"),
  };
  label.textContent = `${labels[key] || meta.title || key}${options.required ? " *" : ""}`;
  const fieldId = options.id || `field-${key}`;
  label.setAttribute("for", fieldId);
  wrapper.appendChild(label);

  const section = referenceSection(meta, options);
  const known = options.payload?.[section] || [];
  const currentIds = Array.isArray(value) ? value : value ? [value] : [];
  const choices = new Map(known.map((item) => [item.id, item.title || item.kind || item.id]));
  currentIds.forEach((id) => {
    if (!choices.has(id)) choices.set(id, `${id} (not loaded)`);
  });
  if (meta.type === "array") {
    const selectedIds = new Set(currentIds);
    const checklist = document.createElement("div");
    checklist.id = fieldId;
    checklist.className = "reference-checklist";
    checklist.setAttribute("role", "group");
    checklist.setAttribute("aria-label", label.textContent);
    if (!choices.size) {
      const empty = document.createElement("small");
      empty.className = "field-description";
      empty.textContent = t("field.no_compatible_objects", "No compatible objects have been created yet.");
      checklist.appendChild(empty);
    }
    choices.forEach((title, id) => {
      if (!id) return;
      const option = document.createElement("label");
      option.className = "reference-option";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = selectedIds.has(id);
      checkbox.addEventListener("change", () => {
        if (checkbox.checked) selectedIds.add(id);
        else selectedIds.delete(id);
        onChange([...selectedIds]);
      });
      const text = document.createElement("span");
      text.textContent = title;
      option.append(checkbox, text);
      checklist.appendChild(option);
    });
    wrapper.appendChild(checklist);
    if (currentIds.length) {
      const clearButton = document.createElement("button");
      clearButton.type = "button";
      clearButton.className = "ghost reference-clear";
      clearButton.textContent = t("field.clear_selection", "Clear selection");
      clearButton.addEventListener("click", () => {
        selectedIds.clear();
        checklist.querySelectorAll("input[type=checkbox]").forEach((checkbox) => {
          checkbox.checked = false;
        });
        onChange([]);
      });
      wrapper.appendChild(clearButton);
    }
  } else {
    const control = document.createElement("select");
    control.id = fieldId;
    control.name = key;
    if (!currentIds.length) {
      const blank = document.createElement("option");
      blank.value = "";
      blank.textContent = t("field.select_object", "Select an object…");
      control.appendChild(blank);
    }
    choices.forEach((title, id) => {
      if (!id) return;
      const option = document.createElement("option");
      option.value = id;
      option.textContent = title;
      option.selected = currentIds.includes(id);
      control.appendChild(option);
    });
    control.addEventListener("change", () => onChange(control.value));
    wrapper.appendChild(control);
  }
  const help = document.createElement("small");
  help.className = "field-description";
  help.textContent = meta.type === "array"
    ? t("field.optional_upstream", "Optional: check every upstream object this item depends on. Selections are preserved.")
    : t("field.optional_reference", "Optional: select an existing item from this document.");
  wrapper.appendChild(help);
  if (meta.description) {
    const description = document.createElement("small");
    description.className = "field-description";
    description.textContent = meta.description;
    wrapper.appendChild(description);
  }
  container.appendChild(wrapper);
  return wrapper;
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
    removeButton.textContent = t("field.remove", "Remove");
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
  addButton.textContent = t("field.add_unit", "Add unit");
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
    const itemMeta = meta.items || {};
    const itemProperties = itemMeta.properties || {};
    const required = new Set(itemMeta.required || []);
    let itemValue = item && typeof item === "object" ? {...item} : {};
    Object.entries(itemProperties).forEach(([field, fieldMeta]) => {
      renderField(
        row,
        field,
        fieldMeta,
        itemValue[field],
        (nextValue) => {
          const nextItem = {...itemValue};
          setObjectField(nextItem, field, nextValue, required.has(field));
          itemValue = nextItem;
          values[index] = nextItem;
          onChange([...values]);
        },
        {
          required: required.has(field),
          forceVisible: true,
          payload: options.payload,
          refresh: options.refresh,
          id: `${options.id || key}-${index}-${field}`,
          path: options.path ? `${options.path}/${index}/${field}` : null,
        }
      );
    });
    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.className = "ghost";
    removeButton.textContent = t("field.remove", "Remove");
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
  addButton.textContent = t("field.add_object", "Add object");
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

const renderDataSetFileField = (container, key, meta, value, onChange, options) => {
  const wrapper = document.createElement("div");
  wrapper.className = "form-row data-set-file-field";
  wrapper.dataset.fieldLevel = fieldLevel(key);
  if (options.path) wrapper.dataset.jsonPath = options.path;
  if (options.id) wrapper.id = options.id;
  const heading = document.createElement("strong");
  heading.textContent = `${meta.title || key}${options.required ? " *" : ""}`;
  wrapper.appendChild(heading);
  let fileValue = {...(value || {})};
  Object.entries(meta.properties || {}).forEach(([part, partMeta]) => {
    if (part === "kind") return;
    renderField(
      wrapper,
      part,
      partMeta,
      fileValue[part],
      (nextValue) => {
        const next = {...fileValue, kind: fileValue.kind || "data_set_file"};
        setObjectField(next, part, nextValue, (meta.required || []).includes(part));
        fileValue = next;
        onChange(next);
      },
      {
        required: (meta.required || []).includes(part),
        forceVisible: true,
        payload: options.payload,
        refresh: options.refresh,
        id: `${options.id || key}-${part}`,
        path: options.path ? `${options.path}/${part}` : null,
      }
    );
  });
  if (meta.description) {
    const description = document.createElement("small");
    description.className = "field-description";
    description.textContent = meta.description;
    wrapper.appendChild(description);
  }
  container.appendChild(wrapper);
  return wrapper;
};

const naturalFileOrder = (left, right) => left.localeCompare(right, undefined, {
  numeric: true,
  sensitivity: "base",
});

const renderDataSetListField = (container, key, meta, value, onChange, options) => {
  const wrapper = document.createElement("div");
  wrapper.className = "form-row data-set-list-field";
  wrapper.dataset.fieldLevel = fieldLevel(key);
  if (options.path) wrapper.dataset.jsonPath = options.path;
  if (options.id) wrapper.id = options.id;
  const label = document.createElement("label");
  label.textContent = `${meta.title || key}${options.required ? " *" : ""}`;
  wrapper.appendChild(label);
  const picker = document.createElement("input");
  picker.type = "file";
  picker.multiple = true;
  picker.setAttribute("webkitdirectory", "");
  picker.setAttribute("directory", "");
  picker.addEventListener("change", () => {
    const selected = Array.from(picker.files || []).map((file) => file.webkitRelativePath || file.name);
    const root = selected[0]?.split("/")[0];
    const paths = selected
      .map((path) => root && selected.every((entry) => entry.startsWith(`${root}/`)) ? path.slice(root.length + 1) : path)
      .sort(naturalFileOrder);
    onChange(paths);
    options.refresh?.();
  });
  wrapper.appendChild(picker);
  const summary = document.createElement("small");
  summary.className = "field-description";
  const count = Array.isArray(value) ? value.length : 0;
  summary.textContent = count
    ? t("files.replace_list", "{count} file(s) listed. Select the data folder again to replace the list.", {count})
    : t("files.select_folder", "Select the folder containing the image or measurement files. Files are sorted naturally.");
  wrapper.appendChild(summary);
  if (Array.isArray(value) && value.length) {
    const preview = document.createElement("small");
    preview.className = "field-description data-set-list-preview";
    const visible = value.slice(0, 5);
    preview.textContent = `${visible.join(", ")}${value.length > visible.length ? t("files.more", ", and {count} more", {count: value.length - visible.length}) : ""}`;
    wrapper.appendChild(preview);
  }
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
  if (!isFieldVisible(key, options.required, options.forceVisible, meta)) return null;
  if (isUnitMeta(meta)) return renderUnitField(container, key, meta, value, onChange, options);
  if (meta.ref?.endsWith("data_set_file")) {
    return renderDataSetFileField(container, key, meta, value, onChange, options);
  }
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
  if (key === "values" && meta.type === "array" && meta.items?.type === "string" && options.path?.startsWith("data_sets/")) {
    return renderDataSetListField(container, key, meta, value, onChange, options);
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
    blank.textContent = t("field.select", "Select…");
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
    control.placeholder = t("field.comma_separated", "Comma-separated values");
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
      onChange(parts.map((part) => primitiveValue(part, meta.items || {})));
      return;
    }
    if (complex) {
      try {
        onChange(JSON.parse(control.value));
        control.setCustomValidity("");
      } catch {
        control.setCustomValidity(t("field.invalid_json", "Enter valid JSON"));
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
      {
        required: required.has(key),
        payload,
        path: key,
        id: `field-${key}`,
        refresh: () => buildHeaderForm(properties),
      }
    );
  });
};

const validateItem = async (section, item, index) => {
  const itemTitle = item.title || `${section} #${index + 1}`;
  try {
    const response = await window.R3XARuntime.validateItem(item, item.kind || "");
    if (!response.ok) throw new Error(`Validation request failed (${response.status})`);
    const report = await response.json();
    if (report.valid) {
      outputEl.textContent = `${itemTitle}: ${t("validation.valid", "Valid ✅")}`;
      return;
    }
    const lines = [`${itemTitle}: Invalid ❌`, ""];
    for (const error of report.errors || []) {
      lines.push(`- ${error.path || "<root>"}: ${validationMessage(error)}`);
    }
    outputEl.textContent = lines.join("\n");
  } catch (error) {
    outputEl.textContent = t("validation.unavailable", "Validation unavailable: {message}", {message: error.message});
  }
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
    outputEl.textContent = t("validation.valid", "Valid ✅");
    return;
  }
  const heading = document.createElement("strong");
  heading.textContent = t("validation.invalid", "Invalid ❌");
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
    addButton.textContent = t("guided.add", "Add {item}", {item: meta.title || kind});
    addButton.className = "ghost";
    addButton.type = "button";
    addButton.addEventListener("click", () => appendItem(sectionName, kind));
    actions.appendChild(addButton);
  });
  const localItems = loadLocalRegistryItems().filter((item) => registrySectionForKind(item.kind) === sectionName);
  if (localItems.length) {
    const localHeading = document.createElement("small");
    localHeading.className = "field-description local-registry-heading";
    localHeading.textContent = "Local registry templates (this browser)";
    actions.appendChild(localHeading);
    localItems.forEach((item) => {
      const addButton = document.createElement("button");
      addButton.textContent = `Use ${item.title || item.kind}`;
      addButton.className = "ghost local-registry-add";
      addButton.type = "button";
      addButton.addEventListener("click", () => appendLocalRegistryItem(sectionName, item));
      actions.appendChild(addButton);
    });
  }
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
    removeButton.textContent = t("field.remove", "Remove");
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
    validateButton.textContent = t("registry.validate", "Validate item");
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
      unknown.textContent = t("guided.unknown_object", "No schema catalogue entry is available for {object}.", {object: item.kind || t("guided.object", "this item")});
      form.appendChild(unknown);
    } else {
      const required = new Set(meta.required || []);
      const renderItemField = (key, propertyMeta, target = form) => {
        renderField(
          target,
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
      };
      const entries = Object.entries(meta.properties || {});
      const relationshipEntries = entries.filter(([, propertyMeta]) => isReferenceMeta(propertyMeta));
      if (relationshipEntries.length) {
        const relationshipPanel = document.createElement("div");
        relationshipPanel.className = "relationship-panel";
        const heading = document.createElement("strong");
        heading.textContent = t("guided.relationships", "Optional relationships (pre-filled when possible)");
        relationshipPanel.appendChild(heading);
        const help = document.createElement("small");
        help.className = "field-description";
        help.textContent = t("guided.relationship_help", "Select existing data sources or data sets. Leave empty when there is no dependency.");
        relationshipPanel.appendChild(help);
        relationshipEntries.forEach(([key, propertyMeta]) => renderItemField(key, propertyMeta, relationshipPanel));
        form.appendChild(relationshipPanel);
      }
      entries
        .filter(([, propertyMeta]) => !isReferenceMeta(propertyMeta))
        .forEach(([key, propertyMeta]) => renderItemField(key, propertyMeta));
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
    restoreGuidedStepItems(uiCatalog?.profiles?.[selectedProfile], payload);
    syncHeaderControls(payload);
    buildArrayEditor(settingsEl, "settings");
    buildArrayEditor(dataSourcesEl, "data_sources");
    buildArrayEditor(dataSetsEl, "data_sets");
    renderGuidedSteps();
    saveDraft();
  }
  syncing = false;
};

const consumeLaunchActions = () => {
  const params = new URLSearchParams(window.location.search);
  const hadAction = params.has("new") || params.has("prefill");
  if (!hadAction) return;
  params.delete("new");
  params.delete("prefill");
  const query = params.toString();
  window.history.replaceState(null, "", `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`);
};

const renderSummary = async () => {
  try {
    [schemaCatalog, uiCatalog] = await Promise.all([
      window.R3XARuntime.loadSchemaCatalog(),
      window.R3XARuntime.loadUiCatalog(),
    ]);
    window.R3XAI18N?.installCatalog(uiCatalog);
    populateProfiles();
    pendingTemplateReview = loadPendingTemplateReview();
    updateEditorMode();
    const sections = Object.entries(schemaCatalog.sections || {})
      .map(([name, section]) => `${name}: ${Object.keys(section.kinds || {}).length || "header"}`)
      .join(" · ");
    summaryEl.textContent = t("editor.catalogue_summary", "Schema catalogue version: {version}\n{sections}", {
      version: schemaCatalog.schema_version || "unknown",
      sections,
    });
    const payload = readPayload();
    if (payload && !payload.version && schemaCatalog.schema_version) {
      payload.version = schemaCatalog.schema_version;
      inputEl.value = JSON.stringify(payload, null, 2);
      saveDraft();
    }
    buildHeaderForm(schemaCatalog.sections?.header?.properties || {});
    if (newDocumentRequested) {
      newDocumentRequested = false;
      consumeLaunchActions();
      reset();
    } else if (prefillRequested) {
      prefillRequested = false;
      consumeLaunchActions();
      createPrefilledWorkflow();
    } else {
      syncFormFromJson();
    }
  } catch {
    summaryEl.textContent = t("editor.catalogue_unavailable", "Failed to load schema catalogue.");
  }
};

const reset = () => {
  const payload = cloneJsonValue(defaultPayload);
  payload.version = schemaCatalog?.schema_version || payload.version;
  inputEl.value = JSON.stringify(payload, null, 2);
  guidedStepItems = {};
  saveGuidedStepItems();
  clearAllTemplateReviews();
  guidedStepIndex = 0;
  localStorage.setItem("r3xaGuidedStep", "0");
  outputEl.textContent = "";
  saveDraft();
  syncFormFromJson();
};

const validate = async () => {
  outputEl.textContent = "";
  const payload = readPayload();
  if (!payload) {
    outputEl.textContent = t("validation.parse_error", "Parse error: invalid JSON");
    return;
  }

  try {
    const response = await window.R3XARuntime.validateDocument(payload);
    if (!response.ok) throw new Error(`Validation request failed (${response.status})`);
    const report = await response.json();
    renderValidationReport(report);
  } catch (error) {
    outputEl.textContent = t("validation.unavailable", "Validation unavailable: {message}", {message: error.message});
  }
};

const validateDocumentForSave = async (payload) => {
  try {
    const response = await window.R3XARuntime.validateDocument(payload);
    if (!response.ok) throw new Error(`Validation request failed (${response.status})`);
    const report = await response.json();
    if (!report.valid) {
      renderValidationReport(report);
      return false;
    }
    return true;
  } catch (error) {
    outputEl.textContent = t("validation.unavailable", "Validation unavailable: {message}", {message: error.message});
    return false;
  }
};

const downloadJson = () => {
  if (!requireTemplateReview()) return;
  if (!readPayload()) {
    outputEl.textContent = t("validation.parse_error", "Parse error: invalid JSON");
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
  if (!requireTemplateReview()) return;
  const payload = readPayload();
  if (!payload) {
    outputEl.textContent = t("validation.parse_error", "Parse error: invalid JSON");
    return;
  }
  if (!await validateDocumentForSave(payload)) return;

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
    let payload;
    try {
      payload = JSON.parse(reader.result);
    } catch (error) {
      outputEl.textContent = t("validation.parse_error_detail", "Parse error: {message}", {message: error.message});
      return;
    }
    const normalization = normalizeDocumentIds(payload);
    inputEl.value = JSON.stringify(payload, null, 2);
    guidedStepItems = {};
    saveGuidedStepItems();
    clearAllTemplateReviews();
    saveDraft();
    syncFormFromJson();
    if (normalization.conflicts.length) {
      outputEl.textContent = t(
        "validation.duplicate_ids_migration",
        "ID migration was not applied because these IDs are duplicated: {ids}. Resolve the duplicates before continuing.",
        {ids: normalization.conflicts.join(", ")},
      );
    }
  };
  reader.readAsText(file);
};

const ensureServerStart = () => {
  const appStart = document.body?.dataset?.appStart;
  if (!appStart) return;
  const stored = localStorage.getItem("r3xaAppStart");
  if (stored !== appStart) {
    localStorage.setItem("r3xaAppStart", appStart);
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
    const nextProfile = profileSelectEl.value;
    const current = readPayload();
    const hasItems = ["settings", "data_sources", "data_sets"].some((section) => current?.[section]?.length);
    if (nextProfile === "generic" && selectedProfile !== "generic" && hasItems) {
      const accepted = window.confirm(t(
        "guided.discard_for_generic",
        "Start a new empty custom document and discard the current experiment data?",
      ));
      if (!accepted) {
        profileSelectEl.value = selectedProfile;
        return;
      }
    }
    selectedProfile = nextProfile;
    guidedStepIndex = 0;
    guidedStepItems = loadGuidedStepItems();
    pendingTemplateReview = loadPendingTemplateReview();
    localStorage.setItem("r3xaProfile", selectedProfile);
    localStorage.setItem("r3xaGuidedStep", "0");
    if (selectedProfile === "generic" && hasItems) reset();
    else syncFormFromJson();
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
if (guidedPrefillEl) guidedPrefillEl.addEventListener("click", createPrefilledWorkflow);
document.addEventListener("r3xa-language-changed", () => {
  populateProfiles();
  if (schemaCatalog) syncFormFromJson();
});
inputEl.addEventListener("input", () => {
  saveDraft();
  syncFormFromJson();
});

ensureServerStart();
updateEditorMode();
inputEl.value = loadDraft();
const loadedPayload = readPayload();
const loadedNormalization = loadedPayload
  ? normalizeDocumentIds(loadedPayload)
  : {replacements: new Map(), conflicts: []};
if (loadedNormalization.changed && loadedPayload) {
  inputEl.value = JSON.stringify(loadedPayload, null, 2);
  saveDraft();
}
guidedStepItems = loadGuidedStepItems();
if (loadedNormalization.replacements.size) {
  guidedStepItems = Object.fromEntries(
    Object.entries(guidedStepItems).map(([stepId, itemId]) => [stepId, loadedNormalization.replacements.get(itemId) || itemId]),
  );
  saveGuidedStepItems();
}
renderSummary();
if (loadedNormalization.conflicts.length) {
  outputEl.textContent = t(
    "validation.duplicate_ids_migration",
    "ID migration was not applied because these IDs are duplicated: {ids}. Resolve the duplicates before continuing.",
    {ids: loadedNormalization.conflicts.join(", ")},
  );
}
