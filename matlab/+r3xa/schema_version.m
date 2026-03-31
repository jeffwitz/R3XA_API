function version = schema_version(schema_path)
%SCHEMA_VERSION Read schema version from packaged schema location.
if nargin < 1 || isempty(schema_path)
    here = fileparts(mfilename("fullpath"));
    repo_root = fileparts(fileparts(here));
    schema_path = fullfile(repo_root, "r3xa_api", "resources", "schema.json");
end
if ~isfile(schema_path)
    error("r3xa:schemaNotFound", "Schema file not found: %s", schema_path);
end
schema = jsondecode(fileread(schema_path));
version = "";
if isfield(schema, "properties") && isfield(schema.properties, "version")
    version = string(schema.properties.version.const);
end
end
