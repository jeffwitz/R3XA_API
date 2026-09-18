const defaultRegistryItem = {
  id: "src-generic-example",
  kind: "data_sources/generic",
  title: "Test machine acquisition",
  description: "Acquisition channel recording force and displacement during the tensile test.",
  output_components: 1,
  output_dimension: "point",
  output_units: [{kind: "unit", title: "force", value: 1.0, unit: "N", scale: 1.0}],
  manufacturer: "Instron",
  model: "Bluehill Universal",
};

const inputEl = document.getElementById("registry-json-input");
const highlightEl = document.getElementById("registry-json-highlight");
const outputEl = document.getElementById("registry-validation-output");
const kindEl = document.getElementById("registry-kind");
const profileEl = document.getElementById("registry-profile");
const formEl = document.getElementById("registry-form");
const addLocalButton = document.getElementById("registry-add-local-btn");
const completeButton = document.getElementById("registry-complete-btn");
const localItemsEl = document.getElementById("registry-local-items");

let schemaCatalog = null;
let uiCatalog = null;
let lintTimer = null;
let registryBaseline = "";
let lastStableProfile = "";
let localRegistryStorageError = "";

const {
  hasCanonicalId,
  makeId: createGeneratedId,
  normalizeLocalRegistryItems,
  prefixForKind: canonicalIdPrefix,
} = window.R3XAIdUtils;
let localRegistryMigrationConflicts = [];

const readLocalRegistryItems = () => {
  const stored = window.R3XARegistryStorage.read();
  localRegistryStorageError = stored.error;
  if (stored.corrupt) {
    localRegistryMigrationConflicts = [];
    return [];
  }
  const items = stored.items.filter((item) => item && typeof item === "object");
  const normalized = normalizeLocalRegistryItems(items);
  localRegistryMigrationConflicts = normalized.conflicts;
  if (!normalized.conflicts.length && (stored.migrated || normalized.changed)) {
    const result = window.R3XARegistryStorage.write(normalized.items, schemaCatalog?.schema_version);
    if (!result.ok) localRegistryStorageError = result.error;
  }
  return normalized.items;
};

const writeLocalRegistryItems = (items) => {
  const result = window.R3XARegistryStorage.write(items, schemaCatalog?.schema_version);
  localRegistryStorageError = result.error;
  return result.ok;
};

const generateRegistryId = (kind) => {
  const used = new Set(readLocalRegistryItems().map((item) => item.id).filter(Boolean));
  const current = currentItem();
  if (current?.id) used.add(current.id);
  return createGeneratedId(kind, used);
};

const currentItem = () => {
  try {
    return JSON.parse(inputEl.value);
  } catch {
    return null;
  }
};

const normalizedTitle = (value) => String(value || "").trim().normalize("NFKC").toLocaleLowerCase();

const renderLocalRegistryItems = () => {
  if (!localItemsEl) return;
  localItemsEl.replaceChildren();
  const items = readLocalRegistryItems();
  if (localRegistryStorageError) {
    const warning = document.createElement("p");
    warning.className = "validation-warning";
    warning.textContent = localRegistryStorageError;
    localItemsEl.appendChild(warning);
  }
  if (localRegistryMigrationConflicts.length) {
    const warning = document.createElement("p");
    warning.className = "validation-warning";
    warning.textContent = registryText(
      "registry.duplicate_ids",
      "Local Registry migration was not applied because these IDs are duplicated: {ids}. Export or edit the affected items before continuing.",
      {ids: localRegistryMigrationConflicts.join(", ")},
    );
    localItemsEl.appendChild(warning);
  }
  if (!items.length) {
    const empty = document.createElement("p");
    empty.textContent = registryText("registry.empty", "No local registry item has been saved yet.");
    localItemsEl.appendChild(empty);
    return;
  }
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "registry-local-item";
    const label = document.createElement("span");
    label.textContent = `${item.title || item.id || "Untitled item"} (${item.kind || "unknown kind"})`;
    row.appendChild(label);
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "ghost";
    remove.textContent = "Remove";
    remove.addEventListener("click", () => {
      if (!writeLocalRegistryItems(items.filter((candidate) => candidate.id !== item.id))) return;
      renderLocalRegistryItems();
    });
    row.appendChild(remove);
    localItemsEl.appendChild(row);
  });
};

const escapeHtml = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

