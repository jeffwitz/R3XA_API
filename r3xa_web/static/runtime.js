(() => {
  const config = window.R3XA_RUNTIME_CONFIG || {};
  const apiBase = String(config.apiBase || "/api").replace(/\/$/, "");

  const request = (path, options = {}) => fetch(`${apiBase}${path}`, options);

  const getJson = async (path) => {
    const response = await request(path);
    if (!response.ok) throw new Error(`Request failed (${response.status})`);
    return response.json();
  };

  const postJson = (path, payload) => request(path, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  });

  const renderGraph = (payload, options = {}) => {
    const query = new URLSearchParams({
      show_description: options.showDescription === false ? "false" : "true",
      palette: options.palette || "document",
      backend: options.backend || "graphviz-wasm",
      relations: options.relations || "all",
    });
    return postJson(`/graph?${query.toString()}`, payload);
  };

  window.R3XARuntime = {
    mode: "server",
    graphBackends: ["graphviz-wasm", "graphviz", "pyvis", "matplotlib"],
    request,
    loadSchema: () => getJson("/schema"),
    loadSchemaSummary: () => getJson("/schema/summary"),
    loadSchemaCatalog: () => getJson("/schema/catalog"),
    loadUiCatalog: () => getJson("/ui"),
    loadProfiles: () => getJson("/profiles"),
    validateDocument: (payload) => postJson("/validate", payload),
    validateItem: (item, kind = "") => postJson("/registry/validate", {
      item,
      ...(kind ? {kind} : {}),
    }),
    renderGraph,
  };
})();
