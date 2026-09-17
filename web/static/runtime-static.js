(() => {
  const script = document.currentScript;
  const assetBase = String(script?.dataset?.assetBase || ".").replace(/\/$/, "");

  const loadAsset = async (name) => {
    const response = await fetch(`${assetBase}/${name}`);
    if (!response.ok) throw new Error(`Unable to load ${name} (${response.status})`);
    return response.json();
  };

  const unavailable = (message) => new Response(JSON.stringify({
    valid: false,
    errors: [message],
  }), {
    status: 503,
    headers: {"Content-Type": "application/json"},
  });

  let validatorPromise;
  let catalogPromise;
  const loadValidator = () => {
    validatorPromise ||= import(`${assetBase}/validator.generated.js`);
    return validatorPromise;
  };

  const loadCatalog = () => {
    catalogPromise ||= loadAsset("schema-catalog.json");
    return catalogPromise;
  };

  const integrityErrors = (document) => {
    const errors = [];
    const identifiers = new Map();
    const sourceIds = new Set();
    const dataSetIds = new Set();
    const sections = ["settings", "data_sources", "data_sets"];

    sections.forEach((section) => {
      (Array.isArray(document?.[section]) ? document[section] : []).forEach((item, index) => {
        if (!item || typeof item !== "object" || Array.isArray(item)) return;
        const itemPath = `${section}/${index}`;
        const itemId = item.id;
        if (typeof itemId !== "string" || !itemId) {
          errors.push(`${itemPath}/id: item id must be a non-empty string`);
          return;
        }
        if (identifiers.has(itemId)) {
          errors.push(`${itemPath}/id: duplicate id ${JSON.stringify(itemId)}; already used at ${identifiers.get(itemId)}`);
        } else {
          identifiers.set(itemId, itemPath);
        }
        if (section === "data_sources") sourceIds.add(itemId);
        if (section === "data_sets") dataSetIds.add(itemId);
      });
    });

    sections.forEach((section) => {
      (Array.isArray(document?.[section]) ? document[section] : []).forEach((item, index) => {
        if (!item || typeof item !== "object" || Array.isArray(item)) return;
        const itemPath = `${section}/${index}`;
        const references = section === "data_sets"
          ? item.parent_data_sources
          : section === "data_sources"
            ? item.input_data_sets
            : item.attached_data_sources;
        const knownIds = section === "data_sources" ? dataSetIds : sourceIds;
        const referenceField = section === "data_sets"
          ? "parent_data_sources"
          : section === "data_sources"
            ? "input_data_sets"
            : "attached_data_sources";
        (Array.isArray(references) ? references : []).forEach((reference, referenceIndex) => {
          if (typeof reference !== "string" || !knownIds.has(reference)) {
            errors.push(`${itemPath}/${referenceField}/${referenceIndex}: unknown ${section === "data_sources" ? "data set" : "data source"} reference ${JSON.stringify(reference)}`);
          }
        });
      });
    });

    if (typeof document?.date === "string") {
      const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(document.date);
      if (match) {
        const parsed = new Date(`${document.date}T00:00:00Z`);
        if (Number.isNaN(parsed.valueOf())
          || parsed.getUTCFullYear() !== Number(match[1])
          || parsed.getUTCMonth() + 1 !== Number(match[2])
          || parsed.getUTCDate() !== Number(match[3])) {
          errors.push("date: must be a real calendar date in YYYY-MM-DD format");
        }
      }
    }
    return errors;
  };

  const reportFromErrors = (errors) => errors.map((error) => ({
    path: error.instancePath || "",
    message: error.message || "Validation failed.",
    user_message: error.message || "Validation failed.",
    validator: error.keyword || "schema",
    schema_path: error.schemaPath || "",
  }));

  const responseFromReport = (report) => new Response(JSON.stringify(report), {
    status: 200,
    headers: {"Content-Type": "application/json"},
  });

  window.R3XARuntime = {
    mode: "static",
    loadSchema: () => loadAsset("schema.json"),
    loadSchemaSummary: () => loadAsset("schema-summary.json"),
    loadSchemaCatalog: () => loadAsset("schema-catalog.json"),
    loadUiCatalog: () => loadAsset("ui-catalog.json"),
    loadProfiles: async () => (await loadAsset("ui-catalog.json")).profiles || {},
    validateDocument: async (payload) => {
      const {validate} = await loadValidator();
      const valid = validate(payload);
      const errors = reportFromErrors(validate.errors || []);
      if (valid) {
        integrityErrors(payload).forEach((message) => {
          const [path, detail] = message.split(": ", 2);
          errors.push({
            path: detail === undefined ? "" : path,
            message: detail === undefined ? message : detail,
            user_message: detail === undefined ? message : detail,
            validator: "integrity",
            schema_path: "#/integrity",
          });
        });
      }
      return responseFromReport({valid: errors.length === 0, errors});
    },
    validateItem: async (item, kind = "") => {
      const {validate} = await loadValidator();
      const catalog = await loadCatalog();
      const itemKind = kind || item?.kind;
      const section = typeof itemKind === "string" ? itemKind.split("/", 1)[0] : "";
      if (!["settings", "data_sources", "data_sets"].includes(section)) {
        return unavailable("A Registry item kind must identify settings, data_sources, or data_sets.");
      }
      const document = {
        title: "Registry item",
        description: "Registry item validation",
        version: catalog.schema_version,
        authors: [{name: "Registry validator"}],
        date: "2026-09-17",
        settings: [],
        data_sources: [],
        data_sets: [],
      };
      document[section] = [item];
      const valid = validate(document);
      return responseFromReport({valid, errors: reportFromErrors(validate.errors || [])});
    },
    renderGraph: async () => unavailable("Static graph rendering is not available yet."),
    integrityErrors,
  };
})();