const highlightJson = (text) => escapeHtml(text).replace(
  /(&quot;(?:\\.|[^&])*?&quot;)(\s*:)?|\b(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\b|\b(true|false|null)\b/g,
  (match, stringToken, colon, numberToken, literal) => {
    if (stringToken) return `<span class="json-string">${stringToken}</span>${colon || ""}`;
    if (numberToken) return `<span class="json-number">${numberToken}</span>`;
    return `<span class="json-literal">${literal}</span>`;
  },
);

const updateHighlight = () => {
  if (highlightEl) highlightEl.innerHTML = highlightJson(inputEl.value);
};

const ensureServerStart = () => {
  const appStart = document.body?.dataset?.appStart;
  if (appStart) localStorage.setItem("r3xaRegistryAppStart", appStart);
};

const loadDraft = () => localStorage.getItem("r3xaRegistryDraft") || JSON.stringify(defaultRegistryItem, null, 2);

const registryText = (key, fallback, variables = {}) => (
  typeof t === "function" ? t(key, fallback, variables) : fallback
);

const canonicalRegistryText = (text) => {
  try {
    return JSON.stringify(JSON.parse(text));
  } catch {
    return String(text);
  }
};

const setRegistryBaseline = () => {
  registryBaseline = canonicalRegistryText(inputEl.value);
  lastStableProfile = profileEl?.value || "";
};

const registryIsDirty = () => registryBaseline !== ""
  && canonicalRegistryText(inputEl.value) !== registryBaseline;

const confirmRegistryReplacement = (action) => {
  const dirty = registryIsDirty();
  return !dirty || window.confirm(
  registryText(
    "registry.confirm_replace",
    `Replace the current Registry item and ${action}? Unsaved changes will be discarded.`,
    {action},
  ),
  );
};

const saveDraft = () => {
  localStorage.setItem("r3xaRegistryDraft", inputEl.value);
  localStorage.setItem("r3xaRegistryKind", kindEl.value);
};

const fieldTypes = (meta) => {
  const declared = Array.isArray(meta?.type) ? meta.type : [meta?.type];
  const alternatives = [...(meta?.oneOf || []), ...(meta?.anyOf || [])]
    .flatMap((option) => Array.isArray(option.type) ? option.type : [option.type]);
  return new Set([...declared, ...alternatives].filter(Boolean));
};

const defaultForField = (key, meta, context = {}) => {
  if (meta.const !== undefined) return meta.const;
  if (meta.default !== undefined) return meta.default;
  if (key === "id") return createGeneratedId(context.kind || kindEl.value, new Set());
  const types = fieldTypes(meta);
  if (types.has("array")) return [];
  if (types.has("object")) {
    const object = {};
    Object.entries(meta.properties || {}).forEach(([propertyKey, propertyMeta]) => {
      if ((meta.required || []).includes(propertyKey) || propertyMeta.const !== undefined) {
        object[propertyKey] = defaultForField(propertyKey, propertyMeta, context);
      }
    });
    return object;
  }
  if (types.has("boolean")) return false;
  if (types.has("number") || types.has("integer")) return undefined;
  return "";
};

const kindExamples = {
  "settings/generic": {
    title: "Lighting setup",
    description: "LED illumination used to light the specimen during image acquisition.",
  },
  "settings/specimen": {
    title: "316L tensile specimen",
    description: "Flat dog-bone specimen prepared for a uniaxial tensile test.",
  },
  "settings/testing_machine": {
    title: "Universal testing machine",
    description: "Electromechanical machine used to apply tensile loading to the specimen.",
    manufacturer: "Instron",
    model: "5985",
  },
  "settings/stereorig": {
    title: "Stereo rig",
    description: "Rigid mount carrying two synchronized cameras for stereo-DIC acquisition.",
  },
  "data_sources/generic": {
    title: "Test machine acquisition",
    description: "Acquisition channel recording force and displacement during the test.",
    manufacturer: "Instron",
    model: "Bluehill Universal",
  },
  "data_sources/camera": {
    title: "Visible camera",
    description: "Monochrome camera recording the specimen surface during the tensile test.",
    manufacturer: "Allied Vision Technologies",
    model: "Dolphin F-145B",
  },
  "data_sources/infrared": {
    title: "Infrared camera",
    description: "Infrared camera recording the specimen temperature field during loading.",
    manufacturer: "FLIR",
    model: "A655sc",
  },
  "data_sources/tomograph": {
    title: "Laboratory X-ray tomograph",
    description: "Cone-beam X-ray tomograph used to reconstruct the internal specimen volume.",
    manufacturer: "Nikon Metrology",
    model: "XT H 225",
  },
  "data_sources/load_cell": {
    title: "Tension load cell",
    description: "Force transducer measuring the tensile load applied to the specimen.",
    manufacturer: "HBM",
    model: "U10M 10 kN",
  },
  "data_sources/strain_gauge": {
    title: "Foil strain gauge",
    description: "Bonded foil gauge measuring the longitudinal strain of the specimen.",
    manufacturer: "HBK",
    model: "LY11-6/120",
  },
  "data_sources/point_temperature": {
    title: "Specimen temperature sensor",
    description: "Non-contact sensor measuring the temperature at the specimen surface.",
    manufacturer: "Optris",
    model: "CTlaser 3MH",
  },
  "data_sources/dic_measurement": {
    title: "2D DIC processing",
    description: "Digital image correlation processing measuring the in-plane displacement field.",
    manufacturer: "Pyxel",
    model: "2.0",
  },
  "data_sources/mechanical_analysis": {
    title: "Finite element analysis",
    description: "Mechanical analysis producing a displacement or strain field from the experiment.",
    manufacturer: "Abaqus",
    model: "2024",
  },
  "data_sources/identification": {
    title: "Material parameter identification",
    description: "Inverse analysis identifying material parameters from measured force and displacement.",
    manufacturer: "MFront",
    model: "TFEL 3.2",
  },
  "data_sources/strain_computation": {
    title: "Strain computation",
    description: "Computation of strain fields from the measured displacement field.",
    manufacturer: "Pyxel",
    model: "2.0",
  },
  "data_sets/generic": {
    title: "Experimental data file",
    description: "Data file containing measurements associated with the experiment.",
  },
  "data_sets/file": {
    title: "Force and displacement data",
    description: "CSV file containing synchronized force and displacement measurements.",
  },
  "data_sets/list": {
    title: "Raw camera images",
    description: "Ordered image sequence recorded during the experiment.",
  },
};

const unitExamples = {
  exposure: ["exposure time", 0.01, "s"],
  image_scale: ["pixel size", 0.05, "mm/px"],
  focal_length: ["focal length", 25, "mm"],
  standoff_distance: ["standoff distance", 500, "mm"],
  uncertainty: ["measurement uncertainty", 0.01, "mm"],
  capacity: ["capacity", 10, "kN"],
  stereo_angle: ["stereo angle", 25, "deg"],
  patterning_feature_size: ["pattern feature size", 0.5, "mm"],
  step_size: ["DIC step size", 5, "px"],
  regularisation_length: ["regularisation length", 2, "mm"],
  virtual_strain_gauge_size: ["virtual gauge length", 5, "mm"],
  voltage: ["tube voltage", 150, "kV"],
  current: ["tube current", 2, "mA"],
  scan_duration: ["scan duration", 12, "min"],
  tube_to_detector_distance: ["tube-detector distance", 800, "mm"],
  source_to_object_distance: ["source-object distance", 600, "mm"],
  angular_amplitude: ["angular amplitude", 360, "deg"],
  emissivity: ["emissivity", 0.95, "1"],
  transmissivity: ["transmissivity", 1, "1"],
  time_reference: ["time reference", 0, "s"],
};

const itemExample = (context = {}) => kindExamples[context.kind] || {};

const isPlaceholder = (value) => typeof value === "string" && (
  !value.trim()
  || /^not specified$/i.test(value.trim())
  || /^unknown$/i.test(value.trim())
  || /^example\b/i.test(value.trim())
  || /^item$/i.test(value.trim())
  || value.trim() === "unit"
);

const unitExample = (key, context = {}) => {
  const field = context.parentKey || key;
  const named = unitExamples[field];
  if (named) {
    return {kind: "unit", title: named[0], value: named[1], unit: named[2], scale: 1.0};
  }
  const arrayPosition = context.arrayPosition;
  if (["image_size", "field_of_view", "calibration_target_size", "sizes", "subset_size"].includes(field)) {
    const labels = field === "sizes" ? ["width", "height", "thickness"] : ["width", "height"];
    const values = field === "image_size" ? [1392, 1040] : field === "field_of_view" ? [70, 50] : field === "calibration_target_size" ? [300, 200] : field === "subset_size" ? [31, 31] : [30, 12, 1];
    const units = field === "image_size" ? ["px", "px"] : field === "subset_size" ? ["px", "px"] : ["mm", "mm", "mm"];
    const index = Math.min(arrayPosition || 0, labels.length - 1);
    return {kind: "unit", title: labels[index], value: values[index], unit: units[index], scale: 1.0};
  }
  if (field === "output_units") {
    const kind = context.kind || "";
    if (kind.includes("camera")) return {kind: "unit", title: "gray level", value: 1, unit: "gl", scale: 1.0};
    if (kind.includes("load_cell")) return {kind: "unit", title: "force", value: 1, unit: "N", scale: 1.0};
    if (kind.includes("temperature")) return {kind: "unit", title: "temperature", value: 1, unit: "degC", scale: 1.0};
    if (kind.includes("strain")) return {kind: "unit", title: "strain", value: 1, unit: "%", scale: 1.0};
    if (kind.includes("dic") || kind.includes("mechanical")) return {kind: "unit", title: "displacement", value: 1, unit: "mm", scale: 1.0};
    return {kind: "unit", title: "measurement", value: 1, unit: "mm", scale: 1.0};
  }
  return {kind: "unit", title: "measurement", value: 1, unit: "mm", scale: 1.0};
};

const exampleString = (key, meta, context = {}) => {
  if (meta.enum?.length) return meta.enum[0];
  const item = itemExample(context);
  if (["title", "description", "manufacturer", "model"].includes(key) && item[key]) return item[key];
  if (["file_type", "data_type"].includes(key)) {
    return context.kind === "data_sets/list" ? "image/tiff" : "text/csv";
  }
  if (key === "delimiter") return ";";
  if (key === "path") {
    if (context.kind === "data_sets/list") return "experiment/images/";
    if (context.kind === "data_sets/file") return "experiment/data/";
    return "experiment/data/";
  }
  if (key === "filename") return context.kind === "data_sets/list" ? "camera_000001.tif" : "machine_force_displacement.csv";
  if (key === "documentation") return "documentation/instrument-manual.pdf";
  if (key === "lens") return "Schneider-Kreuznach Xenoplan 1.4/23";
  if (key === "filter") return context.kind === "data_sources/infrared" ? "8-14 um long-pass filter" : "No optical filter";
  if (key === "aperture") return "f/8";
  if (key === "source") return "Tungsten target, 150 kV microfocus tube";
  if (key === "detector") return "Flat-panel detector, 200 um pixel pitch";
  if (key === "target") return "Aluminium calibration target";
  if (key === "type") return context.kind === "data_sources/load_cell" ? "strain-gauge bridge" : "tensile";
  if (key === "calibration_target_type") return "Checkerboard calibration plate";
  if (key === "image_filtering") return "Gaussian filter, sigma 1 px";
  if (key === "interpolant") return "cubic spline";
  if (key === "matching_criterion") return "ZNSSD";
  if (key === "shape_function") return "affine";
  if (key === "camera_model") return "pinhole with Brown-Conrady distortion";
  if (key === "camera_parameters") return "calibration/camera_intrinsics.json";
  if (key === "regularization_type") return "weak elastic regularization";
  if (["displacement_filtering", "strain_filtering"].includes(key)) return "Gaussian filter, sigma 1 px";
  if (["nuc_file", "calibration_file", "aquisition_param_file", "reconstruction_param_file"].includes(key)) return `calibration/${key}.json`;
  if (key === "unit") return "mm";
  if (key === "description") return `Recorded ${String(meta.title || "measurement").toLowerCase()} for the experiment.`;
  if (key === "title") return "Experimental measurement";
  return `Measured ${String(meta.title || key).toLowerCase()}`;
};

const exampleForField = (key, meta, context = {}) => {
  if (meta.const !== undefined) return meta.const;
  if (meta.default !== undefined) return cloneJsonValue(meta.default);
  if (key === "id") return createGeneratedId(context.kind || kindEl.value, new Set());
  if (["parent_data_sources", "attached_data_sources", "input_data_sets"].includes(key)) return [];
  const types = fieldTypes(meta);
  if (key === "col") return 0;
  if (key === "rows") return [0, null];
  if (meta.properties?.unit && meta.properties?.value) return unitExample(key, context);
  if (types.has("array")) {
    const itemMeta = meta.items || {};
    if (context.kind === "data_sources/camera" && key === "image_size") return [unitExample(key, {...context, arrayPosition: 0}), unitExample(key, {...context, arrayPosition: 1})];
    if (["field_of_view", "calibration_target_size", "sizes", "subset_size", "bandwidth", "range"].includes(key)) {
      return [unitExample(key, {...context, arrayPosition: 0}), unitExample(key, {...context, arrayPosition: 1})];
    }
    if (key === "output_units") return [unitExample(key, context)];
    if (key === "values") return context.kind === "data_sets/list" ? ["camera_000001.tif", "camera_000002.tif", "camera_000003.tif"] : ["machine_force_displacement.csv"];
    if (key === "timestamps") return [0.0, 0.1, 0.2];
    if (key === "keywords") return ["tensile test", "calibration", "measurement"];
    const itemContext = {...context, parentKey: key};
    return [exampleForField("item", itemMeta, itemContext)];
  }
  if (types.has("object")) {
    const object = {};
    const properties = meta.properties || {};
    Object.entries(properties).forEach(([propertyKey, propertyMeta]) => {
      object[propertyKey] = exampleForField(propertyKey, propertyMeta, {...context, parentKey: key});
    });
    return object;
  }
  if (types.has("number") || types.has("integer")) {
    if (key === "output_components") return context.kind?.includes("dic") ? 2 : 1;
    if (key === "number_of_projections") return 1440;
    if (Number.isFinite(meta.minimum)) return Math.max(1, meta.minimum);
    return 1;
  }
  if (types.has("boolean")) return false;
  return exampleString(key, meta, context);
};

const completeExampleValue = (key, value, meta, context = {}) => {
  const types = fieldTypes(meta);
  if (meta.properties?.unit && meta.properties?.value) {
    const example = unitExample(key, context);
    const object = value && typeof value === "object" && !Array.isArray(value) ? cloneJsonValue(value) : {};
    const unitIsPlaceholder = isPlaceholder(object.unit);
    return {
      ...example,
      ...object,
      kind: meta.properties.kind?.const || "unit",
      title: isPlaceholder(object.title) ? example.title : (object.title || example.title),
      value: unitIsPlaceholder || object.value === undefined ? example.value : object.value,
      unit: unitIsPlaceholder || !object.unit ? example.unit : object.unit,
      scale: object.scale === undefined ? example.scale : object.scale,
    };
  }
  if (types.has("object") || meta.properties) {
    const object = value && typeof value === "object" && !Array.isArray(value)
      ? cloneJsonValue(value)
      : {};
    Object.entries(meta.properties || {}).forEach(([propertyKey, propertyMeta]) => {
      object[propertyKey] = completeExampleValue(propertyKey, object[propertyKey], propertyMeta, {...context, parentKey: key});
    });
    return object;
  }
  if (types.has("array")) {
    if (context.kind === "data_sets/list" && ["values", "timestamps"].includes(key)) {
      return exampleForField(key, meta, context);
    }
    if (Array.isArray(value) && value.length) {
      const itemMeta = meta.items || {};
      return value.map((entry, index) => completeExampleValue("item", entry, itemMeta, {...context, parentKey: key, arrayPosition: index}));
    }
    return exampleForField(key, meta, context);
  }
  if (value !== undefined && value !== "" && !isPlaceholder(value)) return value;
  return exampleForField(key, meta, context);
};

const cloneJsonValue = (value) => JSON.parse(JSON.stringify(value));

const collectExampleChanges = (before, after, path = "", changes = []) => {
  if (JSON.stringify(before) === JSON.stringify(after)) return changes;
  const beforeObject = before && typeof before === "object";
  const afterObject = after && typeof after === "object";
  if (beforeObject && afterObject && !Array.isArray(before) && !Array.isArray(after)) {
    const keys = new Set([...Object.keys(before), ...Object.keys(after)]);
    keys.forEach((key) => collectExampleChanges(
      before[key],
      after[key],
      path ? `${path}.${key}` : key,
      changes,
    ));
    return changes;
  }
  changes.push({path: path || "item", value: after});
  return changes;
};

const profileStepsForKind = (kind) => Object.entries(uiCatalog?.profiles || {})
  .flatMap(([profileId, profile]) => (profile.steps || [])
    .filter((step) => step.kind === kind && step.defaults && Object.keys(step.defaults).length)
    .map((step) => ({profileId, profile, step})));

const renderProfileOptions = (kind, selectedProfile = "") => {
  if (!profileEl) return;
  profileEl.replaceChildren();
  const none = document.createElement("option");
  none.value = "";
  none.textContent = "Schema defaults only";
  profileEl.appendChild(none);
  const seen = new Set();
  profileStepsForKind(kind).forEach(({profileId, profile}) => {
    if (seen.has(profileId)) return;
    seen.add(profileId);
    const option = document.createElement("option");
    option.value = profileId;
    option.textContent = profile.title || profileId;
    option.title = profile.description || "";
    profileEl.appendChild(option);
  });
  profileEl.value = selectedProfile && seen.has(selectedProfile)
    ? selectedProfile
    : (profileEl.querySelector("option[value]:not([value=''])")?.value || "");
};

const selectedProfileDefaults = (kind) => {
  const selected = profileEl?.value;
  if (profileEl && !selected) return {};
  const candidates = profileStepsForKind(kind);
  const match = candidates.find(({profileId}) => profileId === selected) || candidates[0];
  return match?.step?.defaults ? cloneJsonValue(match.step.defaults) : {};
};

const itemForKind = (kind, meta) => {
  const item = selectedProfileDefaults(kind);
  Object.entries(meta?.properties || {}).forEach(([key, propertyMeta]) => {
    if (key === "kind") item[key] = propertyMeta.const || kind;
    else item[key] = completeExampleValue(key, item[key], propertyMeta, {kind});
  });
  item.kind = meta.properties?.kind?.const || kind;
  return item;
};

const primitiveValue = (value, meta) => {
  const types = fieldTypes(meta);
  if (value === "null" && types.has("null")) return null;
  if (types.has("integer") && /^[-+]?\d+$/.test(value)) return Number(value);
  if (types.has("number") && value !== "" && Number.isFinite(Number(value))) return Number(value);
  return value;
};

const setValue = (target, key, value, required) => {
  if (value === undefined || (value === "" && !required)) delete target[key];
  else target[key] = value;
};

const selectedMeta = (kind) => {
  const section = kind?.split("/", 1)[0];
  return schemaCatalog?.sections?.[section]?.kinds?.[kind] || null;
};

const createField = (container, key, meta, value, onChange, path, required = false) => {
  const wrapper = document.createElement("div");
  wrapper.className = "form-row registry-field";
  wrapper.dataset.jsonPath = path;
  const label = document.createElement("label");
  label.textContent = `${meta.title || key}${required ? " *" : ""}`;
  const fieldId = `registry-field-${path.replaceAll("/", "-")}`;
  label.setAttribute("for", fieldId);
  wrapper.appendChild(label);

  const types = fieldTypes(meta);
  if (meta.type === "object" || meta.properties) {
    let object = value && typeof value === "object" && !Array.isArray(value) ? {...value} : {};
    const fieldset = document.createElement("fieldset");
    fieldset.className = "registry-object-field";
    Object.entries(meta.properties || {}).forEach(([part, partMeta]) => {
      if (part === "kind" && partMeta.const !== undefined) return;
      createField(
        fieldset,
        part,
        partMeta,
        object[part],
        (next) => {
          const updated = {...object};
          setValue(updated, part, next, (meta.required || []).includes(part));
          object = updated;
          onChange(updated);
        },
        `${path}/${part}`,
        (meta.required || []).includes(part),
      );
    });
    wrapper.appendChild(fieldset);
  } else if (types.has("array")) {
    const values = Array.isArray(value) ? [...value] : [];
    const list = document.createElement("div");
    list.className = "registry-array-list";
    const renderList = () => {
      list.replaceChildren();
      if (!values.length) {
        const empty = document.createElement("small");
        empty.className = "field-description";
        empty.textContent = ["parent_data_sources", "attached_data_sources", "input_data_sets"].includes(key)
          ? "No dependency (optional)."
          : "No example entries.";
        list.appendChild(empty);
      }
      values.forEach((entry, index) => {
        const row = document.createElement("div");
        row.className = "registry-array-row";
        createField(row, String(index), meta.items || {}, entry, (next) => {
          values[index] = next;
          onChange([...values]);
        }, `${path}/${index}`, true);
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "ghost";
        remove.textContent = "Remove";
        remove.addEventListener("click", () => {
          values.splice(index, 1);
          onChange([...values]);
          renderList();
        });
        row.appendChild(remove);
        list.appendChild(row);
      });
    };
    renderList();
    wrapper.appendChild(list);
    const add = document.createElement("button");
    add.type = "button";
    add.className = "ghost";
    add.textContent = "Add value";
    add.addEventListener("click", () => {
      values.push(exampleForField("item", meta.items || {}));
      onChange([...values]);
      renderList();
    });
    wrapper.appendChild(add);
  } else {
    let control;
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
    } else if (types.has("boolean") && types.size === 1) {
      control = document.createElement("input");
      control.type = "checkbox";
      control.checked = Boolean(value);
    } else if ((types.has("number") || types.has("integer")) && types.size === 1) {
      control = document.createElement("input");
      control.type = "number";
      control.step = types.has("integer") ? "1" : "any";
      control.value = value ?? "";
    } else {
      control = document.createElement(key === "description" ? "textarea" : "input");
      control.type = "text";
      control.value = value ?? "";
    }
    control.id = fieldId;
    control.name = key;
    const update = () => {
      if (meta.const !== undefined) return;
      let next;
      if (control.type === "checkbox") next = control.checked;
      else if (control.type === "number") next = control.value === "" ? undefined : Number(control.value);
      else next = primitiveValue(control.value, meta);
      onChange(next);
    };
    control.addEventListener(meta.enum || control.type === "checkbox" ? "change" : "input", update);
    if (key === "id") {
      const idControls = document.createElement("div");
      idControls.className = "registry-id-controls";
      idControls.appendChild(control);
      const generate = document.createElement("button");
      generate.type = "button";
      generate.className = "ghost";
      generate.textContent = "Generate new ID";
      generate.title = "Generate a unique ID with the R3XA section prefix.";
      generate.addEventListener("click", () => {
        const next = generateRegistryId(kindEl.value);
        control.value = next;
        onChange(next);
      });
      idControls.appendChild(generate);
      wrapper.appendChild(idControls);
    } else {
      wrapper.appendChild(control);
    }
  }
  if (meta.description) {
    const description = document.createElement("small");
    description.className = "field-description";
    description.textContent = meta.description;
    wrapper.appendChild(description);
  }
  container.appendChild(wrapper);
};

