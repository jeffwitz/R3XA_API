import {readFile, writeFile} from "node:fs/promises";
import Ajv2020 from "ajv/dist/2020.js";
import standaloneCode from "ajv/dist/standalone/index.js";

const [schemaPath, outputPath] = process.argv.slice(2);
if (!schemaPath || !outputPath) {
  throw new Error("Usage: node scripts/build-validator.mjs SCHEMA OUTPUT");
}

const schema = JSON.parse(await readFile(schemaPath, "utf8"));
const ajv = new Ajv2020({
  allErrors: true,
  code: {esm: true, source: true},
  strict: false,
  validateFormats: false,
});
const validate = ajv.compile(schema);
const ucs2length = `const ucs2length = (str) => {
  let length = str.length;
  let index = length;
  let result = 0;
  while (index) {
    const first = str.charCodeAt(length - index);
    index -= 1;
    if (first >= 0xd800 && first <= 0xdbff && index) {
      const second = str.charCodeAt(length - index);
      if (second >= 0xdc00 && second <= 0xdfff) index -= 1;
    }
    result += 1;
  }
  return result;
};
`;
const moduleCode = standaloneCode(ajv, validate).replace(
  'require("ajv/dist/runtime/ucs2length").default',
  "ucs2length",
);
await writeFile(outputPath, `${ucs2length}${moduleCode}\n`, "utf8");
