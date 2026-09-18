(() => {
  const script = document.currentScript;
  const assetBase = String(script?.dataset?.assetBase || ".").replace(/\/$/, "");
  const assetVersion = String(script?.dataset?.assetVersion || "");
  const assetUrl = (name) => `${assetBase}/${name}${assetVersion ? `?v=${encodeURIComponent(assetVersion)}` : ""}`;

  const loadAsset = async (name) => {
    const response = await fetch(assetUrl(name));
    if (!response.ok) throw new Error(`Unable to load ${name} (${response.status})`);
    return response.json();
  };

  const unavailable = (message) => new Response(JSON.stringify({
    detail: message,
    valid: false,
    errors: [message],
  }), {
    status: 503,
    headers: {"Content-Type": "application/json"},
  });

  let validatorPromise;
  let catalogPromise;
  let graphPalettePromise;
  let graphPromise;
  const loadValidator = () => {
    validatorPromise ||= import(assetUrl("validator.generated.js"));
    return validatorPromise;
  };

  const loadCatalog = () => {
    catalogPromise ||= loadAsset("schema-catalog.json");
    return catalogPromise;
  };

  const loadGraphPalettes = () => {
    graphPalettePromise ||= loadAsset("graph-palettes.json");
    return graphPalettePromise;
  };

  const loadGraph = () => {
    graphPromise ||= import(assetUrl("graph.generated.js"));
    return graphPromise;
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

  const friendlyMessage = (error) => {
    const params = error.params || {};
    if (error.keyword === "required") {
      return `Add the required field '${params.missingProperty || "information"}'.`;
    }
    if (error.keyword === "type") {
      const expected = Array.isArray(params.type) ? params.type.join(", ") : params.type;
      return `Enter a value of type '${expected}'.`;
    }
    if (error.keyword === "enum") {
      return `Choose one of: ${(params.allowedValues || []).join(", ")}.`;
    }
    if (error.keyword === "const") {
      return `Use the required value '${params.allowedValue}'.`;
    }
    if (error.keyword === "pattern") return "Use the expected text format.";
    if (error.keyword === "minLength") return `Enter at least ${params.limit} character(s).`;
    if (error.keyword === "minItems") return `Add at least ${params.limit} item(s).`;
    if (error.keyword === "maxItems") return `Use no more than ${params.limit} item(s).`;
    if (["minimum", "exclusiveMinimum"].includes(error.keyword)) {
      return `Enter a value greater than or equal to ${params.limit}.`;
    }
    if (["maximum", "exclusiveMaximum"].includes(error.keyword)) {
      return `Enter a value less than or equal to ${params.limit}.`;
    }
    if (error.keyword === "additionalProperties") {
      return "Remove unsupported fields before continuing.";
    }
    if (["anyOf", "oneOf"].includes(error.keyword)) return "Choose a valid value.";
    return error.message || "Validation failed.";
  };

  const reportFromErrors = (errors) => {
    const combinators = errors.filter((error) => ["anyOf", "oneOf"].includes(error.keyword));
    const relevantErrors = errors.filter((error) => {
      if (["anyOf", "oneOf"].includes(error.keyword)) return true;
      const errorPath = error.instancePath || "";
      return !combinators.some((combinator) => {
        const combinatorPath = combinator.instancePath || "";
        return errorPath === combinatorPath || errorPath.startsWith(`${combinatorPath}/`);
      });
    });
    return relevantErrors.map((error) => ({
      path: (error.instancePath || "").replace(/^\/+/, ""),
      message: error.message || "Validation failed.",
      user_message: friendlyMessage(error),
      validator: error.keyword || "schema",
      schema_path: error.schemaPath || "",
    }));
  };

  const responseFromReport = (report) => new Response(JSON.stringify(report), {
    status: 200,
    headers: {"Content-Type": "application/json"},
  });

  window.R3XARuntime = {
    mode: "static",
    graphBackends: ["graphviz"],
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
      const {validateRegistryItem} = await loadValidator();
      const itemKind = kind || item?.kind;
      const valid = validateRegistryItem(item, itemKind);
      return responseFromReport({valid, errors: reportFromErrors(validateRegistryItem.errors || [])});
    },
    renderGraph: async (payload, options = {}) => {
      if ((options.backend || "graphviz") !== "graphviz") {
        return unavailable("The static WebUI supports Graphviz SVG rendering in the browser. Select the Graphviz backend.");
      }
      try {
        const [{renderGraph}, palettes] = await Promise.all([loadGraph(), loadGraphPalettes()]);
        const svg = await renderGraph(payload, {
          includeDescription: options.showDescription !== false,
          palette: options.palette || "document",
        }, palettes);
        return new Response(svg, {
          status: 200,
          headers: {
            "Content-Type": "image/svg+xml",
            "X-R3XA-Graph-Backend": "graphviz",
          },
        });
      } catch (error) {
        return unavailable(`Graphviz WASM rendering failed: ${error.message || error}`);
      }
    },
    integrityErrors,
  };
})();
