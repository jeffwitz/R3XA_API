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
const documentSchema = {...schema, $id: "r3xa-document"};
ajv.addSchema(documentSchema, "r3xa-document");
const registrySchemas = {};
const registryEntries = [];
for (const section of ["settings", "data_sources", "data_sets"]) {
  for (const kind of Object.keys(schema.$defs?.[section] || {})) {
    const exportName = `registry_${section}_${kind}`;
    const schemaId = `r3xa-${exportName}`;
    ajv.addSchema({
      $id: schemaId,
      $ref: `#/$defs/${section}/${kind}`,
      $defs: schema.$defs,
    }, exportName);
    registrySchemas[exportName] = exportName;
    registryEntries.push({kind: `${section}/${kind}`, exportName});
  }
}
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
const moduleCode = standaloneCode(ajv, {
  validate: "r3xa-document",
  ...registrySchemas,
}).replace(
  'require("ajv/dist/runtime/ucs2length").default',
  "ucs2length",
);
const registryMap = registryEntries
  .map(({kind, exportName}) => `  ${JSON.stringify(kind)}: ${exportName}`)
  .join(",\n");
await writeFile(outputPath, `${ucs2length}${moduleCode}

const registryValidators = {
${registryMap}
};

export const registryKinds = Object.keys(registryValidators);

export function validateRegistryItem(item, kind) {
  const validator = registryValidators[kind];
  if (!validator) {
    validateRegistryItem.errors = [{
      instancePath: "",
      keyword: "kind",
      params: {kind},
      message: "must be a supported Registry item kind",
    }];
    return false;
  }
  const valid = validator(item);
  validateRegistryItem.errors = validator.errors;
  return valid;
}
`, "utf8");