const renderKindOptions = (currentKind = "") => {
  kindEl.replaceChildren();
  Object.entries(schemaCatalog?.sections || {}).forEach(([section, data]) => {
    if (!data.kinds) return;
    const group = document.createElement("optgroup");
    group.label = data.title || section;
    Object.entries(data.kinds).forEach(([kind, meta]) => {
      const option = document.createElement("option");
      option.value = kind;
      option.textContent = `${meta.title || kind} (${kind})`;
      group.appendChild(option);
    });
    kindEl.appendChild(group);
  });
  if (currentKind && !selectedMeta(currentKind)) {
    const option = document.createElement("option");
    option.value = currentKind;
    option.textContent = `${currentKind} (not in current schema)`;
    kindEl.appendChild(option);
  }
  kindEl.value = currentKind;
};

const renderForm = () => {
  formEl.replaceChildren();
  let item;
  try {
    item = JSON.parse(inputEl.value);
  } catch {
    formEl.textContent = "Enter valid JSON to use the form editor.";
    return;
  }
  const kind = kindEl.value || item.kind || "";
  const meta = selectedMeta(kind);
  if (!meta) {
    formEl.textContent = "No schema definition is available for this kind. Use the expert JSON editor.";
    return;
  }
  Object.entries(meta.properties || {}).forEach(([key, propertyMeta]) => {
    if (key === "kind") return;
    createField(formEl, key, propertyMeta, item[key], (value) => {
      const updated = {...item};
      setValue(updated, key, value, (meta.required || []).includes(key));
      item = updated;
      inputEl.value = JSON.stringify(updated, null, 2);
      saveDraft();
      updateHighlight();
      scheduleLint();
    }, key, (meta.required || []).includes(key));
  });
};

