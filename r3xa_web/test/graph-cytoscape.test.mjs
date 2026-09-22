import test from "node:test";
import assert from "node:assert/strict";

import {resolveNodeOverlaps, styleFor} from "../static/graph-cytoscape.mjs";

test("Cytoscape uses dark text when a legacy palette omits fontcolor", () => {
  assert.equal(styleFor({fillcolor: "white"}).text, "#000000");
  assert.equal(styleFor({fillcolor: "#9a6636", fontcolor: "#ffffff"}).text, "#ffffff");
});

test("Cytoscape separates nodes enlarged beyond their Graphviz bounds", () => {
  const positions = resolveNodeOverlaps(
    [
      {id: "setting", width: 72, height: 42},
      {id: "source", width: 260, height: 64},
    ],
    {
      setting: {x: 0, y: 0},
      source: {x: 150, y: 0},
    },
  );
  assert.ok(Math.abs(positions.source.x - positions.setting.x) >= (72 + 260) * 0.5 + 12);
});
