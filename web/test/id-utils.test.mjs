import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {runInNewContext} from "node:vm";

const source = readFileSync(new URL("../static/id-utils.js", import.meta.url), "utf8");

const loadUtils = () => {
  const window = {
    crypto: {randomUUID: () => "11111111-2222-3333-4444-555555555555"},
  };
  runInNewContext(source, {window, Math});
  return window.R3XAIdUtils;
};

test("ID utilities generate canonical section prefixes", () => {
  const utils = loadUtils();

  assert.equal(utils.prefixForKind("settings/specimen"), "stg-specimen-");
  assert.equal(utils.prefixForKind("data_sources/camera"), "src-camera-");
  assert.equal(utils.prefixForKind("data_sets/file"), "set-file-");
  assert.equal(utils.makeId("data_sources/camera", new Set()), "src-camera-111111112222");
  assert.equal(utils.hasCanonicalId({kind: "data_sources/camera", id: "src-camera-abc"}), true);
});

test("ID migration remaps relationships and preserves duplicate conflicts", () => {
  const utils = loadUtils();
  const items = [
    {id: "camera", kind: "data_sources/camera", title: "Camera"},
    {id: "images", kind: "data_sets/list", parent_data_sources: ["camera"]},
  ];
  const normalized = utils.normalizeLocalRegistryItems(items);

  assert.equal(normalized.conflicts.length, 0);
  assert.equal(normalized.items[0].id, "src-camera-111111112222");
  assert.equal(normalized.items[1].id, "set-list-111111112222");
  assert.deepEqual(
    JSON.parse(JSON.stringify(normalized.items[1].parent_data_sources)),
    [normalized.items[0].id],
  );

  const conflict = utils.normalizeLocalRegistryItems([
    {id: "duplicate", kind: "data_sources/camera"},
    {id: "duplicate", kind: "data_sets/list"},
  ]);
  assert.deepEqual(JSON.parse(JSON.stringify(conflict.conflicts)), ["duplicate"]);
  assert.deepEqual(conflict.items[0].id, "duplicate");
});