const formatError = (error) => {
  if (typeof error === "string") return error;
  const path = error.path ? `${error.path}: ` : "";
  return `${path}${error.user_message || error.message || "Validation failed."}`;
};

const lint = async () => {
  let item;
  try {
    item = JSON.parse(inputEl.value);
  } catch (error) {
    outputEl.textContent = `JSON error: ${error.message}`;
    return;
  }
  try {
    const response = await window.R3XARuntime.validateItem(item, kindEl.value);
    const report = await response.json();
    if (report.valid) {
      outputEl.textContent = "Valid registry item ✅";
      if (addLocalButton) addLocalButton.disabled = false;
      return;
    }
    if (addLocalButton) addLocalButton.disabled = true;
    outputEl.textContent = ["Invalid registry item ❌", "", ...(report.errors || []).map(formatError)].join("\n");
  } catch (error) {
    if (addLocalButton) addLocalButton.disabled = true;
    outputEl.textContent = `Validation unavailable: ${error.message}`;
  }
};

const scheduleLint = () => {
  window.clearTimeout(lintTimer);
  lintTimer = window.setTimeout(lint, 350);
};

const syncFromJson = () => {
  let item;
  try {
    item = JSON.parse(inputEl.value);
  } catch {
    updateHighlight();
    formEl.textContent = "Enter valid JSON to use the form editor.";
    return;
  }
  renderKindOptions(item.kind || kindEl.value || "");
  renderProfileOptions(item.kind || kindEl.value || "", localStorage.getItem("r3xaRegistryProfile") || "");
  renderForm();
  updateHighlight();
  if (addLocalButton) addLocalButton.disabled = true;
  renderLocalRegistryItems();
  saveDraft();
  scheduleLint();
};

