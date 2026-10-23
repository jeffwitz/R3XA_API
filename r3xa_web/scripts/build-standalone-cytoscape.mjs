import {build} from "esbuild";
import {appendFile, readFile} from "node:fs/promises";

const [entryPoint, outputFile] = process.argv.slice(2);
if (!entryPoint || !outputFile) {
  throw new Error("Usage: node build-standalone-cytoscape.mjs ENTRY_POINT OUTPUT_FILE");
}

await build({
  entryPoints: [entryPoint],
  outfile: outputFile,
  bundle: true,
  format: "iife",
  globalName: "R3XAStandaloneGraph",
  platform: "browser",
  target: "es2020",
  legalComments: "eof",
  minify: true,
});

const licensePath = new URL("../node_modules/cytoscape/LICENSE", import.meta.url);
const license = await readFile(licensePath, "utf8");
await appendFile(outputFile, `\n/* Cytoscape.js license\n${license}\n*/\n`);
