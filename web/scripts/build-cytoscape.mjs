import {build} from "esbuild";

const [entryPoint, outputFile] = process.argv.slice(2);
if (!entryPoint || !outputFile) {
  throw new Error("Usage: build-cytoscape.mjs ENTRY_POINT OUTPUT_FILE");
}

await build({
  entryPoints: [entryPoint],
  outfile: outputFile,
  bundle: true,
  format: "esm",
  platform: "browser",
  target: "es2020",
  legalComments: "eof",
  minify: false,
});