const reset = () => {
  if (!confirmRegistryReplacement("reset the item")) return;
  inputEl.value = JSON.stringify(defaultRegistryItem, null, 2);
  outputEl.textContent = "";
  syncFromJson();
  setRegistryBaseline();
};

const changeKind = () => {
  const meta = selectedMeta(kindEl.value);
  if (!meta) return;
  if (!confirmRegistryReplacement("change its kind")) {
    const current = currentItem();
    renderKindOptions(current?.kind || "");
    renderProfileOptions(current?.kind || "", lastStableProfile);
    return;
  }
  renderProfileOptions(kindEl.value);
  inputEl.value = JSON.stringify(itemForKind(kindEl.value, meta), null, 2);
  syncFromJson();
  setRegistryBaseline();
};

const changeProfile = () => {
  if (!confirmRegistryReplacement("change its example profile")) {
    profileEl.value = lastStableProfile;
    return;
  }
  localStorage.setItem("r3xaRegistryProfile", profileEl.value);
  const meta = selectedMeta(kindEl.value);
  if (!meta) return;
  inputEl.value = JSON.stringify(itemForKind(kindEl.value, meta), null, 2);
  syncFromJson();
  setRegistryBaseline();
};

const downloadJson = () => {
  try {
    JSON.parse(inputEl.value);
  } catch (error) {
    outputEl.textContent = `JSON error: ${error.message}`;
    return;
  }
  const blob = new Blob([inputEl.value], {type: "application/json"});
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "registry-item.json";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
};

