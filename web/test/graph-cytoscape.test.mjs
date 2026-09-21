import test from "node:test";
import assert from "node:assert/strict";

import {styleFor} from "../static/graph-cytoscape.mjs";

test("Cytoscape uses dark text when a legacy palette omits fontcolor", () => {
  assert.equal(styleFor({fillcolor: "white"}).text, "#000000");
  assert.equal(styleFor({fillcolor: "#9a6636", fontcolor: "#ffffff"}).text, "#ffffff");
});
