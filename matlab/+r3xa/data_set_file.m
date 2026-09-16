function payload = data_set_file(filename, varargin)
%DATA_SET_FILE Create a data_set_file payload.
if mod(numel(varargin), 2) ~= 0
    error("data_set_file:NameValue", "Extra fields must be name/value pairs.");
end
payload = struct( ...
    "kind", "data_set_file", ...
    "filename", filename ...
);
for i = 1:2:numel(varargin)
    field = varargin{i};
    value = varargin{i + 1};
    if ~ischar(field) && ~isstring(field)
        error("data_set_file:NameValue", "Field names must be strings.");
    end
    field = char(field);
    payload.(field) = value;
end
end