const saveWithDialog = async () => {
  if (window.showSaveFilePicker) {
    try {
      const handle = await window.showSaveFilePicker({
        suggestedName: "registry-item.json",
        types: [{description: "JSON", accept: {"application/json": [".json"]}}],
      });
      const writable = await handle.createWritable();
      await writable.write(inputEl.value);
      await writable.close();
      return;
    } catch (error) {
      if (error?.name === "AbortError") return;
    }
  }
  downloadJson();
};

const loadJsonFile = (file) => {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    if (!confirmRegistryReplacement("load the selected JSON item")) return;
    inputEl.value = reader.result;
    syncFromJson();
    setRegistryBaseline();
  };
  reader.readAsText(file);
};

const completeCurrentItemWithExamples = () => {
  const item = currentItem();
  const kind = item?.kind || kindEl.value;
  const meta = selectedMeta(kind);
  if (!item || !meta) return;
  const enriched = {...item};
  Object.entries(meta.properties || {}).forEach(([key, propertyMeta]) => {
    if (key !== "kind") enriched[key] = completeExampleValue(key, enriched[key], propertyMeta, {kind});
  });
  enriched.kind = meta.properties?.kind?.const || kind;
  const changes = collectExampleChanges(item, enriched);
  if (!changes.length) {
    outputEl.textContent = registryText("registry.complete_none", "No missing or placeholder fields were found.");
    return;
  }
  const preview = changes.map(({path, value}) => `${path}: ${JSON.stringify(value)}`).join("\n");
  outputEl.textContent = `${registryText("registry.complete_preview", "Proposed example values:")}\n${preview}`;
  if (!window.confirm(registryText(
    "registry.confirm_complete",
    `Apply ${changes.length} example value(s) to the current item?`,
    {count: changes.length},
  ))) {
    outputEl.textContent = registryText("registry.complete_cancelled", "Example completion cancelled.");
    return;
  }
  inputEl.value = JSON.stringify(enriched, null, 2);
  syncFromJson();
};

