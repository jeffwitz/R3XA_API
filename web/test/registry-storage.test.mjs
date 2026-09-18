import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {runInNewContext} from "node:vm";

const source = readFileSync(new URL("../static/registry-storage.js", import.meta.url), "utf8");

const loadStorage = (initial = null) => {
  const values = new Map(initial ? [["r3xaLocalRegistryItems", initial]] : []);
  const localStorage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)),
  };
  const window = {localStorage};
  runInNewContext(source, {window, Date});
  return {storage: window.R3XARegistryStorage, values};
};

test("Registry storage writes a versioned local envelope", () => {
  const {storage, values} = loadStorage();
  const items = [{id: "src-camera-example", kind: "data_sources/camera"}];

  assert.deepEqual(JSON.parse(JSON.stringify(storage.read())), {items: [], migrated: false, corrupt: false, error: ""});
  assert.equal(storage.write(items, "2026.9.18").ok, true);
  const stored = JSON.parse(values.get("r3xaLocalRegistryItems"));
  assert.equal(stored.format_version, storage.formatVersion);
  assert.equal(stored.schema_version, "2026.9.18");
  assert.deepEqual(JSON.parse(JSON.stringify(storage.read().items)), items);
});

test("Registry storage detects legacy and corrupt values", () => {
  const legacy = JSON.stringify([{id: "src-camera-example"}]);
  assert.equal(loadStorage(legacy).storage.read().migrated, true);

  const corrupt = loadStorage("not-json").storage.read();
  assert.equal(corrupt.corrupt, true);
  assert.match(corrupt.error, /corrupt/i);
});
