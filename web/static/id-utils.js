(function attachR3XAIdUtils(global) {
  const sectionPrefixes = {
    settings: "stg",
    data_sources: "src",
    data_sets: "set",
  };
  const relationshipFields = ["parent_data_sources", "attached_data_sources", "input_data_sets"];

  const prefixForKind = (kind) => {
    const [section, kindName] = String(kind || "").split("/");
    return `${sectionPrefixes[section] || "r3xa"}-${kindName || "item"}-`;
  };

  const hasCanonicalId = (item) => typeof item?.id === "string"
    && item.id.startsWith(prefixForKind(item.kind));

  const makeId = (kind, used = new Set()) => {
    let identifier;
    do {
      const random = global.crypto?.randomUUID?.().replaceAll("-", "").slice(0, 12)
        || Math.random().toString(36).slice(2, 14);
      identifier = `${prefixForKind(kind)}${random}`;
    } while (used.has(identifier));
    return identifier;
  };

  const itemsInPayload = (payload) => [
    ...(payload?.settings || []),
    ...(payload?.data_sources || []),
    ...(payload?.data_sets || []),
  ];

  const duplicateIds = (items) => {
    const counts = new Map();
    items.forEach((item) => {
      if (item?.id) counts.set(item.id, (counts.get(item.id) || 0) + 1);
    });
    return [...counts.entries()].filter(([, count]) => count > 1).map(([id]) => id);
  };

  const normalizeItems = (items) => {
    const duplicates = duplicateIds(items);
    if (duplicates.length) {
      return {items, replacements: new Map(), conflicts: duplicates, changed: false};
    }

    const used = new Set(items.map((item) => item?.id).filter(Boolean));
    const replacements = new Map();
    const normalized = items.map((item) => {
      const copy = JSON.parse(JSON.stringify(item));
      if (!hasCanonicalId(copy)) {
        const oldId = copy.id;
        copy.id = makeId(copy.kind, used);
        used.add(copy.id);
        if (oldId) replacements.set(oldId, copy.id);
      }
      return copy;
    });
    normalized.forEach((item) => {
      relationshipFields.forEach((field) => {
        if (Array.isArray(item[field])) {
          item[field] = item[field].map((reference) => replacements.get(reference) || reference);
        }
      });
    });
    return {
      items: normalized,
      replacements,
      conflicts: [],
      changed: JSON.stringify(normalized) !== JSON.stringify(items),
    };
  };

  const normalizeDocumentIds = (payload) => {
    const originalItems = itemsInPayload(payload);
    const result = normalizeItems(originalItems);
    if (result.conflicts.length) return result;

    let offset = 0;
    ["settings", "data_sources", "data_sets"].forEach((section) => {
      const count = payload?.[section]?.length || 0;
      if (count) payload[section] = result.items.slice(offset, offset + count);
      offset += count;
    });
    return result;
  };

  const normalizeLocalRegistryItems = (items) => normalizeItems(items);

  global.R3XAIdUtils = Object.freeze({
    hasCanonicalId,
    makeId,
    normalizeDocumentIds,
    normalizeLocalRegistryItems,
    prefixForKind,
    relationshipFields,
  });
})(window);