const validateItem = async () => {
  await lint();
  saveDraft();
};

const addToLocalRegistry = async () => {
  const item = currentItem();
  if (!item) return;
  try {
    const response = await window.R3XARuntime.validateItem(item, kindEl.value);
    const report = await response.json();
    if (!report.valid) {
      outputEl.textContent = ["Invalid registry item ❌", "", ...(report.errors || []).map(formatError)].join("\n");
      if (addLocalButton) addLocalButton.disabled = true;
      return;
    }
    const items = readLocalRegistryItems();
    const sameId = items.find((candidate) => candidate.id === item.id);
    if (sameId && (sameId.title !== item.title || sameId.kind !== item.kind)) {
      outputEl.textContent = "Cannot save this item: its ID is already used by another local registry item. Generate a new ID first.";
      return;
    }
    const sameTitle = items.find((candidate) => (
      normalizedTitle(candidate.title) === normalizedTitle(item.title)
      && candidate.id !== item.id
    ));
    if (sameTitle) {
      outputEl.textContent = "Cannot save this item: its title is already used by another local registry item. Choose a different title.";
      return;
    }
    const updated = [...items.filter((candidate) => candidate.id !== item.id), item];
    if (!writeLocalRegistryItems(updated)) {
      outputEl.textContent = localRegistryStorageError || "Local Registry could not be saved.";
      return;
    }
    renderLocalRegistryItems();
    outputEl.textContent = "Valid registry item ✅ Saved in this browser's local registry.";
  } catch (error) {
    outputEl.textContent = `Validation unavailable: ${error.message}`;
  }
};

