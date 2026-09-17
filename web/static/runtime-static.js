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

  window.R3XARuntime = {
    mode: "static",
    loadSchema: () => loadAsset("schema.json"),
    loadSchemaSummary: () => loadAsset("schema-summary.json"),
    loadSchemaCatalog: () => loadAsset("schema-catalog.json"),
    loadUiCatalog: () => loadAsset("ui-catalog.json"),
    loadProfiles: async () => (await loadAsset("ui-catalog.json")).profiles || {},
    validateDocument: async () => unavailable("Static document validation is not available yet."),
    validateItem: async () => unavailable("Static Registry validation is not available yet."),
    renderGraph: async () => unavailable("Static graph rendering is not available yet."),
  };
})();
