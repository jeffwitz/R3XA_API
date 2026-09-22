(function attachR3XARegistryStorage(global) {
  const storageKey = "r3xaLocalRegistryItems";
  const formatVersion = 1;

  const read = () => {
    const raw = global.localStorage.getItem(storageKey);
    if (!raw) return {items: [], migrated: false, corrupt: false, error: ""};
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        return {
          items: parsed.filter((item) => item && typeof item === "object"),
          migrated: true,
          corrupt: false,
          error: "",
        };
      }
      if (parsed && parsed.format_version === formatVersion && Array.isArray(parsed.items)) {
        return {
          items: parsed.items.filter((item) => item && typeof item === "object"),
          migrated: false,
          corrupt: false,
          error: "",
        };
      }
      return {items: [], migrated: false, corrupt: true, error: "Unsupported local Registry storage format."};
    } catch (error) {
      return {items: [], migrated: false, corrupt: true, error: `Local Registry storage is corrupt: ${error.message}`};
    }
  };

  const write = (items, schemaVersion = "") => {
    const envelope = {
      format_version: formatVersion,
      schema_version: schemaVersion || "",
      updated_at: new Date().toISOString(),
      items,
    };
    try {
      global.localStorage.setItem(storageKey, JSON.stringify(envelope));
      return {ok: true, error: ""};
    } catch (error) {
      return {ok: false, error: `Local Registry could not be saved: ${error.message}`};
    }
  };

  global.R3XARegistryStorage = Object.freeze({formatVersion, read, write});
})(window);