const init = async () => {
  ensureServerStart();
  try {
    [schemaCatalog, uiCatalog] = await Promise.all([
      window.R3XARuntime.loadSchemaCatalog(),
      window.R3XARuntime.loadUiCatalog(),
    ]);
  } catch (error) {
    outputEl.textContent = `Schema catalogue unavailable: ${error.message}`;
    return;
  }
  inputEl.value = loadDraft();
  try {
    JSON.parse(inputEl.value);
  } catch {
    inputEl.value = JSON.stringify(defaultRegistryItem, null, 2);
  }
  syncFromJson();
  setRegistryBaseline();
};

document.getElementById("registry-validate-btn").addEventListener("click", validateItem);
completeButton?.addEventListener("click", completeCurrentItemWithExamples);
addLocalButton?.addEventListener("click", addToLocalRegistry);
document.getElementById("registry-reset-btn").addEventListener("click", reset);
document.getElementById("registry-save-btn").addEventListener("click", saveWithDialog);
document.getElementById("registry-load-input").addEventListener("change", (event) => {
  loadJsonFile(event.target.files?.[0]);
  event.target.value = "";
});
inputEl.addEventListener("input", () => {
  updateHighlight();
  saveDraft();
  try {
    JSON.parse(inputEl.value);
    syncFromJson();
  } catch {
    formEl.textContent = "Enter valid JSON to use the form editor.";
    scheduleLint();
  }
});
kindEl.addEventListener("change", changeKind);
profileEl?.addEventListener("change", changeProfile);

init();
