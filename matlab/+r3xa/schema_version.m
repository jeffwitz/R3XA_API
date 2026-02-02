function version = schema_version(schema_path)
%SCHEMA_VERSION Read the schema version from resources/schema.json.
if nargin < 1 || isempty(schema_path)
    here = fileparts(mfilename("fullpath"));
    repo_root = fileparts(fileparts(here));
    schema_path = fullfile(repo_root, "resources", "schema.json");
end
schema = jsondecode(fileread(schema_path));
version = "";
if isfield(schema, "properties") && isfield(schema.properties, "version")
    version = string(schema.properties.version.const);
end
end
