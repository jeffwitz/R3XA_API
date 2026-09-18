import test from "node:test";
import assert from "node:assert/strict";

import {buildDot, buildGraphModel} from "../static/graph-core.mjs";

const document = {
  settings: [{id: "stg-rig", title: "Stereo rig", attached_data_sources: ["src-camera"]}],
  data_sources: [
    {id: "src-camera", title: "Camera", input_data_sets: ["set-images"]},
  ],
  data_sets: [{id: "set-images", title: "Images", parent_data_sources: ["src-camera"]}],
};

test("graph model preserves R3XA dependency roles", () => {
  const model = buildGraphModel(document);

  assert.deepEqual(model.settingIds, ["stg-rig"]);
  assert.deepEqual(model.sourceIds, ["src-camera"]);
  assert.deepEqual(model.dataSetIds, ["set-images"]);
  assert.deepEqual(model.intermediateSources, ["src-camera"]);
  assert.deepEqual(model.usedDatasets, ["set-images"]);
  assert.deepEqual(model.edgeRecords, [
    {src: "stg-rig", dst: "src-camera", styleKey: "setting"},
    {src: "set-images", dst: "src-camera", styleKey: "input"},
    {src: "src-camera", dst: "set-images", styleKey: "data"},
  ]);
});

test("graph DOT output uses node labels and palette styles", () => {
  const dot = buildDot(document, {includeDescription: false}, {
    settings: {root: {shape: "hexagon", color: "ochre"}},
    data_sources: {
      initial: {shape: "ellipse", color: "crimson"},
      intermediate: {shape: "ellipse", color: "crimson-dark"},
    },
    data_sets: {
      initial: {shape: "box", color: "teal"},
      intermediate: {shape: "box", color: "teal"},
      final: {shape: "box", color: "teal-dark"},
    },
    edges: {setting: {}, input: {}, data: {}, data_initial: {}},
  });

  assert.match(dot, /"stg-rig"/);
  assert.match(dot, /label="Stereo rig"/);
  assert.match(dot, /shape="hexagon"/);
  assert.match(dot, /"src-camera"/);
  assert.match(dot, /"set-images"/);
});
